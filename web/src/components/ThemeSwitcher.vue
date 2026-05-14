<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { Palette, Check } from "lucide-vue-next";
import { useThemeStore } from "@/stores/themeStore";
import { BUILTIN_THEMES } from "@/themes/presets";
import { useI18n } from "vue-i18n";

const { themeName, availableThemes, setTheme } = useThemeStore();
const { t } = useI18n();

const open = ref(false);
const target = ref<HTMLElement | null>(null);

function onMouseDown(e: MouseEvent) {
  if (target.value && !target.value.contains(e.target as Node)) {
    open.value = false;
  }
}
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") open.value = false;
}

onMounted(() => {
  document.addEventListener("mousedown", onMouseDown, true);
  document.addEventListener("keydown", onKey, true);
});
onUnmounted(() => {
  document.removeEventListener("mousedown", onMouseDown, true);
  document.removeEventListener("keydown", onKey, true);
});

const current = computed(() =>
  availableThemes.find((th) => th.name === themeName),
);
const label = computed(() => current.value?.label ?? themeName);
</script>

<template>
  <div ref="target" class="relative">
    <button
      type="button"
      class="group relative inline-flex items-center gap-1.5 px-2 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-midground"
      :title="t('theme.switchTheme')"
      :aria-label="t('theme.switchTheme')"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="open = !open"
    >
      <Palette class="h-3.5 w-3.5" />
      <span class="hidden sm:inline font-mondwest tracking-wide uppercase text-[0.65rem]">{{ label }}</span>
    </button>

    <div
      v-if="open"
      role="listbox"
      :aria-label="t('theme.title')"
      class="absolute z-50 right-0 top-full mt-1 min-w-[240px] border border-current/20 bg-background-base/95 backdrop-blur-sm shadow-[0_12px_32px_-8px_rgba(0,0,0,0.6)]"
    >
      <div class="border-b border-current/20 px-3 py-2">
        <span class="font-mondwest text-[0.65rem] tracking-[0.15em] uppercase text-midground/70">
          {{ t('theme.title') }}
        </span>
      </div>

      <button
        v-for="th in availableThemes"
        :key="th.name"
        type="button"
        role="option"
        :aria-selected="th.name === themeName"
        class="flex w-full items-center gap-3 px-3 py-2 text-left transition-colors cursor-pointer hover:bg-midground/10"
        :class="th.name === themeName ? 'text-midground' : 'text-midground/60'"
        @click="setTheme(th.name); open = false"
      >
        <template v-if="BUILTIN_THEMES[th.name]">
          <span class="flex h-4 w-9 shrink-0 overflow-hidden border border-current/20" aria-hidden>
            <span class="flex-1" :style="{ background: BUILTIN_THEMES[th.name].palette.background.hex }" />
            <span class="flex-1" :style="{ background: BUILTIN_THEMES[th.name].palette.midground.hex }" />
            <span class="flex-1" :style="{ background: BUILTIN_THEMES[th.name].palette.warmGlow }" />
          </span>
        </template>
        <span v-else class="h-4 w-9 shrink-0 border border-dashed border-current/20" aria-hidden />

        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="font-mondwest truncate text-[0.75rem] tracking-wide uppercase">{{ th.label }}</span>
          <span v-if="th.description" class="truncate text-[0.65rem] normal-case tracking-normal text-midground/50">{{ th.description }}</span>
        </div>

        <Check class="h-3 w-3 shrink-0 text-midground" :class="th.name === themeName ? 'opacity-100' : 'opacity-0'" />
      </button>
    </div>
  </div>
</template>
