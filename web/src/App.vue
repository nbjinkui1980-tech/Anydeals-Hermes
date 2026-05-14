<script setup lang="ts">
import { computed, type FunctionalComponent } from "vue";
import { MessageSquare, BarChart3, FileText, Clock, Package, Settings, KeyRound, BookOpen, Brain, Puzzle, Users } from "lucide-vue-next";
import { useThemeStore } from "@/stores/themeStore";
import Backdrop from "@/components/Backdrop.vue";

// Initialize theme system — applyTheme() fires via watch(immediate:true)
useThemeStore();

interface NavItem {
  path: string;
  label: string;
  icon: FunctionalComponent;
}

const navItems: NavItem[] = [
  { path: "/sessions", label: "Sessions", icon: MessageSquare },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
  { path: "/logs", label: "Logs", icon: FileText },
  { path: "/cron", label: "Cron", icon: Clock },
  { path: "/models", label: "Models", icon: Brain },
  { path: "/plugins", label: "Plugins", icon: Puzzle },
  { path: "/profiles", label: "Profiles", icon: Users },
  { path: "/skills", label: "Skills", icon: Package },
  { path: "/config", label: "Config", icon: Settings },
  { path: "/env", label: "Keys", icon: KeyRound },
  { path: "/docs", label: "Docs", icon: BookOpen },
];

const sidebarStyle = computed(() => ({
  background: "var(--component-sidebar-background, var(--color-card))",
  borderColor: "var(--component-sidebar-border-color, var(--color-border))",
  backdropFilter: "var(--component-sidebar-backdrop-filter, none)",
  WebkitBackdropFilter: "var(--component-sidebar-backdrop-filter, none)",
}) as Record<string, string>);

const brandStyle = {
  mixBlendMode: "plus-lighter",
} as Record<string, string>;
</script>

<template>
  <div class="font-mondwest flex h-dvh max-h-dvh min-h-0 flex-col overflow-hidden bg-black text-midground antialiased">
    <Backdrop />
    <div class="flex min-h-0 min-w-0 flex-1 flex-col">
      <div class="flex min-h-0 min-w-0 flex-1">
        <!-- Sidebar -->
        <aside
          class="w-64 shrink-0 border-r hidden lg:flex flex-col"
          :style="sidebarStyle"
        >
          <div class="flex h-14 shrink-0 items-center px-5 border-b border-current/10">
            <span
              class="font-bold text-[1.125rem] leading-[0.95] tracking-[0.0525rem]"
              :style="brandStyle"
            >
              AnyDeals<br />Agent
            </span>
          </div>
          <nav class="min-h-0 flex-1 overflow-y-auto py-2">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="flex items-center gap-3 px-5 py-2.5 font-mondwest text-[0.8rem] tracking-[0.12em] whitespace-nowrap transition-all duration-200 rounded-lg mx-2 opacity-60 hover:opacity-100"
              active-class="!opacity-100 !bg-white/5"
              :class="{ '!opacity-100': $route.path === item.path }"
            >
              <component :is="item.icon" class="h-3.5 w-3.5 shrink-0" />
              <span class="truncate">{{ item.label }}</span>
            </router-link>
          </nav>
        </aside>

        <!-- Main content -->
        <main class="relative z-2 flex min-w-0 min-h-0 flex-1 flex-col px-3 sm:px-6 pt-2 sm:pt-4 lg:pt-6 pb-4 sm:pb-8 overflow-y-auto">
          <div class="w-full min-w-0 max-w-[1800px] mx-auto">
            <router-view />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>
