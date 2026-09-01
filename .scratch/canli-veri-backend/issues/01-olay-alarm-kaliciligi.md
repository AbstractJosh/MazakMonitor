# Olay/alarm kaliciligi (DB fazi)

Status: open
Role: backend

Olay gecmisi ve durum bugun yalniz bellekte (`LiveHub`). Sonuclari:

- Backend yeniden baslarsa `/api/stream`'e bagli TUM izleyicilerin gorunumu
  bos anlik goruntuyle sifirlanir (folly modunda istemci kendi gecmisini
  koruyordu — bilinen parite farki, inceleme bulgusu).
- `/api/events` en fazla son 500 kaydi doner; rapor/gecmis ekranlari icin
  yetersiz.
- Alarm "onay" damgasi (ADR-0004: kendi DB'mizde goruldu isareti) icin de
  tablo gerekiyor.

Yapilacak: alembic migration (events, alarms tablolari), hub'dan DB'ye yazan
kuyruk, `/api/events`in DB'den sayfalanmasi.
