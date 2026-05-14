<script setup lang="ts">
import { AlertTriangle, Radio, Wifi, WifiOff } from "lucide-vue-next";
import { NTag } from "naive-ui";
import type { PlatformStatus } from "@/lib/api";
import { isoTimeAgo } from "@/lib/utils";
import { useI18n } from "vue-i18n";

defineProps<{
  platforms: [string, PlatformStatus][];
}>();

const { t } = useI18n();

const stateMeta: Record<string, { type: "success" | "warning" | "error"; label: string }> = {
  connected: { type: "success", label: t("status.connected") },
  disconnected: { type: "warning", label: t("status.disconnected") },
  fatal: { type: "error", label: t("status.error") },
};
</script>

<template>
  <div class="border border-border bg-card">
    <div class="px-4 py-3 border-b border-border flex items-center gap-2">
      <Radio class="h-5 w-5 text-muted-foreground" />
      <span class="text-base font-semibold">{{ t('status.connectedPlatforms') }}</span>
    </div>

    <div class="grid gap-3 p-4">
      <div
        v-for="[name, info] in platforms"
        :key="name"
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border border-border p-3 w-full"
      >
        <div class="flex items-center gap-3 min-w-0 w-full">
          <Wifi
            v-if="info.state === 'connected'"
            class="h-4 w-4 shrink-0 text-success"
          />
          <AlertTriangle
            v-else-if="info.state === 'fatal'"
            class="h-4 w-4 shrink-0 text-destructive"
          />
          <WifiOff
            v-else
            class="h-4 w-4 shrink-0 text-warning"
          />

          <div class="flex flex-col gap-0.5 min-w-0">
            <span class="text-sm font-medium capitalize truncate">{{ name }}</span>
            <span v-if="info.error_message" class="text-xs text-destructive">
              {{ info.error_message }}
            </span>
            <span v-if="info.updated_at" class="text-xs text-muted-foreground">
              {{ t('status.lastUpdate') }}: {{ isoTimeAgo(info.updated_at) }}
            </span>
          </div>
        </div>

        <NTag
          :type="(stateMeta[info.state]?.type as any) || 'default'"
          size="small"
          :bordered="false"
        >
          <span
            v-if="stateMeta[info.state]?.type === 'success'"
            class="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current"
          />
          {{ stateMeta[info.state]?.label || info.state }}
        </NTag>
      </div>
    </div>
  </div>
</template>
