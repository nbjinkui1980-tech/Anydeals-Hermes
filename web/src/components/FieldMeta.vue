<script setup lang="ts">
defineProps<{
  keyPath: string;
  description: string;
}>();
</script>

<template>
  <div v-if="keyPath || description" class="flex flex-col gap-0.5">
    <span v-if="keyPath" class="text-[10px] font-mono text-muted-foreground/50">{{ keyPath }}</span>
    <span v-if="description" class="text-xs text-muted-foreground/70">{{ description }}</span>
  </div>
</template>
