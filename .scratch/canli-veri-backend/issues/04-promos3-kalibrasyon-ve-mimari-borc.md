# Promos3: kalibrasyon ve bilincli mimari borc

Status: open
Role: backend + frontend

Promos3 okuma yolu (app/promos3/*, adapters/promos3_udp.py) eklendi. Asagidakiler
BILINEREK yapilmadi; her biri ya bir yakalama bekliyor ya da kapsam disi kaldi.

## 1. FAZ 0 — kalibrasyon (her seyi kilitleyen tek is)

Mesaj basliginin TEL uzerindeki bayt yerlesimi dogrulanmadi (rapor §0.5/1).
Iki nokta isaretli:

- `promos3/messages.py: parse_header` — [group][command][len] on eki TAHMIN.
- `promos3/transport.py: Reassembler.expected_len` — 0 doner; tamamlanma
  kararini "kisa cerceve mesaji bitirir" yedek kurali veriyor.

Nasil yapilir (Wireshark GEREKMEZ): `PROVISsettings.ini [ErrorManager]
LogCANMessage=1` yapip cihaza karsi bir dakika kosun; ham CAN cerceveleri loga
yazilir. Capa: cmd 0x06 (MC_GIVEKONFIG) govdesi "Version 229 Channels 1
Sensors 4" vermeli.

Bitince: iki islevi duzelt + `HEADER_CALIBRATED = True`. Baska hicbir yer
degismez; guven merdiveni tum degerleri kendiliginden "confirmed" yapar.

**Kalibrasyon oncesi beklenen hal:** cerceveler akar, mesajlar "cozulemedi"
gorunur. Bu ARIZA DEGIL. Ekranda Telgraf seridi bunu soyler ve cozulemeyen
mesajin bas kismini hex olarak gosterir (kalibrasyonun tek ipucu).

## 2. Uretici bekleyen sozlesme alanlari

Sozlesme (domain.py / types.ts) rapordaki GERCEK veri modeline gore
sekillendirildi; bazi alanlarin henuz yazani yok. Ekran bunlari dururken "—"
gosterir, uydurma deger URETMEZ. Yazan gelene dek asagidaki arayuz dallari
CALISMAZ (okuyarak dogrulanmis, ekranda gorulmemis):

- `Feature.limitLevel / limits / pct` → limit cizgisi ve yuzde. SGrenzRec'in
  alan OFSETLERI raporda yok (bkz. records.py'deki uzun not); esik uydurmak
  sessizce yanlis yuzde uretirdi. Kaynak: yapilandirma SQLite'i ya da
  kalibrasyondan sonra LIMIT_INFO.
- `Feature.statusCode / statusLabel` → grafik kartinin kirmizi alarm hali ve
  durum etiketi. Alarm yolu baglanmadan tetiklenmez.
- `Feature.featureNr / mask` → ozellik kimliginin tam hali (asagidaki 3'e bagli).
- `UnitInfo.gType / gSubType / model / generation / miSensTypes / sampleDiv /
  reduzLim / firmware` → `records.parse_device_record` bunlari DOGRULANMIS
  bicimde okuyor ama tel uzerinde SGeraetRec tasiyan bir yol henuz cozulmedi;
  KONFIG ozeti yalniz surum/kanal/sensor sayisini veriyor.
- `SensorInfo.*` → MC3_SENSOR_INFO grup 2 yolundan gelir; bu kutu grup 1.

## 3. Ozellik adi tanesi (channelKey ↔ SKanalRec maskesi)

`_feature_label` adlari TEL uzerindeki `channelKey`e gore arar. Gercek adlar
SKanalRec'in +0x4D'deki 4 yuvasinda (maske 0x01/0x02/0x04/0x08) ve
`records.parse_feature_slots` onlari dogrulanmis bicimde okuyor.

**Rapor bu ikisi arasindaki karsiligi KURMUYOR.** Bu kurulumda 1 kanal +
4 ozellik var, yani channelKey muhtemelen ozelligi seciyor — ama dogrulanmadi.
Bu yuzden:

- `PROMOS3_FEATURE_NAMES` bir GECICI ELLE GECERSIZ KILMADIR; ancak yakalamada
  hangi channelKey'in hangi ozelligi tasidigini GORDUKTEN sonra doldurulmali.
- `trace_feature_id` izleri `(unite, tool, channel)` ile kimliklendiriyor;
  ozellik boyutu YOK. Bir kanalda 4 ozellik varsa dordu ayni grafige duser.
  Kalibrasyondan sonra kimlik tanesi gozden gecirilmeli.

## 4. Kapsam disi birakilan mimari bulgular (inceleme notlari)

Dordu de gecerli ama bu isin kapsamini asiyor:

- **Hub kaynaga duyarli.** `hub.py` artik `app.promos3`'u (WireStats,
  HEADER_CALIBRATED, Promos3Message) import ediyor ve esleyiciyi hub cagiriyor.
  Daha derin bicim: `hub.apply(mapper)` + `hub.mark_nc_seen()`; her adaptor
  kendi esleyicisini ve kendi yapilandirmasini tasir, hub yalniz `app.domain`
  bilir. Ucuncu kaynak (ADR-0003 NC koprusu) eklenirken yapilmali.
- **WireStats kaynak-notr sozlesmede CAN sozcuguyle duruyor** (`datagrams`,
  `canFrames`, `headerCalibrated`). NC koprusu geldiginde ya bu alanlari
  durustce olmayan bicimde yeniden kullanir ya da ikinci bir tanesi olur.
  Daha derin bicim: `sources[].diagnostics` altinda kaynak basina teshis
  (ayni yerde kaynak basina durumla birlikte).
- **Teshis sayaclari DURUM kanalindan gidiyor**, yani her mesajda tam anlik
  goruntu (125 ornekli izler dahil) yeniden serilestiriliyor. Sayac
  guncellemeleri artik degismedikce yayin yapmiyor ama mesajlar hala her
  seferinde bump ediyor. Bkz. issue 02 (yayin olcek tavani).
- **`Feature` tek modelde iki sekil tasiyor** (`kind: trace|series`). Tek
  render edici icin dogru karar; ama `rawCounts` ile `kind` su an her ureticide
  ayni sonucu veriyor (ikisi ayri soru: "ham sayim mi" eksen tam olcegini,
  "cerceve mi" ornek sayisi satirini belirler). Olcekli iz gelirse ikisi
  ayrisir — o zaman gozden gecir.

## 5. Sim (`alp-ui-shim`) kaldirma protokolu

ChartCard'a `yDomain` prop'u eklendi (ham 0..255 izin SABIT eksene ihtiyaci
var; kendine olceklenen eksende 2 sayimlik titresim tam salinim gibi gorunur).

**Sim kaldirilirken gercek `@alp/ui` ChartCard'inin `yDomain` desteklemesi
SART.** Desteklemezse ya `tsc` aciklamasiz patlar ya da — props gevsekse —
eksen sessizce kendine olceklenmeye doner; yani prop'un engellemek icin var
oldugu hataya geri donulur. Simin bas yorumundaki kaldirma listesi bunu
soylemiyor.
