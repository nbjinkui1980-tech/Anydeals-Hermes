<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";
import { NButton, NInput } from "naive-ui";
import { ExternalLink, Copy, X, Check, Loader2 } from "lucide-vue-next";
import { api, type OAuthProvider, type OAuthStartResponse } from "@/lib/api";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  provider: OAuthProvider;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "success", msg: string): void;
  (e: "error", msg: string): void;
}>();

const { t } = useI18n();

type Phase =
  | "idle"
  | "starting"
  | "awaiting_user"
  | "submitting"
  | "polling"
  | "approved"
  | "error";

const phase = ref<Phase>("starting");
const start = ref<OAuthStartResponse | null>(null);
const pkceCode = ref("");
const errorMsg = ref<string | null>(null);
const secondsLeft = ref<number | null>(null);
const codeCopied = ref(false);
let isMounted = true;
let pollTimer: ReturnType<typeof setInterval> | null = null;
let countdownTimer: ReturnType<typeof setInterval> | null = null;

function fmtTime(s: number | null) {
  if (s === null) return "";
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

onMounted(async () => {
  isMounted = true;

  // Countdown tick
  countdownTimer = setInterval(() => {
    if (!isMounted) return;
    if (phase.value === "approved" || phase.value === "error") return;
    const s = secondsLeft.value;
    if (s !== null && s <= 1) {
      phase.value = "error";
      errorMsg.value = t("oauth.sessionExpired");
      secondsLeft.value = 0;
      return;
    }
    secondsLeft.value = s !== null && s > 0 ? s - 1 : 0;
  }, 1000);

  try {
    const resp = await api.startOAuthLogin(props.provider.id);
    if (!isMounted) return;
    start.value = resp;
    secondsLeft.value = resp.expires_in;
    phase.value = resp.flow === "device_code" ? "polling" : "awaiting_user";
    if (resp.flow === "pkce") {
      window.open(resp.auth_url, "_blank", "noopener,noreferrer");
    } else {
      window.open(resp.verification_url, "_blank", "noopener,noreferrer");
    }
  } catch (e) {
    if (!isMounted) return;
    phase.value = "error";
    errorMsg.value = `Failed to start login: ${e}`;
  }
});

onUnmounted(() => {
  isMounted = false;
  if (pollTimer) clearInterval(pollTimer);
  if (countdownTimer) clearInterval(countdownTimer);
});

// Device-code polling
watch([() => start.value, phase], ([s, p]) => {
  if (!s || s.flow !== "device_code" || p !== "polling") {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    return;
  }
  const sid = s.session_id;
  pollTimer = setInterval(async () => {
    try {
      const resp = await api.pollOAuthSession(props.provider.id, sid);
      if (!isMounted) return;
      if (resp.status === "approved") {
        phase.value = "approved";
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
        emit("success", `${props.provider.name} connected`);
        setTimeout(() => { if (isMounted) emit("close"); }, 1500);
      } else if (resp.status !== "pending") {
        phase.value = "error";
        errorMsg.value = resp.error_message || `Login ${resp.status}`;
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      }
    } catch (e) {
      if (!isMounted) return;
      phase.value = "error";
      errorMsg.value = `Polling failed: ${e}`;
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }
  }, 2000);
});

async function handleSubmitPkceCode() {
  if (!start.value || start.value.flow !== "pkce") return;
  if (!pkceCode.value.trim()) return;
  phase.value = "submitting";
  errorMsg.value = null;
  try {
    const resp = await api.submitOAuthCode(
      props.provider.id,
      start.value.session_id,
      pkceCode.value.trim(),
    );
    if (!isMounted) return;
    if (resp.ok && resp.status === "approved") {
      phase.value = "approved";
      emit("success", `${props.provider.name} connected`);
      setTimeout(() => { if (isMounted) emit("close"); }, 1500);
    } else {
      phase.value = "error";
      errorMsg.value = resp.message || "Token exchange failed";
    }
  } catch (e) {
    if (!isMounted) return;
    phase.value = "error";
    errorMsg.value = `Submit failed: ${e}`;
  }
}

async function handleClose() {
  if (start.value && phase.value !== "approved" && phase.value !== "error") {
    try { await api.cancelOAuthSession(start.value.session_id); } catch { /* ignore */ }
  }
  emit("close");
}

async function handleCopyUserCode(code: string) {
  try {
    await navigator.clipboard.writeText(code);
    codeCopied.value = true;
    setTimeout(() => { if (isMounted) codeCopied.value = false; }, 1500);
  } catch {
    emit("error", "Clipboard write failed");
  }
}

function handleRetry() {
  if (start.value?.session_id) {
    api.cancelOAuthSession(start.value.session_id).catch(() => {});
  }
  errorMsg.value = null;
  start.value = null;
  pkceCode.value = "";
  phase.value = "starting";
  api.startOAuthLogin(props.provider.id)
    .then((resp) => {
      if (!isMounted) return;
      start.value = resp;
      secondsLeft.value = resp.expires_in;
      phase.value = resp.flow === "device_code" ? "polling" : "awaiting_user";
      if (resp.flow === "pkce") {
        window.open(resp.auth_url, "_blank", "noopener,noreferrer");
      } else {
        window.open(resp.verification_url, "_blank", "noopener,noreferrer");
      }
    })
    .catch((e) => {
      if (!isMounted) return;
      phase.value = "error";
      errorMsg.value = `${t("common.retry")} failed: ${e}`;
    });
}
</script>

<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-background/85 backdrop-blur-sm p-4"
    role="dialog"
    aria-modal="true"
    aria-labelledby="oauth-modal-title"
    @click.self="handleClose"
  >
    <div class="relative w-full max-w-md border border-border bg-card shadow-2xl">
      <button
        type="button"
        class="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
        :aria-label="t('common.close')"
        @click="handleClose"
      >
        <X class="h-5 w-5" />
      </button>
      <div class="p-6 flex flex-col gap-4">
        <div>
          <h2
            id="oauth-modal-title"
            class="font-mondwest text-sm tracking-wider uppercase"
          >
            {{ t('oauth.connect') }} {{ provider.name }}
          </h2>
          <p
            v-if="secondsLeft !== null && phase !== 'approved' && phase !== 'error'"
            class="text-xs text-muted-foreground mt-1"
          >
            {{ t('oauth.sessionExpires').replace('{time}', fmtTime(secondsLeft)) }}
          </p>
        </div>

        <!-- starting -->
        <div v-if="phase === 'starting'" class="flex items-center gap-3 py-6 text-sm text-muted-foreground">
          <Loader2 class="h-4 w-4 animate-spin" />
          {{ t('oauth.initiatingLogin') }}
        </div>

        <!-- PKCE: paste code -->
        <template v-if="start?.flow === 'pkce' && phase === 'awaiting_user'">
          <ol class="text-sm space-y-2 list-decimal list-inside text-muted-foreground">
            <li>{{ t('oauth.pkceStep1') }}</li>
            <li>{{ t('oauth.pkceStep2') }}</li>
            <li>{{ t('oauth.pkceStep3') }}</li>
          </ol>
          <div class="flex flex-col gap-2">
            <NInput
              size="small"
              :value="pkceCode"
              @update:value="(v: string) => pkceCode = v"
              :placeholder="t('oauth.pasteCode')"
              @keydown="(e: KeyboardEvent) => e.key === 'Enter' && handleSubmitPkceCode()"
            />
            <div class="flex items-center gap-2 justify-between">
              <a
                :href="(start as any).auth_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
              >
                <ExternalLink class="h-3 w-3" />
                {{ t('oauth.reOpenAuth') }}
              </a>
              <NButton
                size="small"
                type="primary"
                :disabled="!pkceCode.trim()"
                @click="handleSubmitPkceCode"
              >
                {{ t('oauth.submitCode') }}
              </NButton>
            </div>
          </div>
        </template>

        <!-- submitting -->
        <div v-if="phase === 'submitting'" class="flex items-center gap-3 py-6 text-sm text-muted-foreground">
          <Loader2 class="h-4 w-4 animate-spin" />
          {{ t('oauth.exchangingCode') }}
        </div>

        <!-- Device code: show code + URL, polling -->
        <template v-if="start?.flow === 'device_code' && phase === 'polling'">
          <p class="text-sm text-muted-foreground">
            {{ t('oauth.enterCodePrompt') }}
          </p>
          <div class="flex items-center justify-between gap-2 border border-border bg-secondary/30 p-4">
            <code class="font-mono-ui text-2xl tracking-widest text-foreground">
              {{ (start as any).user_code }}
            </code>
            <NButton
              size="small"
              @click="handleCopyUserCode((start as any).user_code)"
            >
              <template #icon>
                <Check v-if="codeCopied" class="h-3 w-3" />
                <Copy v-else class="h-3 w-3" />
              </template>
            </NButton>
          </div>
          <a
            :href="(start as any).verification_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
          >
            <ExternalLink class="h-3 w-3" />
            {{ t('oauth.reOpenVerification') }}
          </a>
          <div class="flex items-center gap-2 text-xs text-muted-foreground border-t border-border pt-3">
            <Loader2 class="h-3 w-3 animate-spin" />
            {{ t('oauth.waitingAuth') }}
          </div>
        </template>

        <!-- approved -->
        <div v-if="phase === 'approved'" class="flex items-center gap-3 py-6 text-sm text-success">
          <Check class="h-5 w-5" />
          {{ t('oauth.connectedClosing') }}
        </div>

        <!-- error -->
        <template v-if="phase === 'error'">
          <div class="border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {{ errorMsg || t('oauth.loginFailed') }}
          </div>
          <div class="flex justify-end gap-2">
            <NButton size="small" @click="handleClose">
              {{ t('common.close') }}
            </NButton>
            <NButton size="small" type="primary" @click="handleRetry">
              {{ t('common.retry') }}
            </NButton>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
