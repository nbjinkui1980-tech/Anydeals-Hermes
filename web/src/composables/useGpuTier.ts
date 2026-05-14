import { ref, onMounted } from "vue";

/**
 * Returns 0 when WebGL is unavailable, the renderer is a software
 * rasterizer (SwiftShader/llvmpipe), or the user has
 * prefers-reduced-motion set. Otherwise returns 1.
 */
export function useGpuTier() {
  const gpuTier = ref(0);

  onMounted(() => {
    try {
      const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
      if (mq.matches) return;

      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl") ?? canvas.getContext("experimental-webgl");
      if (!gl) return;
      const wgl = gl as WebGLRenderingContext;

      const debugInfo = wgl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        const renderer = wgl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) as string;
        if (/swiftshader|llvmpipe/i.test(renderer)) return;
      }

      gpuTier.value = 1;
    } catch {
      // leave at 0
    }
  });

  return gpuTier;
}
