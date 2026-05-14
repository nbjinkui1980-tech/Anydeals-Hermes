<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { ChevronRight } from "lucide-vue-next";
import type { GatewayClient } from "@/lib/gatewayClient";

export interface CompletionItem {
  display: string;
  text: string;
  meta?: string;
}

interface CompletionResponse {
  items?: CompletionItem[];
  replace_from?: number;
}

const DEBOUNCE_MS = 60;

const props = defineProps<{
  input: string;
  gw: GatewayClient | null;
}>();

const emit = defineEmits<{
  (e: "apply", nextInput: string): void;
}>();

const items = ref<CompletionItem[]>([]);
const selected = ref(0);
const replaceFrom = ref(1);
let lastInput = "";

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.input,
  (trimmed) => {
    trimmed = trimmed ?? "";

    if (
      !props.gw ||
      !trimmed.startsWith("/") ||
      trimmed === lastInput
    ) {
      if (!trimmed.startsWith("/")) lastInput = "";
      return;
    }
    lastInput = trimmed;

    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      if (lastInput !== trimmed) return;
      try {
        const r = await props.gw!.request<CompletionResponse>(
          "complete.slash",
          { text: trimmed },
        );
        if (lastInput !== trimmed) return;
        items.value = r?.items ?? [];
        replaceFrom.value = r?.replace_from ?? 1;
        selected.value = 0;
      } catch {
        if (lastInput === trimmed) items.value = [];
      }
    }, DEBOUNCE_MS);
  },
);

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer);
});

const visible = computed(
  () => items.value.length > 0 && props.input.startsWith("/"),
);

function apply(item: CompletionItem) {
  emit("apply", props.input.slice(0, replaceFrom.value) + item.text);
}

function handleKey(e: KeyboardEvent): boolean {
  if (!visible.value) return false;

  switch (e.key) {
    case "ArrowDown":
      e.preventDefault();
      selected.value = (selected.value + 1) % items.value.length;
      return true;

    case "ArrowUp":
      e.preventDefault();
      selected.value =
        (selected.value - 1 + items.value.length) % items.value.length;
      return true;

    case "Tab": {
      e.preventDefault();
      const item = items.value[selected.value];
      if (item) apply(item);
      return true;
    }

    case "Escape":
      e.preventDefault();
      items.value = [];
      return true;

    default:
      return false;
  }
}

defineExpose({ handleKey });
</script>

<template>
  <div
    v-if="visible"
    class="absolute bottom-full left-0 right-0 mb-2 max-h-64 overflow-y-auto rounded-md border border-border bg-popover shadow-xl text-sm"
    role="listbox"
  >
    <button
      v-for="(it, i) in items"
      :key="`${it.text}-${i}`"
      type="button"
      role="option"
      :aria-selected="i === selected"
      class="w-full flex items-center gap-2 px-3 py-1.5 text-left cursor-pointer transition-colors"
      :class="
        i === selected
          ? 'bg-primary/10 text-foreground'
          : 'text-muted-foreground hover:bg-muted/60'
      "
      @mouseenter="selected = i"
      @click="apply(it)"
    >
      <ChevronRight
        class="h-3 w-3 shrink-0"
        :class="i === selected ? 'text-primary' : 'text-transparent'"
      />

      <span class="font-mono text-xs shrink-0 truncate">
        {{ it.display }}
      </span>

      <span
        v-if="it.meta"
        class="text-[0.7rem] text-muted-foreground/70 truncate ml-auto"
      >
        {{ it.meta }}
      </span>
    </button>
  </div>
</template>
