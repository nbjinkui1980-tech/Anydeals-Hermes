<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick, h } from "vue";
import { useRouter } from "vue-router";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  Database,
  Globe,
  Hash,
  Loader2,
  MessageCircle,
  MessageSquare,
  Play,
  Search,
  Terminal,
  Trash2,
  X,
} from "lucide-vue-next";
import { NButton, NTag, NInput } from "naive-ui";
import { api } from "@/lib/api";
import type {
  SessionInfo,
  SessionMessage,
  SessionSearchResult,
  StatusResponse,
} from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import Markdown from "@/components/Markdown.vue";
import PlatformsCard from "@/components/PlatformsCard.vue";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog.vue";
import { useConfirmDelete } from "@/composables/useConfirmDelete";
import { useSystemActionsStore } from "@/stores/systemActionsStore";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";
import PluginSlot from "@/components/PluginSlot.vue";
import { isDashboardEmbeddedChatEnabled } from "@/lib/dashboard-flags";

const { t } = useI18n();
const { setAfterTitle, setEnd } = usePageHeader();
const router = useRouter();
const systemActions = useSystemActionsStore();

const SOURCE_CONFIG: Record<string, { icon: any; color: string }> = {
  cli: { icon: Terminal, color: "text-primary" },
  telegram: { icon: MessageCircle, color: "text-[oklch(0.65_0.15_250)]" },
  discord: { icon: Hash, color: "text-[oklch(0.65_0.15_280)]" },
  slack: { icon: MessageSquare, color: "text-[oklch(0.7_0.15_155)]" },
  whatsapp: { icon: Globe, color: "text-success" },
  cron: { icon: Clock, color: "text-warning" },
};

const resumeInChatEnabled = isDashboardEmbeddedChatEnabled();

/* ---- State ---- */

const sessions = ref<SessionInfo[]>([]);
const total = ref(0);
const page = ref(0);
const PAGE_SIZE = 20;
const loading = ref(true);
const search = ref("");
const expandedId = ref<string | null>(null);
const searchResults = ref<SessionSearchResult[] | null>(null);
const searching = ref(false);
const status = ref<StatusResponse | null>(null);
const overviewSessions = ref<SessionInfo[]>([]);
const logScrollRef = ref<HTMLPreElement | null>(null);
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

/* ---- Load data ---- */

async function loadSessions(p: number) {
  loading.value = true;
  try {
    const resp = await api.getSessions(PAGE_SIZE, p * PAGE_SIZE);
    sessions.value = resp.sessions;
    total.value = resp.total;
  } catch {
    // keep previous
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadSessions(page.value);
});

watch(page, (p) => {
  loadSessions(p);
});

/* ---- Status overview polling ---- */

let overviewTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  const loadOverview = () => {
    api.getStatus().then((s) => { status.value = s; }).catch(() => {});
    api
      .getSessions(50)
      .then((r) => { overviewSessions.value = r.sessions; })
      .catch(() => {});
  };
  loadOverview();
  overviewTimer = setInterval(loadOverview, 5000);
});

onUnmounted(() => {
  if (overviewTimer) clearInterval(overviewTimer);
  if (debounceTimer) clearTimeout(debounceTimer);
});

/* ---- Action log scroll ---- */

watch(
  () => systemActions.actionStatus?.lines,
  () => {
    nextTick(() => {
      const el = logScrollRef.value;
      if (el) el.scrollTop = el.scrollHeight;
    });
  },
);

/* ---- Debounced search ---- */

watch(search, (q) => {
  if (debounceTimer) clearTimeout(debounceTimer);

  if (!q.trim()) {
    searchResults.value = null;
    searching.value = false;
    return;
  }

  searching.value = true;
  debounceTimer = setTimeout(() => {
    api
      .searchSessions(q.trim())
      .then((resp) => { searchResults.value = resp.results; })
      .catch(() => { searchResults.value = null; })
      .finally(() => { searching.value = false; });
  }, 300);
});

/* ---- Page header ---- */

watch(
  [loading, total, search, searching],
  () => {
    if (loading.value) {
      setAfterTitle(null);
      setEnd(null);
      return;
    }
    setAfterTitle(
      h(NTag, { bordered: false, size: "small" }, { default: () => String(total.value) }),
    );
    setEnd(
      h("div", { class: "relative w-full min-w-0 sm:max-w-xs" }, [
        searching.value
          ? h("div", {
              class:
                "absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 animate-spin rounded-full border-[1.5px] border-primary border-t-transparent",
            })
          : h(Search, {
              class:
                "absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground",
            }),
        h(NInput, {
          size: "small",
          placeholder: t("sessions.searchPlaceholder"),
          value: search.value,
          onUpdateValue: (v: string) => { search.value = v; },
          style: "padding-left: 2rem; padding-right: 1.75rem; height: 2rem; font-size: 0.75rem;",
        }),
        search.value
          ? h(
              "button",
              {
                type: "button",
                class:
                  "absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-muted-foreground hover:text-foreground",
                onClick: () => { search.value = ""; },
              },
              h(X, { class: "h-3 w-3" }),
            )
          : null,
      ]),
    );
  },
  { immediate: true },
);

/* ---- Delete ---- */

const sessionDelete = useConfirmDelete<string>(async (id: string) => {
  await api.deleteSession(id);
  sessions.value = sessions.value.filter((s) => s.id !== id);
  total.value = total.value - 1;
  if (expandedId.value === id) expandedId.value = null;
});

/* ---- Derived ---- */

const snippetMap = computed(() => {
  const map = new Map<string, string>();
  if (searchResults.value) {
    for (const r of searchResults.value) {
      map.set(r.session_id, r.snippet);
    }
  }
  return map;
});

const filtered = computed(() => {
  if (searchResults.value) {
    return sessions.value.filter((s) => snippetMap.value.has(s.id));
  }
  return sessions.value;
});

const platformEntries = computed(() => {
  if (!status.value) return [];
  return Object.entries(status.value.gateway_platforms ?? {});
});

const recentSessions = computed(() =>
  overviewSessions.value.filter((s) => !s.is_active).slice(0, 5),
);

/* ---- Alerts ---- */

interface Alert {
  message: string;
  detail?: string;
}

const alerts = computed<Alert[]>(() => {
  const result: Alert[] = [];
  if (!status.value) return result;
  if (status.value.gateway_state === "startup_failed") {
    result.push({
      message: t("status.gatewayFailedToStart"),
      detail: status.value.gateway_exit_reason ?? undefined,
    });
  }
  const failedEntries = platformEntries.value.filter(
    ([, info]) => info.state === "fatal" || info.state === "disconnected",
  );
  for (const [name, info] of failedEntries) {
    const stateLabel =
      info.state === "fatal"
        ? t("status.platformError")
        : t("status.platformDisconnected");
    result.push({
      message: `${name.charAt(0).toUpperCase() + name.slice(1)} ${stateLabel}`,
      detail: info.error_message ?? undefined,
    });
  }
  return result;
});

/* ---- Session detail ---- */

const sessionMessages = ref<Map<string, SessionMessage[]>>(new Map());
const sessionMessagesLoading = ref<Set<string>>(new Set());
const sessionMessagesError = ref<Map<string, string>>(new Map());

async function toggleSession(id: string) {
  if (expandedId.value === id) {
    if (!sessionMessagesLoading.value.has(id)) {
      expandedId.value = null;
    }
    return;
  }
  expandedId.value = id;
  if (!sessionMessages.value.has(id) && !sessionMessagesLoading.value.has(id)) {
    sessionMessagesLoading.value = new Set(sessionMessagesLoading.value).add(id);
    try {
      const resp = await api.getSessionMessages(id);
      sessionMessages.value = new Map(sessionMessages.value).set(id, resp.messages);
    } catch (err) {
      sessionMessagesError.value = new Map(sessionMessagesError.value).set(id, String(err));
    } finally {
      const s = new Set(sessionMessagesLoading.value);
      s.delete(id);
      sessionMessagesLoading.value = s;
    }
  }
}

/* ---- Delete description ---- */

const pendingSession = computed(() => {
  const pid = sessionDelete.pendingId.value;
  if (!pid) return null;
  return sessions.value.find((s) => s.id === pid) ?? null;
});

const deleteDescription = computed(() => {
  const ps = pendingSession.value;
  if (ps?.title && ps.title !== "Untitled") {
    return `"${ps.title}" — ${t("sessions.confirmDeleteMessage")}`;
  }
  return t("sessions.confirmDeleteMessage");
});

/* ---- Tool call expansion ---- */

const expandedToolCalls = ref(new Set<string>());

function toggleToolCall(key: string) {
  const next = new Set(expandedToolCalls.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  expandedToolCalls.value = next;
}

function formatToolArgs(args: string): string {
  try {
    return JSON.stringify(JSON.parse(args), null, 2);
  } catch {
    return args;
  }
}

/* ---- Search hit check ---- */

function isSearchHit(msg: SessionMessage, highlight: string): boolean {
  if (!highlight || !msg.content) return false;
  const content = msg.content.toLowerCase();
  const terms = highlight.toLowerCase().split(/\s+/).filter(Boolean);
  return terms.some((term) => content.includes(term));
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <PluginSlot name="sessions:top" />

    <DeleteConfirmDialog
      :open="sessionDelete.isOpen()"
      :title="t('sessions.confirmDeleteTitle')"
      :description="deleteDescription"
      :loading="sessionDelete.isDeleting.value"
      @cancel="sessionDelete.cancel()"
      @confirm="sessionDelete.confirm()"
    />

    <!-- Alerts -->
    <div v-if="alerts.length > 0" class="border border-destructive/30 bg-destructive/[0.06] p-4">
      <div class="flex items-start gap-3">
        <AlertTriangle class="h-5 w-5 text-destructive shrink-0 mt-0.5" />
        <div class="flex flex-col gap-2 min-w-0">
          <div v-for="(alert, i) in alerts" :key="i">
            <p class="text-sm font-medium text-destructive">{{ alert.message }}</p>
            <p v-if="alert.detail" class="text-xs text-destructive/70 mt-0.5">{{ alert.detail }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Action log -->
    <div v-if="systemActions.activeAction" class="border border-border bg-background-base/50">
      <div class="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div class="flex items-center gap-2 min-w-0">
          <Loader2
            v-if="systemActions.actionStatus?.running"
            class="h-3.5 w-3.5 shrink-0 animate-spin text-warning"
          />
          <CheckCircle2
            v-else-if="systemActions.actionStatus?.exit_code === 0"
            class="h-3.5 w-3.5 shrink-0 text-success"
          />
          <AlertTriangle
            v-else-if="systemActions.actionStatus !== null"
            class="h-3.5 w-3.5 shrink-0 text-destructive"
          />
          <Loader2
            v-else
            class="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground"
          />

          <span class="text-xs font-mondwest tracking-[0.12em] truncate">
            {{ systemActions.activeAction === 'restart' ? t('status.restartGateway') : t('status.updateAnyDeals') }}
          </span>

          <NTag
            :type="systemActions.actionStatus?.running
              ? 'warning'
              : systemActions.actionStatus?.exit_code === 0
                ? 'success'
                : systemActions.actionStatus
                  ? 'error'
                  : 'default'"
            size="small"
            :bordered="false"
          >
            {{ systemActions.actionStatus?.running
              ? t('status.running')
              : systemActions.actionStatus?.exit_code === 0
                ? t('status.actionFinished')
                : systemActions.actionStatus
                  ? `${t('status.actionFailed')} (${systemActions.actionStatus.exit_code ?? '?'})`
                  : t('common.loading') }}
          </NTag>
        </div>

        <button
          type="button"
          @click="systemActions.dismissLog()"
          class="shrink-0 opacity-60 hover:opacity-100 cursor-pointer"
          :aria-label="t('common.close')"
        >
          <X class="h-3.5 w-3.5" />
        </button>
      </div>

      <pre
        ref="logScrollRef"
        class="max-h-72 overflow-auto px-3 py-2 font-mono-ui text-[11px] leading-relaxed whitespace-pre-wrap break-all"
      >{{ systemActions.actionStatus?.lines && systemActions.actionStatus.lines.length > 0
        ? systemActions.actionStatus.lines.join('\n')
        : t('status.waitingForOutput') }}</pre>
    </div>

    <!-- Platforms -->
    <PlatformsCard
      v-if="platformEntries.length > 0 && status"
      :platforms="platformEntries"
    />

    <!-- Recent sessions -->
    <div v-if="recentSessions.length > 0" class="border border-border bg-card">
      <div class="px-4 py-3 border-b border-border flex items-center gap-2">
        <Clock class="h-5 w-5 text-muted-foreground" />
        <span class="text-base font-semibold">{{ t('status.recentSessions') }}</span>
      </div>
      <div class="grid gap-3 p-4">
        <div
          v-for="s in recentSessions"
          :key="s.id"
          class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border border-border p-3 w-full"
        >
          <div class="flex flex-col gap-1 min-w-0 w-full">
            <span class="font-medium text-sm truncate">{{ s.title ?? t('common.untitled') }}</span>
            <span class="text-xs text-muted-foreground truncate">
              <span class="font-mono-ui">{{ (s.model ?? t('common.unknown')).split('/').pop() }}</span>
              · {{ s.message_count }} {{ t('common.msgs') }} · {{ timeAgo(s.last_active) }}
            </span>
            <span v-if="s.preview" class="text-xs text-muted-foreground/70 truncate">{{ s.preview }}</span>
          </div>
          <NTag :bordered="true" size="small">
            <template #icon><Database class="mr-1 h-3 w-3" /></template>
            {{ s.source ?? 'local' }}
          </NTag>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="filtered.length === 0"
      class="flex flex-col items-center justify-center py-16 text-muted-foreground"
    >
      <Clock class="h-8 w-8 mb-3 opacity-40" />
      <p class="text-sm font-medium">
        {{ search ? t('sessions.noMatch') : t('sessions.noSessions') }}
      </p>
      <p v-if="!search" class="text-xs mt-1 text-muted-foreground/60">
        {{ t('sessions.startConversation') }}
      </p>
    </div>

    <!-- Session list -->
    <template v-else>
      <div class="flex flex-col gap-1.5">
        <div
          v-for="s in filtered"
          :key="s.id"
          class="border overflow-hidden transition-colors"
          :class="s.is_active ? 'border-success/30 bg-success/[0.03]' : 'border-border'"
        >
          <!-- Session row header -->
          <div
            class="flex items-center justify-between p-3 cursor-pointer hover:bg-secondary/30 transition-colors"
            @click="toggleSession(s.id)"
          >
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <component
                :is="(SOURCE_CONFIG[s.source ?? ''] ?? { icon: Globe, color: 'text-muted-foreground' }).icon"
                class="h-4 w-4 shrink-0"
                :class="(SOURCE_CONFIG[s.source ?? ''] ?? { icon: Globe, color: 'text-muted-foreground' }).color"
              />
              <div class="flex flex-col gap-0.5 min-w-0">
                <div class="flex items-center gap-2">
                  <span
                    class="text-sm truncate pr-2"
                    :class="s.title && s.title !== 'Untitled' ? 'font-medium' : 'text-muted-foreground italic'"
                  >
                    {{ s.title && s.title !== 'Untitled'
                      ? s.title
                      : s.preview
                        ? s.preview.slice(0, 60)
                        : t('sessions.untitledSession') }}
                  </span>
                  <NTag v-if="s.is_active" type="success" size="small" :bordered="false">
                    <span class="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
                    {{ t('common.live') }}
                  </NTag>
                </div>
                <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span class="truncate max-w-[120px] sm:max-w-[180px]">
                    {{ (s.model ?? t('common.unknown')).split('/').pop() }}
                  </span>
                  <span class="text-border">&middot;</span>
                  <span>{{ s.message_count }} {{ t('common.msgs') }}</span>
                  <template v-if="s.tool_call_count > 0">
                    <span class="text-border">&middot;</span>
                    <span>{{ s.tool_call_count }} {{ t('common.tools') }}</span>
                  </template>
                  <span class="text-border">&middot;</span>
                  <span>{{ timeAgo(s.last_active) }}</span>
                </div>
                <!-- Search snippet -->
                <p
                  v-if="snippetMap.get(s.id)"
                  class="text-xs text-muted-foreground/80 truncate max-w-lg mt-0.5"
                >
                  <template
                    v-for="(part, pi) in snippetMap.get(s.id)!.split(/(>>>.*?<<<)/g)"
                    :key="pi"
                  >
                    <mark
                      v-if="part.startsWith('>>>') && part.endsWith('<<<')"
                      class="bg-warning/30 text-warning px-0.5"
                    >{{ part.slice(3, -3) }}</mark>
                    <template v-else>{{ part }}</template>
                  </template>
                </p>
              </div>
            </div>

            <div class="flex items-center gap-2 shrink-0">
              <NTag :bordered="true" size="small">
                {{ s.source ?? 'local' }}
              </NTag>
              <NButton
                v-if="resumeInChatEnabled"
                text
                class="h-7 w-7 !text-muted-foreground hover:!text-success"
                :title="t('sessions.resumeInChat')"
                @click.stop="router.push(`/chat?resume=${encodeURIComponent(s.id)}`)"
              >
                <template #icon><Play class="h-3.5 w-3.5" /></template>
              </NButton>
              <NButton
                text
                class="h-7 w-7 !text-muted-foreground hover:!text-destructive"
                :title="t('sessions.deleteSession')"
                @click.stop="sessionDelete.requestDelete(s.id)"
              >
                <template #icon><Trash2 class="h-3.5 w-3.5" /></template>
              </NButton>
            </div>
          </div>

          <!-- Expanded messages -->
          <div
            v-if="expandedId === s.id"
            class="border-t border-border bg-background/50 p-4"
          >
            <!-- Loading messages -->
            <div
              v-if="sessionMessagesLoading.has(s.id)"
              class="flex items-center justify-center py-8"
            >
              <div class="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>

            <!-- Error -->
            <p
              v-else-if="sessionMessagesError.has(s.id)"
              class="text-sm text-destructive py-4 text-center"
            >{{ sessionMessagesError.get(s.id) }}</p>

            <!-- No messages -->
            <p
              v-else-if="!sessionMessages.has(s.id) || sessionMessages.get(s.id)!.length === 0"
              class="text-sm text-muted-foreground py-4 text-center"
            >{{ t('sessions.noMessages') }}</p>

            <!-- Message list -->
            <div
              v-else
              class="flex flex-col gap-3 max-h-[600px] overflow-y-auto pr-2"
            >
              <div
                v-for="(msg, mi) in sessionMessages.get(s.id)!"
                :key="mi"
              >
                <!-- Role style computation -->
                <div
                  class="p-3"
                  :class="{
                    'bg-primary/10 ring-1 ring-warning/40': msg.role === 'user' && isSearchHit(msg, search),
                    'bg-primary/10': msg.role === 'user' && !isSearchHit(msg, search),
                    'bg-success/10 ring-1 ring-warning/40': msg.role === 'assistant' && isSearchHit(msg, search),
                    'bg-success/10': msg.role === 'assistant' && !isSearchHit(msg, search),
                    'bg-muted ring-1 ring-warning/40': msg.role === 'system' && isSearchHit(msg, search),
                    'bg-muted': msg.role === 'system' && !isSearchHit(msg, search),
                    'bg-warning/10 ring-1 ring-warning/40': (msg.role === 'tool' || !['user','assistant','system'].includes(msg.role)) && isSearchHit(msg, search),
                    'bg-warning/10': (msg.role === 'tool' || !['user','assistant','system'].includes(msg.role)) && !isSearchHit(msg, search),
                  }"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <span
                      class="text-xs font-semibold"
                      :class="{
                        'text-primary': msg.role === 'user',
                        'text-success': msg.role === 'assistant',
                        'text-muted-foreground': msg.role === 'system',
                        'text-warning': msg.role === 'tool' || !['user','assistant','system'].includes(msg.role),
                      }"
                    >
                      {{ msg.tool_name ? `${t('sessions.roles.tool')}: ${msg.tool_name}` : t(`sessions.roles.${msg.role}` as any) || t('sessions.roles.system') }}
                    </span>
                    <NTag v-if="isSearchHit(msg, search)" type="warning" size="small" :bordered="false">
                      {{ t('common.match') }}
                    </NTag>
                    <span v-if="msg.timestamp" class="text-[10px] text-muted-foreground">
                      {{ timeAgo(msg.timestamp) }}
                    </span>
                  </div>

                  <!-- System role: plain text -->
                  <div
                    v-if="msg.content && msg.role === 'system'"
                    class="text-sm text-foreground whitespace-pre-wrap leading-relaxed"
                  >{{ msg.content }}</div>

                  <!-- Other roles: Markdown -->
                  <Markdown
                    v-else-if="msg.content"
                    :content="msg.content"
                    :highlightTerms="isSearchHit(msg, search) ? search.split(/\\s+/).filter(Boolean) : []"
                  />

                  <!-- Tool calls -->
                  <div v-if="msg.tool_calls && msg.tool_calls.length > 0" class="mt-1 flex flex-col gap-1">
                    <div
                      v-for="tc in msg.tool_calls"
                      :key="tc.id"
                      class="border border-warning/20 bg-warning/5"
                    >
                      <button
                        type="button"
                        class="flex w-full items-center gap-2 px-3 py-2 text-xs text-warning cursor-pointer hover:bg-warning/10 transition-colors"
                        @click="toggleToolCall(`${msg.timestamp || mi}-${tc.id}`)"
                      >
                        <ChevronDown
                          v-if="expandedToolCalls.has(`${msg.timestamp || mi}-${tc.id}`)"
                          class="h-3 w-3"
                        />
                        <ChevronRight v-else class="h-3 w-3" />
                        <span class="font-mono-ui font-medium">{{ tc.function.name }}</span>
                        <span class="text-warning/50 ml-auto">{{ tc.id }}</span>
                      </button>
                      <pre
                        v-if="expandedToolCalls.has(`${msg.timestamp || mi}-${tc.id}`)"
                        class="border-t border-warning/20 px-3 py-2 text-xs text-warning/80 overflow-x-auto whitespace-pre-wrap font-mono"
                      >{{ formatToolArgs(tc.function.arguments) }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div
        v-if="!searchResults && total > PAGE_SIZE"
        class="flex items-center justify-between pt-2"
      >
        <span class="text-xs text-muted-foreground">
          {{ page * PAGE_SIZE + 1 }}–{{ Math.min((page + 1) * PAGE_SIZE, total) }}
          {{ t('common.of') }} {{ total }}
        </span>
        <div class="flex items-center gap-1">
          <NButton
            size="tiny"
            :disabled="page === 0"
            @click="page = page - 1"
            :title="t('sessions.previousPage')"
          >
            <template #icon><ChevronLeft class="h-4 w-4" /></template>
          </NButton>
          <span class="text-xs text-muted-foreground px-2">
            {{ t('common.page') }} {{ page + 1 }} {{ t('common.of') }}
            {{ Math.ceil(total / PAGE_SIZE) }}
          </span>
          <NButton
            size="tiny"
            :disabled="(page + 1) * PAGE_SIZE >= total"
            @click="page = page + 1"
            :title="t('sessions.nextPage')"
          >
            <template #icon><ChevronRight class="h-4 w-4" /></template>
          </NButton>
        </div>
      </div>
    </template>

    <PluginSlot name="sessions:bottom" />
  </div>
</template>
