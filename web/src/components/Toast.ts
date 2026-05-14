import { h, render } from "vue";

export interface ToastState {
  message: string;
  type: "success" | "error";
}

export function showToast(toast: ToastState) {
  const container = document.createElement("div");
  document.body.appendChild(container);

  const vm = h(
    "div",
    {
      role: "status",
      "aria-live": "polite",
      class: `fixed top-16 right-4 z-50 border px-4 py-2.5 font-courier text-xs tracking-wider uppercase backdrop-blur-sm ${
        toast.type === "success"
          ? "bg-success/15 text-success border-success/30"
          : "bg-destructive/15 text-destructive border-destructive/30"
      }`,
      style: "animation: toast-in 200ms ease-out forwards",
    },
    toast.message,
  );

  render(vm, container);

  setTimeout(() => {
    render(null, container);
    document.body.removeChild(container);
  }, 4000);
}
