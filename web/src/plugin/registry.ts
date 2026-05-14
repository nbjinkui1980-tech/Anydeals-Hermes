import { h, ref, reactive, computed, watch, onMounted, onUnmounted, defineComponent } from "vue";
import type { Component } from "vue";
import { NButton, NInput, NSelect, NSwitch, NTag, NCard, NModal, NDataTable } from "naive-ui";
import { api, fetchJSON } from "@/lib/api";
import { cn, timeAgo, isoTimeAgo } from "@/lib/utils";
import { registerSlot, unregisterPluginSlots } from "./slots";
import PluginSlot from "@/components/PluginSlot.vue";
import { useI18n } from "vue-i18n";

type RegistryListener = () => void;

const _registered: Map<string, Component> = new Map();
const _listeners: Set<RegistryListener> = new Set();
const _loadErrors: Map<string, string> = new Map();

function _notify() {
  for (const fn of _listeners) {
    try { fn(); } catch { /* ignore */ }
  }
}

export function notifyPluginRegistry() {
  _notify();
}

export function registerPlugin(name: string, component: Component) {
  _registered.set(name, component);
  _loadErrors.delete(name);
  _notify();
}

export function getPluginComponent(name: string): Component | undefined {
  return _registered.get(name);
}

export function getRegisteredCount(): number {
  return _registered.size;
}

export function getPluginLoadError(name: string): string | null {
  return _loadErrors.get(name) ?? null;
}

export function setPluginLoadError(name: string, error: string) {
  _loadErrors.set(name, error);
  _notify();
}

export function onPluginRegistered(fn: RegistryListener): () => void {
  _listeners.add(fn);
  return () => _listeners.delete(fn);
}

export function exposePluginSDK() {
  const plugins = {
    register: registerPlugin,
    registerSlot,
    unregisterSlots: unregisterPluginSlots,
  };

  const sdk = {
    // Vue core — plugins use these via h() to create components
    vue: { h, ref, reactive, computed, watch, onMounted, onUnmounted, defineComponent },

    // Naive UI components for plugin UI
    components: {
      NButton,
      NInput,
      NSelect,
      NSwitch,
      NTag,
      NCard,
      NModal,
      NDataTable,
      PluginSlot,
    },

    // API client
    api,
    fetchJSON,

    // Utilities
    utils: { cn, timeAgo, isoTimeAgo },

    // i18n composable
    useI18n,
  };

  (window as any).__ANYDEALS_PLUGINS__ = plugins;
  (window as any).__ANYDEALS_PLUGIN_SDK__ = sdk;
  (window as any).__HERMES_PLUGINS__ = plugins;
  (window as any).__HERMES_PLUGIN_SDK__ = sdk;
}
