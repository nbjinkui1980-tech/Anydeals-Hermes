import type { Component } from "vue";

export interface PluginManifest {
  name: string;
  label: string;
  description: string;
  icon: string;
  version: string;
  tab: {
    path: string;
    position?: string;
    override?: string;
    hidden?: boolean;
  };
  slots?: string[];
  entry: string;
  css?: string | null;
  has_api: boolean;
  source: string;
}

export interface RegisteredPlugin {
  manifest: PluginManifest;
  component: Component;
}
