<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { NButton, NInput } from "naive-ui";
import { Check, Loader2, Search, X } from "lucide-vue-next";
import type { GatewayClient } from "@/lib/gatewayClient";

interface ModelOptionProvider {
  name: string;
  slug: string;
  models?: string[];
  total_models?: number;
  is_current?: boolean;
  warning?: string;
}

interface ModelOptionsResponse {
  model?: string;
  provider?: string;
  providers?: ModelOptionProvider[];
}

const props = defineProps<{
  gw: GatewayClient;
  sessionId: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", slashCommand: string): void;
}>();

const providers = ref<ModelOptionProvider[]>([]);
const currentModel = ref("");
const currentProviderSlug = ref("");
const loading = ref(true);
const error = ref<string | null>(null);
const selectedSlug = ref("");
const selectedModel = ref("");
const query = ref("");
const persistGlobal = ref(false);
let closed = false;

onMounted(async () => {
  closed = false;
  try {
    const r = await props.gw.request<ModelOptionsResponse>(
      "model.options",
      props.sessionId ? { session_id: props.sessionId } : {},
    );
    if (closed) return;
    const next = r?.providers ?? [];
    providers.value = next;
    currentModel.value = String(r?.model ?? "");
    currentProviderSlug.value = String(r?.provider ?? "");
    selectedSlug.value =
      (next.find((p) => p.is_current) ?? next[0])?.slug ?? "";
    selectedModel.value = "";
    loading.value = false;
  } catch (e) {
    if (closed) return;
    error.value = e instanceof Error ? e.message : String(e);
    loading.value = false;
  }
});

onUnmounted(() => {
  closed = true;
});

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") {
    e.preventDefault();
    emit("close");
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKey);
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKey);
});

const selectedProvider = computed(
  () => providers.value.find((p) => p.slug === selectedSlug.value) ?? null,
);

const models = computed(() => selectedProvider.value?.models ?? []);

const needle = computed(() => query.value.trim().toLowerCase());

const filteredProviders = computed(() =>
  !needle.value
    ? providers.value
    : providers.value.filter(
        (p) =>
          p.name.toLowerCase().includes(needle.value) ||
          p.slug.toLowerCase().includes(needle.value) ||
          (p.models ?? []).some((m) =>
            m.toLowerCase().includes(needle.value),
          ),
      ),
);

const filteredModels = computed(() =>
  !needle.value
    ? models.value
    : models.value.filter((m) => m.toLowerCase().includes(needle.value)),
);

const canConfirm = computed(
  () => !!selectedProvider.value && !!selectedModel.value,
);

function confirm() {
  if (!canConfirm.value) return;
  const global = persistGlobal.value ? " --global" : "";
  emit(
    "submit",
    `/model ${selectedModel.value} --provider ${selectedProvider.value!.slug}${global}`,
  );
  emit("close");
}
</script>

<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-background/85 backdrop-blur-sm p-4"
    role="dialog"
    aria-modal="true"
    aria-labelledby="model-picker-title"
    @click.self="emit('close')"
  >
    <div
      class="relative w-full max-w-3xl max-h-[80vh] border border-border bg-card shadow-2xl flex flex-col"
    >
      <button
        type="button"
        class="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        aria-label="Close"
        @click="emit('close')"
      >
        <X class="h-5 w-5" />
      </button>

      <header class="p-5 pb-3 border-b border-border">
        <h2
          id="model-picker-title"
          class="font-display text-base tracking-wider uppercase"
        >
          Switch Model
        </h2>
        <p class="text-xs text-muted-foreground mt-1 font-mono">
          current: {{ currentModel || "(unknown)" }}
          <template v-if="currentProviderSlug"> · {{ currentProviderSlug }}</template>
        </p>
      </header>

      <div class="px-5 pt-3 pb-2 border-b border-border">
        <div class="relative">
          <Search class="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <NInput
            size="small"
            placeholder="Filter providers and models…"
            :value="query"
            @update:value="(v: string) => query = v"
          />
        </div>
      </div>

      <div class="flex-1 min-h-0 grid grid-cols-[200px_1fr] overflow-hidden">
        <!-- Provider column -->
        <div class="border-r border-border overflow-y-auto">
          <div v-if="loading" class="flex items-center gap-2 p-4 text-xs text-muted-foreground">
            <Loader2 class="h-3 w-3 animate-spin" /> loading…
          </div>

          <div v-else-if="error" class="p-4 text-xs text-destructive">{{ error }}</div>

          <div
            v-else-if="filteredProviders.length === 0"
            class="p-4 text-xs text-muted-foreground italic"
          >
            {{ query ? 'no matches' : providers.length === 0 ? 'no authenticated providers' : 'no matches' }}
          </div>

          <button
            v-for="p in filteredProviders"
            :key="p.slug"
            type="button"
            class="w-full text-left px-3 py-2 text-xs border-l-2 transition-colors cursor-pointer flex items-start gap-2"
            :class="
              p.slug === selectedSlug
                ? 'bg-primary/10 border-l-primary text-foreground'
                : 'border-l-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
            "
            @click="selectedSlug = p.slug; selectedModel = ''"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="font-medium truncate">{{ p.name }}</span>
                <span
                  v-if="p.is_current"
                  class="text-[0.6rem] uppercase tracking-wider text-primary/80 shrink-0"
                >current</span>
              </div>
              <div class="text-[0.65rem] text-muted-foreground/80 font-mono truncate">
                {{ p.slug }} · {{ p.total_models ?? p.models?.length ?? 0 }} models
              </div>
            </div>
          </button>
        </div>

        <!-- Model column -->
        <div class="overflow-y-auto">
          <div
            v-if="!selectedProvider"
            class="p-4 text-xs text-muted-foreground italic"
          >
            pick a provider →
          </div>

          <template v-else>
            <div
              v-if="selectedProvider.warning"
              class="p-3 text-xs text-destructive border-b border-border"
            >
              {{ selectedProvider.warning }}
            </div>

            <div
              v-if="filteredModels.length === 0"
              class="p-4 text-xs text-muted-foreground italic"
            >
              {{ models.length ? 'no models match your filter' : 'no models listed for this provider' }}
            </div>

            <button
              v-for="m in filteredModels"
              :key="m"
              type="button"
              class="w-full text-left px-3 py-1.5 text-xs font-mono transition-colors cursor-pointer flex items-center gap-2"
              :class="
                m === selectedModel
                  ? 'bg-primary/15 text-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
              "
              @click="selectedModel = m"
              @dblclick="selectedModel = m; confirm()"
            >
              <Check
                class="h-3 w-3 shrink-0"
                :class="m === selectedModel ? 'text-primary' : 'text-transparent'"
              />
              <span class="flex-1 truncate">{{ m }}</span>
              <span
                v-if="m === currentModel && selectedProvider.slug === currentProviderSlug"
                class="text-[0.6rem] uppercase tracking-wider text-primary/80 shrink-0"
              >current</span>
            </button>
          </template>
        </div>
      </div>

      <footer class="border-t border-border p-3 flex items-center justify-between gap-3 flex-wrap">
        <label class="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none">
          <input
            type="checkbox"
            :checked="persistGlobal"
            @change="persistGlobal = ($event.target as HTMLInputElement).checked"
            class="cursor-pointer"
          />
          Persist globally (otherwise this session only)
        </label>

        <div class="flex items-center gap-2 ml-auto">
          <NButton size="small" @click="emit('close')">
            Cancel
          </NButton>
          <NButton size="small" type="primary" :disabled="!canConfirm" @click="confirm">
            Switch
          </NButton>
        </div>
      </footer>
    </div>
  </div>
</template>
