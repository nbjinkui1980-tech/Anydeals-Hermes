<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  Eye,
  EyeOff,
  ExternalLink,
  KeyRound,
  MessageSquare,
  Pencil,
  Save,
  Settings,
  Trash2,
  X,
  Zap,
  ChevronDown,
  ChevronRight,
} from "lucide-vue-next";
import { NButton, NTag } from "naive-ui";
import { api, type EnvVarInfo } from "@/lib/api";
import { useI18n } from "vue-i18n";
import { useConfirmDelete } from "@/composables/useConfirmDelete";
import { showToast } from "@/components/Toast";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog.vue";
import OAuthProvidersCard from "@/components/OAuthProvidersCard.vue";
import PluginSlot from "@/components/PluginSlot.vue";

const { t } = useI18n();

/* ------------------------------------------------------------------ */
/*  Provider grouping                                                  */
/* ------------------------------------------------------------------ */

const PROVIDER_GROUPS: { prefix: string; name: string; priority: number }[] = [
  { prefix: "NOUS_",            name: "Nous Portal",       priority: 0 },
  { prefix: "ANTHROPIC_",       name: "Anthropic",         priority: 1 },
  { prefix: "DASHSCOPE_",       name: "DashScope (Qwen)",  priority: 2 },
  { prefix: "ANYDEALS_QWEN_",    name: "DashScope (Qwen)",  priority: 2 },
  { prefix: "DEEPSEEK_",        name: "DeepSeek",          priority: 3 },
  { prefix: "GOOGLE_",          name: "Gemini",            priority: 4 },
  { prefix: "GEMINI_",          name: "Gemini",            priority: 4 },
  { prefix: "GLM_",             name: "GLM / Z.AI",        priority: 5 },
  { prefix: "ZAI_",             name: "GLM / Z.AI",        priority: 5 },
  { prefix: "Z_AI_",            name: "GLM / Z.AI",        priority: 5 },
  { prefix: "HF_",              name: "Hugging Face",      priority: 6 },
  { prefix: "KIMI_",            name: "Kimi / Moonshot",   priority: 7 },
  { prefix: "MINIMAX_CN_",      name: "MiniMax (China)",   priority: 9 },
  { prefix: "MINIMAX_",         name: "MiniMax",           priority: 8 },
  { prefix: "OPENCODE_GO_",     name: "OpenCode Go",       priority: 10 },
  { prefix: "OPENCODE_ZEN_",    name: "OpenCode Zen",      priority: 11 },
  { prefix: "OPENROUTER_",      name: "OpenRouter",        priority: 12 },
  { prefix: "XIAOMI_",          name: "Xiaomi MiMo",       priority: 13 },
];

function getProviderGroup(key: string): string {
  for (const g of PROVIDER_GROUPS) {
    if (key.startsWith(g.prefix)) return g.name;
  }
  return "Other";
}

function getProviderPriority(groupName: string): number {
  const entry = PROVIDER_GROUPS.find((g) => g.name === groupName);
  return entry?.priority ?? 99;
}

function getKeyUrl(group: ProviderGroup): string | undefined {
  const entry = group.entries.find(([, info]) => info.url);
  if (!entry) return undefined;
  const url = entry[1]?.url;
  return typeof url === "string" ? url : undefined;
}

interface ProviderGroup {
  name: string;
  priority: number;
  entries: [string, EnvVarInfo][];
  hasAnySet: boolean;
}

const CATEGORY_META_ICONS: Record<string, any> = {
  provider: Zap,
  tool: KeyRound,
  messaging: MessageSquare,
  setting: Settings,
};

/* ------------------------------------------------------------------ */
/*  State                                                              */
/* ------------------------------------------------------------------ */

const vars = ref<Record<string, EnvVarInfo> | null>(null);
const edits = ref<Record<string, string>>({});
const revealed = ref<Record<string, string>>({});
const saving = ref<string | null>(null);
const showAdvanced = ref(true);
const loading = ref(true);

onMounted(async () => {
  try {
    vars.value = await api.getEnvVars();
  } catch {
    // keep null
  } finally {
    loading.value = false;
  }
});

/* ---- Actions ---- */

async function handleSave(key: string) {
  const value = edits.value[key];
  if (!value) return;
  saving.value = key;
  try {
    await api.setEnvVar(key, value);
    if (vars.value) {
      vars.value = {
        ...vars.value,
        [key]: {
          ...vars.value[key],
          is_set: true,
          redacted_value: value.slice(0, 4) + "..." + value.slice(-4),
        },
      };
    }
    const n = { ...edits.value };
    delete n[key];
    edits.value = n;
    const r = { ...revealed.value };
    delete r[key];
    revealed.value = r;
    showToast({ message: `${key} saved`, type: "success" });
  } catch (e) {
    showToast({ message: `${t("config.failedToSave")} ${key}: ${e}`, type: "error" });
  } finally {
    saving.value = null;
  }
}

const keyClear = useConfirmDelete<string>(async (key: string) => {
  saving.value = key;
  try {
    await api.deleteEnvVar(key);
    if (vars.value) {
      vars.value = {
        ...vars.value,
        [key]: { ...vars.value[key], is_set: false, redacted_value: null },
      };
    }
    const n = { ...edits.value };
    delete n[key];
    edits.value = n;
    const r = { ...revealed.value };
    delete r[key];
    revealed.value = r;
    showToast({ message: `${key} ${t("common.removed")}`, type: "success" });
  } catch (e) {
    showToast({ message: `${t("common.failedToRemove")} ${key}: ${e}`, type: "error" });
    throw e;
  } finally {
    saving.value = null;
  }
});

async function handleReveal(key: string) {
  if (revealed.value[key]) {
    const n = { ...revealed.value };
    delete n[key];
    revealed.value = n;
    return;
  }
  try {
    const resp = await api.revealEnvVar(key);
    revealed.value = { ...revealed.value, [key]: resp.value };
  } catch {
    showToast({ message: `${t("common.failedToReveal")} ${key}`, type: "error" });
  }
}

function cancelEdit(key: string) {
  const n = { ...edits.value };
  delete n[key];
  edits.value = n;
}

/* ---- Derived ---- */

const providerGroups = computed(() => {
  if (!vars.value) return [];
  const providerEntries = Object.entries(vars.value).filter(
    ([, info]) => info.category === "provider" && (showAdvanced.value || !info.advanced),
  );
  const groupMap = new Map<string, [string, EnvVarInfo][]>();
  for (const entry of providerEntries) {
    const gn = getProviderGroup(entry[0]);
    if (!groupMap.has(gn)) groupMap.set(gn, []);
    groupMap.get(gn)!.push(entry);
  }
  const groups: ProviderGroup[] = Array.from(groupMap.entries())
    .map(([name, entries]) => ({
      name,
      priority: getProviderPriority(name),
      entries,
      hasAnySet: entries.some(([, info]) => info.is_set),
    }))
    .sort((a, b) => a.priority - b.priority);
  return groups;
});

const configuredProviders = computed(
  () => providerGroups.value.filter((g) => g.hasAnySet).length,
);

const nonProviderGrouped = computed(() => {
  if (!vars.value) return [];
  const CATEGORY_META_LABELS: Record<string, string> = {
    tool: t("app.nav.keys"),
    messaging: t("common.messaging"),
    setting: t("app.nav.config"),
  };
  const otherCategories = ["tool", "messaging", "setting"];
  return otherCategories.map((cat) => {
    const entries = Object.entries(vars.value!).filter(
      ([, info]) => info.category === cat && (showAdvanced.value || !info.advanced),
    );
    const setEntries = entries.filter(([, info]) => info.is_set);
    const unsetEntries = entries.filter(([, info]) => !info.is_set);
    return {
      label: CATEGORY_META_LABELS[cat] ?? cat,
      icon: CATEGORY_META_ICONS[cat] ?? KeyRound,
      category: cat,
      setEntries,
      unsetEntries,
      totalEntries: entries.length,
    };
  });
});

/* ---- Delete description ---- */

const clearDescription = computed(() => {
  const pk = keyClear.pendingId.value;
  if (pk && vars.value) {
    const desc = vars.value[pk]?.description;
    return `${pk}${desc ? ` — ${desc}` : ""}. ${t("env.confirmClearMessage")}`;
  }
  return t("env.confirmClearMessage");
});

/* ---- Provider group expanded state ---- */

const expandedGroups = ref<Record<string, boolean>>({});

function toggleGroup(name: string) {
  expandedGroups.value = { ...expandedGroups.value, [name]: !expandedGroups.value[name] };
}

/* ---- Unset collapsed state ---- */

const unsetCollapsed = ref<Record<string, boolean>>({});

function toggleUnset(cat: string) {
  unsetCollapsed.value = { ...unsetCollapsed.value, [cat]: !unsetCollapsed.value[cat] };
}

/* ---- Edits helper ---- */

function setEdit(key: string, value: string) {
  edits.value = { ...edits.value, [key]: value };
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <PluginSlot name="env:top" />

    <DeleteConfirmDialog
      :open="keyClear.isOpen()"
      :title="t('env.confirmClearTitle')"
      :description="clearDescription"
      :loading="keyClear.isDeleting.value"
      @cancel="keyClear.cancel()"
      @confirm="keyClear.confirm()"
    />

    <div class="flex items-center justify-between">
      <div class="flex flex-col gap-1">
        <p class="text-sm text-muted-foreground">
          {{ t('env.description') }} <code>~/.anydeals/.env</code>
        </p>
        <p class="text-[0.7rem] text-muted-foreground/70">
          {{ t('env.changesNote') }}
        </p>
      </div>
      <NButton size="small" text @click="showAdvanced = !showAdvanced">
        {{ showAdvanced ? t('env.hideAdvanced') : t('env.showAdvanced') }}
      </NButton>
    </div>

    <!-- Loading -->
    <div
      v-if="loading && !vars"
      class="flex items-center justify-center py-24"
    >
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <template v-if="vars">
      <!-- OAuth -->
      <OAuthProvidersCard
        @error="(msg: string) => showToast({ message: msg, type: 'error' })"
        @success="(msg: string) => showToast({ message: msg, type: 'success' })"
      />

      <!-- LLM Providers -->
      <div class="border border-border bg-card">
        <div class="px-4 py-3 border-b border-border flex items-center gap-2">
          <Zap class="h-5 w-5 text-muted-foreground" />
          <span class="text-base font-semibold">{{ t('env.llmProviders') }}</span>
        </div>
        <p class="px-4 py-2 text-xs text-muted-foreground border-b border-border">
          {{ t('env.providersConfigured').replace('{configured}', String(configuredProviders)).replace('{total}', String(providerGroups.length)) }}
        </p>

        <div class="flex flex-col">
          <div
            v-for="group in providerGroups"
            :key="group.name"
            class="border-b border-border last:border-b-0"
          >
            <!-- Provider group header -->
            <button
              type="button"
              class="flex w-full items-center justify-between gap-3 px-4 py-3 cursor-pointer hover:bg-primary/5 transition-colors"
              @click="toggleGroup(group.name)"
            >
              <div class="flex items-center gap-3 min-w-0">
                <ChevronDown
                  v-if="expandedGroups[group.name]"
                  class="h-3.5 w-3.5 text-muted-foreground shrink-0"
                />
                <ChevronRight
                  v-else
                  class="h-3.5 w-3.5 text-muted-foreground shrink-0"
                />
                <span class="font-semibold text-sm tracking-wide">
                  {{ group.name === 'Other' ? t('common.other') : group.name }}
                </span>
                <NTag v-if="group.hasAnySet" type="success" size="small" :bordered="false">
                  {{ group.entries.filter(([, info]) => info.is_set).length }} {{ t('common.set').toLowerCase() }}
                </NTag>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <a
                  v-if="getKeyUrl(group)"
                  :href="getKeyUrl(group)"
                  target="_blank"
                  rel="noreferrer"
                  class="inline-flex items-center gap-1 text-[0.65rem] text-primary hover:underline"
                  @click.stop
                >
                  {{ t('env.getKey') }} <ExternalLink class="h-2.5 w-2.5" />
                </a>
                <span class="text-[0.65rem] text-muted-foreground/60">
                  {{ t('env.keysCount').replace('{count}', String(group.entries.length)).replace('{s}', group.entries.length !== 1 ? 's' : '') }}
                </span>
              </div>
            </button>

            <!-- Expanded entries -->
            <div
              v-if="expandedGroups[group.name]"
              class="border-t border-border px-4 py-3 grid gap-2"
            >
              <template v-for="[key, info] in group.entries" :key="key">
                <!-- Compact unset row -->
                <div
                  v-if="!info.is_set && edits[key] === undefined"
                  class="flex items-center justify-between gap-3 py-1.5 opacity-50 hover:opacity-100 transition-opacity"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="font-mono-ui text-[0.7rem] text-muted-foreground">{{ key }}</span>
                    <span class="text-[0.65rem] text-muted-foreground/60 truncate hidden sm:block">{{ info.description }}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <a
                      v-if="info.url"
                      :href="info.url"
                      target="_blank"
                      rel="noreferrer"
                      class="inline-flex items-center gap-1 text-[0.65rem] text-primary hover:underline"
                    >
                      {{ t('env.getKey') }} <ExternalLink class="h-2.5 w-2.5" />
                    </a>
                    <NButton
                      size="tiny"
                      @click="setEdit(key, '')"
                    >
                      <template #icon><Pencil class="h-2.5 w-2.5" /></template>
                      {{ t('common.set') }}
                    </NButton>
                  </div>
                </div>

                <!-- Full row (set or editing) -->
                <div
                  v-else
                  class="grid gap-2 border border-border p-4"
                >
                  <div class="flex items-center justify-between gap-2 flex-wrap">
                    <div class="flex items-center gap-2">
                      <span class="font-mono-ui text-[0.7rem]">{{ key }}</span>
                      <NTag :type="info.is_set ? 'success' : 'default'" size="small" :bordered="!info.is_set">
                        {{ info.is_set ? t('common.set') : t('env.notSet') }}
                      </NTag>
                    </div>
                    <a
                      v-if="info.url"
                      :href="info.url"
                      target="_blank"
                      rel="noreferrer"
                      class="inline-flex items-center gap-1 text-[0.65rem] text-primary hover:underline"
                    >
                      {{ t('env.getKey') }} <ExternalLink class="h-2.5 w-2.5" />
                    </a>
                  </div>

                  <p class="text-xs text-muted-foreground">{{ info.description }}</p>

                  <div v-if="info.tools.length > 0" class="flex flex-wrap gap-1">
                    <NTag
                      v-for="tool in info.tools"
                      :key="tool"
                      size="small"
                      :bordered="true"
                    >
                      {{ tool }}
                    </NTag>
                  </div>

                  <!-- Not editing: show value -->
                  <div v-if="edits[key] === undefined" class="flex items-center gap-2">
                    <div
                      class="flex-1 border border-border px-3 py-2 font-mono-ui text-xs"
                      :class="revealed[key] ? 'bg-background text-foreground select-all' : 'bg-muted/30 text-muted-foreground'"
                    >
                      {{ info.is_set ? (revealed[key] || info.redacted_value) : '---' }}
                    </div>

                    <NButton
                      v-if="info.is_set"
                      size="small"
                      text
                      @click="handleReveal(key)"
                      :title="revealed[key] ? t('env.hideValue') : t('env.showValue')"
                    >
                      <template #icon>
                        <EyeOff v-if="revealed[key]" class="h-4 w-4" />
                        <Eye v-else class="h-4 w-4" />
                      </template>
                    </NButton>

                    <NButton size="small" @click="setEdit(key, '')">
                      <template #icon><Pencil class="h-3 w-3" /></template>
                      {{ info.is_set ? t('common.replace') : t('common.set') }}
                    </NButton>

                    <NButton
                      v-if="info.is_set"
                      size="small"
                      text
                      class="!text-destructive hover:!text-destructive"
                      :disabled="saving === key || keyClear.isOpen()"
                      @click="keyClear.requestDelete(key)"
                    >
                      <template #icon><Trash2 class="h-3 w-3" /></template>
                      {{ saving === key ? '...' : t('common.clear') }}
                    </NButton>
                  </div>

                  <!-- Editing -->
                  <div v-else class="flex items-center gap-2">
                    <input
                      type="text"
                      class="flex-1 border border-border bg-transparent px-3 py-2 font-mono-ui text-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      :value="edits[key]"
                      @input="(e: Event) => setEdit(key, (e.target as HTMLInputElement).value)"
                      :placeholder="info.is_set ? t('env.replaceCurrentValue').replace('{preview}', info.redacted_value ?? '---') : t('env.enterValue')"
                    />
                    <NButton
                      size="small"
                      :disabled="saving === key || !edits[key]"
                      @click="handleSave(key)"
                    >
                      <template #icon><Save class="h-3 w-3" /></template>
                      {{ saving === key ? '...' : t('common.save') }}
                    </NButton>
                    <NButton size="small" text @click="cancelEdit(key)">
                      <template #icon><X class="h-3 w-3" /></template>
                      {{ t('common.cancel') }}
                    </NButton>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Non-provider categories -->
      <template v-for="ng in nonProviderGrouped" :key="ng.category">
        <div v-if="ng.totalEntries > 0" class="border border-border bg-card">
          <div class="px-4 py-3 border-b border-border flex items-center gap-2">
            <component :is="ng.icon" class="h-5 w-5 text-muted-foreground" />
            <span class="text-base font-semibold">{{ ng.label }}</span>
          </div>
          <p class="px-4 py-2 text-xs text-muted-foreground border-b border-border">
            {{ ng.setEntries.length }} {{ t('common.of') }} {{ ng.totalEntries }} {{ t('common.configured') }}
          </p>

          <div class="grid gap-3 p-4">
            <!-- Set entries -->
            <template v-for="[key, info] in ng.setEntries" :key="key">
              <div class="grid gap-2 border border-border p-4">
                <div class="flex items-center justify-between gap-2 flex-wrap">
                  <div class="flex items-center gap-2">
                    <span class="font-mono-ui text-[0.7rem]">{{ key }}</span>
                    <NTag type="success" size="small" :bordered="false">
                      {{ t('common.set') }}
                    </NTag>
                  </div>
                  <a
                    v-if="info.url"
                    :href="info.url"
                    target="_blank"
                    rel="noreferrer"
                    class="inline-flex items-center gap-1 text-[0.65rem] text-primary hover:underline"
                  >
                    {{ t('env.getKey') }} <ExternalLink class="h-2.5 w-2.5" />
                  </a>
                </div>

                <p class="text-xs text-muted-foreground">{{ info.description }}</p>

                <div v-if="info.tools.length > 0" class="flex flex-wrap gap-1">
                  <NTag v-for="tool in info.tools" :key="tool" size="small" :bordered="true">
                    {{ tool }}
                  </NTag>
                </div>

                <div v-if="edits[key] === undefined" class="flex items-center gap-2">
                  <div
                    class="flex-1 border border-border px-3 py-2 font-mono-ui text-xs"
                    :class="revealed[key] ? 'bg-background text-foreground select-all' : 'bg-muted/30 text-muted-foreground'"
                  >
                    {{ revealed[key] || info.redacted_value }}
                  </div>

                  <NButton
                    size="small"
                    text
                    @click="handleReveal(key)"
                    :title="revealed[key] ? t('env.hideValue') : t('env.showValue')"
                  >
                    <template #icon>
                      <EyeOff v-if="revealed[key]" class="h-4 w-4" />
                      <Eye v-else class="h-4 w-4" />
                    </template>
                  </NButton>

                  <NButton size="small" @click="setEdit(key, '')">
                    <template #icon><Pencil class="h-3 w-3" /></template>
                    {{ t('common.replace') }}
                  </NButton>

                  <NButton
                    size="small"
                    text
                    class="!text-destructive hover:!text-destructive"
                    :disabled="saving === key || keyClear.isOpen()"
                    @click="keyClear.requestDelete(key)"
                  >
                    <template #icon><Trash2 class="h-3 w-3" /></template>
                    {{ saving === key ? '...' : t('common.clear') }}
                  </NButton>
                </div>

                <div v-else class="flex items-center gap-2">
                  <input
                    type="text"
                    class="flex-1 border border-border bg-transparent px-3 py-2 font-mono-ui text-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    :value="edits[key]"
                    @input="(e: Event) => setEdit(key, (e.target as HTMLInputElement).value)"
                    :placeholder="t('env.replaceCurrentValue').replace('{preview}', info.redacted_value ?? '---')"
                  />
                  <NButton
                    size="small"
                    :disabled="saving === key || !edits[key]"
                    @click="handleSave(key)"
                  >
                    <template #icon><Save class="h-3 w-3" /></template>
                    {{ saving === key ? '...' : t('common.save') }}
                  </NButton>
                  <NButton size="small" text @click="cancelEdit(key)">
                    <template #icon><X class="h-3 w-3" /></template>
                    {{ t('common.cancel') }}
                  </NButton>
                </div>
              </div>
            </template>

            <!-- Collapsible unset entries -->
            <template v-if="ng.unsetEntries.length > 0">
              <button
                type="button"
                class="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer pt-1"
                @click="toggleUnset(ng.category)"
              >
                <ChevronRight v-if="unsetCollapsed[ng.category] !== false" class="h-3 w-3" />
                <ChevronDown v-else class="h-3 w-3" />
                <span>{{ t('env.notConfigured').replace('{count}', String(ng.unsetEntries.length)) }}</span>
              </button>

              <template v-if="unsetCollapsed[ng.category] === false">
                <div
                  v-for="[key, info] in ng.unsetEntries"
                  :key="key"
                  class="flex items-center justify-between gap-3 border border-border/50 px-4 py-2.5 opacity-60 hover:opacity-100 transition-opacity"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <span class="font-mono-ui text-[0.7rem] text-muted-foreground">{{ key }}</span>
                    <span class="text-[0.65rem] text-muted-foreground/60 truncate hidden sm:block">{{ info.description }}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <a
                      v-if="info.url"
                      :href="info.url"
                      target="_blank"
                      rel="noreferrer"
                      class="inline-flex items-center gap-1 text-[0.65rem] text-primary hover:underline"
                    >
                      {{ t('env.getKey') }} <ExternalLink class="h-2.5 w-2.5" />
                    </a>
                    <NButton size="tiny" @click="setEdit(key, '')">
                      <template #icon><Pencil class="h-3 w-3" /></template>
                      {{ t('common.set') }}
                    </NButton>
                  </div>
                </div>
              </template>
            </template>
          </div>
        </div>
      </template>
    </template>

    <PluginSlot name="env:bottom" />
  </div>
</template>
