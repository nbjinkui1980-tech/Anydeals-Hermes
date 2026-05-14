<script setup lang="ts">
import { ref, onUnmounted } from "vue";
import { Loader2 } from "lucide-vue-next";
import {
  getPluginComponent,
  getPluginLoadError,
  onPluginRegistered,
} from "@/plugin/registry";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  name: string;
}>();

const { t } = useI18n();

const Component = ref(getPluginComponent(props.name) ?? null);
const loadError = ref(getPluginLoadError(props.name) ?? null);

const unsub = onPluginRegistered(() => {
  Component.value = getPluginComponent(props.name) ?? null;
  loadError.value = getPluginLoadError(props.name) ?? null;
});

onUnmounted(unsub);
</script>

<template>
  <component v-if="Component" :is="Component" />

  <div
    v-else-if="loadError"
    class="max-w-lg p-4 font-mondwest text-sm tracking-[0.08em] text-midground/80"
    role="alert"
  >
    <template v-if="loadError === 'LOAD_FAILED'">{{ t('common.pluginLoadFailed') }}</template>
    <template v-else-if="loadError === 'NO_REGISTER'">{{ t('common.pluginNotRegistered') }}</template>
    <template v-else>{{ loadError }}</template>
  </div>

  <div
    v-else
    class="flex items-center gap-2 p-4 font-mondwest text-sm tracking-[0.1em] text-midground/60"
  >
    <Loader2 class="h-4 w-4 shrink-0 animate-spin" aria-hidden />
    <span>{{ t('common.loading') }}</span>
  </div>
</template>
