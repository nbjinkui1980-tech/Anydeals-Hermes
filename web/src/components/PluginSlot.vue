<script setup lang="ts">
import { ref, onUnmounted } from "vue";
import { getSlotEntries, onSlotRegistered, type SlotEntry } from "@/plugin/slots";

const props = defineProps<{
  name: string;
}>();

const entries = ref<SlotEntry[]>(getSlotEntries(props.name));

const unsub = onSlotRegistered(() => {
  entries.value = getSlotEntries(props.name);
});

onUnmounted(unsub);
</script>

<template>
  <template v-if="entries.length === 0">
    <slot />
  </template>
  <template v-else>
    <component
      v-for="entry in entries"
      :key="entry.plugin"
      :is="entry.component"
    />
  </template>
</template>
