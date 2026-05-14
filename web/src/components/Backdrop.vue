<script setup lang="ts">
import { computed } from "vue";
import { useGpuTier } from "@/composables/useGpuTier";

const NOISE_SVG =
  "data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' fill='%23eaeaea' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E";

const gpuTier = useGpuTier();

const fillerStyle = computed(() => ({
  mixBlendMode: "var(--component-backdrop-filler-blend-mode, difference)",
  opacity: "var(--component-backdrop-filler-opacity, 0.033)",
  backgroundImage: "var(--theme-asset-bg)",
  backgroundSize: "var(--component-backdrop-background-size, cover)",
  backgroundPosition: "var(--component-backdrop-background-position, center)",
}) as Record<string, string>);

const glowStyle = computed(() => ({
  background: "var(--component-backdrop-glow, radial-gradient(ellipse at 0% 0%, transparent 60%, var(--warm-glow) 100%))",
  mixBlendMode: "lighten",
  opacity: 0.22,
}) as Record<string, string | number>);

const noiseStyle = computed(() => ({
  backgroundImage: `url(${NOISE_SVG})`,
  backgroundSize: "512px 512px",
  mixBlendMode: "color-dodge",
  opacity: "calc(0.55 * var(--noise-opacity-mul, 1))",
}) as Record<string, string>);

const bgStyle = {
  backgroundColor: "var(--background-base)",
  mixBlendMode: "difference",
} as Record<string, string>;
</script>

<template>
  <div
    aria-hidden
    class="pointer-events-none fixed inset-0 z-[1]"
    :style="bgStyle"
  />

  <div
    aria-hidden
    class="pointer-events-none fixed inset-0 z-[2]"
    :style="fillerStyle"
  >
    <img
      alt=""
      class="h-[150dvh] w-auto min-w-[100dvw] object-cover object-top-left invert theme-default-filler"
      fetchpriority="low"
      src="/ds-assets/filler-bg0.jpg"
    />
  </div>

  <div
    aria-hidden
    class="pointer-events-none fixed inset-0 z-[99]"
    :style="glowStyle"
  />

  <div
    v-if="gpuTier > 0"
    aria-hidden
    class="pointer-events-none fixed inset-0 z-[101]"
    :style="noiseStyle"
  />
</template>
