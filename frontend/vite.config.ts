import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const yerel = (dosya: string) =>
  fileURLToPath(new URL(`./src/alp-local/${dosya}`, import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // SIRA YUK TASIR: eslesme ilk kuraldan kazanir ve `@alp/design-system`
    // kendi alt yollarinin da onekidir. Genel kural once yazilsaydi
    // ".../charts" de index'e duserdi.
    //
    // NEDEN TAKMA AD: paket ic Gitea registry'sindedir ve ALP agi disinda
    // erisilemez (public npm'de 404). Takma ad sayesinde 13 ekran dosyasinin
    // TEK BIR import satiri bile degismedi; paket geri geldiginde bu bes kural
    // ve src/alp-local/ silinir, uygulama oldugu gibi pakete doner.
    alias: [
      { find: "@alp/design-system/charts", replacement: yerel("charts.tsx") },
      { find: "@alp/design-system/screens", replacement: yerel("screens.tsx") },
      { find: "@alp/design-system/styles.css", replacement: yerel("styles.css") },
      { find: "@alp/design-system/theme.css", replacement: yerel("theme.css") },
      { find: "@alp/design-system", replacement: yerel("index.tsx") },
      { find: "@", replacement: fileURLToPath(new URL("./src", import.meta.url)) },
    ],
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
