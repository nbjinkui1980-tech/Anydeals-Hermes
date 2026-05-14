import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/lib/api";
import type { ActionStatusResponse } from "@/lib/api";

export type SystemAction = "restart" | "update";

const ACTION_NAMES: Record<SystemAction, string> = {
  restart: "gateway-restart",
  update: "anydeals-update",
};

export interface ToastState {
  message: string;
  type: "success" | "error";
}

export const useSystemActionsStore = defineStore("systemActions", () => {
  const pendingAction = ref<SystemAction | null>(null);
  const activeAction = ref<SystemAction | null>(null);
  const actionStatus = ref<ActionStatusResponse | null>(null);
  const toast = ref<ToastState | null>(null);
  const { t } = useI18n();

  const isRunning = computed(
    () => activeAction.value !== null && actionStatus.value?.running !== false,
  );
  const isBusy = computed(() => pendingAction.value !== null || isRunning.value);

  let pollTimer: ReturnType<typeof setTimeout> | null = null;

  function stopPolling() {
    if (pollTimer !== null) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  }

  async function pollStatus() {
    if (!activeAction.value) return;
    const name = ACTION_NAMES[activeAction.value];
    try {
      const resp = await api.getActionStatus(name);
      actionStatus.value = resp;
      if (!resp.running) {
        const ok = resp.exit_code === 0;
        toast.value = {
          type: ok ? "success" : "error",
          message: ok
            ? t("status.actionFinished")
            : `${t("status.actionFailed")} (exit ${resp.exit_code ?? "?"})`,
        };
        return;
      }
    } catch {
      // transient fetch error; keep polling
    }
    pollTimer = setTimeout(pollStatus, 1500);
  }

  async function runAction(action: SystemAction) {
    pendingAction.value = action;
    actionStatus.value = null;
    try {
      if (action === "restart") {
        await api.restartGateway();
      } else {
        await api.updateAnyDeals();
      }
      activeAction.value = action;
      pollStatus();
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      toast.value = {
        type: "error",
        message: `${t("status.actionFailed")}: ${detail}`,
      };
    } finally {
      pendingAction.value = null;
    }
  }

  function dismissLog() {
    stopPolling();
    activeAction.value = null;
    actionStatus.value = null;
  }

  return {
    actionStatus,
    activeAction,
    dismissLog,
    isBusy,
    isRunning,
    pendingAction,
    runAction,
    toast,
  };
});
