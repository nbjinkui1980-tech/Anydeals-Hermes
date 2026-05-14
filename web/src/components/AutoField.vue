<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { NInput, NSelect, NSwitch } from "naive-ui";
import { useI18n } from "vue-i18n";
import FieldMeta from "@/components/FieldMeta.vue";

const props = defineProps<{
  schemaKey: string;
  schema: Record<string, unknown>;
  value: unknown;
}>();

const emit = defineEmits<{
  (e: "change", value: unknown): void;
}>();

const { t } = useI18n();

const rawLabel = props.schemaKey.split(".").pop() ?? props.schemaKey;
const label = rawLabel
  .replace(/_/g, " ")
  .replace(/\b\w/g, (c) => c.toUpperCase());

const keyPath =
  props.schemaKey.includes(".") ? props.schemaKey : "";
const description = props.schema.description
  ? String(props.schema.description)
  : "";

/* Select — local ref for immediate NSelect feedback, synced from props */
const selectValue = ref(String(props.value ?? ""));

watch(
  () => props.value,
  (v) => {
    const str = String(v ?? "");
    if (str !== selectValue.value) {
      selectValue.value = str;
    }
  },
);

const selectOptions = computed(() =>
  ((props.schema.options as string[]) ?? []).map((opt: string) => ({
    label: opt || t("common.noneOption"),
    value: opt,
  })),
);
</script>

<template>
  <!-- Boolean -->
  <div v-if="schema.type === 'boolean'" class="flex items-center justify-between gap-4">
    <div class="flex flex-col gap-0.5">
      <span class="text-sm">{{ label }}</span>
      <FieldMeta :key-path="keyPath" :description="description" />
    </div>
    <NSwitch :value="!!value" @update:value="(v: boolean) => emit('change', v)" size="small" />
  </div>

  <!-- Select -->
  <div v-else-if="schema.type === 'select'" class="grid gap-1.5">
    <span class="text-sm">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <NSelect
      size="small"
      :value="selectValue"
      :options="selectOptions"
      @update:value="(v: string) => { selectValue = v; emit('change', v); }"
    />
  </div>

  <!-- Number -->
  <div v-else-if="schema.type === 'number'" class="grid gap-1.5">
    <span class="text-sm">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <NInput
      size="small"
      :value="value === undefined || value === null ? '' : String(value)"
      @update:value="(v: string) => {
        if (v === '') { emit('change', 0); return; }
        const n = Number(v);
        if (!Number.isNaN(n)) emit('change', n);
      }"
    />
  </div>

  <!-- Text -->
  <div v-else-if="schema.type === 'text'" class="grid gap-1.5">
    <span class="text-sm">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <textarea
      class="flex min-h-[80px] w-full border border-border bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      :value="String(value ?? '')"
      @input="emit('change', ($event.target as HTMLTextAreaElement).value)"
    />
  </div>

  <!-- List -->
  <div v-else-if="schema.type === 'list'" class="grid gap-1.5">
    <span class="text-sm">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <NInput
      size="small"
      :value="Array.isArray(value) ? value.join(', ') : String(value ?? '')"
      :placeholder="t('common.commaSeparatedPlaceholder')"
      @update:value="(v: string) => emit('change', v.split(',').map(s => s.trim()).filter(Boolean))"
    />
  </div>

  <!-- Object (inline sub-fields) -->
  <div v-else-if="typeof value === 'object' && value !== null && !Array.isArray(value)" class="grid gap-3 border border-border p-3">
    <span class="text-xs font-medium">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <div v-for="(subVal, subKey) in (value as Record<string, unknown>)" :key="subKey" class="grid gap-1">
      <span class="text-xs text-muted-foreground">{{ subKey }}</span>
      <NInput
        size="small"
        :value="String(subVal ?? '')"
        @update:value="(v: string) => {
          const obj = { ...(value as Record<string, unknown>), [subKey]: v };
          emit('change', obj);
        }"
      />
    </div>
  </div>

  <!-- Default: string input -->
  <div v-else class="grid gap-1.5">
    <span class="text-sm">{{ label }}</span>
    <FieldMeta :key-path="keyPath" :description="description" />
    <NInput
      size="small"
      :value="String(value ?? '')"
      @update:value="(v: string) => emit('change', v)"
    />
  </div>
</template>
