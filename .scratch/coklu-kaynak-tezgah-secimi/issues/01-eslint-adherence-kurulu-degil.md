# Tasarim dili bekcisi kurulu DEGIL (eslint adherence)

Status: open
Role: frontend

`frontend/eslint.config.js` paketin `adherence` kural setini KURMUYOR
(`@alp/design-system/adherence`). Icinde hala olu `@alp/ui` / `antd` yasagi
duruyor - CLAUDE.md'nin kendisi bunu "olu kural" diye anlatiyor.

Sonuc: ham hex/px ve arbitrary Tailwind degerleri BEKCISIZ. `bun run lint`
gectiginde tasarim diline uyulmus gibi gorunuyor ama o kontrol hic kosmuyor;
lint yalnizca eslint + `tsc --noEmit`.

Bu dalda (coklu kaynak + karsilama ekrani) uyum ELLE dogrulandi: hem yazan
hem inceleyen ajan `COMPONENTS.md` ve `docs/design-language.md` karsisinda
tek tek kontrol etti ve ihlal bulunmadi. Ama elle dogrulama bir sonraki
ekranda hayatta kalmaz.

Yapilacak: `@alp/design-system/adherence` kural setini `eslint.config.js`'e
ekle, olu antd yasagini kaldir, cikan ihlalleri temizle. Kurulum ve gerekce:
paket icinde `docs/adherence/README.md`.

Kaynak: 2026-08-11 coklu-kaynak dali, Task 5 uygulama raporu + nihai inceleme
(nihai inceleme bu dalda ihlal bulamadi, ama "schedule it" dedi).
