import { ref } from "vue";

export function useConfirmDelete<TId>(onDelete: (id: TId) => Promise<void>) {
  const pendingId = ref<TId | null>(null);
  const isDeleting = ref(false);

  function requestDelete(id: TId) {
    pendingId.value = id;
  }

  function cancel() {
    if (!isDeleting.value) pendingId.value = null;
  }

  async function confirm() {
    if (pendingId.value === null) return;
    const id = pendingId.value;
    isDeleting.value = true;
    try {
      await onDelete(id);
      pendingId.value = null;
    } catch {
      // Dialog stays open; caller surfaces errors in onDelete
    } finally {
      isDeleting.value = false;
    }
  }

  return {
    cancel,
    confirm,
    isDeleting,
    isOpen: () => pendingId.value !== null,
    pendingId,
    requestDelete,
  };
}
