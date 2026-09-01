# Kucuk borclar (coklu kaynak dalindan kalanlar)

Status: open
Role: fullstack

Hepsi bilerek ertelendi; hicbiri birlestirmeyi engellemiyor. Her biri
inceleme tarafindan "defer" diye siniflandirildi.

## Backend

- `LiveHub.__init__` hala `source_name="promos3"` varsayilani tasiyor
  (`hub.py:58`). Bu artik gecerli bir `SourceKind` DEGIL (`provis` /
  `promos3-sim` / `csv`), ve `backend.ts` `status.source`'u siki tipliyor.
  `main.py` her zaman gercek kimligi geciyor, yani yanlis bir sey YAYINLANMIYOR
  - ama varsayilan gizli bir sozlesme uyusmazligi.
- `adapters/promos3_udp.py` `set_source_status("promos3", ...)` cagiriyor,
  hub'in kimligi `provis` ya da `promos3-sim` olsa bile. `upstream_connected`
  anahtardan bagimsiz oldugu icin zararsiz; yalniz `status_wire()["sources"]`
  sozlugu `source_name` ile celisiyor.
- `sim/replay.py::_with_lock_retry` imzasi `Callable[[], int] -> int`, ama
  `csv_replay` ona liste donduren bir cagrilabilir veriyor; kilit tukendiginde
  `0` (int) donuyor ve yalnizca `records or []` deyimi `TypeError`i onluyor.
  Kazayla dogru; bir dahaki dokunusta imzayi genislet.
- `csv_replay.py` iptal yolunda ic gorevin istisnasini hic almiyor ("Task
  exception was never retrieved" log gurultusu olabilir); `-> _T` ek aciklamasi
  `func` tipsiz oldugu icin anlamsiz.
- `machines.find_machine` ve `MachineOut.source_port` yalniz testlerde
  kullaniliyor; `hub.reset_run()` hic kullanilmiyor.
- `/api/machines` govdesinin GERCEKTEN camelCase oldugunu hicbir test HTTP
  seviyesinde dogrulamiyor (yalniz `model_dump(by_alias=True)` test ediliyor).
  Bugun zararsiz: tek cok-kelimeli alan `sourcePort` ve onu kimse okumuyor.

## Frontend

- `katalog.ts` `yenile` iptal edilemez bir fetch kosuyor ve `durum`u
  `"loading"`a geri almiyor - hata durumundaki "Tekrar dene" dugmesi olu
  hissettiriyor.
- Bos katalog (`facilities: []`) karsilama ekraninda sessiz bos sayfa
  cizer. Bugun ulasilamaz (katalog sabitlerden uretilir).
- Karsilama sekme paneli `aria-labelledby` yerine `aria-label` kullaniyor;
  Radix tetikleyici id'sini disari vermedigi icin mecburi, ad yine de
  okunuyor.
- Hata metnindeki "BILINMIYOR" buyuk harf vurgusu - yorum uslubunun arayuz
  metnine sizmasi.
- Katalogda OLMAYAN bir tezgah kimligi (elle yazilmis `?tezgah=tesis-z/...`)
  "kaynak tanimlanmamis" diyor. Bilinmeyen bir sey hakkinda kesin bir
  yapilandirma iddiasi; `catalog-loading` icin zaten duzeltilen hatanin ayni
  sekli. `KabukIc` icinde ~3 satir.

## Betik

- `basla.bat` `[3/3]` banner'i yalniz A/2'nin sentetik oldugunu soyluyor;
  A/3 (CSV) de ayni kosumda sessizce yazmaya basliyor ve penceresi olmadigi
  icin hic gorunmuyor.

Kaynak: 2026-08-11 coklu-kaynak dali, gorev incelemeleri + nihai inceleme.
