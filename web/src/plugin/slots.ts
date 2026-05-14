import type { Component } from "vue";

export const KNOWN_SLOT_NAMES = [
  "backdrop",
  "header-left",
  "header-right",
  "header-banner",
  "sidebar",
  "pre-main",
  "post-main",
  "footer-left",
  "footer-right",
  "overlay",
  "sessions:top",
  "sessions:bottom",
  "analytics:top",
  "analytics:bottom",
  "logs:top",
  "logs:bottom",
  "cron:top",
  "cron:bottom",
  "skills:top",
  "skills:bottom",
  "config:top",
  "config:bottom",
  "env:top",
  "env:bottom",
  "docs:top",
  "docs:bottom",
  "chat:top",
  "chat:bottom",
] as const;

export type KnownSlotName = (typeof KNOWN_SLOT_NAMES)[number];

type SlotListener = () => void;

export interface SlotEntry {
  plugin: string;
  component: Component;
}

const _slotRegistry: Map<string, SlotEntry[]> = new Map();
const _slotListeners: Set<SlotListener> = new Set();

function _notifySlots() {
  for (const fn of _slotListeners) {
    try { fn(); } catch { /* ignore */ }
  }
}

export function registerSlot(
  plugin: string,
  slot: string,
  component: Component,
): void {
  const existing = _slotRegistry.get(slot) ?? [];
  const filtered = existing.filter((e) => e.plugin !== plugin);
  filtered.push({ plugin, component });
  _slotRegistry.set(slot, filtered);
  _notifySlots();
}

export function getSlotEntries(slot: string): SlotEntry[] {
  return (_slotRegistry.get(slot) ?? []).slice();
}

export function onSlotRegistered(fn: SlotListener): () => void {
  _slotListeners.add(fn);
  return () => _slotListeners.delete(fn);
}

export function unregisterPluginSlots(plugin: string): void {
  let changed = false;
  for (const [slot, entries] of _slotRegistry.entries()) {
    const kept = entries.filter((e) => e.plugin !== plugin);
    if (kept.length !== entries.length) {
      changed = true;
      if (kept.length === 0) _slotRegistry.delete(slot);
      else _slotRegistry.set(slot, kept);
    }
  }
  if (changed) _notifySlots();
}
