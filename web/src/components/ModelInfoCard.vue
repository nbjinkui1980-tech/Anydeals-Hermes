<script setup lang="ts">
import { ref, watch } from "vue";
import {
  Brain,
  Eye,
  Gauge,
  Lightbulb,
  Wrench,
  Loader2,
} from "lucide-vue-next";
import { api } from "@/lib/api";
import type { ModelInfoResponse } from "@/lib/api";
import { formatTokenCount } from "@/lib/format";

const props = defineProps<{
  currentModel: string;
  refreshKey?: number;
}>();

const info = ref<ModelInfoResponse | null>(null);
const loading = ref(false);
let lastFetchKey = "";

watch(
  () => `${props.currentModel}:${props.refreshKey ?? 0}`,
  (fetchKey) => {
    if (!props.currentModel) return;
    if (fetchKey === lastFetchKey) return;
    lastFetchKey = fetchKey;
    loading.value = true;
    api
      .getModelInfo()
      .then((r) => {
        info.value = r;
      })
      .catch(() => {
        info.value = null;
      })
      .finally(() => {
        loading.value = false;
      });
  },
  { immediate: true },
);
</script>

<template>
  <div v-if="loading" class="flex items-center gap-2 py-2 text-xs text-muted-foreground">
    <Loader2 class="h-3 w-3 animate-spin" />
    Loading model info…
  </div>

  <div
    v-else-if="info && info.model && info.effective_context_length > 0"
    class="border border-border/60 bg-muted/30 px-3 py-2.5 space-y-2"
  >
    <!-- Context window -->
    <div class="flex items-center gap-4 text-xs">
      <div class="flex items-center gap-1.5 text-muted-foreground">
        <Gauge class="h-3.5 w-3.5" />
        <span class="font-medium">Context Window</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="font-mono font-semibold text-foreground">
          {{ formatTokenCount(info.effective_context_length) }}
        </span>
        <span
          v-if="info.config_context_length > 0"
          class="text-amber-500/80 text-[10px]"
        >
          (override — auto: {{ formatTokenCount(info.auto_context_length) }})
        </span>
        <span v-else class="text-muted-foreground/60 text-[10px]">auto-detected</span>
      </div>
    </div>

    <!-- Max output -->
    <div
      v-if="info.capabilities.max_output_tokens && info.capabilities.max_output_tokens > 0"
      class="flex items-center gap-4 text-xs"
    >
      <div class="flex items-center gap-1.5 text-muted-foreground">
        <Lightbulb class="h-3.5 w-3.5" />
        <span class="font-medium">Max Output</span>
      </div>
      <span class="font-mono font-semibold text-foreground">
        {{ formatTokenCount(info.capabilities.max_output_tokens) }}
      </span>
    </div>

    <!-- Capability badges -->
    <div v-if="info.capabilities" class="flex flex-wrap items-center gap-1.5 pt-0.5">
      <span
        v-if="info.capabilities.supports_tools"
        class="inline-flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400"
      >
        <Wrench class="h-2.5 w-2.5" /> Tools
      </span>
      <span
        v-if="info.capabilities.supports_vision"
        class="inline-flex items-center gap-1 bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-600 dark:text-blue-400"
      >
        <Eye class="h-2.5 w-2.5" /> Vision
      </span>
      <span
        v-if="info.capabilities.supports_reasoning"
        class="inline-flex items-center gap-1 bg-purple-500/10 px-2 py-0.5 text-[10px] font-medium text-purple-600 dark:text-purple-400"
      >
        <Brain class="h-2.5 w-2.5" /> Reasoning
      </span>
      <span
        v-if="info.capabilities.model_family"
        class="inline-flex items-center gap-1 bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
      >
        {{ info.capabilities.model_family }}
      </span>
    </div>
  </div>
</template>
