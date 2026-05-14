<script setup lang="ts">
import { ref, computed, onUnmounted } from "vue";
import {
  AlertCircle,
  Check,
  ChevronDown,
  ChevronRight,
  Zap,
} from "lucide-vue-next";

export interface ToolEntry {
  kind: "tool";
  id: string;
  tool_id: string;
  name: string;
  context?: string;
  preview?: string;
  summary?: string;
  error?: string;
  inline_diff?: string;
  status: "running" | "done" | "error";
  startedAt: number;
  completedAt?: number;
}

const props = defineProps<{ tool: ToolEntry }>();

const STATUS_TONE: Record<ToolEntry["status"], string> = {
  running: "border-primary/40 bg-primary/[0.04]",
  done: "border-border bg-muted/20",
  error: "border-destructive/50 bg-destructive/[0.04]",
};

const BULLET_TONE: Record<ToolEntry["status"], string> = {
  running: "text-primary",
  done: "text-primary/80",
  error: "text-destructive",
};

const TICK_MS = 500;

const userOverride = ref<boolean | null>(null);
const open = computed(
  () => userOverride.value ?? props.tool.status === "error",
);

const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | null = null;

if (props.tool.status === "running") {
  timer = setInterval(() => {
    now.value = Date.now();
  }, TICK_MS);
}

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const hasTimestamps = props.tool.startedAt > 0;
const elapsed = computed(() => {
  if (!hasTimestamps) return null;
  return fmtElapsed(
    (props.tool.completedAt ?? now.value) - props.tool.startedAt,
  );
});

const hasBody = computed(
  () =>
    !!(
      props.tool.context ||
      props.tool.preview ||
      props.tool.summary ||
      props.tool.error ||
      props.tool.inline_diff
    ),
);

function fmtElapsed(ms: number): string {
  const sec = Math.max(0, ms) / 1000;
  if (sec < 1) return `${Math.round(ms)}ms`;
  if (sec < 10) return `${sec.toFixed(1)}s`;
  if (sec < 60) return `${Math.round(sec)}s`;

  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return s ? `${m}m ${s}s` : `${m}m`;
}

function diffLineClass(line: string): string {
  if (line.startsWith("+") && !line.startsWith("+++"))
    return "text-emerald-500 dark:text-emerald-400";
  if (line.startsWith("-") && !line.startsWith("---")) return "text-destructive";
  if (line.startsWith("@@")) return "text-primary";
  return "text-muted-foreground/80";
}
</script>

<template>
  <div class="rounded-md border overflow-hidden" :class="STATUS_TONE[tool.status]">
    <button
      type="button"
      :disabled="!hasBody"
      :aria-expanded="open"
      class="w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-xs hover:bg-foreground/2 disabled:cursor-default cursor-pointer transition-colors"
      @click="userOverride = !open"
    >
      <ChevronDown v-if="open && hasBody" class="h-3 w-3 shrink-0 text-muted-foreground" />
      <ChevronRight v-else-if="hasBody" class="h-3 w-3 shrink-0 text-muted-foreground" />
      <span v-else class="w-3 shrink-0" />

      <Zap class="h-3 w-3 shrink-0" :class="BULLET_TONE[tool.status]" />

      <span class="font-mono font-medium shrink-0">{{ tool.name }}</span>

      <span class="font-mono text-muted-foreground/80 truncate min-w-0 flex-1">
        {{ tool.context ?? "" }}
      </span>

      <span
        v-if="tool.status === 'running'"
        class="inline-block h-2 w-2 rounded-full bg-primary animate-pulse shrink-0"
        title="running"
      />
      <AlertCircle
        v-if="tool.status === 'error'"
        class="h-3 w-3 shrink-0 text-destructive"
        aria-label="error"
      />
      <Check
        v-if="tool.status === 'done'"
        class="h-3 w-3 shrink-0 text-primary/80"
        aria-label="done"
      />

      <span
        v-if="elapsed"
        class="font-mono text-[0.65rem] text-muted-foreground tabular-nums shrink-0"
      >
        {{ elapsed }}
      </span>
    </button>

    <div
      v-if="open && hasBody"
      class="border-t border-border/60 px-3 py-2 space-y-2 text-xs font-mono"
    >
      <div v-if="tool.context" class="flex gap-3">
        <span class="uppercase tracking-wider text-[0.6rem] shrink-0 w-14 pt-0.5 text-muted-foreground/60">
          context
        </span>
        <div class="flex-1 min-w-0 text-muted-foreground">{{ tool.context }}</div>
      </div>

      <div v-if="tool.preview && tool.status === 'running'" class="flex gap-3">
        <span class="uppercase tracking-wider text-[0.6rem] shrink-0 w-14 pt-0.5 text-muted-foreground/60">
          streaming
        </span>
        <div class="flex-1 min-w-0 text-muted-foreground">
          {{ tool.preview }}
          <span class="inline-block w-1.5 h-3 align-middle bg-foreground/40 ml-0.5 animate-pulse" />
        </div>
      </div>

      <div v-if="tool.inline_diff" class="flex gap-3">
        <span class="uppercase tracking-wider text-[0.6rem] shrink-0 w-14 pt-0.5 text-muted-foreground/60">
          diff
        </span>
        <pre class="flex-1 min-w-0 whitespace-pre overflow-x-auto text-[0.7rem] leading-snug">
          <div
            v-for="(line, idx) in tool.inline_diff.split('\n')"
            :key="idx"
            :class="diffLineClass(line)"
          >
            {{ line || ' ' }}
          </div>
        </pre>
      </div>

      <div v-if="tool.summary" class="flex gap-3">
        <span class="uppercase tracking-wider text-[0.6rem] shrink-0 w-14 pt-0.5 text-muted-foreground/60">
          result
        </span>
        <div class="flex-1 min-w-0 text-foreground/90 whitespace-pre-wrap">{{ tool.summary }}</div>
      </div>

      <div v-if="tool.error" class="flex gap-3">
        <span class="uppercase tracking-wider text-[0.6rem] shrink-0 w-14 pt-0.5 text-destructive/80">
          error
        </span>
        <div class="flex-1 min-w-0 text-destructive whitespace-pre-wrap">{{ tool.error }}</div>
      </div>
    </div>
  </div>
</template>
