<script setup lang="ts">
import { setLocale } from "@/i18n";
import { useI18n } from "vue-i18n";

const { t, locale } = useI18n();

function toggle() {
  setLocale((locale.value as string) === "en" ? "zh" : "en");
}
</script>

<template>
  <button
    type="button"
    class="group relative inline-flex items-center gap-1.5 px-2 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
    :title="t('language.switchTo')"
    :aria-label="t('language.switchTo')"
    @click="toggle"
  >
    <span class="text-base leading-none">{{ locale === 'en' ? '🇬🇧' : '🇨🇳' }}</span>
    <span class="hidden sm:inline font-mondwest tracking-wide uppercase text-[0.65rem]">
      {{ locale === 'en' ? 'EN' : '中文' }}
    </span>
  </button>
</template>
