<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  ShieldCheck,
  ShieldOff,
  Copy,
  ExternalLink,
  RefreshCw,
  LogOut,
  LogIn,
  Terminal,
} from "lucide-vue-next";
import { NButton, NTag } from "naive-ui";
import { api, type OAuthProvider } from "@/lib/api";
import { useI18n } from "vue-i18n";
import OAuthLoginModal from "@/components/OAuthLoginModal.vue";

const emit = defineEmits<{
  (e: "error", msg: string): void;
  (e: "success", msg: string): void;
}>();

const { t } = useI18n();

const providers = ref<OAuthProvider[] | null>(null);
const loading = ref(true);
const busyId = ref<string | null>(null);
const copiedId = ref<string | null>(null);
const loginFor = ref<OAuthProvider | null>(null);

function formatExpiresAt(
  expiresAt: string | null | undefined,
): string | null {
  if (!expiresAt) return null;
  try {
    const dt = new Date(expiresAt);
    if (Number.isNaN(dt.getTime())) return null;
    const diff = dt.getTime() - Date.now();
    if (diff < 0) return "expired";
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return t("oauth.expiresIn").replace("{time}", `${mins}m`);
    const hours = Math.floor(mins / 60);
    if (hours < 24)
      return t("oauth.expiresIn").replace("{time}", `${hours}h`);
    const days = Math.floor(hours / 24);
    return t("oauth.expiresIn").replace("{time}", `${days}d`);
  } catch {
    return null;
  }
}

async function refresh() {
  loading.value = true;
  try {
    const resp = await api.getOAuthProviders();
    providers.value = resp.providers;
  } catch (e) {
    emit("error", `Failed to load providers: ${e}`);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  refresh();
});

async function handleCopy(p: OAuthProvider) {
  try {
    await navigator.clipboard.writeText(p.cli_command);
    copiedId.value = p.id;
    emit("success", `Copied: ${p.cli_command}`);
    setTimeout(() => {
      copiedId.value = copiedId.value === p.id ? null : copiedId.value;
    }, 1500);
  } catch {
    emit("error", "Clipboard write failed — copy the command manually");
  }
}

async function handleDisconnect(p: OAuthProvider) {
  if (!confirm(`${t("oauth.disconnect")} ${p.name}?`)) return;
  busyId.value = p.id;
  try {
    await api.disconnectOAuthProvider(p.id);
    emit("success", `${p.name} ${t("oauth.disconnect").toLowerCase()}ed`);
    refresh();
  } catch (e) {
    emit("error", `${t("oauth.disconnect")} failed: ${e}`);
  } finally {
    busyId.value = null;
  }
}

const connectedCount = computed(
  () => providers.value?.filter((p) => p.status.logged_in).length ?? 0,
);
const totalCount = computed(() => providers.value?.length ?? 0);
</script>

<template>
  <div class="border border-border bg-card">
    <div class="px-4 py-3 border-b border-border flex items-center justify-between">
      <div class="flex items-center gap-2">
        <ShieldCheck class="h-5 w-5 text-muted-foreground" />
        <span class="text-base font-semibold">{{ t('oauth.providerLogins') }}</span>
      </div>
      <NButton size="small" :disabled="loading" @click="refresh">
        <template #icon><RefreshCw class="h-3 w-3" :class="loading ? 'animate-spin' : ''" /></template>
        {{ t('common.refresh') }}
      </NButton>
    </div>
    <div class="px-4 py-2 border-b border-border">
      <p class="text-xs text-muted-foreground">
        {{ t('oauth.description')
          .replace('{connected}', String(connectedCount))
          .replace('{total}', String(totalCount)) }}
      </p>
    </div>
    <div class="p-0">
      <div v-if="loading && providers === null" class="flex items-center justify-center py-8">
        <div class="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
      <p
        v-else-if="providers && providers.length === 0"
        class="text-sm text-muted-foreground text-center py-8"
      >
        {{ t('oauth.noProviders') }}
      </p>
      <div v-else class="flex flex-col divide-y divide-border">
        <div
          v-for="p in providers"
          :key="p.id"
          class="flex items-center justify-between gap-4 py-3 px-4"
        >
          <!-- Left: status icon + name + details -->
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <ShieldCheck
              v-if="p.status.logged_in"
              class="h-5 w-5 text-success shrink-0 mt-0.5"
            />
            <ShieldOff
              v-else
              class="h-5 w-5 text-muted-foreground shrink-0 mt-0.5"
            />
            <div class="flex flex-col min-w-0 gap-0.5">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-medium text-sm">{{ p.name }}</span>
                <NTag :bordered="true" size="small">
                  <span class="text-[11px] uppercase tracking-wide">
                    {{ t(`oauth.flowLabels.${p.flow}`) }}
                  </span>
                </NTag>
                <NTag v-if="p.status.logged_in" type="success" size="small" :bordered="false">
                  {{ t('oauth.connected') }}
                </NTag>
                <NTag
                  v-if="formatExpiresAt(p.status.expires_at) === 'expired'"
                  type="error"
                  size="small"
                  :bordered="false"
                >
                  {{ t('oauth.expired') }}
                </NTag>
                <NTag
                  v-else-if="formatExpiresAt(p.status.expires_at) && formatExpiresAt(p.status.expires_at) !== 'expired'"
                  :bordered="true"
                  size="small"
                >
                  {{ formatExpiresAt(p.status.expires_at) }}
                </NTag>
              </div>
              <code v-if="p.status.logged_in && p.status.token_preview" class="text-xs font-mono-ui truncate">
                <span class="opacity-50">token </span>
                {{ p.status.token_preview }}
                <span v-if="p.status.source_label" class="opacity-40">
                  · {{ p.status.source_label }}
                </span>
              </code>
              <span v-if="!p.status.logged_in" class="text-xs text-muted-foreground/80">
                {{ t('oauth.notConnected').split('{command}')[0] }}
                <code class="text-foreground bg-secondary/40 px-1">{{ p.cli_command }}</code>
                {{ t('oauth.notConnected').split('{command}')[1] || '' }}
              </span>
              <span v-if="p.status.error" class="text-xs text-destructive">
                {{ p.status.error }}
              </span>
            </div>
          </div>

          <!-- Right: action buttons -->
          <div class="flex items-center gap-1.5 shrink-0">
            <a
              v-if="p.docs_url"
              :href="p.docs_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex"
              :title="`Open ${p.name} docs`"
            >
              <NButton size="small" text>
                <template #icon><ExternalLink class="h-3.5 w-3.5" /></template>
              </NButton>
            </a>
            <NButton
              v-if="!p.status.logged_in && p.flow !== 'external'"
              size="small"
              type="primary"
              @click="loginFor = p"
            >
              <template #icon><LogIn class="h-3 w-3" /></template>
              {{ t('oauth.login') }}
            </NButton>
            <NButton
              v-if="!p.status.logged_in"
              size="small"
              @click="handleCopy(p)"
              :title="t('oauth.copyCliCommand')"
            >
              <template v-if="copiedId === p.id">
                {{ t('oauth.copied') }}
              </template>
              <template v-else>
                <Copy class="h-3 w-3" />
                {{ t('oauth.cli') }}
              </template>
            </NButton>
            <template v-if="p.status.logged_in && p.flow !== 'external'">
              <NButton
                size="small"
                :disabled="busyId === p.id"
                @click="handleDisconnect(p)"
              >
                <template #icon>
                  <RefreshCw v-if="busyId === p.id" class="h-3 w-3 animate-spin" />
                  <LogOut v-else class="h-3 w-3" />
                </template>
                {{ t('oauth.disconnect') }}
              </NButton>
            </template>
            <span
              v-if="p.status.logged_in && p.flow === 'external'"
              class="text-[11px] text-muted-foreground italic px-2"
            >
              <Terminal class="h-3 w-3 inline mr-0.5" />
              {{ t('oauth.managedExternally') }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <OAuthLoginModal
    v-if="loginFor"
    :provider="loginFor"
    @close="loginFor = null; refresh()"
    @success="(msg: string) => emit('success', msg)"
    @error="(msg: string) => emit('error', msg)"
  />
</template>
