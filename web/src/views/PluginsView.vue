<script setup lang="ts">
import { ref, onMounted, watch, h } from "vue";
import {
  ExternalLink,
  Eye,
  EyeOff,
  Puzzle,
  RefreshCw,
  Trash2,
} from "lucide-vue-next";
import { NButton, NTag, NInput } from "naive-ui";
import { api } from "@/lib/api";
import type { PluginsHubResponse } from "@/lib/api";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog.vue";
import PluginSlot from "@/components/PluginSlot.vue";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";

const { t } = useI18n();
const { setEnd } = usePageHeader();

const MEMORY_PROVIDER_BUILTIN = "__hermes_memory_builtin__";

const hub = ref<PluginsHubResponse | null>(null);
const loading = ref(true);
const installId = ref("");
const installForce = ref(false);
const installEnable = ref(true);
const installBusy = ref(false);
const rescanBusy = ref(false);
const memorySel = ref(MEMORY_PROVIDER_BUILTIN);
const contextSel = ref("compressor");
const providerBusy = ref(false);
const rowBusy = ref<string | null>(null);
const error = ref<string | null>(null);
const toastMsg = ref<string | null>(null);
const toastVariant = ref<"success" | "error">("success");
let toastTimer: ReturnType<typeof setTimeout> | null = null;

function showToast(msg: string, variant: "success" | "error") {
  toastMsg.value = msg;
  toastVariant.value = variant;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastMsg.value = null; }, 4000);
}

async function loadHub() {
  try {
    const h = await api.getPluginsHub();
    hub.value = h;
    if (h.providers) {
      memorySel.value = h.providers.memory_provider || MEMORY_PROVIDER_BUILTIN;
      contextSel.value = h.providers.context_engine || "compressor";
    }
  } catch (e) {
    error.value = String(e);
  }
}

onMounted(async () => {
  loading.value = true;
  await loadHub();
  loading.value = false;
});

watch([loading, rescanBusy], () => {
  setEnd(
    h(NButton, {
      size: "small",
      disabled: loading.value || rescanBusy.value,
      onClick: onRescan,
    }, {
      default: () => [
        rescanBusy.value
          ? h("span", { class: "h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary border-t-transparent" })
          : h(RefreshCw, { class: "h-3.5 w-3.5" }),
      ],
    }),
  );
}, { immediate: true });

async function onInstall() {
  const id = installId.value.trim();
  if (!id) { showToast(t('plugins.installHint'), "error"); return; }
  installBusy.value = true;
  try {
    const r = await api.installAgentPlugin({ identifier: id, force: installForce.value, enable: installEnable.value });
    showToast(`${r.plugin_name ?? id} installed`, "success");
    if (r.warnings?.length) showToast(r.warnings.join(" "), "error");
    if (r.missing_env?.length) showToast(`Missing env: ${r.missing_env.join(", ")}`, "error");
    installId.value = "";
    await loadHub();
  } catch (e) {
    showToast(e instanceof Error ? e.message : "Install failed", "error");
  } finally {
    installBusy.value = false;
  }
}

async function onRescan() {
  rescanBusy.value = true;
  try {
    await api.rescanPlugins();
    await loadHub();
    showToast(t('plugins.refreshDashboard'), "success");
  } catch (e) {
    showToast(e instanceof Error ? e.message : "Rescan failed", "error");
  } finally {
    rescanBusy.value = false;
  }
}

async function onSaveProviders() {
  providerBusy.value = true;
  try {
    await api.savePluginProviders({
      memory_provider: memorySel.value === MEMORY_PROVIDER_BUILTIN ? "" : memorySel.value,
      context_engine: contextSel.value,
    });
    showToast(t('plugins.savedProviders'), "success");
    await loadHub();
  } catch (e) {
    showToast(e instanceof Error ? e.message : "Save failed", "error");
  } finally {
    providerBusy.value = false;
  }
}

async function setRuntimeLoading(name: string, fn: () => Promise<unknown>) {
  rowBusy.value = name;
  try {
    await fn();
    await loadHub();
  } catch (e) {
    showToast(e instanceof Error ? e.message : "Failed", "error");
  } finally {
    rowBusy.value = null;
  }
}

const rowToRemove = ref<string | null>(null);

const removeDescription = () => rowToRemove.value ? `Remove "${rowToRemove.value}" from your agent?` : "";

async function confirmRemove() {
  const name = rowToRemove.value;
  if (!name) return;
  await setRuntimeLoading(name, () => api.removeAgentPlugin(name));
  rowToRemove.value = null;
}

const rows = () => hub.value?.plugins ?? [];
const providers = () => hub.value?.providers;
</script>

<template>
  <div class="flex flex-col gap-6">
    <PluginSlot name="plugins:top" />

    <!-- Toast -->
    <div
      v-if="toastMsg"
      :class="[
        'fixed top-4 right-4 z-[9999] px-4 py-2 text-sm shadow-lg border',
        toastVariant === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400',
      ]"
    >
      {{ toastMsg }}
    </div>

    <div v-if="error" class="border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">{{ error }}</div>

    <!-- Providers -->
    <div v-if="providers()" class="border border-border bg-card">
      <div class="px-5 py-3 border-b border-border/50">
        <h3 class="text-sm font-medium tracking-wider uppercase">Providers</h3>
        <p class="text-[0.7rem] tracking-[0.08em] text-midground/55 normal-case mt-1">Select the memory and context engines for the agent.</p>
      </div>
      <div class="p-4 space-y-4">
        <div class="grid gap-6 sm:grid-cols-2">
          <div class="grid gap-2">
            <label for="mem-provider" class="text-xs tracking-wider uppercase text-muted-foreground">Memory Provider</label>
            <select
              id="mem-provider"
              v-model="memorySel"
              class="w-full border border-border bg-transparent px-3 py-2 text-sm"
            >
              <option :value="MEMORY_PROVIDER_BUILTIN">(defaults)</option>
              <option v-for="o in providers()?.memory_options" :key="o.name" :value="o.name">{{ o.description || o.name }}</option>
            </select>
          </div>
          <div class="grid gap-2">
            <label for="ctx-engine" class="text-xs tracking-wider uppercase text-muted-foreground">Context Engine</label>
            <select
              id="ctx-engine"
              v-model="contextSel"
              class="w-full border border-border bg-transparent px-3 py-2 text-sm"
            >
              <option value="compressor">compressor</option>
              <option v-for="o in providers()?.context_options.filter((c) => c.name !== 'compressor')" :key="o.name" :value="o.name">{{ o.description || o.name }}</option>
            </select>
          </div>
        </div>
        <NButton size="small" :disabled="providerBusy" @click="onSaveProviders">
          {{ providerBusy ? '...' : t('plugins.saveProviders') }}
        </NButton>
      </div>
    </div>

    <!-- Install -->
    <div class="border border-border bg-card">
      <div class="px-5 py-3 border-b border-border/50">
        <h3 class="text-sm font-medium tracking-wider uppercase">{{ t('plugins.installHeading') }}</h3>
        <p class="text-[0.7rem] tracking-[0.08em] text-midground/55 normal-case mt-1">{{ t('plugins.installHint') }}</p>
      </div>
      <div class="p-4 space-y-4">
        <div class="grid gap-2">
          <label for="install-url" class="text-xs tracking-wider uppercase text-muted-foreground">{{ t('plugins.identifierLabel') }}</label>
          <NInput
            id="install-url"
            v-model:value="installId"
            size="small"
            placeholder="owner/repo or https://..."
          />
        </div>
        <div class="flex flex-wrap items-center gap-8">
          <label class="flex items-center gap-2 text-[0.7rem] tracking-[0.06em] text-midforeground/85 normal-case">
            <input type="checkbox" v-model="installForce" class="w-3.5 h-3.5" />
            {{ t('plugins.forceReinstall') }}
          </label>
          <label class="flex items-center gap-2 text-[0.7rem] tracking-[0.06em] text-midforeground/85 normal-case">
            <input type="checkbox" v-model="installEnable" class="w-3.5 h-3.5" />
            {{ t('plugins.enableAfterInstall') }}
          </label>
        </div>
        <NButton size="small" :disabled="installBusy" @click="onInstall">
          <Puzzle class="h-3.5 w-3.5 mr-1" />
          {{ t('plugins.installBtn') }}
        </NButton>
      </div>
    </div>

    <!-- Plugin list -->
    <div class="flex flex-col gap-3">
      <h3 class="font-mondwest text-[0.75rem] tracking-[0.12em] text-midground/85">{{ t('plugins.pluginListHeading') }}</h3>

      <div v-if="loading" class="flex items-center gap-2 py-8 text-[0.8rem] text-midforeground/65">
        <span class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>{{ t('common.loading') }}</span>
      </div>

      <p v-else-if="rows().length === 0" class="text-[0.75rem] text-midforeground/55 normal-case">{{ t('common.noResults') }}</p>

      <div v-else class="flex flex-col gap-3">
        <div
          v-for="row in rows()"
          :key="row.name"
          class="border border-border bg-card p-4 flex flex-col gap-4"
          :class="{ 'opacity-70': rowBusy === row.name }"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-3">
                <span class="truncate font-semibold">{{ row.name }}</span>
                <NTag bordered size="small">{{ row.source }}</NTag>
                <NTag bordered size="small">v{{ row.version || "—" }}</NTag>
                <NTag :type="row.runtime_status === 'enabled' ? 'success' : row.runtime_status === 'disabled' ? 'error' : 'default'" size="small">
                  {{ row.runtime_status }}
                </NTag>
                <NTag v-if="row.auth_required" type="error" size="small">{{ t('plugins.authRequired') }}</NTag>
              </div>
              <p v-if="row.description" class="mt-2 max-w-2xl text-[0.7rem] tracking-[0.06em] text-midforeground/75 normal-case">
                {{ row.description }}
              </p>
              <p v-if="row.dashboard_manifest?.slots?.length" class="mt-1 text-[0.65rem] tracking-[0.05em] text-midforeground/55 normal-case">
                {{ t('plugins.dashboardSlots') }}: {{ row.dashboard_manifest.slots.join(", ") }}
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-2 shrink-0">
              <NButton
                size="tiny"
                :disabled="rowBusy === row.name || row.runtime_status === 'enabled'"
                @click="setRuntimeLoading(row.name, () => api.enableAgentPlugin(row.name))"
              >{{ t('plugins.enableRuntime') }}</NButton>
              <NButton
                size="tiny"
                :disabled="rowBusy === row.name || row.runtime_status === 'disabled'"
                @click="setRuntimeLoading(row.name, () => api.disableAgentPlugin(row.name))"
              >{{ t('plugins.disableRuntime') }}</NButton>
              <router-link
                v-if="row.dashboard_manifest?.tab && !row.dashboard_manifest.tab.hidden"
                :to="row.dashboard_manifest.tab.override ?? row.dashboard_manifest.tab.path"
                class="inline-flex items-center rounded-none px-3 py-1.5 border border-current/25 hover:bg-current/10 font-mondwest text-[0.65rem] tracking-[0.1em] uppercase"
              >
                {{ t('plugins.openTab') }}
              </router-link>
              <NButton
                v-if="row.can_update_git"
                size="tiny"
                :disabled="rowBusy === row.name"
                @click="setRuntimeLoading(row.name, () => api.updateAgentPlugin(row.name))"
              >{{ t('plugins.updateGit') }}</NButton>
              <NButton
                v-if="row.has_dashboard_manifest"
                size="tiny"
                :disabled="rowBusy === row.name"
                @click="setRuntimeLoading(row.name, () => api.setPluginVisibility(row.name, !row.user_hidden))"
              >
                <EyeOff v-if="row.user_hidden" class="h-3.5 w-3.5" />
                <Eye v-else class="h-3.5 w-3.5" />
              </NButton>
              <NButton
                v-if="row.can_remove"
                size="tiny"
                type="error"
                :disabled="rowBusy === row.name"
                @click="rowToRemove = row.name"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </NButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Orphan plugins -->
    <div v-if="(hub?.orphan_dashboard_plugins?.length ?? 0) > 0" class="flex flex-col gap-3">
      <h3 class="font-mondwest text-[0.75rem] tracking-[0.12em] text-midforeground/85">{{ t('plugins.orphanHeading') }}</h3>
      <ul class="flex flex-col gap-2 rounded border border-current/15 p-4">
        <li v-for="m in hub!.orphan_dashboard_plugins" :key="m.name" class="text-[0.7rem] normal-case opacity-85">
          {{ m.label ?? m.name }} — {{ m.description || m.tab?.path }}
          <router-link
            v-if="m.tab && !m.tab.hidden"
            :to="m.tab.path"
            class="ml-3 inline-flex items-center gap-1 underline"
          >
            <ExternalLink class="h-3 w-3 opacity-65" />
            {{ t('plugins.openTab') }}
          </router-link>
        </li>
      </ul>
    </div>

    <!-- Delete confirm -->
    <DeleteConfirmDialog
      :open="rowToRemove !== null"
      :title="t('plugins.removeConfirm') || 'Remove plugin?'"
      :description="removeDescription()"
      :destructive="true"
      :loading="rowBusy !== null && rowToRemove !== null"
      @confirm="confirmRemove"
      @cancel="rowToRemove = null"
    />

    <PluginSlot name="plugins:bottom" />
  </div>
</template>
