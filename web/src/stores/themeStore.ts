import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { api } from "@/lib/api";
import { BUILTIN_THEMES, defaultTheme } from "@/themes/presets";
import { applyTheme, STORAGE_KEY } from "@/themes/apply";
import type { DashboardTheme } from "@/themes/types";

export const useThemeStore = defineStore("theme", () => {
  const themeName = ref<string>(
    typeof window !== "undefined"
      ? window.localStorage.getItem(STORAGE_KEY) ?? "aurora"
      : "aurora",
  );

  const availableThemes = ref<
    Array<{ description: string; label: string; name: string }>
  >(
    Object.values(BUILTIN_THEMES).map((t) => ({
      name: t.name,
      label: t.label,
      description: t.description,
    })),
  );

  const userThemeDefs = ref<Record<string, DashboardTheme>>({});

  function resolveTheme(name: string): DashboardTheme {
    return BUILTIN_THEMES[name] ?? userThemeDefs.value[name] ?? defaultTheme;
  }

  const theme = ref<DashboardTheme>(resolveTheme(themeName.value));

  function setTheme(name: string) {
    const knownNames = new Set([
      ...Object.keys(BUILTIN_THEMES),
      ...availableThemes.value.map((t) => t.name),
      ...Object.keys(userThemeDefs.value),
    ]);
    const next = knownNames.has(name) ? name : "aurora";
    themeName.value = next;
    theme.value = resolveTheme(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
    api.setTheme(next).catch(() => {});
  }

  // Watch themeName and re-apply theme
  watch(themeName, (name) => {
    theme.value = resolveTheme(name);
    applyTheme(theme.value);
  }, { immediate: true });

  // Watch userThemeDefs — may resolve a previously unknown theme
  watch(userThemeDefs, () => {
    theme.value = resolveTheme(themeName.value);
    applyTheme(theme.value);
  }, { deep: true });

  // Load server-side themes on init
  api
    .getThemes()
    .then((resp) => {
      if (resp.themes?.length) {
        availableThemes.value = resp.themes.map((t) => ({
          name: t.name,
          label: t.label,
          description: t.description,
        }));
        const defs: Record<string, DashboardTheme> = {};
        for (const entry of resp.themes) {
          if (entry.definition) {
            defs[entry.name] = entry.definition;
          }
        }
        if (Object.keys(defs).length > 0) userThemeDefs.value = defs;
      }
      if (resp.active && resp.active !== themeName.value) {
        setTheme(resp.active);
      }
    })
    .catch(() => {});

  return {
    theme,
    themeName,
    availableThemes,
    setTheme,
  };
});
