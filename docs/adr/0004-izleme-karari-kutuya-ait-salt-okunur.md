# İzleme kararı kutuya ait; uygulama (MVP) salt-okunur gözlemci

Sinyal işleme, limit kontrolü ve alarm üretme kararını **Prometec izleme
üniteleri** verir; uygulama bu mantığı **yeniden yazmaz**. MVP'de uygulama
donanıma **hiç yazmaz** (ne yapılandırma ne alarm onayı) — yalnız okur, gösterir,
kaydeder. "Onayla" MVP'de yalnız **kendi DB'mizde "görüldü" damgasıdır.**

Bu, eski Provis3 ile **paralel/gölge** çalışmayı güvenli kılar (iki master
çakışması olmaz) ve tüm donanım-yazma yollarını (yapılandırma düzenleme, alarma
kutuya-onay) sonraki faza erteler.

## Consequences

- Alarm bilgi amaçlıdır; tezgah alarmda durmaz (operatör onayı tezgahın devamı
  için şart değildir) — bu yüzden salt-okunur MVP operasyonel olarak yeterlidir.
- Açık risk: kutunun, onaylanmamış alarmı kendi içinde "aktif" tutup bir sonraki
  alarm için onay bekleyip beklemediği donanımda doğrulanacak; gerekirse
  kutuya-onay ayrı bir kararla (faz B) eklenir.
