import { defineConfig, type Plugin } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

const BACKEND = process.env.ANYDEALS_DASHBOARD_URL ?? "http://127.0.0.1:9119";

function anydealsDevToken(): Plugin {
  const TOKEN_RE = /window\.__ANYDEALS_SESSION_TOKEN__\s*=\s*"([^"]+)"/;
  const EMBEDDED_RE =
    /window\.__ANYDEALS_DASHBOARD_EMBEDDED_CHAT__\s*=\s*(true|false)/;
  const LEGACY_TUI_RE =
    /window\.__ANYDEALS_DASHBOARD_TUI__\s*=\s*(true|false)/;

  return {
    name: "anydeals.dev-session-token",
    apply: "serve",
    async transformIndexHtml() {
      try {
        const res = await fetch(BACKEND, { headers: { accept: "text/html" } });
        const html = await res.text();
        const match = html.match(TOKEN_RE);
        if (!match) {
          console.warn(
            `[anydeals] Could not find session token in ${BACKEND} — ` +
              `is \`anydeals-agent dashboard\` running? /api calls will 401.`,
          );
          return;
        }
        const embeddedMatch = html.match(EMBEDDED_RE);
        const legacyMatch = html.match(LEGACY_TUI_RE);
        const embeddedJs = embeddedMatch
          ? embeddedMatch[1]
          : legacyMatch
            ? legacyMatch[1]
            : "false";
        return [
          {
            tag: "script",
            injectTo: "head",
            children:
              `window.__ANYDEALS_SESSION_TOKEN__="${match[1]}";` +
              `window.__ANYDEALS_DASHBOARD_EMBEDDED_CHAT__=${embeddedJs};`,
          },
        ];
      } catch (err) {
        console.warn(
          `[anydeals] Dashboard at ${BACKEND} unreachable — ` +
            `start it with \`anydeals-agent dashboard\` or set ANYDEALS_DASHBOARD_URL. ` +
            `(${(err as Error).message})`,
        );
      }
    },
  };
}

export default defineConfig({
  plugins: [vue(), tailwindcss(), anydealsDevToken()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "../anydeals_cli/web_dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": {
        target: BACKEND,
        ws: true,
      },
      "/dashboard-plugins": BACKEND,
    },
  },
});
