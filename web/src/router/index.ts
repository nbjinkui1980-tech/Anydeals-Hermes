import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/sessions",
    },
    {
      path: "/sessions",
      name: "sessions",
      component: () => import("@/views/SessionsView.vue"),
    },
    {
      path: "/analytics",
      name: "analytics",
      component: () => import("@/views/AnalyticsView.vue"),
    },
    {
      path: "/logs",
      name: "logs",
      component: () => import("@/views/LogsView.vue"),
    },
    {
      path: "/cron",
      name: "cron",
      component: () => import("@/views/CronView.vue"),
    },
    {
      path: "/models",
      name: "models",
      component: () => import("@/views/ModelsView.vue"),
    },
    {
      path: "/plugins",
      name: "plugins",
      component: () => import("@/views/PluginsView.vue"),
    },
    {
      path: "/profiles",
      name: "profiles",
      component: () => import("@/views/ProfilesView.vue"),
    },
    {
      path: "/skills",
      name: "skills",
      component: () => import("@/views/SkillsView.vue"),
    },
    {
      path: "/config",
      name: "config",
      component: () => import("@/views/ConfigView.vue"),
    },
    {
      path: "/env",
      name: "env",
      component: () => import("@/views/EnvView.vue"),
    },
    {
      path: "/docs",
      name: "docs",
      component: () => import("@/views/DocsView.vue"),
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("@/views/ChatView.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/sessions",
    },
  ],
});

export { router };
