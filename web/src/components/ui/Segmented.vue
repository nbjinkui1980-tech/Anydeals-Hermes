<script setup lang="ts">
import { NRadioGroup, NRadio, NSpace } from "naive-ui";

defineProps<{
  modelValue: string;
  options: { value: string; label: string }[];
  embedded?: boolean;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();
</script>

<template>
  <NRadioGroup :value="modelValue" @update:value="(v: string) => emit('update:modelValue', v)">
    <NSpace :size="0" :wrap="false" :class="embedded ? '' : 'border border-border/50'">
      <NRadio
        v-for="opt in options"
        :key="opt.value"
        :value="opt.value"
        :checked="modelValue === opt.value"
      >
        <span class="text-xs tracking-wide uppercase px-2 py-1">{{ opt.label }}</span>
      </NRadio>
    </NSpace>
  </NRadioGroup>
</template>
