<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import { RefreshCw } from "lucide-vue-next";
import { NButton, NSelect, NSwitch, NTag } from "naive-ui";
import { api } from "@/lib/api";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const FILES = ["agent", "errors", "gateway"] as const;
const LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"] as const;
const COMPONENTS = ["all", "gateway", "agent", "tools", "cli", "cron"] as const;
const LINE_COUNTS = [50, 100, 200, 500] as const;

const file = ref<string>("agent");
const level = ref<string>("ALL");
const component = ref<string>("all");
const lineCount = ref<number>(100);
const autoRefresh = ref(false);
const lines = ref<string[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const scrollRef = ref<HTMLElement | null>(null);

const fileOpts = FILES.map((v) => ({ label: v, value: v }));
const levelOpts = LEVELS.map((v) => ({ label: v, value: v }));
const compOpts = COMPONENTS.map((v) => ({ label: v, value: v }));
const lineOpts = LINE_COUNTS.map((n) => ({ label: String(n), value: n }));

function classifyLine(line: string): string {
  const upper = line.toUpperCase();
  if (upper.includes("ERROR") || upper.includes("CRITICAL") || upper.includes("FATAL")) return "error";
  if (upper.includes("WARNING") || upper.includes("WARN")) return "warning";
  if (upper.includes("DEBUG")) return "debug";
  return "info";
}

const LINE_COLORS: Record<string, string> = {
  error: "text-destructive",
  warning: "text-warning",
  info: "text-foreground",
  debug: "text-muted-foreground/60",
};

async function fetchLogs() {
  loading.value = true;
  error.value = null;
  try {
    const resp = await api.getLogs({ file: file.value, lines: lineCount.value, level: level.value, component: component.value });
    lines.value = resp.lines;
    await nextTick();
    if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
  } catch (err) {
    error.value = String(err);
  } finally {
    loading.value = false;
  }
}

let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  fetchLogs();
});

watch(autoRefresh, (on) => {
  if (timer) { clearInterval(timer); timer = null; }
  if (on) timer = setInterval(fetchLogs, 5000);
});

watch([file, level, component, lineCount], () => {
  fetchLogs();
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Filter toolbar -->
    <div role="toolbar" :aria-label="t('logs.title')" class="flex flex-wrap items-center gap-x-6 gap-y-2">
      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-foreground">{{ t('logs.file') }}</span>
        <NSelect v-model:value="file" :options="fileOpts" size="small" style="width:100px" />
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-foreground">{{ t('logs.level') }}</span>
        <NSelect v-model:value="level" :options="levelOpts" size="small" style="width:100px" />
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-foreground">{{ t('logs.component') }}</span>
        <NSelect v-model:value="component" :options="compOpts" size="small" style="width:110px" />
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-foreground">{{ t('logs.lines') }}</span>
        <NSelect v-model:value="lineCount" :options="lineOpts" size="small" style="width:80px" />
      </div>
    </div>

    <!-- Controls bar -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <NSwitch v-model:value="autoRefresh" size="small" />
        <span class="text-xs cursor-pointer">{{ t('logs.autoRefresh') }}</span>
        <NTag v-if="autoRefresh" type="success" size="small" :bordered="false">
          <span class="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
          {{ t('common.live') }}
        </NTag>
      </div>
      <NButton size="small" :disabled="loading" @click="fetchLogs">
        <template #icon><RefreshCw class="h-3 w-3" /></template>
        {{ t('common.refresh') }}
      </NButton>
    </div>

    <!-- Log viewer -->
    <div class="border border-border bg-card">
      <div class="py-3 px-4 border-b border-border flex items-center gap-2">
        <span class="text-sm font-semibold tracking-wide">{{ file }}.log</span>
        <NTag size="small" :bordered="false">{{ level }} · {{ component }} · {{ lines.length }} lines</NTag>
      </div>

      <div v-if="error" class="bg-destructive/10 border-b border-destructive/20 p-3">
        <p class="text-sm text-destructive">{{ error }}</p>
      </div>

      <div
        ref="scrollRef"
        class="p-4 font-mono text-xs leading-5 overflow-auto min-h-[400px] max-h-[calc(100vh-280px)]"
      >
        <p v-if="lines.length === 0 && !loading" class="text-muted-foreground text-center py-8">
          {{ t('logs.noLogLines') }}
        </p>
        <div
          v-for="(line, i) in lines"
          :key="i"
          class="hover:bg-secondary/20 px-1 -mx-1"
          :class="LINE_COLORS[classifyLine(line)]"
        >
          {{ line }}
        </div>
      </div>
    </div>
  </div>
</template>
