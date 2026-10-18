import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
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
});
