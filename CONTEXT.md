# Mazak İzleme

Bir Mazak CNC tezgahındaki takım/proses izlemesini operatöre ve ofise açan,
veriyi kendi elimizde tutan uygulamanın ortak dili. İzleme kararını (sinyal
işleme, limit kontrolü, alarm üretme) tezgaha bağlı Prometec izleme üniteleri
verir; bu uygulama o veriyi **görünür + sahip olunabilir** kılar.

> Bu dosya bir **sözlüktür** — mimari/uygulama kararları burada değil,
> `docs/adr/` altındadır.

## Dil

**Tesis**:
Tezgahların bulunduğu saha/fabrika. Hiyerarşinin en üstü: bir tesis altında bir
veya daha çok tezgah bulunur. Yalnızca bir **adlandırma/gruplama** birimidir —
Promos3 telgrafında karşılığı YOKTUR, yapılandırmadan gelir.
_Kod/kaynak_: `facility`
_Kaçın_: fabrika, saha, lokasyon

**Tezgah**:
İzlenen CNC makinesi (buradaki kurulumda tek bir Mazak). Modelde birinci sınıf
varlık; altında bir veya daha çok izleme ünitesi bulunur. Bir tesise aittir.
_Kod/kaynak_: `machine`
_Kaçın_: makine, cihaz

**İzleme ünitesi**:
Tezgaha bağlı, sinyalleri işleyip alarm üreten Prometec donanım kutusu (bu
kurulumda seri no 10659 ve 10663). Asıl izleme kararını bu verir; uygulama ona
bağlanıp okur.
_Kod/kaynak_: `device` (Provis: "Device")
_Kaçın_: cihaz, kutu, RTM

**Kanal**:
Bir izleme ünitesi içinde tek bir izleme hattı; sensörleri ve çevrimleri taşır.
_Kod/kaynak_: `channel`

**Çevrim**:
Adı ve süresi olan, izlenen bir operasyon segmenti; hangi özelliklerin, hangi
limitlerle, hangi sensörlerle izleneceğini bağlar.
_Kod/kaynak_: `cycle` (Provis/Almanca: "Zyklus")
_Kaçın_: döngü, Cycle

**Özellik**:
Bir çevrim boyunca sinyalden ölçülen tek bir karakteristik (örn. tepe kesme
kuvveti). Üstüne limit(ler) konur.
_Kod/kaynak_: `feature` (Provis/Almanca: "Merkmal")
_Kaçın_: ölçüt, karakteristik, Feature

**Limit**:
Bir özelliğin sinyaline konan sınır — **alt limit** ve **üst limit**. İkisi
birlikte bir **bant (zarf)** oluşturur. Sinyal bandın dışına çıkarsa (altına ya
da üstüne) izleme ünitesi alarm üretir.
_Kod/kaynak_: `limit`
_Kaçın_: eşik (tek yönlü izlenimi verir)

**İzleme durumu**:
Bir özelliğin o anki durumu: sinyal alt/üst limit bandının **içindeyken**
"izleniyor" (normal); **dışına çıkınca** alarm. Operatörün canlı grafikte
gördüğü sinyal-ve-bant görünümü bu durumu gösterir.
_Kod/kaynak_: `monitoring status`
_Kaçın_: monitoring (Türkçe metinde), takip

**Sensör**:
İzleme ünitesine sinyal besleyen fiziksel algılayıcı (kuvvet/yük vb.).
_Kod/kaynak_: `sensor`

**Alarm**:
Bir özelliğin limitini aşması sonucu izleme ünitesinin ürettiği uyarı; belirli
bir (kanal, çevrim, özellik, limit) dörtlüsüne bağlıdır. İki durumu vardır:
**aktif** ve **onaylandı**.
_Kod/kaynak_: `alarm`

**Onay** (onaylamak):
Aktif bir alarmı operatörün gördüğüne dair işaretleyip **onaylandı** durumuna
geçirmesi. Alarmın kendisini yok etmez; yalnızca görüldü olarak damgalar.
_Kod/kaynak_: `acknowledge` (Provis: "Ack")
_Kaçın_: kapatma, silme, kabul

**Olay**:
İzleme sırasında düşen tek bir kayıt satırı (hangi iş parçası, program, kanal,
takım, o anki durum). Geçmiş ve raporların ham malzemesi.
_Kod/kaynak_: `event` (Provis: "Log")
_Kaçın_: log, kayıt

**Takım**:
Tezgahta o an kesme yapan kesici (takım numarasıyla anılır).
_Kod/kaynak_: `tool`

**İş parçası**:
İşlenmekte olan parça (iş parçası numarasıyla anılır).
_Kod/kaynak_: `workpiece`
_Kaçın_: parça, WorkPiece

**NC Programı**:
Tezgahta çalışan CNC programı (program numarasıyla anılır); olayların ve
alarmların bağlamını verir.
_Kod/kaynak_: `program` (Provis: "ProgNum")
_Kaçın_: parça programı
