import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { connectOrigin, injectCsp, originOf } from "./csp";
import vercel from "./vercel.json";

const DEFAULT_API_URL = "http://localhost:8000";

/** The vercel.json header must allow the same API the build talks to. */
function checkVercelHeader(apiOrigin: string): void {
  const header = vercel.headers
    .flatMap((rule) => rule.headers)
    .find((entry) => entry.key === "Content-Security-Policy");
  const allowed = header ? connectOrigin(header.value) : null;
  if (allowed !== apiOrigin) {
    throw new Error(
      `vercel.json permite ${allowed ?? "ningún origen"} en connect-src, pero VITE_API_URL apunta a ${apiOrigin}. ` +
        "Actualiza el connect-src de vercel.json (docs/despliegue.md).",
    );
  }
}

/** Inject the CSP `<meta>` in builds only: the dev server needs inline scripts for React Refresh. */
function contentSecurityPolicy(apiUrl: string, onVercel: boolean): Plugin {
  const apiOrigin = originOf(apiUrl);
  return {
    name: "predicta-csp",
    apply: "build",
    buildStart() {
      if (onVercel) checkVercelHeader(apiOrigin);
    },
    transformIndexHtml(html) {
      return injectCsp(html, apiOrigin);
    },
  };
}

export default defineConfig(({ mode }) => {
  // "" loads every variable, including VERCEL, which Vercel sets in its builds.
  const env = loadEnv(mode, ".", "");
  return {
    plugins: [
      react(),
      tailwindcss(),
      contentSecurityPolicy(env.VITE_API_URL || DEFAULT_API_URL, Boolean(env.VERCEL)),
    ],
    build: {
      rollupOptions: {
        onwarn(warning, warn) {
          const isZodAnnotationWarning =
            warning.id?.includes("node_modules/zod") &&
            warning.message.includes("contains an annotation that Rollup cannot interpret");
          if (!isZodAnnotationWarning) warn(warning);
        },
      },
    },
    server: {
      port: 5173,
    },
  };
});
