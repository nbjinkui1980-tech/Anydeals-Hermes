import { ref, onMounted, onUnmounted, watch } from "vue";
import { api } from "@/lib/api";
import { getPluginComponent, onPluginRegistered, notifyPluginRegistry, setPluginLoadError } from "@/plugin/registry";
import type { PluginManifest, RegisteredPlugin } from "@/plugin/types";

export function usePlugins() {
  const manifests = ref<PluginManifest[]>([]);
  const plugins = ref<RegisteredPlugin[]>([]);
  const loading = ref(true);
  const loadedScripts = new Set<string>();

  function resolvePlugins() {
    const resolved: RegisteredPlugin[] = [];
    for (const manifest of manifests.value) {
      const component = getPluginComponent(manifest.name);
      if (component) {
        resolved.push({ manifest, component });
      }
    }
    plugins.value = resolved;
    if (resolved.length === manifests.value.length && manifests.value.length > 0) {
      loading.value = false;
    }
  }

  // Fetch manifests on mount
  onMounted(async () => {
    try {
      const list = await api.getPlugins();
      manifests.value = list;
      if (list.length === 0) loading.value = false;
    } catch {
      loading.value = false;
    }
  });

  // Load plugin assets when manifests arrive
  watch(manifests, (list) => {
    if (list.length === 0) return;

    for (const manifest of list) {
      if (manifest.css) {
        const cssUrl = `/dashboard-plugins/${manifest.name}/${manifest.css}`;
        if (!document.querySelector(`link[href="${cssUrl}"]`)) {
          const link = document.createElement("link");
          link.rel = "stylesheet";
          link.href = cssUrl;
          document.head.appendChild(link);
        }
      }

      const baseUrl = `/dashboard-plugins/${manifest.name}/${manifest.entry}`;
      const scriptSrc = import.meta.env.DEV
        ? `${baseUrl}?anydeals_dv=${Date.now()}`
        : baseUrl;
      if (!import.meta.env.DEV) {
        if (loadedScripts.has(baseUrl)) continue;
        loadedScripts.add(baseUrl);
      }

      const script = document.createElement("script");
      script.setAttribute("data-anydeals-plugin", manifest.name);
      script.src = scriptSrc;
      script.async = true;
      script.onerror = () => {
        setPluginLoadError(manifest.name, "LOAD_FAILED");
        console.warn(
          `[plugins] Failed to load ${manifest.name} from ${scriptSrc}`,
        );
      };
      script.onload = () => {
        notifyPluginRegistry();
        queueMicrotask(() => {
          if (getPluginComponent(manifest.name)) return;
          setPluginLoadError(manifest.name, "NO_REGISTER");
        });
      };
      document.body.appendChild(script);
    }

    setTimeout(() => { loading.value = false; }, 2000);
  });

  const unsub = onPluginRegistered(resolvePlugins);

  onUnmounted(unsub);

  return { plugins, manifests, loading };
}
