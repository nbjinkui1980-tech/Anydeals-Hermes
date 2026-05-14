<script setup lang="ts">
import { ref, computed, watch, onMounted, h } from "vue";
import {
  Code,
  Download,
  FormInput,
  RotateCcw,
  Save,
  Search,
  Upload,
  X,
  Settings2,
  FileText,
  Settings,
  Bot,
  Monitor,
  Palette,
  Users,
  Brain,
  Package,
  Lock,
  Globe,
  Mic,
  Volume2,
  Ear,
  ClipboardList,
  MessageCircle,
  Wrench,
  FileQuestion,
  Filter,
} from "lucide-vue-next";
import { NButton, NTag, NInput } from "naive-ui";
import { api } from "@/lib/api";
import { getNestedValue, setNestedValue } from "@/lib/nested";
import { showToast } from "@/components/Toast";
import AutoField from "@/components/AutoField.vue";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";
import PluginSlot from "@/components/PluginSlot.vue";

const { t } = useI18n();
const { setEnd } = usePageHeader();

const CATEGORY_ICONS: Record<string, any> = {
  general: Settings,
  agent: Bot,
  terminal: Monitor,
  display: Palette,
  delegation: Users,
  memory: Brain,
  compression: Package,
  security: Lock,
  browser: Globe,
  voice: Mic,
  tts: Volume2,
  stt: Ear,
  logging: ClipboardList,
  discord: MessageCircle,
  auxiliary: Wrench,
};

function getCategoryIcon(cat: string) {
  return CATEGORY_ICONS[cat] ?? FileQuestion;
}

function prettyCategoryName(cat: string): string {
  const tr = (t as any)("config.categories." + cat);
  if (tr && tr !== "config.categories." + cat) return tr;
  return cat.charAt(0).toUpperCase() + cat.slice(1);
}

/* ---- State ---- */

const config = ref<Record<string, unknown> | null>(null);
const schema = ref<Record<string, Record<string, unknown>> | null>(null);
const categoryOrder = ref<string[]>([]);
const defaults = ref<Record<string, unknown> | null>(null);
const saving = ref(false);
const searchQuery = ref("");
const yamlMode = ref(false);
const yamlText = ref("");
const yamlLoading = ref(false);
const yamlSaving = ref(false);
const activeCategory = ref("");
const fileInputRef = ref<HTMLInputElement | null>(null);

onMounted(async () => {
  try { config.value = await api.getConfig(); } catch { /* */ }
  try {
    const resp = await api.getSchema();
    schema.value = resp.fields as Record<string, Record<string, unknown>>;
    categoryOrder.value = resp.category_order ?? [];
  } catch { /* */ }
  try { defaults.value = await api.getDefaults(); } catch { /* */ }
});

/* ---- Page header search ---- */

watch([config, schema, searchQuery], () => {
  if (!config.value || !schema.value) {
    setEnd(null);
    return;
  }
  setEnd(
    h("div", { class: "relative w-full min-w-0 sm:max-w-xs" }, [
      h(Search, { class: "absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" }),
      h(NInput, {
        size: "small",
        class: "pl-8 pr-7 text-xs",
        placeholder: t("common.search"),
        value: searchQuery.value,
        onUpdateValue: (v: string) => { searchQuery.value = v; },
      }),
      searchQuery.value
        ? h(
            "button",
            {
              type: "button",
              class: "absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground",
              onClick: () => { searchQuery.value = ""; },
            },
            h(X, { class: "h-3 w-3" }),
          )
        : null,
    ]),
  );
}, { immediate: true });

/* ---- Derived ---- */

const categories = computed(() => {
  if (!schema.value) return [];
  const allCats = [...new Set(Object.values(schema.value).map((s) => String(s.category ?? "general")))];
  const ordered = categoryOrder.value.filter((c) => allCats.includes(c));
  const extra = allCats.filter((c) => !categoryOrder.value.includes(c)).sort();
  return [...ordered, ...extra];
});

const categoryCounts = computed(() => {
  if (!schema.value) return {} as Record<string, number>;
  const counts: Record<string, number> = {};
  for (const s of Object.values(schema.value)) {
    const cat = String(s.category ?? "general");
    counts[cat] = (counts[cat] || 0) + 1;
  }
  return counts;
});

const isSearching = computed(() => searchQuery.value.trim().length > 0);
const lowerSearch = computed(() => searchQuery.value.toLowerCase());

const searchMatchedFields = computed(() => {
  if (!isSearching.value || !schema.value) return [];
  return Object.entries(schema.value).filter(([key, s]) => {
    const label = key.split(".").pop() ?? key;
    const humanLabel = label.replace(/_/g, " ");
    return (
      key.toLowerCase().includes(lowerSearch.value) ||
      humanLabel.toLowerCase().includes(lowerSearch.value) ||
      String(s.category ?? "").toLowerCase().includes(lowerSearch.value) ||
      String(s.description ?? "").toLowerCase().includes(lowerSearch.value)
    );
  });
});

const activeFields = computed(() => {
  if (!schema.value || isSearching.value) return [];
  return Object.entries(schema.value).filter(
    ([, s]) => String(s.category ?? "general") === activeCategory.value,
  );
});

/* ---- Set active category when categories load ---- */

watch(categories, (cats) => {
  if (cats.length > 0 && !activeCategory.value) {
    activeCategory.value = cats[0];
  }
});

/* ---- Load YAML when switching to YAML mode ---- */

watch(yamlMode, (ym) => {
  if (ym) {
    yamlLoading.value = true;
    api
      .getConfigRaw()
      .then((resp) => { yamlText.value = resp.yaml; })
      .catch(() => showToast({ message: t("config.failedToLoadRaw"), type: "error" }))
      .finally(() => { yamlLoading.value = false; });
  }
});

/* ---- Handlers ---- */

async function handleSave() {
  if (!config.value) return;
  saving.value = true;
  try {
    await api.saveConfig(config.value);
    showToast({ message: t("config.configSaved"), type: "success" });
  } catch (e) {
    showToast({ message: `${t("config.failedToSave")}: ${e}`, type: "error" });
  } finally {
    saving.value = false;
  }
}

async function handleYamlSave() {
  yamlSaving.value = true;
  try {
    await api.saveConfigRaw(yamlText.value);
    showToast({ message: t("config.yamlConfigSaved"), type: "success" });
    try { config.value = await api.getConfig(); } catch { /* */ }
  } catch (e) {
    showToast({ message: `${t("config.failedToSaveYaml")}: ${e}`, type: "error" });
  } finally {
    yamlSaving.value = false;
  }
}

function handleReset() {
  if (!defaults.value || !config.value) return;
  const scopedFields = isSearching.value ? searchMatchedFields.value : activeFields.value;
  if (scopedFields.length === 0) return;
  const scopeLabel = isSearching.value
    ? t("config.searchResults")
    : prettyCategoryName(activeCategory.value);
  const message = t("config.confirmResetScope").replace("{scope}", scopeLabel);
  if (!window.confirm(message)) return;
  let next: Record<string, unknown> = config.value;
  for (const [key] of scopedFields) {
    next = setNestedValue(next, key, getNestedValue(defaults.value, key));
  }
  config.value = next;
  showToast({ message: t("config.resetScopeToast").replace("{scope}", scopeLabel), type: "success" });
}

function handleExport() {
  if (!config.value) return;
  const blob = new Blob([JSON.stringify(config.value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "anydeals-config.json";
  a.click();
  URL.revokeObjectURL(url);
}

function handleImport(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const imported = JSON.parse(reader.result as string);
      config.value = imported;
      showToast({ message: t("config.configImported"), type: "success" });
    } catch {
      showToast({ message: t("config.invalidJson"), type: "error" });
    }
  };
  reader.readAsText(file);
}

/* ---- Loading state ---- */

const ready = computed(() => config.value && schema.value);
</script>

<template>
  <div class="flex flex-col gap-4">
    <PluginSlot name="config:top" />

    <!-- Loading -->
    <div
      v-if="!ready"
      class="flex items-center justify-center py-24"
    >
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <template v-if="ready">
      <!-- Header Bar -->
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <Settings2 class="h-4 w-4 text-muted-foreground" />
          <code class="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5">
            {{ t('config.configPath') }}
          </code>
        </div>
        <div class="flex items-center gap-1.5">
          <NButton text size="small" @click="handleExport" :title="t('config.exportConfig')">
            <template #icon><Download class="h-3.5 w-3.5" /></template>
          </NButton>
          <NButton text size="small" @click="fileInputRef?.click()" :title="t('config.importConfig')">
            <template #icon><Upload class="h-3.5 w-3.5" /></template>
          </NButton>
          <input ref="fileInputRef" type="file" accept=".json" class="hidden" @change="handleImport" />

          <NButton
            v-if="!yamlMode"
            text
            size="small"
            @click="handleReset"
            :title="t('config.resetScopeTooltip').replace('{scope}', isSearching ? t('config.searchResults') : prettyCategoryName(activeCategory))"
          >
            <template #icon><RotateCcw class="h-3.5 w-3.5" /></template>
          </NButton>

          <div class="w-px h-5 bg-border mx-1" />

          <NButton
            :type="yamlMode ? 'primary' : 'default'"
            size="small"
            @click="yamlMode = !yamlMode"
          >
            <template #icon>
              <FormInput v-if="yamlMode" class="h-3.5 w-3.5" />
              <Code v-else class="h-3.5 w-3.5" />
            </template>
            {{ yamlMode ? t('common.form') : 'YAML' }}
          </NButton>

          <NButton
            v-if="yamlMode"
            size="small"
            :disabled="yamlSaving"
            @click="handleYamlSave"
          >
            <template #icon><Save class="h-3.5 w-3.5" /></template>
            {{ yamlSaving ? t('common.saving') : t('common.save') }}
          </NButton>
          <NButton
            v-else
            size="small"
            :disabled="saving"
            @click="handleSave"
          >
            <template #icon><Save class="h-3.5 w-3.5" /></template>
            {{ saving ? t('common.saving') : t('common.save') }}
          </NButton>
        </div>
      </div>

      <!-- YAML Mode -->
      <div v-if="yamlMode" class="border border-border bg-card">
        <div class="px-4 py-3 border-b border-border">
          <span class="text-sm font-semibold flex items-center gap-2">
            <FileText class="h-4 w-4" />
            {{ t('config.rawYaml') }}
          </span>
        </div>
        <div>
          <div
            v-if="yamlLoading"
            class="flex items-center justify-center py-12"
          >
            <div class="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
          <textarea
            v-else
            class="flex min-h-[600px] w-full bg-transparent px-4 py-3 text-sm font-mono leading-relaxed placeholder:text-muted-foreground focus-visible:outline-none border-t border-border"
            :value="yamlText"
            @input="(e: Event) => yamlText = (e.target as HTMLTextAreaElement).value"
            spellcheck="false"
          />
        </div>
      </div>

      <!-- Form Mode -->
      <div v-else class="flex flex-col sm:flex-row gap-4">
        <!-- Filter panel -->
        <aside class="sm:w-56 sm:shrink-0">
          <div class="sm:sticky sm:top-4">
            <div class="flex flex-col border border-border bg-muted/20">
              <div class="hidden sm:flex items-center gap-2 px-3 py-2 border-b border-border">
                <Filter class="h-3 w-3 text-muted-foreground" />
                <span class="font-mondwest text-[0.65rem] tracking-[0.12em] uppercase text-muted-foreground">
                  {{ t('config.filters') }}
                </span>
              </div>

              <div class="hidden sm:block px-3 pt-2 pb-1 font-mondwest text-[0.6rem] tracking-[0.12em] uppercase text-muted-foreground/70">
                {{ t('config.sections') }}
              </div>

              <div class="flex sm:flex-col gap-1 sm:gap-px p-2 sm:pt-1 overflow-x-auto sm:overflow-x-visible scrollbar-none sm:max-h-[calc(100vh-260px)] sm:overflow-y-auto">
                <button
                  v-for="cat in categories"
                  :key="cat"
                  type="button"
                  class="group flex items-center gap-2 px-2 py-1 rounded-sm text-left text-[11px] cursor-pointer whitespace-nowrap transition-colors"
                  :class="!isSearching && activeCategory === cat
                    ? 'bg-foreground/10 text-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-foreground/5'"
                  @click="searchQuery = ''; activeCategory = cat"
                >
                  <component :is="getCategoryIcon(cat)" class="h-3.5 w-3.5 shrink-0" />
                  <span class="flex-1 truncate">{{ prettyCategoryName(cat) }}</span>
                  <span
                    class="text-[10px] tabular-nums"
                    :class="!isSearching && activeCategory === cat ? 'text-foreground/60' : 'text-muted-foreground/50'"
                  >
                    {{ categoryCounts[cat] || 0 }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </aside>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <!-- Search results -->
          <div v-if="isSearching" class="border border-border bg-card">
            <div class="px-4 py-3 border-b border-border">
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold flex items-center gap-2">
                  <Search class="h-4 w-4" />
                  {{ t('config.searchResults') }}
                </span>
                <NTag :bordered="true" size="small">
                  {{ searchMatchedFields.length }} {{ t('config.fields').replace('{s}', searchMatchedFields.length !== 1 ? 's' : '') }}
                </NTag>
              </div>
            </div>
            <div class="grid gap-2 px-4 pb-4">
              <p
                v-if="searchMatchedFields.length === 0"
                class="text-sm text-muted-foreground text-center py-8"
              >
                {{ t('config.noFieldsMatch').replace('{query}', searchQuery) }}
              </p>
              <template v-else>
                <template v-for="[key, s] in searchMatchedFields" :key="key">
                  <div class="py-1">
                    <AutoField
                      :schemaKey="key"
                      :schema="s"
                      :value="getNestedValue(config!, key)"
                      @change="(v: unknown) => config = setNestedValue(config!, key, v)"
                    />
                  </div>
                </template>
              </template>
            </div>
          </div>

          <!-- Active category -->
          <div v-else class="border border-border bg-card">
            <div class="px-4 py-3 border-b border-border">
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold flex items-center gap-2">
                  <component :is="getCategoryIcon(activeCategory)" class="h-4 w-4" />
                  {{ prettyCategoryName(activeCategory) }}
                </span>
                <NTag :bordered="true" size="small">
                  {{ activeFields.length }} {{ t('config.fields').replace('{s}', activeFields.length !== 1 ? 's' : '') }}
                </NTag>
              </div>
            </div>
            <div class="grid gap-2 px-4 pb-4">
              <template v-for="[key, s] in activeFields" :key="key">
                <div class="py-1">
                  <AutoField
                    :schemaKey="key"
                    :schema="s"
                    :value="getNestedValue(config!, key)"
                    @change="(v: unknown) => config = setNestedValue(config!, key, v)"
                  />
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <PluginSlot name="config:bottom" />
  </div>
</template>
