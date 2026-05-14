import { ref, provide, inject, type Ref, type VNode } from "vue";

const TITLE_KEY = Symbol("pageHeaderTitle");
const AFTER_TITLE_KEY = Symbol("pageHeaderAfterTitle");
const END_KEY = Symbol("pageHeaderEnd");

export function createPageHeaderProvider() {
  const title = ref<string | null>(null);
  const afterTitle = ref<VNode | null>(null);
  const end = ref<VNode | null>(null);

  provide(TITLE_KEY, title);
  provide(AFTER_TITLE_KEY, afterTitle);
  provide(END_KEY, end);

  return { title, afterTitle, end };
}

export function usePageHeader() {
  const title = inject<Ref<string | null>>(TITLE_KEY);
  const afterTitle = inject<Ref<VNode | null>>(AFTER_TITLE_KEY);
  const end = inject<Ref<VNode | null>>(END_KEY);

  return {
    setTitle: (val: string | null) => { title && (title.value = val); },
    setAfterTitle: (val: VNode | null) => { afterTitle && (afterTitle.value = val); },
    setEnd: (val: VNode | null) => { end && (end.value = val); },
  };
}
