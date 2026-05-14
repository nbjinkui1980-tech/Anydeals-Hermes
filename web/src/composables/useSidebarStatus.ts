import { ref, onMounted, onUnmounted } from "vue";
import { api } from "@/lib/api";
import type { StatusResponse } from "@/lib/api";

const POLL_MS = 10_000;

export function useSidebarStatus() {
  const status = ref<StatusResponse | null>(null);
  let timer: ReturnType<typeof setInterval> | null = null;

  async function load() {
    try {
      status.value = await api.getStatus();
    } catch {
      // keep previous value
    }
  }

  onMounted(() => {
    load();
    timer = setInterval(load, POLL_MS);
  });

  onUnmounted(() => {
    if (timer !== null) clearInterval(timer);
  });

  return status;
}
