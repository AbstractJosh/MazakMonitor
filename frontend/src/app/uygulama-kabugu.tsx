// Uygulama kabuğu — Mazak İzleme. Offline LAN web uygulaması (ADR-0001).
//
// Akış BURADA yaşar, ekranlarda değil: Canlı ↔ Alarmlar ↔ Olaylar geçişi
// bağlantıyı düşürmemeli ve Olaylar geçmişi hangi ekrandayken gelirse gelsin
// birikmeye devam etmelidir.

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Navigate,
  Outlet,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import {
  AppShell,
  Badge,
  Button,
  IconButton,
  Switch,
  Toggle,
  IKON,
  type ShellNavItem,
} from "@alp/design-system";
import { Activity, Bell, FileText, History } from "lucide-react";
import { useLive, type LiveConnection, type LiveLink } from "@/domain/useLive";
import { initialLiveState } from "@/domain/live";
import { findFacility, findMachine, machineTitle, useKatalog } from "@/domain/katalog";
import { baglantiBoslugu } from "@/domain/baglanti-bosluk";
import { ALT_SAPMA_VARSAYILAN, sapmaOku } from "@/domain/esik";
import AlarmPenceresi, { PENCERE_ID } from "@/features/alarmlar/alarm-penceresi";
import type { IzlemeBaglami } from "./izleme-baglami";
import { URUN_ADI } from "./urun";

// ALARMLAR BURADA YOK ve bu bir eksiklik değil: alarm bir EKRANIN değil
// TEZGAHIN durumudur, sekme olduğunda ancak oraya GİDİLDİĞİNDE görünüyordu.
// Yerini sağ altta sürekli duran `AlarmPenceresi` aldı. `/alarmlar` rotası
// DURUYOR — bir detay sayfasına dönüştü ve üç yerden varılır: pencerenin
// altındaki bağlantı, Canlı'daki KPI kutucuğu, kırmızı bant.
const MENU_TABAN: ShellNavItem[] = [
  { id: "canli", label: "Canlı İzleme", icon: <Activity size={IKON.md} /> },
  { id: "olaylar", label: "Olaylar", icon: <FileText size={IKON.md} /> },
];

// TAM KOŞUM YALNIZ CSV KAYNAKLI TEZGAHTA BASILIR. Koşum kaydı `veri/`
// altındaki CSV korpusudur ve o korpus TEK BİR tezgaha bağlıdır
// (backend/app/machines.py). Madde her tezgahta dursaydı, gerçek PROVIS
// tezgahının navigasyonu BAŞKA bir tezgahın ölçümlerini vaat ederdi — bu
// projenin baştan beri kaçındığı hata. Backend de aynı kuralı uygular
// (/api/kosum, kaynağı CSV olmayan tezgahta 404).
const KOSUM_MADDESI: ShellNavItem = {
  id: "kosum",
  label: "Tam Koşum",
  icon: <History size={IKON.md} />,
};

// Akış HİÇ kurulmadığında ekranlara verilen boş durum (kaynaksız tezgah ve
// katalog bilinmezken). Modül düzeyinde SABİT: her çizimde yeni nesne üretmek,
// alt ekranların memo'larını boşuna bozardı.
const BOS_DURUM = initialLiveState();

/** Üst bardaki akış özeti — yalnız SÖYLENECEK bir şey varsa. */
export function streamLabel(paused: boolean, link: LiveLink): string | null {
  // Katalog bilinmeden kaynak hakkında hiçbir iddia edilmez; bu ikisi
  // duraklatmadan da ÖNCE söylenir. Henüz kurulmamış bir akış için
  // "duraklatıldı" demek, olmayan bir şeyin durdurulduğunu iddia ederdi.
  if (link === "catalog-loading") return "tezgah bilgisi yükleniyor";
  if (link === "catalog-down") return "tezgah listesi alınamadı";
  // "no-source" arıza DEĞİLDİR (bu tezgaha kaynak tanımlanmamıştır), bu yüzden
  // duraklatmadan bile önce söylenir: aksi halde duraklatılmış gibi görünürdü.
  if (link === "no-source") return "bu tezgah için canlı kaynak tanımlı değil";
  if (paused) return "duraklatıldı";
  if (link === "stream-down") return "backend akışına bağlanılamıyor";
  if (link === "source-down") return "backend kaynağa ulaşamıyor";
  return null;
}

export default function UygulamaKabugu() {
  const [params] = useSearchParams();
  const machineId = params.get("tezgah");
  // Sapmalar tezgaha ÖZEL DEĞİLDİR (gösterim tercihidir), o yüzden `key`e
  // girmezler: değişmeleri kabuğu baştan kurup onay damgalarını silmemeli.
  //
  // Adres anahtarı `sapma` ÜST sınırındır ve öyle KALIR: alt sınır eklenince
  // `ustSapma`/`altSapma` diye simetrikleştirmek daha okunur olurdu ama bu
  // sabah yayınlanmış adresleri kozmetik bir sebeple kırardı.
  const sapma = sapmaOku(params.get("sapma"));
  const altSapma = sapmaOku(params.get("altSapma"), ALT_SAPMA_VARSAYILAN);

  // Tezgah SEÇİLMEDİYSE varsayılana düşülmez — kullanıcı seçsin diye
  // karşılama ekranı var. Sessiz varsayılan, bu işin tam tersiydi.
  if (!machineId) return <Navigate to="/" replace />;

  // key={machineId}: tezgah değişince kabuk BAŞTAN kurulur. Onay damgaları,
  // grafik adları ve duraklatma tezgaha özeldir; taşınsalardı bir tezgahın
  // onayı başka tezgahın alarmına düşerdi.
  return (
    <KabukIc key={machineId} machineId={machineId} sapma={sapma} altSapma={altSapma} />
  );
}

function KabukIc({
  machineId,
  sapma,
  altSapma,
}: {
  machineId: string;
  sapma: number;
  altSapma: number;
}) {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // Kabukta yoklama YOK: buradaki bağlantı durumunu SSE `status` olayı zaten
  // taşır, katalog yalnız ad ve kaynak bağlaması için okunur.
  const { katalog, durum: katalogDurum, yenile: katalogYenile } = useKatalog();
  const machine = findMachine(katalog, machineId);
  const facility = findFacility(katalog, machineId.split("/")[0] ?? "");
  // Katalog gelene dek ham kimlik gösterilir: ad uydurmaktansa dürüst.
  const baslik = facility && machine ? machineTitle(facility, machine) : machineId;

  // Kaynak kararı KATALOG GELMEDEN verilmez.
  //
  // Eskiden doğrudan `machine?.source != null` okunuyordu: katalog yoldayken
  // `machine` undefined olduğu için hasSource false çıkıyor, akış kurulmuyor ve
  // ekran "bu tezgaha kaynak tanımlanmamış, bu bir arıza değil yapılandırmadır"
  // diye YAPILANDIRMA İDDİASINDA bulunuyordu — bilmediği bir şeyi biliyormuş
  // gibi. Katalog isteği düşerse iddia KALICI da oluyordu (kabuk yoklamaz).
  // Bilgisizlik ile yapılandırma ayrı raporlanır; LiveLink zaten bunun içindir.
  const hasSource = katalogDurum === "ready" && machine?.source != null;

  const [paused, setPaused] = useState(false);
  const streamed = useLive(hasSource && !paused ? machineId : null);

  // Alarm penceresi KAPALI açılır: açık başlasaydı her ekran girişinde
  // içeriğin bir köşesini kaplardı. Kapalı şerit sayıyı zaten gösteriyor.
  const [alarmAcik, setAlarmAcik] = useState(false);
  // Tam ekran alarm ızgarasındayız: pencere de zili de basılmaz (aşağıya bak).
  const alarmEkrani = pathname.startsWith("/alarmlar");

  // KOYU TEMA ELDE TUTULUR, KOMPAKT ATILIR. Paketin `themeControls` bayrağı
  // ikisini TEK anahtarla basar (AppShell içinde yan yana iki Switch), yani
  // "Kompakt"ı kaldırmanın tek yolu bayrağı kapatıp Koyu'yu buraya taşımaktır.
  //
  // Kompakt bu uygulamada pratikte ölüydü: çevirdiği belirteçler (--row-h,
  // --cell-pad-x, --control-h) yalnız tablo/denetim bileşenlerinde okunur ve
  // ekranlarımız Card/KPICard/Badge/Accordion kullanır. Ölçüldü: /alarmlar'da
  // HİÇBİR kutu değişmiyordu; tek etkisi Canlı İzleme'nin en altındaki
  // "İzleme üniteleri" tablosunun 92 px'ten 80 px'e inmesiydi — ekranın
  // görünen hiçbir yerinde karşılığı olmayan bir anahtar.
  //
  // Başlangıç değeri DOM'dan okunur, state'ten değil: kabuk tezgah değişiminde
  // `key` ile YENİDEN KURULUR (bkz. UygulamaKabugu) ve state'e güvenseydik tema
  // her tezgah değişiminde açığa dönerdi. Paket de tam olarak bunu yapıyordu.
  const [dark, setDark] = useState(
    () => document.documentElement.getAttribute("data-theme") === "dark",
  );
  useEffect(() => {
    if (dark) document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
  }, [dark]);

  // Kancanın kendi durumunu göstermek yeterli DEĞİLDİR: useLive kapatılınca son
  // kareyi elinde tutar (duraklatmanın istenen davranışı budur), yani kaynaksız
  // tezgahta bir öncekinin verisi bu tezgahın adı altında görünürdü.
  //
  // Katalog bilinmiyorken de akış kurulmaz ve durum DÜRÜSTÇE "bilmiyorum" der;
  // o hâl "kaynak yok" DEĞİLDİR ve öyle raporlanmaz.
  //
  // Katalog düştüğünde akışı yine de denemek cazip ama yanlış: iki uç da AYNI
  // backend sürecidir, yani /api/machines'e ulaşılamıyorsa /api/stream'e de
  // ulaşılamaz. Tek kazancı, kaynaksız bir tezgahta 404'e karşı beş saniyede
  // bir sonsuz yeniden deneme olurdu — ve kopan halkayı akışa yıkardı.
  const katalogLink: LiveLink | null =
    katalogDurum === "loading"
      ? "catalog-loading"
      : katalogDurum === "error"
        ? "catalog-down"
        : null;

  // Boş bağlantının ortak gövdesi: veri YOK ve öyle olduğu söylenir.
  const bosBaglanti = {
    connected: false,
    source: null,
    frames: 0,
    dataAgeS: null,
    dataFresh: false,
    state: BOS_DURUM,
  } as const;

  const live: LiveConnection = katalogLink
    ? { ...bosBaglanti, link: katalogLink }
    : hasSource
      ? {
          ...streamed,
          // Kaynak kimliği KATALOGDAN tamamlanır: `status` olayı gelene dek
          // (açılışın ilk ~1 sn'si) akış onu bilmez ve tam o aralıkta link
          // "source-down"dur — yani hata metninin kaynağı adlandırması
          // gerektiği an, akışın en az bildiği andır.
          source: streamed.source ?? machine?.source ?? null,
        }
      : { ...bosBaglanti, link: "no-source" };

  const [graphTitles, setGraphTitles] = useState<Record<string, string>>({});
  const onRenameGraph = useCallback((id: string, name: string) => {
    setGraphTitles((prev) => {
      const next = { ...prev };
      if (name) next[id] = name;
      else delete next[id]; // boş ad → varsayılan "Grafik N" adına dön
      return next;
    });
  }, []);

  // Onay damgası İSTEMCİDE tutulur: backend tam anlık görüntü yayınlar, yani
  // gelen her kare listeyi baştan yazar — onayı listenin içine yazsaydık ilk
  // güncellemede silinirdi (ADR-0004).
  const [ackIds, setAckIds] = useState<ReadonlySet<string>>(() => new Set());
  const alarms = useMemo(
    () =>
      live.state.alarms.map((a) =>
        ackIds.has(a.id) ? { ...a, state: "acknowledged" as const } : a,
      ),
    [live.state.alarms, ackIds],
  );
  const active = useMemo(() => alarms.filter((a) => a.state === "active"), [alarms]);

  const onToggleAck = useCallback((id: string) => {
    setAckIds((prev) => {
      const next = new Set(prev);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }, []);

  const onAckAll = useCallback(() => {
    setAckIds((prev) => {
      const next = new Set(prev);
      for (const a of alarms) if (a.state === "active") next.add(a.id);
      return next;
    });
  }, [alarms]);

  // Veri canlı mı: zincir sağlam VE veri ŞU AN akıyor.
  //
  // ESKİDEN `wire.parsed > 0` bakılıyordu. `wire` PROMOS3 TAŞIMA teşhisidir
  // (datagram/CAN çerçeve sayaçları); CSV tezgahının teli yoktur, yani
  // kusursuz akan bir tezgahta bu satır "Veri Yok" yazardı.
  //
  // SONRA `frames > 0` denendi ve o da yanlıştı: `frames` "HİÇ geldi mi"
  // sorusunu cevaplar, geri saymaz. Bir tek kare geldikten sonra kaynak
  // sussa bile "Veri Akışı Aktif" SONSUZA DEK yazıyordu. Doğru soru "şu an
  // geliyor mu"dur; cevabı backend'in yaş damgasıdır (`dataFresh`) ve
  // sessizlikte nabızla tazelenir.
  const dataLive = live.connected && live.dataFresh;
  const akis = streamLabel(paused, live.link);

  // Katalog GELENE DEK koşum maddesi basılmaz: kaynağı bilmeden kayıt vaat
  // etmek, `hasSource`un aynı gerekçesidir (bilinmiyor ≠ yapılandırılmış).
  const menu = useMemo(
    () => (machine?.source === "csv" ? [...MENU_TABAN, KOSUM_MADDESI] : MENU_TABAN),
    [machine?.source],
  );

  const aktifId = menu.find((m) => pathname.startsWith(`/${m.id}`))?.id ?? "";
  const git = (id: string) => navigate({ pathname: `/${id}`, search: location.search });

  const baglam: IzlemeBaglami = {
    live,
    katalogYenile,
    alarms,
    active,
    events: live.state.events,
    paused,
    onToggleAck,
    onAckAll,
    graphTitles,
    onRenameGraph,
    sapma,
    altSapma,
  };

  return (
    <AppShell
      product={URUN_ADI}
      items={menu}
      activeId={aktifId}
      onNavigate={git}
      // title VERİLMEZ: sayfa başlığı PageShell'indir, ikisi birden iki h1 eder.
      subtitle={`${baslik} · Çevrim ${live.state.cycle ?? "—"}${akis ? ` · ${akis}` : ""}`}
      // Kapalı: paketin Koyu+Kompakt ikilisi yerine yalnız Koyu basılır (yukarı bak).
      themeControls={false}
      topbarActions={
        <div className="flex items-center gap-2">
          {/* Tezgah "çalışıyor" iddiası bu akıştan türetilemez (üretim nabzı
              yok); etiket dürüstçe VERİ canlılığını söyler. */}
          <Badge tone={!paused && dataLive ? "success" : "neutral"} dot>
            {paused ? "Duraklatıldı" : dataLive ? "Veri Akışı Aktif" : "Veri Yok"}
          </Badge>
          {/* Toggle, Switch değil: duraklatma bir EYLEMİN etkin olmasıdır,
              kaydedilen bir ayar değil. */}
          <Toggle
            pressed={paused}
            onPressedChange={setPaused}
            label={paused ? "Devam et" : "Duraklat"}
            variant="outline"
            size="sm"
          >
            {paused ? "Devam" : "Duraklat"}
          </Toggle>
          {/* Sorgu OLDUĞU GİBİ taşınır (`git` ile aynı idiom): `tezgah` zaten
              geri dönüş için gerekiyordu, `sapma` da onunla gider. Adresi elle
              kurmak sapmayı düşürürdü ve karşılama ekranı kullanıcının az önce
              seçtiği yüzde yerine varsayılanı gösterirdi. */}
          <Button
            size="sm"
            variant="secondary"
            onClick={() => navigate({ pathname: "/", search: location.search })}
          >
            Değiştir
          </Button>
          {/* Zil artık KENDİ listesini açmıyor, sağ alttaki pencereyi açıp
              kapatıyor. Popover'ı bırakması bir sadeleştirme değil TEKRARIN
              kaldırılmasıdır: ikisi de aynı aktif alarmları, aynı tek dokunuş
              onayla, iki ayrı yüzen kutuda gösteriyordu.
              Alarm ekranında basılmaz: `aria-controls` DOM'da olmayan bir
              öğeyi işaret ederdi ve düğme hiçbir şey açmazdı. */}
          {!alarmEkrani && (
            <IconButton
              label={`Alarm penceresi${active.length ? ` (${active.length} aktif)` : ""}`}
              variant="ghost"
              size="sm"
              aria-expanded={alarmAcik}
              aria-controls={PENCERE_ID}
              onClick={() => setAlarmAcik((v) => !v)}
            >
              <Bell size={IKON.md} />
            </IconButton>
          )}
          <Switch checked={dark} onChange={setDark} label="Koyu" />
        </div>
      }
    >
      {/* Alt dolgu YALNIZ pencere varken: kapalı şerit sayfanın son kartının
          üstüne oturmasın. Yerleşik pencere `fixed`tir, yani akıştan çıkar ve
          altındaki içeriği kendiliğinden itmez.

          `flex min-h-0 flex-1 flex-col` SÜS DEĞİL, KAYDIRMANIN ŞARTI. AppShell'in
          `main`i `has-[[data-slot=page-shell]]` ile kip değiştirir ve bu bir
          TORUN seçicisidir (`:has([data-slot=page-shell])`) — araya div koymak
          onu kapatmaz: `main` `display:flex` + `overflow:hidden` olarak KALIR.
          O kipte kaydıran şey `page-shell-content`tir ve yüksekliğini
          PageShell'in `flex-1`inden alır; yani PageShell'in `main`in flex
          ÇOCUĞU olması gerekir. Sade bir `<div>` araya girince flex öğesi O
          olur (`flex:0 1 auto`, `min-height:auto` = içerik boyu), PageShell'in
          `flex-1`i etkisiz kalır, scroller hiç taşmaz ve `main` gerisini keser.
          Ölçüldü (1fe8461 ile gelen regresyon): main 659/1076, sayfada
          kaydırılabilir TEK bir öğe bile yoktu, son kart 313 px altta kalıyordu.

          DOLGU SCROLLER'IN İÇİNDE, DIŞINDA DEĞİL. Eskiden burada `pb-20` vardı
          (paketin alt tab bar için `main`de yaptığının aynısı) ve pencereye yeri
          SCROLLER'I KISALTARAK açıyordu. Bedeli görünür bir arızaydı: ölçüldü —
          1600×1000 pencerede `main` 65–904'e kadar inerken `page-shell-content`
          824'te bitiyor, altında 80 px'lik ÖLÜ BİR ŞERİT kalıyordu. Grafik
          kartları o kenarda cümle ortasından kesiliyor, sayfa pencerenin sonuna
          kadar hiç ulaşmıyordu. Üstelik şerit TÜM GENİŞLİKTİ, oysa pencere yalnız
          sağ alttaki 384 px'i kaplar (ölçüldü: sol kenarı 1182).

          Artık boşluğu `mzi-pencere-payi` veriyor (app.css, YERLEŞİM bloğu):
          scroller pencerenin sonuna kadar iner ve payı KENDİ alt dolgusundan
          verir. Yani pay kaydırma payıdır — son kart pencerenin üstüne
          kaydırılabilir — ama boş bir bant olarak durmaz. Alarm ekranında sınıf
          basılmaz: orada pencere zaten yok, ayıracak yer de yok. */}
      <div
        className={`flex min-h-0 flex-1 flex-col${alarmEkrani ? "" : " mzi-pencere-payi"}`}
      >
        <Outlet context={baglam} />
      </div>

      {/* PENCERE ALARM EKRANINDA BASILMAZ. Ölçüldü: `/alarmlar`da açık pencere
          ızgaranın sağ kolonlarını (Özellik, Limit, Aşım ve İŞLEM sütunu)
          örtüyordu — yani onay düğmelerinin durduğu yeri. Zaten listenin
          TAMAMINA bakılan ekranda, aynı listenin yüzen bir özetini üstüne
          koymak hem tekrar hem engel. */}
      {!alarmEkrani && (
        <AlarmPenceresi
          active={active}
          // Zincir kopuksa pencere kendi olumlu cümlesini KURMAZ: "0 aktif
          // alarm" ancak kaynak öyle diyorsa doğrudur.
          bosluk={baglantiBoslugu(live.link, live.source)}
          acik={alarmAcik}
          onToggle={() => setAlarmAcik((v) => !v)}
          onToggleAck={onToggleAck}
          onTumunuGor={() => navigate({ pathname: "/alarmlar", search: location.search })}
        />
      )}
    </AppShell>
  );
}
