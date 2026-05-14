<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { AlertCircle, ChevronDown, RefreshCw } from "lucide-vue-next";
import { NButton, NTag } from "naive-ui";
import ModelPickerDialog from "@/components/ModelPickerDialog.vue";
import ToolCall from "@/components/ToolCall.vue";
import type { ToolEntry } from "@/components/ToolCall.vue";
import { GatewayClient, type ConnectionState } from "@/lib/gatewayClient";

const props = defineProps<{
  channel: string;
  className?: string;
}>();
const TOOL_LIMIT = 20;

const STATE_LABEL: Record<ConnectionState, string> = {
  idle: "idle",
  connecting: "connecting",
  open: "live",
  closed: "closed",
  error: "error",
};

const STATE_TONE: Record<ConnectionState, string> = {
  idle: "bg-muted text-muted-foreground",
  connecting: "bg-primary/10 text-primary",
  open: "bg-emerald-500/10 text-emerald-500 dark:text-emerald-400",
  closed: "bg-muted text-muted-foreground",
  error: "bg-destructive/10 text-destructive",
};

interface SessionInfo {
  cwd?: string;
  model?: string;
  provider?: string;
  credential_warning?: string;
}

interface RpcEnvelope {
  method?: string;
  params?: { type?: string; payload?: unknown };
}

const version = ref(0);
let gw: GatewayClient;

const state = ref<ConnectionState>("idle");
const sessionId = ref<string | null>(null);
const info = ref<SessionInfo>({});
const tools = ref<ToolEntry[]>([]);
const modelOpen = ref(false);
const error = ref<string | null>(null);
let eventsWs: WebSocket | null = null;
let unmountingEvents = false;
let cancelledSidecar = false;

function createGw() {
  return new GatewayClient();
}

function reconnect() {
  error.value = null;
  tools.value = [];
  version.value = version.value + 1;
}

const canPickModel = computed(() => state.value === "open" && !!sessionId.value);
const modelLabel = computed(() => (info.value.model ?? "—").split("/").slice(-1)[0] ?? "—");
const banner = computed(() => error.value ?? info.value.credential_warning ?? null);

function onModelSubmit(slashCommand: string) {
  if (!sessionId.value) return;
  void gw.request("slash.exec", {
    session_id: sessionId.value,
    command: slashCommand,
  });
  modelOpen.value = false;
}

/* ---- Sidecar WebSocket ---- */

function setupSidecar(gwInstance: GatewayClient) {
  cancelledSidecar = false;

  const offState = gwInstance.onState((s) => {
    state.value = s;
  });

  const offSessionInfo = gwInstance.on<SessionInfo & { session_id?: string }>("session.info", (ev) => {
    if (ev.session_id) {
      sessionId.value = ev.session_id;
    }
    if (ev.payload) {
      info.value = { ...info.value, ...ev.payload };
    }
  });

  const offError = gwInstance.on<{ message?: string }>("error", (ev) => {
    const msg = ev.payload?.message;
    if (msg) {
      error.value = msg;
    }
  });

  gwInstance.connect()
    .then(() => {
      if (cancelledSidecar) return;
      return gwInstance.request<{ session_id: string }>("session.create", {});
    })
    .then((created) => {
      if (cancelledSidecar || !created?.session_id) return;
      sessionId.value = created.session_id;
    })
    .catch((e: Error) => {
      if (!cancelledSidecar) {
        error.value = e.message;
      }
    });

  return () => {
    cancelledSidecar = true;
    offState();
    offSessionInfo();
    offError();
    gwInstance.close();
  };
}

let cleanupSidecar: (() => void) | null = null;

onMounted(async () => {
  gw = createGw();
  cleanupSidecar = setupSidecar(gw);
});

/* ---- Event subscriber WebSocket ---- */

function setupEvents(channel: string) {
  const token = window.__ANYDEALS_SESSION_TOKEN__;
  if (!token || !channel) return;

  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const qs = new URLSearchParams({ token, channel });
  const ws = new WebSocket(
    `${proto}//${window.location.host}/api/events?${qs.toString()}`,
  );
  eventsWs = ws;

  const DISCONNECTED = "events feed disconnected — tool calls may not appear";

  ws.addEventListener("error", () => {
    if (!unmountingEvents) error.value = DISCONNECTED;
  });

  ws.addEventListener("close", (ev) => {
    if (ev.code === 4401 || ev.code === 4403) {
      if (!unmountingEvents) error.value = `events feed rejected (${ev.code}) — reload the page`;
    } else if (ev.code !== 1000 && !unmountingEvents) {
      error.value = DISCONNECTED;
    }
  });

  ws.addEventListener("message", (ev) => {
    let frame: RpcEnvelope;
    try {
      frame = JSON.parse(ev.data);
    } catch {
      return;
    }
    if (frame.method !== "event" || !frame.params) return;

    const { type, payload } = frame.params;

    if (type === "tool.start") {
      const p = payload as { tool_id?: string; name?: string; context?: string } | undefined;
      const toolId = p?.tool_id;
      if (!toolId) return;
      tools.value = [
        ...tools.value,
        {
          kind: "tool" as const,
          id: `tool-${toolId}-${tools.value.length}`,
          tool_id: toolId,
          name: p?.name ?? "tool",
          context: p?.context,
          status: "running" as const,
          startedAt: Date.now(),
        },
      ].slice(-TOOL_LIMIT);
    } else if (type === "tool.progress") {
      const p = payload as { name?: string; preview?: string } | undefined;
      if (!p?.name || !p.preview) return;
      tools.value = tools.value.map((t) =>
        t.status === "running" && t.name === p.name
          ? { ...t, preview: p.preview }
          : t,
      );
    } else if (type === "tool.complete") {
      const p = payload as {
        tool_id?: string;
        summary?: string;
        error?: string;
        inline_diff?: string;
      } | undefined;
      if (!p?.tool_id) return;
      tools.value = tools.value.map((t) =>
        t.tool_id === p.tool_id
          ? {
              ...t,
              status: p.error ? "error" : "done",
              summary: p.summary,
              error: p.error,
              inline_diff: p.inline_diff,
              completedAt: Date.now(),
            }
          : t,
      );
    }
  });
}

onMounted(() => {
  setupEvents(props.channel);
});

onUnmounted(() => {
  unmountingEvents = true;
  eventsWs?.close();
  eventsWs = null;
  cleanupSidecar?.();
});
</script>

<template>
  <aside
    class="flex h-full w-full min-w-0 shrink-0 flex-col gap-3 normal-case lg:w-80"
    :class="className"
  >
    <!-- Model card -->
    <div class="border border-border bg-card flex items-center justify-between gap-2 px-3 py-2">
      <div class="min-w-0">
        <div class="text-xs uppercase tracking-wider text-muted-foreground">model</div>
        <button
          type="button"
          :disabled="!canPickModel"
          class="flex items-center gap-1 truncate text-sm font-medium hover:underline disabled:cursor-not-allowed disabled:opacity-60 disabled:no-underline cursor-pointer"
          :title="info.model ?? 'switch model'"
          @click="modelOpen = true"
        >
          <span class="truncate">{{ modelLabel }}</span>
          <ChevronDown v-if="canPickModel" class="h-3 w-3 shrink-0 opacity-60" />
        </button>
      </div>
      <NTag :bordered="true" size="small" :class="STATE_TONE[state]">
        {{ STATE_LABEL[state] }}
      </NTag>
    </div>

    <!-- Error banner -->
    <div
      v-if="banner"
      class="border border-destructive/40 bg-destructive/5 flex items-start gap-2 px-3 py-2 text-xs"
    >
      <AlertCircle class="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
      <div class="min-w-0 flex-1">
        <div class="wrap-break-word text-destructive">{{ banner }}</div>
        <NButton
          v-if="error"
          size="tiny"
          class="mt-1"
          @click="reconnect"
        >
          <template #icon><RefreshCw class="h-3 w-3" /></template>
          reconnect
        </NButton>
      </div>
    </div>

    <!-- Tools list -->
    <div class="border border-border bg-card flex min-h-0 flex-1 flex-col px-2 py-2">
      <div class="px-1 pb-2 text-xs uppercase tracking-wider text-muted-foreground">tools</div>
      <div class="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto pr-1">
        <div
          v-if="tools.length === 0"
          class="px-2 py-4 text-center text-xs text-muted-foreground"
        >no tool calls yet</div>
        <ToolCall
          v-for="t in tools"
          :key="t.id"
          :tool="t"
        />
      </div>
    </div>

    <!-- Model picker -->
    <ModelPickerDialog
      v-if="modelOpen && canPickModel && sessionId"
      :gw="gw"
      :sessionId="sessionId"
      @close="modelOpen = false"
      @submit="onModelSubmit"
    />
  </aside>
</template>
