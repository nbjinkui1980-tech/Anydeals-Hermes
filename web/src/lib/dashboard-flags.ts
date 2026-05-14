declare global {
  interface Window {
    /** Set true by the server only for `anydeals-agent dashboard --tui` (or ANYDEALS_DASHBOARD_TUI=1). */
    __ANYDEALS_DASHBOARD_EMBEDDED_CHAT__?: boolean;
    /** @deprecated Older injected name; treated as on when true. */
    __ANYDEALS_DASHBOARD_TUI__?: boolean;
  }
}

/** True only when the dashboard was started with embedded TUI Chat (`anydeals-agent dashboard --tui`). */
export function isDashboardEmbeddedChatEnabled(): boolean {
  if (typeof window === "undefined") return false;
  if (window.__ANYDEALS_DASHBOARD_EMBEDDED_CHAT__ === true) return true;
  return window.__ANYDEALS_DASHBOARD_TUI__ === true;
}
