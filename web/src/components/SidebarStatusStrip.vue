<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import { useSidebarStatus } from "@/composables/useSidebarStatus";
import { useI18n } from "vue-i18n";
import type { StatusResponse } from "@/lib/api";

const status = useSidebarStatus();
const { t } = useI18n();

function gatewayLine(s: StatusResponse) {
  const byState: Record<string, { label: string; tone: string }> = {
    running: { label: t("app.gatewayStrip.running"), tone: "text-success" },
    starting: { label: t("app.gatewayStrip.starting"), tone: "text-warning" },
    startup_failed: { label: t("app.gatewayStrip.failed"), tone: "text-destructive" },
    stopped: { label: t("app.gatewayStrip.stopped"), tone: "text-muted-foreground" },
  };
  if (s.gateway_state && byState[s.gateway_state]) {
    return byState[s.gateway_state];
  }
  return s.gateway_running
    ? { label: byState.running.label, tone: "text-success" }
    : { label: t("app.gatewayStrip.off"), tone: "text-muted-foreground" };
}

const gw = computed(() => {
  if (!status.value)
    return { label: "…", tone: "text-muted-foreground" };
  try {
    return gatewayLine(status.value);
  } catch {
    return { label: "—", tone: "text-muted-foreground" };
  }
});
</script>

<template>
  <div v-if="status === null" class="px-5 py-1.5" aria-hidden>
    <div class="h-2 w-[80%] max-w-full animate-pulse rounded-sm bg-midground/10" />
  </div>

  <RouterLink
    v-else
    to="/sessions"
    :title="t('app.statusOverview')"
    class="block text-left px-5 pb-2 pt-0.5 text-muted-foreground/70 transition-colors hover:text-muted-foreground/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-midground/40 focus-visible:ring-inset"
  >
    <div class="flex flex-col gap-1 font-mondwest text-[0.55rem] leading-snug tracking-[0.12em]">
      <p class="break-words">
        <span class="text-muted-foreground/50">{{ t('app.gatewayStatusLabel') }}</span>
        <span class="font-medium" :class="gw.tone">{{ gw.label }}</span>
      </p>
      <p class="break-words">
        <span class="text-muted-foreground/50">{{ t('app.activeSessionsLabel') }}</span>
        <span class="tabular-nums text-muted-foreground/70">{{ status?.active_sessions }}</span>
      </p>
    </div>
  </RouterLink>
</template>
