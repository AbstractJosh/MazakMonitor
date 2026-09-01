# Hub yayininda olcek tavani (dusuk oncelik)

Status: open
Role: backend

Inceleme bulgusu (dogrulanmadi, dusuk): `LiveHub.sse_frames` her degisimde
HER abone icin ayri `model_dump` + `json.dumps` calistirir. Kiosk + birkac
ofis PC'sinde sorun degil; cok abone + yuksek hizli tekrar oynatmada
(speed=1000) olay dongusu doygunlasabilir.

Gerekirse: ayni `_state_ver` icin cerceveyi BIR kez serilestirip paylas.

Ayrica bilinip kabul edilen sinir: tek process/tek worker varsayimi
(main.py'de yorumla belgelendi); `uvicorn --workers N` kullanilamaz.
