# Canli Veri: Backend Hatti

Frontend'in canli veriyi backend'den alabilmesi (2026-07-29'da kuruldu).

## Ne yapildi
- Alan modeli sozlesmesi: `backend/app/domain.py` = `frontend/src/domain/types.ts`
  (tel camelCase; bos opsiyoneller telde yok — exclude_none).
- Saf esleyici: `backend/app/live.py` (live.ts'in Python portu, pytest'li).
- `LiveHub` (`backend/app/hub.py`): latest-wins SSE dagitimi.
- Giris adaptoru: `backend/app/adapters/folly.py` (MazakFolly /stream tuketicisi;
  seq korumasi, startedAt ile kosu sifirlama, zehirli cerceve dayanikliligi,
  45 sn sessizlik bekcisi). Gercek kaynak (Prometec UDP / NC koprusu) ayni
  hub'a yazan ikinci adaptor olarak eklenecek.
- API: `/api/stream` (SSE: status+state+ping), `/api/live`, `/api/events`,
  `/api/alarms` (bos; kaynakta alarm verisi yok).
- Frontend kaynak secimi: `VITE_LIVE_SOURCE` (dev=folly, prod=backend);
  `useBackendLive` (CLOSED EventSource'u 5 sn'de yeniden kurar),
  `useLive` facade, `LiveLink` ile dogru halkayi soyleyen hata mesaji.

## Dogrulama
- backend: 26 pytest + ruff temiz; frontend: eslint + tsc temiz.
- Uctan uca: sentetik LogFile -> MazakFolly -> backend -> /api/stream;
  folly oldurme/yeniden baslatma/yeni kosu senaryolari dogrulandi.
- 13 ajanli cekismeli inceleme: 8 bulgu dogrulandi ve duzeltildi.
