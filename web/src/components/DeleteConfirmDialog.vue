<script setup lang="ts">
import { NModal, NButton } from "naive-ui";
import { AlertTriangle } from "lucide-vue-next";
import { useI18n } from "vue-i18n";

defineProps<{
  open: boolean;
  title: string;
  description?: string;
  loading?: boolean;
  destructive?: boolean;
}>();

const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "cancel"): void;
}>();

const { t } = useI18n();
</script>

<template>
  <NModal
    :show="open"
    :mask-closable="!loading"
    @update:show="(v: boolean) => !v && emit('cancel')"
  >
    <div class="relative w-full max-w-md border border-border bg-card shadow-lg" style="margin: 0 auto">
      <div class="flex items-start gap-3 p-4 border-b border-border">
        <div v-if="destructive" aria-hidden class="mt-0.5 shrink-0 text-destructive">
          <AlertTriangle class="h-4 w-4" />
        </div>
        <div class="flex-1 min-w-0 flex flex-col gap-1">
          <h2 class="font-expanded text-sm font-bold tracking-[0.08em] uppercase blend-lighter">
            {{ title }}
          </h2>
          <p v-if="description" class="font-mondwest text-xs text-muted-foreground leading-relaxed">
            {{ description }}
          </p>
        </div>
      </div>
      <div class="flex items-center justify-end gap-2 p-3">
        <NButton size="small" :disabled="loading" @click="emit('cancel')">
          {{ t('common.cancel') }}
        </NButton>
        <NButton
          size="small"
          :type="destructive ? 'error' : 'primary'"
          :disabled="loading"
          @click="emit('confirm')"
        >
          {{ loading ? '…' : t('common.confirm') }}
        </NButton>
      </div>
    </div>
  </NModal>
</template>
