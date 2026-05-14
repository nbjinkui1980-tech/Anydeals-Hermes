<script setup lang="ts">
import { useSidebarStatus } from "@/composables/useSidebarStatus";
import { useI18n } from "vue-i18n";

const status = useSidebarStatus();
const { t } = useI18n();
</script>

<template>
  <div
    class="flex shrink-0 items-center justify-between gap-2 px-5 py-2.5 border-t border-current/10"
  >
    <span class="font-mono-ui text-[0.7rem] tabular-nums tracking-[0.1em] text-muted-foreground/70">
      {{ status?.version != null ? `v${status.version}` : "—" }}
    </span>

    <a
      href="https://nousresearch.com"
      target="_blank"
      rel="noopener noreferrer"
      class="font-mondwest text-[0.65rem] tracking-[0.15em] text-midground transition-opacity hover:opacity-90 focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-midground/40"
      style="mix-blend-mode: plus-lighter"
    >
      {{ t('app.footer.org') }}
    </a>
  </div>
</template>
