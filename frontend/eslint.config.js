// ESLint düz (flat) config — ALP frontend kuralları.
// Asıl kural: UI yalnızca "@alp/ui"den gelir; "antd"den doğrudan import YASAK.
// Bu, yapay zekânın ham antd ile arayüz üretmesini hata seviyesinde engeller.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import globals from "globals";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "antd",
              message:
                "Ham antd import YASAK. Bileşenleri @alp/ui'den al (antd'yi re-export eder). Karşılığı yoksa kullanıcıya sor.",
            },
          ],
          patterns: [
            {
              group: ["antd/*", "@ant-design/*"],
              message: "Ham antd / @ant-design import YASAK. @alp/ui kullan.",
            },
          ],
        },
      ],
      // Statik Modal.confirm/info/... tema + tr locale tüketmez (antd uyarısı).
      // message/notification zaten @alp/ui'den export edilmez; Modal component
      // kalır ama statik metotları yasak. Doğrusu: App.useApp().modal.
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "MemberExpression[object.name='Modal'][property.name=/^(confirm|info|success|error|warning|warn)$/]",
          message:
            "Statik Modal.confirm/info/... tema/locale tüketmez. Bileşende const { modal } = App.useApp() kullan.",
        },
      ],
    },
  },
);
