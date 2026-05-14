<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h } from "vue";
import { useRoute } from "vue-router";
import { FitAddon } from "@xterm/addon-fit";
import { Unicode11Addon } from "@xterm/addon-unicode11";
import { WebLinksAddon } from "@xterm/addon-web-links";
import { WebglAddon } from "@xterm/addon-webgl";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import { Copy, PanelRight } from "lucide-vue-next";
import { NButton } from "naive-ui";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";
import ChatSidebar from "@/components/ChatSidebar.vue";
import PluginSlot from "@/components/PluginSlot.vue";

const route = useRoute();
const { t } = useI18n();
const { setEnd } = usePageHeader();

/* ---- Helpers ---- */

function buildWsUrl(token: string, resume: string | null, channel: string): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const qs = new URLSearchParams({ token, channel });
  if (resume) qs.set("resume", resume);
  return `${proto}//${window.location.host}/api/pty?${qs.toString()}`;
}

function generateChannelId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `chat-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
}

const TERMINAL_THEME = {
  background: "#0d2626",
  foreground: "#f0e6d2",
  cursor: "#f0e6d2",
  cursorAccent: "#0d2626",
  selectionBackground: "#f0e6d244",
};

function terminalTierWidthPx(host: HTMLElement | null): number {
  if (typeof window === "undefined") return 1280;
  const fromHost = host?.clientWidth ?? 0;
  if (fromHost > 2) return Math.round(fromHost);
  const doc = document.documentElement?.clientWidth ?? 0;
  const vv = window.visualViewport;
  const inner = window.innerWidth;
  const vvw = vv?.width ?? inner;
  const layout = Math.min(inner, vvw, doc > 0 ? doc : inner);
  return Math.max(1, Math.round(layout));
}

function terminalFontSizeForWidth(layoutWidthPx: number): number {
  if (layoutWidthPx < 300) return 7;
  if (layoutWidthPx < 360) return 8;
  if (layoutWidthPx < 420) return 9;
  if (layoutWidthPx < 520) return 10;
  if (layoutWidthPx < 720) return 11;
  if (layoutWidthPx < 1024) return 12;
  return 14;
}

function terminalLineHeightForWidth(layoutWidthPx: number): number {
  return layoutWidthPx < 1024 ? 1.02 : 1.15;
}

/* ---- State ---- */

const hostRef = ref<HTMLDivElement | null>(null);
const banner = ref<string | null>(
  typeof window !== "undefined" && !window.__ANYDEALS_SESSION_TOKEN__
    ? t("chat.sessionTokenUnavailable")
    : null,
);
const copyState = ref<"idle" | "copied">("idle");
const mobilePanelOpen = ref(false);

const resumeParam = computed(() => (route.query.resume as string) || null);
const channel = generateChannelId();

let term: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let ws: WebSocket | null = null;
let unmounting = false;
let copyResetTimer: ReturnType<typeof setTimeout> | null = null;

/* ---- Narrow detection ---- */

const narrow = ref(
  typeof window !== "undefined"
    ? window.matchMedia("(max-width: 1023px)").matches
    : false,
);

onMounted(() => {
  const mql = window.matchMedia("(max-width: 1023px)");
  const sync = () => { narrow.value = mql.matches; };
  mql.addEventListener("change", sync);
  return () => mql.removeEventListener("change", sync);
});

/* ---- Mobile panel keyboard & overflow ---- */

watch(mobilePanelOpen, (open) => {
  if (!open) return;
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") { mobilePanelOpen.value = false; }
  };
  document.addEventListener("keydown", onKey);
  const prevOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";
  return () => {
    document.removeEventListener("keydown", onKey);
    document.body.style.overflow = prevOverflow;
  };
});

/* ---- Close mobile panel on lg+ ---- */

onMounted(() => {
  const mql = window.matchMedia("(min-width: 1024px)");
  const onChange = (e: MediaQueryListEvent) => {
    if (e.matches) mobilePanelOpen.value = false;
  };
  mql.addEventListener("change", onChange);
  return () => mql.removeEventListener("change", onChange);
});

/* ---- Page header (mobile) ---- */

const modelToolsLabel = computed(
  () => `${t("app.modelToolsSheetTitle")} ${t("app.modelToolsSheetSubtitle")}`,
);

watch([narrow, mobilePanelOpen, modelToolsLabel], () => {
  if (!narrow.value) {
    setEnd(null);
    return;
  }
  setEnd(
    h(
      NButton,
      {
        size: "small",
        onClick: () => { mobilePanelOpen.value = true; },
      },
      {
        default: () => [
          h(PanelRight, { class: "h-3 w-3 shrink-0" }),
          modelToolsLabel.value,
        ],
      },
    ),
  );
}, { immediate: true });

/* ---- Copy last response ---- */

async function handleCopyLast() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  copyState.value = "copied";
  ws.send("/copy\n");
  if (copyResetTimer) clearTimeout(copyResetTimer);
  copyResetTimer = setTimeout(() => {
    copyState.value = "idle";
    copyResetTimer = null;
  }, 2000);
}

/* ---- Terminal setup ---- */

onMounted(() => {
  if (banner.value) return;

  const host = hostRef.value;
  if (!host) return;

  const layoutW = terminalTierWidthPx(host);
  const fontSize = terminalFontSizeForWidth(layoutW);
  const lineHeight = terminalLineHeightForWidth(layoutW);

  // Create terminal
  term = new Terminal({
    allowProposedApi: true,
    allowTransparency: false,
    cursorBlink: true,
    cursorStyle: "bar",
    fontSize,
    lineHeight,
    fontFamily: '"Fira Code", "Cascadia Code", "JetBrains Mono", "SF Mono", "Menlo", monospace',
    theme: TERMINAL_THEME,
    smoothScrollDuration: 60,
  });

  // Addons
  fitAddon = new FitAddon();
  const unicode11Addon = new Unicode11Addon();
  const webLinksAddon = new WebLinksAddon();
  term.loadAddon(fitAddon);
  term.loadAddon(unicode11Addon);
  term.loadAddon(webLinksAddon);

  // WebGL addon: try, fallback to canvas
  try {
    const webglAddon = new WebglAddon();
    term.loadAddon(webglAddon);
  } catch {
    // canvas renderer is the default
  }

  term.unicode.activeVersion = "11";
  term.open(host);

  // Initial fit
  fitAddon.fit();

  // ResizeObserver
  let metricsDebounce: ReturnType<typeof setTimeout> | null = null;
  const syncTerminalMetrics = () => {
    if (!term || !hostRef.value) return;
    const w = terminalTierWidthPx(hostRef.value);
    const fs = terminalFontSizeForWidth(w);
    const lh = terminalLineHeightForWidth(w);
    term.options.fontSize = fs;
    term.options.lineHeight = lh;
  };
  const scheduleSyncTerminalMetrics = () => {
    if (metricsDebounce) clearTimeout(metricsDebounce);
    metricsDebounce = setTimeout(() => {
      syncTerminalMetrics();
      if (fitAddon && term) {
        try { fitAddon.fit(); } catch { /* */ }
      }
      metricsDebounce = null;
    }, 100);
  };

  window.addEventListener("resize", scheduleSyncTerminalMetrics);
  window.visualViewport?.addEventListener("resize", scheduleSyncTerminalMetrics);
  window.visualViewport?.addEventListener("scroll", scheduleSyncTerminalMetrics);

  // ResizeObserver for the terminal host + fit
  let hostSyncRaf: number | null = null;
  let settleRaf1: number | null = null;
  let settleRaf2: number | null = null;

  const ro = new ResizeObserver(() => {
    if (hostSyncRaf) cancelAnimationFrame(hostSyncRaf);
    hostSyncRaf = requestAnimationFrame(() => {
      hostSyncRaf = null;
      syncTerminalMetrics();
      if (fitAddon && term) {
        try {
          fitAddon.fit();
          // Double-fit for layout settling
          if (settleRaf1) cancelAnimationFrame(settleRaf1);
          settleRaf1 = requestAnimationFrame(() => {
            settleRaf1 = null;
            try { fitAddon!.fit(); } catch { /* */ }
            if (settleRaf2) cancelAnimationFrame(settleRaf2);
            settleRaf2 = requestAnimationFrame(() => {
              settleRaf2 = null;
              try { fitAddon!.fit(); } catch { /* */ }
            });
          });
        } catch { /* */ }
      }
    });
  });
  ro.observe(host);

  // WebSocket connection
  const token = window.__ANYDEALS_SESSION_TOKEN__ ?? "";
  const wsUrl = buildWsUrl(token, resumeParam.value, channel);
  const socket = new WebSocket(wsUrl);
  ws = socket;

  socket.addEventListener("open", () => {
    if (unmounting || !term) return;
    term.focus();
    try { fitAddon?.fit(); } catch { /* */ }
  });

  socket.addEventListener("message", (ev) => {
    if (unmounting || !term) return;
    if (ev.data instanceof ArrayBuffer) {
      term.write(new Uint8Array(ev.data));
    } else if (typeof ev.data === "string") {
      term.write(ev.data);
    }
  });

  socket.addEventListener("error", () => {
    if (!unmounting) {
      term?.write("\r\n\n[PTY WebSocket error — connection lost]\r\n");
    }
  });

  socket.addEventListener("close", () => {
    if (!unmounting) {
      term?.write("\r\n\n[PTY WebSocket closed]\r\n");
    }
  });

  // Terminal → WebSocket (with SGR mouse dedup)
  const SGR_MOUSE_RE = /^\x1b\[<(\d+);(\d+);(\d+)([Mm])$/;
  let lastMotionCell = { col: -1, row: -1 };
  let lastMotionCb = -1;

  const onDataDisposable = term.onData((data) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const m = SGR_MOUSE_RE.exec(data);
    if (m) {
      const cb = parseInt(m[1], 10);
      const col = parseInt(m[2], 10);
      const row = parseInt(m[3], 10);
      const released = m[4] === "m";
      const isMotion = (cb & 0x20) !== 0 && (cb & 0x40) === 0;
      const isWheel = (cb & 0x40) !== 0;
      if (isMotion && !isWheel && !released) {
        if (col === lastMotionCell.col && row === lastMotionCell.row && cb === lastMotionCb) {
          return;
        }
        lastMotionCell = { col, row };
        lastMotionCb = cb;
      } else {
        lastMotionCell = { col: -1, row: -1 };
        lastMotionCb = -1;
      }
    }
    if (ws) ws.send(data);
  });

  const onResizeDisposable = term.onResize(({ cols, rows }) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(`\x1b[RESIZE:${cols};${rows}]`);
    }
  });

  term.focus();

  /* ---- Cleanup ---- */
  onUnmounted(() => {
    unmounting = true;
    onDataDisposable.dispose();
    onResizeDisposable.dispose();
    if (metricsDebounce) clearTimeout(metricsDebounce);
    window.removeEventListener("resize", scheduleSyncTerminalMetrics);
    window.visualViewport?.removeEventListener("resize", scheduleSyncTerminalMetrics);
    window.visualViewport?.removeEventListener("scroll", scheduleSyncTerminalMetrics);
    ro.disconnect();
    if (hostSyncRaf) cancelAnimationFrame(hostSyncRaf);
    if (settleRaf1) cancelAnimationFrame(settleRaf1);
    if (settleRaf2) cancelAnimationFrame(settleRaf2);
    socket.close();
    ws = null;
    term?.dispose();
    term = null;
    fitAddon = null;
    if (copyResetTimer) {
      clearTimeout(copyResetTimer);
      copyResetTimer = null;
    }
  });
});
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col gap-2 normal-case">
    <PluginSlot name="chat:top" />

    <!-- Banner -->
    <div
      v-if="banner"
      class="border border-warning/50 bg-warning/10 text-warning px-3 py-2 text-xs tracking-wide"
    >{{ banner }}</div>

    <div class="flex min-h-0 flex-1 flex-col gap-2 lg:flex-row lg:gap-3">
      <!-- Terminal pane -->
      <div
        class="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg p-2 sm:p-3"
        :style="{
          backgroundColor: TERMINAL_THEME.background,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        }"
      >
        <div
          ref="hostRef"
          class="anydeals-chat-xterm-host min-h-0 min-w-0 flex-1"
        />

        <!-- Copy button -->
        <button
          v-if="!banner"
          type="button"
          class="absolute z-10 flex items-center gap-1.5 rounded border border-current/30 bg-black/20 backdrop-blur-sm opacity-60 hover:opacity-100 hover:border-current/60 transition-opacity duration-150 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-current cursor-pointer bottom-2 right-2 px-2 py-1 text-[0.65rem] sm:bottom-3 sm:right-3 sm:px-2.5 sm:py-1.5 sm:text-xs lg:bottom-4 lg:right-4"
          :style="{ color: TERMINAL_THEME.foreground }"
          :title="t('chat.copyLastAssistant')"
          :aria-label="t('chat.copyLastAssistant')"
          @click="handleCopyLast"
        >
          <Copy class="h-3 w-3 shrink-0" />
          <span class="hidden min-[400px]:inline tracking-wide">
            {{ copyState === 'copied' ? t('common.copied') : t('common.copyLastResponse') }}
          </span>
        </button>
      </div>

      <!-- Desktop sidebar -->
      <div
        v-if="!narrow"
        id="chat-side-panel"
        role="complementary"
        :aria-label="modelToolsLabel"
        class="flex min-h-0 shrink-0 flex-col lg:h-full lg:w-80"
      >
        <div class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
          <ChatSidebar :channel="channel" />
        </div>
      </div>
    </div>

    <PluginSlot name="chat:bottom" />
  </div>
</template>
