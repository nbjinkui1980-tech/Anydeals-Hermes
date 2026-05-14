<script setup lang="ts">
import { ref, computed, onMounted, watch, h } from "vue";
import {
  Brain,
  Cpu,
  Eye,
  RefreshCw,
  Settings2,
  Star,
  Wrench,
} from "lucide-vue-next";
import { NButton, NTag } from "naive-ui";
import { api } from "@/lib/api";
import type { ModelsAnalyticsResponse, AuxiliaryModelsResponse, ModelsAnalyticsModelEntry } from "@/lib/api";
import PluginSlot from "@/components/PluginSlot.vue";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";

const { t } = useI18n();
const { setAfterTitle, setEnd } = usePageHeader();

const PERIODS = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

const AUX_TASKS = [
  { key: "vision", label: "Vision", hint: "Image analysis" },
  { key: "web_extract", label: "Web Extract", hint: "Page summarization" },
  { key: "compression", label: "Compression", hint: "Context compaction" },
  { key: "session_search", label: "Session Search", hint: "Recall queries" },
  { key: "skills_hub", label: "Skills Hub", hint: "Skill search" },
  { key: "approval", label: "Approval", hint: "Smart auto-approve" },
  { key: "mcp", label: "MCP", hint: "MCP tool routing" },
  { key: "title_generation", label: "Title Gen", hint: "Session titles" },
  { key: "curator", label: "Curator", hint: "Skill-usage review" },
] as const;

const days = ref(30);
const data = ref<ModelsAnalyticsResponse | null>(null);
const aux = ref<AuxiliaryModelsResponse | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const useAsMenuOpen = ref<string | null>(null);
const useAsBusy = ref<string | null>(null);
const assignError = ref<string | null>(null);
const pickerTarget = ref<{ kind: "main" } | { kind: "aux"; task: string } | null>(null);

function shortModelName(model: string): string {
  const idx = model.indexOf("/");
  return idx > 0 ? model.slice(idx + 1) : model;
}

function modelVendor(model: string, fallback?: string): string {
  const idx = model.indexOf("/");
  return idx > 0 ? model.slice(0, idx) : fallback || "";
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatCost(n: number): string {
  if (n >= 1) return `$${n.toFixed(2)}`;
  if (n >= 0.01) return `$${n.toFixed(3)}`;
  if (n > 0) return `$${n.toFixed(4)}`;
  return "$0";
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [models, auxData] = await Promise.all([
      api.getModelsAnalytics(days.value),
      api.getAuxiliaryModels().catch(() => null),
    ]);
    data.value = models;
    aux.value = auxData;
  } catch (err) {
    error.value = String(err);
  } finally {
    loading.value = false;
  }
}

async function assignModel(scope: "main" | "auxiliary", task: string, provider: string, model: string) {
  useAsBusy.value = `${scope}:${task}`;
  assignError.value = null;
  try {
    await api.setModelAssignment({ scope, task, provider, model });
    useAsMenuOpen.value = null;
    pickerTarget.value = null;
    const auxData = await api.getAuxiliaryModels().catch(() => null);
    aux.value = auxData;
  } catch (e) {
    assignError.value = e instanceof Error ? e.message : String(e);
  } finally {
    useAsBusy.value = null;
  }
}

function isMainModel(entry: ModelsAnalyticsModelEntry): boolean {
  if (!aux.value) return false;
  const m = aux.value.main;
  return entry.provider === m.provider && entry.model === m.model;
}

function auxTaskForModel(entry: ModelsAnalyticsModelEntry): string | null {
  if (!aux.value) return null;
  const task = aux.value.tasks.find(
    (t) => t.provider === entry.provider && t.model === entry.model,
  );
  return task?.task ?? null;
}

const auxOverrideCount = computed(() =>
  aux.value?.tasks.filter((t) => t.provider && t.provider !== "auto").length ?? 0,
);

onMounted(() => { load(); });

watch(days, () => { load(); });

watch([loading, data, days], () => {
  const periodLabel = PERIODS.find((p) => p.days === days.value)?.label ?? `${days.value}d`;
  setAfterTitle(
    h("span", { class: "flex items-center gap-2" }, [
      loading.value
        ? h("span", { class: "h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent shrink-0" })
        : null,
      h(NTag, { bordered: false, size: "small" }, { default: () => periodLabel }),
    ]),
  );
  setEnd(
    h("div", { class: "flex items-center gap-2 flex-wrap" }, [
      ...PERIODS.map((p) =>
        h(NButton, {
          size: "small",
          type: days.value === p.days ? "primary" : "default",
          onClick: () => { days.value = p.days; },
        }, { default: () => p.label }),
      ),
      h(NButton, {
        size: "small",
        disabled: loading.value,
        onClick: load,
      }, { default: () => h(RefreshCw, { class: "h-3.5 w-3.5" }) }),
    ]),
  );
}, { immediate: true });

// Close use-as menu on outside click
watch(useAsMenuOpen, (val) => {
  if (!val) return;
  const handler = (e: MouseEvent) => {
    const target = e.target as HTMLElement | null;
    if (target && !target.closest("[data-use-as-menu]")) useAsMenuOpen.value = null;
  };
  window.addEventListener("mousedown", handler, { once: true });
});
</script>

<template>
  <div class="flex flex-col gap-6">
    <PluginSlot name="models:top" />

    <!-- Error banner -->
    <div v-if="error" class="border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
      {{ error }}
    </div>

    <!-- Model Settings & Stats -->
    <div class="grid gap-6 lg:grid-cols-2">
      <!-- Settings card -->
      <div class="border border-border bg-card">
        <div class="flex items-center justify-between gap-3 px-5 py-3 border-b border-border/50">
          <div class="flex items-center gap-2">
            <Settings2 class="h-4 w-4 text-muted-foreground" />
            <h3 class="text-sm font-medium tracking-wider uppercase">Model Settings</h3>
            <span class="text-[10px] text-muted-foreground">applies to new sessions</span>
          </div>
        </div>
        <div class="p-4 space-y-3">
          <!-- Main model row -->
          <div class="flex items-center justify-between gap-3 bg-muted/20 border border-border/50 px-3 py-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-0.5">
                <Star class="h-3 w-3 text-primary" />
                <span class="text-xs font-medium uppercase tracking-wider">Main model</span>
              </div>
              <div class="text-xs font-mono text-muted-foreground truncate">
                {{ aux?.main.provider || "(unset)" }}{{ aux?.main.provider && aux?.main.model ? " · " : "" }}{{ aux?.main.model || "(unset)" }}
              </div>
            </div>
            <NButton size="small" @click="pickerTarget = { kind: 'main' }">Change</NButton>
          </div>

          <!-- Aux tasks row -->
          <div class="flex items-center justify-between gap-3 bg-muted/20 border border-border/50 px-3 py-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-0.5">
                <Cpu class="h-3 w-3 text-muted-foreground" />
                <span class="text-xs font-medium uppercase tracking-wider">Auxiliary tasks</span>
              </div>
              <div class="text-xs font-mono text-muted-foreground truncate">
                {{ auxOverrideCount > 0 ? `${auxOverrideCount} override${auxOverrideCount > 1 ? 's' : ''} · ${AUX_TASKS.length - auxOverrideCount} auto` : `${AUX_TASKS.length} tasks · all auto` }}
              </div>
            </div>
            <NButton size="small" @click="pickerTarget = { kind: 'aux', task: '' }">Configure</NButton>
          </div>
        </div>
      </div>

      <!-- Stats card -->
      <div v-if="data" class="border border-border bg-card">
        <div class="p-5 grid grid-cols-3 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold">{{ data.totals.distinct_models }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Models Used</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold">{{ formatTokens(data.totals.total_input + data.totals.total_output) }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Total Tokens</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold">{{ formatCost(data.totals.total_estimated_cost) }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Est. Cost</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-bold">{{ formatTokens(data.totals.total_input) }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Input</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-bold">{{ formatTokens(data.totals.total_output) }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Output</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-bold">{{ data.totals.total_sessions }}</div>
            <div class="text-[10px] text-muted-foreground uppercase tracking-wider">Sessions</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !data" class="flex items-center justify-center py-24">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <!-- Model cards grid -->
    <template v-if="data">
      <div v-if="data.models.length > 0" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="(entry, i) in data.models"
          :key="`${entry.model}:${entry.provider}`"
          class="border border-border bg-card p-4 flex flex-col gap-3 relative"
        >
          <!-- Rank & name -->
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-[10px] text-muted-foreground font-mono">#{{ i + 1 }}</span>
                <span class="text-sm font-semibold truncate">{{ shortModelName(entry.model) }}</span>
                <span class="text-[10px] text-muted-foreground">{{ modelVendor(entry.model) }}</span>
              </div>
              <!-- Capability badges -->
              <div class="flex flex-wrap items-center gap-1.5">
                <span v-if="entry.capabilities.supports_tools" class="inline-flex items-center gap-1 bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-500">
                  <Wrench class="h-2.5 w-2.5" /> Tools
                </span>
                <span v-if="entry.capabilities.supports_vision" class="inline-flex items-center gap-1 bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-medium text-blue-400">
                  <Eye class="h-2.5 w-2.5" /> Vision
                </span>
                <span v-if="entry.capabilities.supports_reasoning" class="inline-flex items-center gap-1 bg-purple-500/10 px-1.5 py-0.5 text-[10px] font-medium text-purple-400">
                  <Brain class="h-2.5 w-2.5" /> Reasoning
                </span>
                <span v-if="entry.capabilities.model_family" class="bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                  {{ entry.capabilities.model_family }}
                </span>
              </div>
            </div>
            <!-- Use as menu -->
            <div class="relative shrink-0" data-use-as-menu>
              <NButton size="tiny" @click="useAsMenuOpen = useAsMenuOpen === entry.model + entry.provider ? null : entry.model + entry.provider">
                Use as
              </NButton>
              <div
                v-if="useAsMenuOpen === entry.model + entry.provider"
                class="absolute right-0 top-full mt-1 z-50 min-w-[220px] border border-border bg-card shadow-lg"
              >
                <button
                  type="button"
                  class="flex w-full items-center justify-between px-3 py-2 text-xs hover:bg-muted/50 disabled:opacity-40"
                  :disabled="!!useAsBusy"
                  @click="assignModel('main', '', entry.provider, entry.model)"
                >
                  <span class="flex items-center gap-2"><Star class="h-3 w-3" /> Main model</span>
                  <span v-if="isMainModel(entry)" class="text-[9px] uppercase tracking-wider text-primary/80">current</span>
                </button>
                <div class="border-t border-border/50 px-3 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground">Auxiliary task</div>
                <button
                  type="button"
                  class="flex w-full items-center px-3 py-1.5 text-xs hover:bg-muted/50 disabled:opacity-40"
                  :disabled="!!useAsBusy"
                  @click="assignModel('auxiliary', '', entry.provider, entry.model)"
                >All auxiliary tasks</button>
                <button
                  v-for="task in AUX_TASKS"
                  :key="task.key"
                  type="button"
                  class="flex w-full items-center justify-between px-3 py-1.5 text-xs hover:bg-muted/50 disabled:opacity-40"
                  :disabled="!!useAsBusy"
                  @click="assignModel('auxiliary', task.key, entry.provider, entry.model)"
                >
                  <span>{{ task.label }}</span>
                  <span v-if="auxTaskForModel(entry) === task.key" class="text-[9px] uppercase tracking-wider text-primary/80">current</span>
                </button>
                <div v-if="assignError" class="px-3 py-2 text-[10px] text-red-400 border-t border-border/50">{{ assignError }}</div>
              </div>
            </div>
          </div>

          <!-- Token bar -->
          <div class="space-y-1.5">
            <div class="flex h-6 w-full overflow-hidden rounded-sm">
              <div
                v-if="entry.cache_read_tokens"
                class="bg-blue-400/60 flex items-center h-full"
                :style="{ width: `${(entry.cache_read_tokens / (entry.input_tokens + entry.output_tokens + entry.cache_read_tokens + entry.reasoning_tokens)) * 100}%` }"
              />
              <div
                v-if="entry.reasoning_tokens"
                class="bg-purple-400/60 flex items-center h-full"
                :style="{ width: `${(entry.reasoning_tokens / (entry.input_tokens + entry.output_tokens + entry.cache_read_tokens + entry.reasoning_tokens)) * 100}%` }"
              />
              <div
                class="bg-[#ffe6cb]/70 flex items-center h-full"
                :style="{ width: `${(entry.input_tokens / (entry.input_tokens + entry.output_tokens + entry.cache_read_tokens + entry.reasoning_tokens)) * 100}%` }"
              />
              <div
                class="bg-emerald-500/70 flex items-center h-full"
                :style="{ width: `${(entry.output_tokens / (entry.input_tokens + entry.output_tokens + entry.cache_read_tokens + entry.reasoning_tokens)) * 100}%` }"
              />
            </div>
            <div class="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-muted-foreground">
              <span v-if="entry.cache_read_tokens" class="flex items-center gap-1"><span class="inline-block h-1.5 w-1.5 rounded-full bg-blue-400" /> Cache {{ formatTokens(entry.cache_read_tokens) }}</span>
              <span v-if="entry.reasoning_tokens" class="flex items-center gap-1"><span class="inline-block h-1.5 w-1.5 rounded-full bg-purple-400" /> Reasoning {{ formatTokens(entry.reasoning_tokens) }}</span>
              <span class="flex items-center gap-1"><span class="inline-block h-1.5 w-1.5 rounded-full bg-[#ffe6cb]" /> Input {{ formatTokens(entry.input_tokens) }}</span>
              <span class="flex items-center gap-1"><span class="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" /> Output {{ formatTokens(entry.output_tokens) }}</span>
            </div>
          </div>

          <!-- Stats row -->
          <div class="flex items-center justify-between text-[10px] text-muted-foreground">
            <span>{{ entry.sessions }} sessions</span>
            <span>{{ entry.api_calls }} calls</span>
            <span>{{ formatCost(entry.estimated_cost) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Cpu class="h-8 w-8 mb-3 opacity-40" />
        <p class="text-sm font-medium">{{ t('models.noModelsData') }}</p>
        <p class="text-xs mt-1 text-muted-foreground/60">{{ t('models.startSession') }}</p>
      </div>
    </template>

    <PluginSlot name="models:bottom" />
  </div>
</template>
