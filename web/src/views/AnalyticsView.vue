<script setup lang="ts">
import { ref, computed, watch, onMounted, h } from "vue";
import {
  BarChart3,
  Brain,
  Cpu,
  Hash,
  RefreshCw,
  TrendingUp,
} from "lucide-vue-next";
import { NButton, NTag } from "naive-ui";
import { api } from "@/lib/api";
import type {
  AnalyticsResponse,
} from "@/lib/api";
import { timeAgo } from "@/lib/utils";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";
import PluginSlot from "@/components/PluginSlot.vue";

const { t } = useI18n();
const { setAfterTitle, setEnd } = usePageHeader();

const PERIOD_OPTS = [
  { label: "7d", value: "7" },
  { label: "30d", value: "30" },
  { label: "90d", value: "90" },
];

const CHART_HEIGHT_PX = 160;

const days = ref(30);
const data = ref<AnalyticsResponse | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatDate(day: string): string {
  try {
    const d = new Date(day + "T00:00:00");
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return day;
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await api.getAnalytics(days.value);
  } catch (err) {
    error.value = String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  load();
});

/* ---- Derived ---- */

const maxTokens = computed(() => {
  if (!data.value) return 1;
  return Math.max(
    ...data.value.daily.map((d) => d.input_tokens + d.output_tokens),
    1,
  );
});

const sortedDaily = computed(() => {
  if (!data.value) return [];
  return [...data.value.daily].reverse();
});

const sortedModels = computed(() => {
  if (!data.value) return [];
  return [...data.value.by_model].sort(
    (a, b) =>
      b.input_tokens + b.output_tokens - (a.input_tokens + a.output_tokens),
  );
});

const periodLabel = computed(() => {
  const p = PERIOD_OPTS.find((p) => p.value === String(days.value));
  return p?.label ?? `${days.value}d`;
});

/* ---- Page header ---- */

watch(
  [loading, days],
  () => {
    setAfterTitle(
      h("span", { class: "flex items-center gap-2" }, [
        loading.value
          ? h("div", {
              class:
                "h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-primary border-t-transparent",
            })
          : null,
        h(
          NTag,
          { bordered: false, size: "small" },
          { default: () => periodLabel.value },
        ),
      ]),
    );
    setEnd(
      h("div", { class: "flex w-full min-w-0 flex-wrap items-center justify-end gap-2" }, [
        h(
          "div",
          { class: "flex flex-wrap items-center gap-1.5" },
          PERIOD_OPTS.map((p) =>
            h(
              NButton,
              {
                key: p.label,
                size: "small",
                type: days.value === Number(p.value) ? "primary" : "default",
                onClick: () => {
                  days.value = Number(p.value);
                },
              },
              { default: () => p.label },
            ),
          ),
        ),
        h(
          NButton,
          {
            size: "small",
            disabled: loading.value,
            onClick: load,
          },
          {
            default: () => [
              h(RefreshCw, { class: "mr-1 h-3 w-3" }),
              t("common.refresh"),
            ],
          },
        ),
      ]),
    );
  },
  { immediate: true },
);
</script>

<template>
  <div class="flex flex-col gap-6">
    <PluginSlot name="analytics:top" />

    <!-- Loading -->
    <div
      v-if="loading && !data"
      class="flex items-center justify-center py-24"
    >
      <div
        class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"
      />
    </div>

    <!-- Error -->
    <div v-if="error" class="border border-border bg-card p-6">
      <p class="text-sm text-destructive text-center">{{ error }}</p>
    </div>

    <template v-if="data">
      <!-- Summary cards -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div class="border border-border bg-card">
          <div class="flex flex-row items-center justify-between px-4 pt-4 pb-2">
            <span class="text-sm font-medium">{{ t('analytics.totalTokens') }}</span>
            <Hash class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="px-4 pb-4">
            <div class="text-2xl font-bold">
              {{ formatTokens(data.totals.total_input + data.totals.total_output) }}
            </div>
            <p class="text-xs text-muted-foreground mt-1">
              {{ t('analytics.inOut')
                .replace('{input}', formatTokens(data.totals.total_input))
                .replace('{output}', formatTokens(data.totals.total_output)) }}
            </p>
          </div>
        </div>

        <div class="border border-border bg-card">
          <div class="flex flex-row items-center justify-between px-4 pt-4 pb-2">
            <span class="text-sm font-medium">{{ t('analytics.totalSessions') }}</span>
            <BarChart3 class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="px-4 pb-4">
            <div class="text-2xl font-bold">{{ data.totals.total_sessions }}</div>
            <p class="text-xs text-muted-foreground mt-1">
              ~{{ (data.totals.total_sessions / days).toFixed(1) }}{{ t('analytics.perDayAvg') }}
            </p>
          </div>
        </div>

        <div class="border border-border bg-card">
          <div class="flex flex-row items-center justify-between px-4 pt-4 pb-2">
            <span class="text-sm font-medium">{{ t('analytics.apiCalls') }}</span>
            <TrendingUp class="h-4 w-4 text-muted-foreground" />
          </div>
          <div class="px-4 pb-4">
            <div class="text-2xl font-bold">{{ data.totals.total_api_calls }}</div>
            <p class="text-xs text-muted-foreground mt-1">
              {{ t('analytics.acrossModels').replace('{count}', String(data.by_model.length)) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Token bar chart -->
      <div v-if="data.daily.length > 0" class="border border-border bg-card">
        <div class="px-4 pt-4 pb-2">
          <div class="flex items-center gap-2">
            <BarChart3 class="h-5 w-5 text-muted-foreground" />
            <span class="text-base font-semibold">{{ t('analytics.dailyTokenUsage') }}</span>
          </div>
          <div class="flex items-center gap-4 text-xs text-muted-foreground mt-1">
            <div class="flex items-center gap-1.5">
              <div class="h-2.5 w-2.5 bg-[#ffe6cb]" />
              {{ t('analytics.input') }}
            </div>
            <div class="flex items-center gap-1.5">
              <div class="h-2.5 w-2.5 bg-emerald-500" />
              {{ t('analytics.output') }}
            </div>
          </div>
        </div>
        <div class="px-4 pb-4">
          <div class="flex items-end gap-[2px]" :style="{ height: CHART_HEIGHT_PX + 'px' }">
            <div
              v-for="d in data.daily"
              :key="d.day"
              class="flex-1 min-w-0 group relative flex flex-col justify-end"
              :style="{ height: CHART_HEIGHT_PX + 'px' }"
            >
              <div
                class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10 pointer-events-none"
              >
                <div
                  class="bg-card border border-border px-2.5 py-1.5 text-[10px] text-foreground shadow-lg whitespace-nowrap"
                >
                  <div class="font-medium">{{ formatDate(d.day) }}</div>
                  <div>{{ t('analytics.input') }}: {{ formatTokens(d.input_tokens) }}</div>
                  <div>{{ t('analytics.output') }}: {{ formatTokens(d.output_tokens) }}</div>
                  <div>
                    {{ t('analytics.total') }}: {{ formatTokens(d.input_tokens + d.output_tokens) }}
                  </div>
                </div>
              </div>
              <div
                class="w-full bg-[#ffe6cb]/70"
                :style="{
                  height: Math.max(
                    Math.round((d.input_tokens / maxTokens) * CHART_HEIGHT_PX),
                    d.input_tokens + d.output_tokens > 0 ? 1 : 0,
                  ) + 'px',
                }"
              />
              <div
                class="w-full bg-emerald-500/70"
                :style="{
                  height: Math.max(
                    Math.round((d.output_tokens / maxTokens) * CHART_HEIGHT_PX),
                    d.output_tokens > 0 ? 1 : 0,
                  ) + 'px',
                }"
              />
            </div>
          </div>
          <div class="flex justify-between mt-2 text-[10px] text-muted-foreground">
            <span>{{ data.daily.length > 0 ? formatDate(data.daily[0].day) : '' }}</span>
            <span v-if="data.daily.length > 2">
              {{ formatDate(data.daily[Math.floor(data.daily.length / 2)].day) }}
            </span>
            <span>{{ data.daily.length > 1 ? formatDate(data.daily[data.daily.length - 1].day) : '' }}</span>
          </div>
        </div>
      </div>

      <!-- Daily breakdown table -->
      <div v-if="data.daily.length > 0" class="border border-border bg-card">
        <div class="px-4 pt-4 pb-2 flex items-center gap-2">
          <TrendingUp class="h-5 w-5 text-muted-foreground" />
          <span class="text-base font-semibold">{{ t('analytics.dailyBreakdown') }}</span>
        </div>
        <div class="px-4 pb-4 overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border text-muted-foreground text-xs">
                <th class="text-left py-2 pr-4 font-medium">{{ t('analytics.date') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('sessions.title') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('analytics.input') }}</th>
                <th class="text-right py-2 pl-4 font-medium">{{ t('analytics.output') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="d in sortedDaily"
                :key="d.day"
                class="border-b border-border/50 hover:bg-secondary/20 transition-colors"
              >
                <td class="py-2 pr-4 font-medium">{{ formatDate(d.day) }}</td>
                <td class="text-right py-2 px-4 text-muted-foreground">{{ d.sessions }}</td>
                <td class="text-right py-2 px-4">
                  <span class="text-[#ffe6cb]">{{ formatTokens(d.input_tokens) }}</span>
                </td>
                <td class="text-right py-2 pl-4">
                  <span class="text-emerald-400">{{ formatTokens(d.output_tokens) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Per-model breakdown table -->
      <div v-if="data.by_model.length > 0" class="border border-border bg-card">
        <div class="px-4 pt-4 pb-2 flex items-center gap-2">
          <Cpu class="h-5 w-5 text-muted-foreground" />
          <span class="text-base font-semibold">{{ t('analytics.perModelBreakdown') }}</span>
        </div>
        <div class="px-4 pb-4 overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border text-muted-foreground text-xs">
                <th class="text-left py-2 pr-4 font-medium">{{ t('analytics.model') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('sessions.title') }}</th>
                <th class="text-right py-2 pl-4 font-medium">{{ t('analytics.tokens') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="m in sortedModels"
                :key="m.model"
                class="border-b border-border/50 hover:bg-secondary/20 transition-colors"
              >
                <td class="py-2 pr-4">
                  <span class="font-mono-ui text-xs">{{ m.model }}</span>
                </td>
                <td class="text-right py-2 px-4 text-muted-foreground">{{ m.sessions }}</td>
                <td class="text-right py-2 pl-4">
                  <span class="text-[#ffe6cb]">{{ formatTokens(m.input_tokens) }}</span>
                  {{ ' / ' }}
                  <span class="text-emerald-400">{{ formatTokens(m.output_tokens) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Top skills table -->
      <div v-if="data.skills.top_skills.length > 0" class="border border-border bg-card">
        <div class="px-4 pt-4 pb-2 flex items-center gap-2">
          <Brain class="h-5 w-5 text-muted-foreground" />
          <span class="text-base font-semibold">{{ t('analytics.topSkills') }}</span>
        </div>
        <div class="px-4 pb-4 overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border text-muted-foreground text-xs">
                <th class="text-left py-2 pr-4 font-medium">{{ t('analytics.skill') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('analytics.loads') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('analytics.edits') }}</th>
                <th class="text-right py-2 px-4 font-medium">{{ t('analytics.total') }}</th>
                <th class="text-right py-2 pl-4 font-medium">{{ t('analytics.lastUsed') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="skill in data.skills.top_skills"
                :key="skill.skill"
                class="border-b border-border/50 hover:bg-secondary/20 transition-colors"
              >
                <td class="py-2 pr-4">
                  <span class="font-mono-ui text-xs">{{ skill.skill }}</span>
                </td>
                <td class="text-right py-2 px-4 text-muted-foreground">{{ skill.view_count }}</td>
                <td class="text-right py-2 px-4 text-muted-foreground">{{ skill.manage_count }}</td>
                <td class="text-right py-2 px-4">{{ skill.total_count }}</td>
                <td class="text-right py-2 pl-4 text-muted-foreground">
                  {{ skill.last_used_at ? timeAgo(skill.last_used_at) : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div
      v-if="
        data &&
        data.daily.length === 0 &&
        data.by_model.length === 0 &&
        data.skills.top_skills.length === 0
      "
      class="border border-border bg-card py-12"
    >
      <div class="flex flex-col items-center text-muted-foreground">
        <BarChart3 class="h-8 w-8 mb-3 opacity-40" />
        <p class="text-sm font-medium">{{ t('analytics.noUsageData') }}</p>
        <p class="text-xs mt-1 text-muted-foreground/60">
          {{ t('analytics.startSession') }}
        </p>
      </div>
    </div>

    <PluginSlot name="analytics:bottom" />
  </div>
</template>
