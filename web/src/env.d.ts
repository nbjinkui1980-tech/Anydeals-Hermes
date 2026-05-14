/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

declare global {
  interface Window {
    __ANYDEALS_SESSION_TOKEN__?: string;
    __ANYDEALS_DASHBOARD_EMBEDDED_CHAT__?: boolean;
    __ANYDEALS_PLUGIN_SDK__: Record<string, unknown>;
    __ANYDEALS_PLUGINS__: {
      register: (name: string, component: import("vue").Component) => void;
      registerSlot: (plugin: string, slot: string, component: import("vue").Component) => void;
    };
    __HERMES_PLUGIN_SDK__: Record<string, unknown>;
    __HERMES_PLUGINS__: {
      register: (name: string, component: import("vue").Component) => void;
      registerSlot: (plugin: string, slot: string, component: import("vue").Component) => void;
    };
  }
}

export {};
