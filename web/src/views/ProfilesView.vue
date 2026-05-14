<script setup lang="ts">
import { ref, onMounted, h } from "vue";
import {
  Pencil,
  Plus,
  Terminal,
  Trash2,
  Users,
  X,
} from "lucide-vue-next";
import { NButton, NInput, NTag } from "naive-ui";
import { api } from "@/lib/api";
import type { ProfileInfo } from "@/lib/api";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog.vue";
import { useI18n } from "vue-i18n";
import { usePageHeader } from "@/composables/usePageHeader";

const { t } = useI18n();
const { setEnd } = usePageHeader();

const PROFILE_NAME_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/;

const profiles = ref<ProfileInfo[]>([]);
const loading = ref(true);
const toastMsg = ref<string | null>(null);
const toastVariant = ref<"success" | "error">("success");
let toastTimer: ReturnType<typeof setTimeout> | null = null;

function showToast(msg: string, variant: "success" | "error") {
  toastMsg.value = msg;
  toastVariant.value = variant;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastMsg.value = null; }, 4000);
}

// Create modal
const createModalOpen = ref(false);
const newName = ref("");
const cloneFromDefault = ref(true);
const creating = ref(false);

// Rename state
const renamingFrom = ref<string | null>(null);
const renameTo = ref("");

// SOUL editor state
const editingSoulFor = ref<string | null>(null);
const soulText = ref("");
const soulSaving = ref(false);

// Delete
const pendingDelete = ref<string | null>(null);
const isDeleting = ref(false);

async function load() {
  try {
    const res = await api.getProfiles();
    profiles.value = res.profiles;
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
  } finally {
    loading.value = false;
  }
}

onMounted(load);

// Page header
setEnd(
  h(NButton, {
    size: "small",
    onClick: () => { createModalOpen.value = true; },
  }, { default: () => [h(Plus, { class: "h-3 w-3 mr-1" }), t('common.create')] }),
);

// ── Create ──
async function handleCreate() {
  const name = newName.value.trim();
  if (!name) { showToast(t('profiles.nameRequired'), "error"); return; }
  if (!PROFILE_NAME_RE.test(name)) {
    showToast(`${t('profiles.invalidName')}: ${t('profiles.nameRule')}`, "error");
    return;
  }
  creating.value = true;
  try {
    await api.createProfile({ name, clone_from_default: cloneFromDefault.value });
    showToast(`${t('profiles.created')}: ${name}`, "success");
    newName.value = "";
    createModalOpen.value = false;
    await load();
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
  } finally {
    creating.value = false;
  }
}

// ── Rename ──
async function handleRenameSubmit() {
  if (!renamingFrom.value) return;
  const target = renameTo.value.trim();
  if (!target || target === renamingFrom.value) { renamingFrom.value = null; renameTo.value = ""; return; }
  if (!PROFILE_NAME_RE.test(target)) {
    showToast(`${t('profiles.invalidName')}: ${t('profiles.nameRule')}`, "error");
    return;
  }
  try {
    await api.renameProfile(renamingFrom.value, target);
    showToast(`${t('profiles.renamed')}: ${renamingFrom.value} → ${target}`, "success");
    renamingFrom.value = null;
    renameTo.value = "";
    await load();
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
  }
}

// ── SOUL editor ──
async function openSoulEditor(name: string) {
  if (editingSoulFor.value === name) { editingSoulFor.value = null; return; }
  editingSoulFor.value = name;
  soulText.value = "";
  try {
    const soul = await api.getProfileSoul(name);
    if (editingSoulFor.value === name) soulText.value = soul.content;
  } catch (e) {
    if (editingSoulFor.value === name) showToast(`${t('status.error')}: ${e}`, "error");
  }
}

async function handleSaveSoul(name: string) {
  soulSaving.value = true;
  try {
    await api.updateProfileSoul(name, soulText.value);
    showToast(`${t('profiles.soulSaved')}: ${name}`, "success");
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
  } finally {
    soulSaving.value = false;
  }
}

// ── Copy terminal command ──
async function handleCopyCommand(name: string) {
  let cmd: string;
  try {
    const res = await api.getProfileSetupCommand(name);
    cmd = res.command;
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
    return;
  }
  try {
    await navigator.clipboard.writeText(cmd);
    showToast(`${t('profiles.commandCopied')}: ${cmd}`, "success");
  } catch {
    showToast(`${t('profiles.copyFailed')}: ${cmd}`, "error");
  }
}

// ── Delete ──
async function handleDelete() {
  if (!pendingDelete.value) return;
  const name = pendingDelete.value;
  isDeleting.value = true;
  try {
    await api.deleteProfile(name);
    showToast(`${t('profiles.deleted')}: ${name}`, "success");
    pendingDelete.value = null;
    await load();
  } catch (e) {
    showToast(`${t('status.error')}: ${e}`, "error");
  } finally {
    isDeleting.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 normal-case">
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

    <!-- Delete confirm -->
    <DeleteConfirmDialog
      :open="pendingDelete !== null"
      :title="t('profiles.confirmDeleteTitle') || 'Delete profile?'"
      :description="pendingDelete ? (t('profiles.confirmDeleteMessage') || '').replace('{name}', pendingDelete) : ''"
      :destructive="true"
      :loading="isDeleting"
      @confirm="handleDelete"
      @cancel="pendingDelete = null"
    />

    <!-- Create modal -->
    <div
      v-if="createModalOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-background/85 backdrop-blur-sm p-4"
      @click.self="createModalOpen = false"
    >
      <div class="relative w-full max-w-md border border-border bg-card shadow-2xl flex flex-col">
        <button
          type="button"
          class="absolute right-2 top-2 text-muted-foreground hover:text-foreground p-1"
          @click="createModalOpen = false"
        >
          <X class="h-4 w-4" />
        </button>
        <header class="p-5 pb-3 border-b border-border">
          <h2 class="font-display text-base tracking-wider uppercase">{{ t('profiles.newProfile') }}</h2>
        </header>
        <div class="p-5 grid gap-4">
          <div class="grid gap-2">
            <label for="profile-name" class="text-xs tracking-wider uppercase text-muted-foreground">{{ t('profiles.name') }}</label>
            <NInput
              id="profile-name"
              v-model:value="newName"
              size="small"
              :placeholder="t('profiles.namePlaceholder') || 'my-profile'"
              @keydown="(e: KeyboardEvent) => e.key === 'Enter' && handleCreate()"
              :status="newName.trim() !== '' && !PROFILE_NAME_RE.test(newName.trim()) ? 'error' : undefined"
            />
            <p class="text-xs text-muted-foreground">{{ t('profiles.nameRule') }}</p>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" v-model="cloneFromDefault" class="w-3.5 h-3.5" />
            {{ t('profiles.cloneFromDefault') }}
          </label>
          <div class="flex justify-end">
            <NButton size="small" :disabled="creating" @click="handleCreate">
              <Plus class="h-3 w-3 mr-1" />
              {{ creating ? t('common.creating') : t('common.create') }}
            </NButton>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <!-- Profile list -->
    <template v-else>
      <div class="flex flex-col gap-3">
        <div class="flex items-center gap-2 text-muted-foreground text-sm tracking-wider uppercase">
          <Users class="h-4 w-4" />
          <span>{{ t('profiles.allProfiles') }} ({{ profiles.length }})</span>
        </div>

        <p v-if="profiles.length === 0" class="py-8 text-center text-sm text-muted-foreground">
          {{ t('profiles.noProfiles') }}
        </p>

        <div
          v-for="p in profiles"
          :key="p.name"
          class="border border-border bg-card px-4 py-3 flex flex-col gap-3"
        >
          <div class="flex items-center gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <template v-if="renamingFrom === p.name">
                  <NInput
                    v-model:value="renameTo"
                    size="small"
                    class="max-w-xs"
                    :status="renameTo.trim() !== '' && renameTo.trim() !== p.name && !PROFILE_NAME_RE.test(renameTo.trim()) ? 'error' : undefined"
                    @keydown="(e: KeyboardEvent) => { if (e.key === 'Enter') handleRenameSubmit(); if (e.key === 'Escape') renamingFrom = null; }"
                  />
                </template>
                <template v-else>
                  <span class="font-medium text-sm truncate">{{ p.name }}</span>
                </template>
                <NTag v-if="p.is_default" type="info" size="small">{{ t('profiles.defaultBadge') }}</NTag>
                <NTag v-if="p.has_env" bordered size="small">{{ t('profiles.hasEnv') }}</NTag>
              </div>
              <div v-if="renamingFrom === p.name" class="text-xs mb-1" :class="renameTo.trim() !== '' && renameTo.trim() !== p.name && !PROFILE_NAME_RE.test(renameTo.trim()) ? 'text-red-400' : 'text-muted-foreground'">
                {{ t('profiles.nameRule') }}
              </div>
              <div class="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
                <span v-if="p.model">{{ t('profiles.model') }}: {{ p.model }}{{ p.provider ? ` (${p.provider})` : '' }}</span>
                <span>{{ t('profiles.skills') }}: {{ p.skill_count }}</span>
                <span class="font-mono truncate max-w-[28rem]">{{ p.path }}</span>
              </div>
            </div>
            <div class="flex items-center gap-1 shrink-0">
              <template v-if="renamingFrom === p.name">
                <NButton size="tiny" @click="handleRenameSubmit">{{ t('common.save') }}</NButton>
                <NButton size="tiny" @click="renamingFrom = null">{{ t('common.cancel') }}</NButton>
              </template>
              <template v-else>
                <NButton size="tiny" :title="t('profiles.editSoul')" @click="openSoulEditor(p.name)">
                  <span class="text-xs font-bold">S</span>
                </NButton>
                <NButton size="tiny" :title="t('profiles.openInTerminal')" @click="handleCopyCommand(p.name)">
                  <Terminal class="h-4 w-4" />
                </NButton>
                <NButton
                  v-if="!p.is_default"
                  size="tiny"
                  :title="t('profiles.rename')"
                  @click="renamingFrom = p.name; renameTo = p.name"
                >
                  <Pencil class="h-4 w-4" />
                </NButton>
                <NButton
                  v-if="!p.is_default"
                  size="tiny"
                  type="error"
                  :title="t('common.delete')"
                  @click="pendingDelete = p.name"
                >
                  <Trash2 class="h-4 w-4" />
                </NButton>
              </template>
            </div>
          </div>

          <!-- SOUL editor -->
          <div v-if="editingSoulFor === p.name" class="border-t border-border/50 pt-3 flex flex-col gap-2">
            <label class="flex items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
              {{ t('profiles.soulSection') }}
            </label>
            <textarea
              v-model="soulText"
              class="flex min-h-[180px] w-full border border-border bg-transparent px-3 py-2 text-sm font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              :placeholder="t('profiles.soulPlaceholder') || ''"
            />
            <div>
              <NButton size="small" :disabled="soulSaving" @click="handleSaveSoul(p.name)">
                {{ soulSaving ? t('common.saving') : t('profiles.saveSoul') }}
              </NButton>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
