<script setup lang="ts">
import { ref, computed, onMounted, watch, h } from "vue";
import {
  Package, Search, Wrench, X, Cpu, Globe, Shield,
  Eye, Paintbrush, Brain, Blocks, Code, Zap, Filter,
} from "lucide-vue-next";
import { NTag, NSwitch, NInput } from "naive-ui";
import { api } from "@/lib/api";
import type { SkillInfo, ToolsetInfo } from "@/lib/api";
import { useI18n } from "vue-i18n";
import { showToast } from "@/components/Toast";
import { usePageHeader } from "@/composables/usePageHeader";
import PluginSlot from "@/components/PluginSlot.vue";

const { t } = useI18n();
const { setAfterTitle, setEnd } = usePageHeader();

/* ------------------------------------------------------------------ */
/*  Icons & helpers                                                    */
/* ------------------------------------------------------------------ */

const CATEGORY_LABELS: Record<string, string> = {
  mlops: "MLOps",
  "mlops/cloud": "MLOps / Cloud",
  "mlops/evaluation": "MLOps / Evaluation",
  "mlops/inference": "MLOps / Inference",
  "mlops/models": "MLOps / Models",
  "mlops/training": "MLOps / Training",
  "mlops/vector-databases": "MLOps / Vector DBs",
  mcp: "MCP",
  "red-teaming": "Red Teaming",
  ocr: "OCR",
  p5js: "p5.js",
  ai: "AI",
  ux: "UX",
  ui: "UI",
};

function prettyCategory(raw: string | null | undefined): string {
  if (!raw) return t("common.general");
  if (CATEGORY_LABELS[raw]) return CATEGORY_LABELS[raw];
  return raw
    .split(/[-_/]/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const TOOLSET_ICONS: Record<string, typeof Cpu> = {
  computer: Cpu,
  web: Globe,
  security: Shield,
  vision: Eye,
  design: Paintbrush,
  ai: Brain,
  integration: Blocks,
  code: Code,
  automation: Zap,
};

function toolsetIcon(name: string): typeof Cpu {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(TOOLSET_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return Wrench;
}

/* ------------------------------------------------------------------ */
/*  State                                                              */
/* ------------------------------------------------------------------ */

const skills = ref<SkillInfo[]>([]);
const toolsets = ref<ToolsetInfo[]>([]);
const loading = ref(true);
const search = ref("");
const view = ref<"skills" | "toolsets">("skills");
const activeCategory = ref<string | null>(null);
const togglingSkills = ref<Set<string>>(new Set());

/* ---- Load ---- */
onMounted(async () => {
  try {
    const [s, tsets] = await Promise.all([api.getSkills(), api.getToolsets()]);
    skills.value = s;
    toolsets.value = tsets;
  } catch {
    showToast({ message: t("common.loading"), type: "error" });
  } finally {
    loading.value = false;
  }
});

/* ---- Toggle skill ---- */
async function handleToggleSkill(skill: SkillInfo) {
  togglingSkills.value = new Set(togglingSkills.value).add(skill.name);
  try {
    await api.toggleSkill(skill.name, !skill.enabled);
    skills.value = skills.value.map((s) =>
      s.name === skill.name ? { ...s, enabled: !s.enabled } : s,
    );
    showToast({
      message: `${skill.name} ${skill.enabled ? t("common.disabled") : t("common.enabled")}`,
      type: "success",
    });
  } catch {
    showToast({
      message: `${t("common.failedToToggle")} ${skill.name}`,
      type: "error",
    });
  } finally {
    const next = new Set(togglingSkills.value);
    next.delete(skill.name);
    togglingSkills.value = next;
  }
}

/* ---- Derived data ---- */
const lowerSearch = computed(() => search.value.toLowerCase());
const isSearching = computed(() => search.value.trim().length > 0);

const searchMatchedSkills = computed(() => {
  if (!isSearching.value) return [];
  const q = lowerSearch.value;
  return skills.value.filter(
    (s) =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      (s.category ?? "").toLowerCase().includes(q),
  );
});

const activeSkills = computed(() => {
  if (isSearching.value) return [];
  if (!activeCategory.value)
    return [...skills.value].sort((a, b) => a.name.localeCompare(b.name));
  return skills.value
    .filter((s) =>
      activeCategory.value === "__none__"
        ? !s.category
        : s.category === activeCategory.value,
    )
    .sort((a, b) => a.name.localeCompare(b.name));
});

const allCategories = computed(() => {
  const cats = new Map<string, number>();
  for (const s of skills.value) {
    const key = s.category || "__none__";
    cats.set(key, (cats.get(key) || 0) + 1);
  }
  return [...cats.entries()]
    .sort((a, b) => {
      if (a[0] === "__none__") return -1;
      if (b[0] === "__none__") return 1;
      return a[0].localeCompare(b[0]);
    })
    .map(([key, count]) => ({
      key,
      name: prettyCategory(key === "__none__" ? null : key),
      count,
    }));
});

const filteredToolsets = computed(() => {
  if (!search.value) return toolsets.value;
  const q = lowerSearch.value;
  return toolsets.value.filter(
    (ts) =>
      ts.name.toLowerCase().includes(q) ||
      ts.label.toLowerCase().includes(q) ||
      ts.description.toLowerCase().includes(q),
  );
});

const enabledCount = computed(() => skills.value.filter((s) => s.enabled).length);

/* ---- Page header ---- */
watch(
  [loading, enabledCount, skills, search, isSearching],
  () => {
    if (loading.value) {
      setAfterTitle(null);
      setEnd(null);
      return;
    }
    setAfterTitle(
      h(
        "span",
        { class: "whitespace-nowrap text-xs text-muted-foreground" },
        t("skills.enabledOf", { enabled: enabledCount.value, total: skills.value.length }),
      ),
    );
    setEnd(
      h("div", { class: "relative w-full min-w-0 sm:max-w-xs" }, [
        h(Search, {
          class:
            "absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground",
        }),
        h(NInput, {
          size: "small",
          placeholder: t("common.search"),
          value: search.value,
          "onUpdate:value": (v: string) => {
            search.value = v;
          },
          class: "h-8 pl-8 pr-7 text-xs",
        }),
        search.value
          ? h(
              "button",
              {
                type: "button",
                class:
                  "absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground",
                onClick: () => {
                  search.value = "";
                },
              },
              [h(X, { class: "h-3 w-3" })],
            )
          : null,
      ]),
    );
  },
  { immediate: true },
);
</script>

<template>
  <div class="flex flex-col gap-4">
    <PluginSlot name="skills:top" />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <template v-else>
      <div class="flex flex-col sm:flex-row sm:items-start gap-4">
        <!-- Filter panel -->
        <aside class="sm:w-56 sm:shrink-0">
          <div class="sm:sticky sm:top-0">
            <div class="flex flex-col border border-border bg-muted/20">
              <!-- Filter heading -->
              <div class="hidden sm:flex items-center gap-2 px-3 py-2 border-b border-border">
                <Filter class="h-3 w-3 text-muted-foreground" />
                <span class="font-mondwest text-[0.65rem] tracking-[0.12em] uppercase text-muted-foreground">
                  {{ t('skills.filters') }}
                </span>
              </div>

              <!-- View switch (Skills / Toolsets) -->
              <div class="flex sm:flex-col gap-1 overflow-x-auto sm:overflow-x-visible scrollbar-none p-2">
                <button
                  type="button"
                  class="group flex items-center gap-2 px-2.5 py-1.5 font-mondwest text-[0.7rem] tracking-[0.08em] uppercase rounded-sm text-left cursor-pointer whitespace-nowrap transition-colors"
                  :class="view === 'skills' && !isSearching
                    ? 'bg-foreground/90 text-background'
                    : 'text-muted-foreground hover:text-foreground hover:bg-foreground/10'"
                  @click="view = 'skills'; activeCategory = null; search = ''"
                >
                  <Package class="h-3.5 w-3.5 shrink-0" />
                  <span class="flex-1 truncate">{{ t('skills.all') }} ({{ skills.length }})</span>
                </button>
                <button
                  type="button"
                  class="group flex items-center gap-2 px-2.5 py-1.5 font-mondwest text-[0.7rem] tracking-[0.08em] uppercase rounded-sm text-left cursor-pointer whitespace-nowrap transition-colors"
                  :class="view === 'toolsets'
                    ? 'bg-foreground/90 text-background'
                    : 'text-muted-foreground hover:text-foreground hover:bg-foreground/10'"
                  @click="view = 'toolsets'; search = ''"
                >
                  <Wrench class="h-3.5 w-3.5 shrink-0" />
                  <span class="flex-1 truncate">{{ t('skills.toolsets') }} ({{ toolsets.length }})</span>
                </button>
              </div>

              <!-- Category sub-filters (only for Skills view) -->
              <div
                v-if="view === 'skills' && !isSearching && allCategories.length > 0"
                class="hidden sm:flex flex-col border-t border-border"
              >
                <div class="px-3 pt-2 pb-1 font-mondwest text-[0.6rem] tracking-[0.12em] uppercase text-muted-foreground/70">
                  {{ t('skills.categories') }}
                </div>
                <div class="flex flex-col p-2 pt-1 gap-px max-h-[calc(100vh-340px)] overflow-y-auto">
                  <button
                    v-for="{ key, name, count } in allCategories"
                    :key="key"
                    type="button"
                    class="group flex items-center gap-2 px-2 py-1 rounded-sm text-left text-[11px] cursor-pointer transition-colors"
                    :class="activeCategory === key
                      ? 'bg-foreground/10 text-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-foreground/5'"
                    @click="activeCategory = activeCategory === key ? null : key"
                  >
                    <span class="flex-1 truncate">{{ name }}</span>
                    <span
                      class="text-[10px] tabular-nums"
                      :class="activeCategory === key ? 'text-foreground/60' : 'text-muted-foreground/50'"
                    >
                      {{ count }}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <!-- Search results -->
          <div v-if="isSearching" class="border border-border bg-card">
            <div class="px-4 py-3 border-b border-border flex items-center justify-between">
              <span class="text-sm flex items-center gap-2">
                <Search class="h-4 w-4" />
                {{ t('skills.title') }}
              </span>
              <NTag :bordered="false" size="small">
                {{ t('skills.resultCount', { count: searchMatchedSkills.length }) }}
              </NTag>
            </div>
            <div class="px-4 pb-4">
              <p
                v-if="searchMatchedSkills.length === 0"
                class="text-sm text-muted-foreground text-center py-8"
              >
                {{ t('skills.noSkillsMatch') }}
              </p>
              <div v-else class="grid gap-1">
                <div
                  v-for="skill in searchMatchedSkills"
                  :key="skill.name"
                  class="group flex items-start gap-3 px-3 py-2.5 transition-colors hover:bg-muted/40"
                >
                  <div class="pt-0.5 shrink-0">
                    <NSwitch
                      :value="skill.enabled"
                      :disabled="togglingSkills.has(skill.name)"
                      @update:value="handleToggleSkill(skill)"
                      size="small"
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                      <span
                        class="font-mono-ui text-sm"
                        :class="skill.enabled ? 'text-foreground' : 'text-muted-foreground'"
                      >
                        {{ skill.name }}
                      </span>
                    </div>
                    <p class="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                      {{ skill.description || t('skills.noDescription') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Skills list -->
          <div v-else-if="view === 'skills'" class="border border-border bg-card">
            <div class="px-4 py-3 border-b border-border flex items-center justify-between">
              <span class="text-sm flex items-center gap-2">
                <Package class="h-4 w-4" />
                {{ activeCategory
                  ? prettyCategory(activeCategory === '__none__' ? null : activeCategory)
                  : t('skills.all') }}
              </span>
              <NTag :bordered="false" size="small">
                {{ t('skills.skillCount', { count: activeSkills.length }) }}
              </NTag>
            </div>
            <div class="px-4 pb-4">
              <p
                v-if="activeSkills.length === 0"
                class="text-sm text-muted-foreground text-center py-8"
              >
                {{ skills.length === 0 ? t('skills.noSkills') : t('skills.noSkillsMatch') }}
              </p>
              <div v-else class="grid gap-1">
                <div
                  v-for="skill in activeSkills"
                  :key="skill.name"
                  class="group flex items-start gap-3 px-3 py-2.5 transition-colors hover:bg-muted/40"
                >
                  <div class="pt-0.5 shrink-0">
                    <NSwitch
                      :value="skill.enabled"
                      :disabled="togglingSkills.has(skill.name)"
                      @update:value="handleToggleSkill(skill)"
                      size="small"
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                      <span
                        class="font-mono-ui text-sm"
                        :class="skill.enabled ? 'text-foreground' : 'text-muted-foreground'"
                      >
                        {{ skill.name }}
                      </span>
                    </div>
                    <p class="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                      {{ skill.description || t('skills.noDescription') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Toolsets grid -->
          <template v-else>
            <div
              v-if="filteredToolsets.length === 0"
              class="border border-border bg-card p-8 text-center text-sm text-muted-foreground"
            >
              {{ t('skills.noToolsetsMatch') }}
            </div>
            <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div
                v-for="ts in filteredToolsets"
                :key="ts.name"
                class="relative border border-border bg-card"
              >
                <div class="p-4">
                  <div class="flex items-start gap-3">
                    <component
                      :is="toolsetIcon(ts.name)"
                      class="h-5 w-5 text-muted-foreground shrink-0 mt-0.5"
                    />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium text-sm">
                          {{ ts.label.replace(/^[\p{Emoji}\s]+/u, '').trim() || ts.name }}
                        </span>
                        <NTag
                          :type="ts.enabled ? 'success' : 'default'"
                          size="small"
                          :bordered="false"
                        >
                          {{ ts.enabled ? t('common.active') : t('common.inactive') }}
                        </NTag>
                      </div>
                      <p class="text-xs text-muted-foreground mb-2">{{ ts.description }}</p>
                      <p v-if="ts.enabled && !ts.configured" class="text-[10px] text-amber-300/80 mb-2">
                        {{ t('skills.setupNeeded') }}
                      </p>
                      <div v-if="ts.tools.length > 0" class="flex flex-wrap gap-1">
                        <NTag
                          v-for="tool in ts.tools"
                          :key="tool"
                          :bordered="false"
                          size="small"
                        >
                          <span class="font-mono text-[10px]">{{ tool }}</span>
                        </NTag>
                      </div>
                      <span v-else class="text-[10px] text-muted-foreground/60">
                        {{ ts.enabled
                          ? t('skills.toolsetLabel').replace('{name}', ts.name)
                          : t('skills.disabledForCli') }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <PluginSlot name="skills:bottom" />
  </div>
</template>
