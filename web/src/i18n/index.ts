import type { App } from "vue";
import { createI18n } from "vue-i18n";
import { en } from "@/i18n/en";
import { zh } from "@/i18n/zh";

type Locale = "en" | "zh";
const STORAGE_KEY = "anydeals-locale";

function getInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "zh") return stored as Locale;
  } catch { /* ignore */ }
  try {
    const nav = navigator.language.toLowerCase();
    if (nav.startsWith("zh")) return "zh";
  } catch { /* ignore */ }
  return "en";
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: "en",
  messages: { en, zh },
});

export function setLocale(l: Locale) {
  (i18n.global.locale as unknown as { value: Locale }).value = l;
  try { localStorage.setItem(STORAGE_KEY, l); } catch { /* ignore */ }
}

export function getLocale(): Locale {
  return i18n.global.locale as unknown as Locale;
}

export const i18nPlugin = {
  install(_app: App) {
    // vue-i18n is already installed via createI18n
  },
};
