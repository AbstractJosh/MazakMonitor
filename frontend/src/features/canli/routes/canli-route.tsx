// Canlı İzleme — operatörün ana ekranı (kiosk).
//
// Sıra pano yasasıdır: bağlam (KPI) → durum/müdahale (Alert) → ölçüm (grafik
// kutucukları) → kimlik (ünite şeridi).
//
// Grafik kutucuğu kapalıyken grafik ÇİZMEZ: yalnız anlık değer + durum gösterir.
// Açma/kapama Accordion'a bırakıldı — eskiden kartın kendisi tıklanabilir bir
// div'di ve klavye/olay yutma koruması elle yazılıyordu (ad kutusundaki boşluk
// tuşu kutucuğu kapatıyordu). Radix bunu bedava ve doğru yapar.
//
// Başarım: iz dönüşümü YALNIZ açık kutucuklarda koşar. Kapalı kutucuk örnek
// dizisine hiç dokunmaz; maliyet operatörün açtığı kadarına çıkar. Bunu RADIX
// sağlar — `AccordionContent` kapalıyken çocuklarını hiç basmaz (`isOpen &&
// children`) — elle yazılmış bir `expanded &&` koşulu DEĞİL. O koşul bir süre
// buradaydı ve kaldırıldı; gerekçesi aşağıdaki AÇILIŞ NOTU'nda.
//
// EKSEN NOTU (bilinen boşluk): ham sayım izleri bugün SABİT 0..255 ekseninde
// çiziliyordu. Paketin LineChart'ında eksen alanı (yDomain) prop'u YOK ve
// `referenceLine` tekil, dolayısıyla 0/255 çapası limit çizgisiyle aynı yuvayı
// paylaşamıyor. Sessizce kendine ölçeklenen bir eksen, 2 sayımlık titreşimi tam
// salınım gibi gösterir ve operatör sakin sinyali alarm sanar. Karar: eksen
// otomatik kalır ama AÇIKÇA öyle olduğu yazılır ve o anki aralık basılır;
// tasarım sistemine `yDomain` + `referenceLine[]` isteği açıldı.

import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  IconButton,
  Input,
  KPICard,
  KPIStrip,
  KeyValue,
  PageShell,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Section,
  CompactList,
  formatNumber,
  IKON,
  type CompactListColumn,
} from "@alp/design-system";
import { LineChart } from "@alp/design-system/charts";
import { Check, LineChart as LineChartIcon, Pencil, RotateCcw } from "lucide-react";
import { useIzleme } from "@/app/izleme-baglami";
import type { Feature, UnitInfo } from "@/domain/types";
import { baglantiBoslugu } from "@/domain/baglanti-bosluk";
import ConfidenceTag from "@/domain/ConfidenceTag";
import {
  deviceTitle,
  featureRouting,
  featureTitle,
  hex,
  pctText,
  RAW_MAX,
  sayi,
  statusTone,
  unitTitle,
} from "@/domain/format";
import { BAND_ETIKETI, altEsik, bandDurumu, esik, esikEtiketi, yuzde } from "@/domain/esik";

/** Kutucuk içinde açılan grafiğin yüksekliği. */
const IZ_YUKSEKLIGI = 180;

/**
 * PLC bit haritasını okunur gösterir (bu kutuda 4 giriş, 1 çıkış).
 * Bit sırası DOĞRULANMADI; ham değer de yanında durur ki yanlış bir sıra
 * sessizce "gerçek" gibi görünmesin.
 */
function bits(value: number | null): string {
  if (value == null) return "—";
  return `${value.toString(2).padStart(4, "0")} (0x${value.toString(16).toUpperCase()})`;
}

export default function CanliRoute() {
  const navigate = useNavigate();
  // Seçili tezgah `?tezgah=` ile URL'de taşınır ve kabuk artık varsayılana
  // DÜŞMEZ: aramayı düşüren bir gezinme operatörü karşılama ekranına atardı.
  const { search } = useLocation();
  const git = (pathname: string) => navigate({ pathname, search });
  const { live, active, paused, graphTitles, onRenameGraph, katalogYenile, sapma, altSapma } =
    useIzleme();
  const { state, connected, link } = live;
  const feats = state.features;
  // Zincir kopuksa boşluğun tarifi; sağlamsa null ve ekran kendi olumlu
  // cümlesini ("Aktif alarm yok") kurmakta serbesttir.
  const bosluk = baglantiBoslugu(link, live.source);

  // Grafik adı: kullanıcı özelleştirmesi varsa o, yoksa akış sırasından
  // "Grafik N" — sıra map()'in indeksidir, ayrıca kimlik→sıra tablosu tutmak
  // aynı bilgiyi ikinci kez saklamak olurdu.
  const defaultGraphName = (i: number) => `Grafik ${i + 1}`;
  const graphName = (id: string, i: number) => graphTitles[id] ?? defaultGraphName(i);

  // Açık grafikler KİMLİKLE tutulur, nesneyle değil: her canlı kare `features`
  // dizisini baştan yazar, nesne saklansaydı grafik ilk karede donardı.
  const [openIds, setOpenIds] = useState<ReadonlySet<string>>(() => new Set());
  const toggleGraph = (id: string) =>
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (!next.delete(id)) next.add(id);
      return next;
    });

  // Sayım EKRANDAKİ kutucuklar üzerinden: akıştan düşen bir özelliğin kimliği
  // kümede kalabilir, o zaman "hiçbiri açık değil"ken "Tümünü kapat" etkin
  // görünürdü.
  const openCount = feats.reduce((n, f) => (openIds.has(f.id) ? n + 1 : n), 0);

  const onlineUnits = state.units.filter((u) => u.online).length;

  return (
    <PageShell
      title="Canlı İzleme"
      description={`${feats.length ? `${feats.length} özellik` : "Özellik bekleniyor"} · ${
        paused ? "duraklatıldı" : connected ? "akış açık" : "akış yok"
      }`}
    >
      <div className="flex flex-col gap-6">
      {/* ── BAĞLAM ─────────────────────────────────────────────── */}
      <KPIStrip banded min="sm">
        <KPICard label="Çevrim" value={sayi(state.cycle)} note="Son karede" />
        <KPICard label="İş Parçası" value={sayi(state.workpiece)} note="Akış sayacı" />
        <KPICard
          label="Bağlı Ünite"
          value={state.units.length ? `${onlineUnits} / ${state.units.length}` : "—"}
          note="Çevrimiçi / tanımlı"
        />
        <KPICard
          label="PLC Girişleri"
          value={<span className="type-code">{bits(state.plcInputs)}</span>}
          note="Bit sırası doğrulanmadı"
        />
        <KPICard
          label="PLC Çıkışları"
          value={<span className="type-code">{bits(state.plcOutputs)}</span>}
          note="Bit sırası doğrulanmadı"
        />
        <KPICard
          label="Aktif Alarm"
          value={formatNumber(active.length)}
          note={active.length ? "Alarmlar ekranına git" : "Onaylananlar saklanır"}
          deltaTone={active.length ? "neg" : undefined}
          onClick={() => git("/alarmlar")}
        />
      </KPIStrip>

      {/* ── MÜDAHALE ───────────────────────────────────────────── */}
      {/* Metin `baglantiBoslugu`ndan gelir (domain/baglanti-bosluk.ts):
          aynı boşluğu Alarmlar ve Olaylar da anlatmak zorunda ve üç ekranın
          aynı olay için farklı cümle kurması, farklı halkayı suçlaması
          demekti. EYLEMLER burada kalır — hangi çıkış yolunun anlamlı olduğu
          ekrana özeldir. */}
      {link === "catalog-loading" ? (
        // Yükleme için BANT BASILMAZ: katalog isteği tipik olarak saniyenin
        // altında biter ve yanıp sönen bir uyarı, olmayan bir sorunu varmış
        // gibi gösterir. Üst bar bu arada "tezgah bilgisi yükleniyor" diyor,
        // yani durum söylenmemiş de olmuyor. (Alarmlar/Olaylar'da boş ızgara
        // sessiz kalamaz, orada bu hâlin de metni vardır.)
        null
      ) : bosluk ? (
        <Alert
          tone={bosluk.tone}
          title={bosluk.title}
          actions={
            link === "catalog-down" ? (
              <Button
                size="sm"
                variant="secondary"
                iconLeft={<RotateCcw size={IKON.sm} />}
                onClick={katalogYenile}
              >
                Tekrar dene
              </Button>
            ) : link === "no-source" ? (
              <Button size="sm" variant="secondary" onClick={() => git("/")}>
                Tezgah değiştir
              </Button>
            ) : link === "stream-down" ? (
              <Button
                size="sm"
                variant="secondary"
                iconLeft={<RotateCcw size={IKON.sm} />}
                onClick={() => window.location.reload()}
              >
                Tekrar dene
              </Button>
            ) : undefined
          }
        >
          {bosluk.description}
        </Alert>
      ) : active.length > 0 ? (
        <Alert
          tone="danger"
          title={`${formatNumber(active.length)} aktif alarm`}
          actions={
            <Button size="sm" variant="secondary" onClick={() => git("/alarmlar")}>
              Alarmları gör
            </Button>
          }
        >
          {active[0] ? `En yenisi: ${featureAdiVarsa(active[0].featureName)}` : null}
        </Alert>
      ) : (
        <Alert tone="success" title="Aktif alarm yok">
          Onaylanan kayıtlar Alarmlar ekranının "Onaylanmış" görünümünde saklanır.
        </Alert>
      )}

      {/* ── ÖLÇÜM ──────────────────────────────────────────────── */}
      {feats.length === 0 ? (
        <EmptyState
          icon={<LineChartIcon size={IKON["2xl"]} />}
          title="Gösterilecek grafik yok"
          description="Akıştan özellik geldiğinde grafikler burada kutucuk olarak listelenir."
        />
      ) : (
        <Section
          title="Grafikler"
          count={feats.length}
          actions={
            <>
              <Button
                size="sm"
                variant="ghost"
                disabledReason={
                  openCount === feats.length ? "Bütün grafikler zaten açık" : undefined
                }
                onClick={() => setOpenIds(new Set(feats.map((f) => f.id)))}
              >
                Tümünü aç
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabledReason={openCount === 0 ? "Açık grafik yok" : undefined}
                onClick={() => setOpenIds(new Set())}
              >
                Tümünü kapat
              </Button>
            </>
          }
        >
          {/* `items-start`: ızgara öğeleri VARSAYILAN olarak esner (align-items
              normal = stretch), yani bir kutucuk açılınca AYNI SATIRDAKİ kapalı
              kutucuklar da onun boyuna uzuyordu. Ölçüldü: 1. kutucuk açıkken
              2/3/4 `data-state="closed"` olmasına rağmen dördü de 370 px'ti —
              operatör hepsi açılmış ama grafik çizmiyor sanıyordu. Hizayı başa
              çekince her kutucuk kendi boyunda kalır. */}
          <div className="alp-oto-izgara items-start">
            {feats.map((f, i) => (
              <OzellikKutucugu
                key={f.id}
                feature={f}
                graphName={graphName(f.id, i)}
                defaultName={defaultGraphName(i)}
                expanded={openIds.has(f.id)}
                onToggle={() => toggleGraph(f.id)}
                onRename={(ad) => onRenameGraph(f.id, ad)}
                connected={connected}
                paused={paused}
                sapma={sapma}
                altSapma={altSapma}
              />
            ))}
          </div>
        </Section>
      )}

      {/* ── KİMLİK ─────────────────────────────────────────────── */}
      {/* Hiç ünite yoksa HİÇBİR ŞEY basılmaz — bu, boş durumdan ve "—"den ayrı
          üçüncü yokluk sözlüğüdür. */}
      {state.units.length > 0 && (
        <Section title="İzleme üniteleri" count={state.units.length}>
          <UniteListesi units={state.units} />
        </Section>
      )}
      </div>
    </PageShell>
  );
}

function featureAdiVarsa(ad: string | undefined): string {
  return ad ?? "özellik adı yok";
}

/**
 * Grafik kutucuğu — kapalıyken grafiksiz özet, açıkken altında tam grafik.
 *
 * Tetikleyici kartın TÜM genişliğini kaplar: kiosk dokunma hedefi eski
 * "kartın her yeri tıklanabilir" davranışından küçülmesin diye.
 *
 * DOLGU: bu iki isteği (metin içeride dursun / dokunma hedefi kenara kadar
 * gitsin) tek bir `padding` sayısı KARŞILAYAMAZ. Eskiden `padding={0}` yazıyordu
 * ve hedef gerçekten kenara kadar gidiyordu, ama METİN de kenara yapışıyordu:
 * ölçüldü (288 px kart) — başlığın soluna 0 px, sağına ise sürgü okunun yediği
 * 25 px düşüyordu. Başlık kartın içinde ortalanmış değil, sol çizgiye dayanmış
 * görünüyordu. Doğrusu ikisini AYIRMAK: kart kendi dolgusunu (12 px) korur,
 * akordiyon negatif kenar boşluğuyla (-mx-3) o dolguyu aşıp kenara uzanır,
 * tetikleyici/içerik dolguyu (px-3) kendi içinde geri verir. Sonuç: dokunma
 * hedefi tam genişlik, metin her iki yandan 12 px içeride.
 *
 * NOT: 12 px iki yerden de sabittir — `Card`ın `padding` varsayılanı düz sayı,
 * `px-3` ise 0.75rem'dir ve "Kompakt" yoğunluk kök punto ile --space-3'ü
 * DEĞİŞTİRMEZ (yalnız <html data-density> yazar). İkisi bu yüzden kaymaz.
 *
 * AD DÜZENLEME `actions` İLE VERİLMEZ, kartın üstüne KONUMLANIR. `Card`a
 * `actions` geçmek başlık ŞERİDİNİ açar; bu kutucukta o şeridin başlık yuvası
 * BOŞTUR (başlık akordiyon tetikleyicisinin içinde), yani şerit yalnız kalemi
 * taşır. Ölçüldü: 44 px'lik o bant başlığı kartın 70,8 px altına itiyordu ve
 * üstte kocaman bir boşluk bırakıyordu. Kalem mutlak konumlanınca şerit hiç
 * doğmaz, başlık ~26 px'e çıkar. Kalem yine tetikleyicinin DIŞINDADIR (iç içe
 * buton yok, olay yutma yok) — sadece artık üstünde duruyor.
 */
function OzellikKutucugu({
  feature: f,
  graphName,
  defaultName,
  expanded,
  onToggle,
  onRename,
  connected,
  paused,
  sapma,
  altSapma,
}: {
  feature: Feature;
  graphName: string;
  defaultName: string;
  expanded: boolean;
  onToggle: () => void;
  onRename: (ad: string) => void;
  connected: boolean;
  paused: boolean;
  sapma: number;
  altSapma: number;
}) {
  const title = featureTitle(f);
  const routing = featureRouting(f);
  // Yüzde `f.pct`'den DEĞİL eşikten türer: CSV kaynağında eşiği bu ekran kurar
  // (ortalama + sapma) ve backend `pct`'yi bilerek boş bırakır. Bkz. esik.ts.
  //
  // YÜZDE ÜST SINIRA GÖREDİR ve öyle kalır — alt sınırın gelmesi "%"in
  // anlamını değiştirmez. Bandın DIŞINA çıkıldığı ayrı bir rozetle, YÖNÜYLE
  // birlikte söylenir: tek başına kırmızı bir "%75" okunamazdı.
  const pctDeger = yuzde(f, sapma);
  const pct = pctText(pctDeger);
  const band = bandDurumu(f, sapma, altSapma);
  const unitLabel = f.unitNo == null ? null : deviceTitle({ unitNo: f.unitNo });
  // Alarm vurgusu: yalnız gerçekten yük/takım sorunu olan durum kodları.
  const alert = statusTone(f.statusCode) === "danger";
  const canliMetin = paused ? "Duraklatıldı" : connected ? "Canlı" : "Akış yok";

  return (
    <Card className={`relative${alert ? " border-danger-600" : ""}`}>
      <Accordion
        className="-mx-3"
        type="multiple"
        value={expanded ? [f.id] : []}
        onValueChange={(v: string[]) => {
          if (v.includes(f.id) !== expanded) onToggle();
        }}
      >
        {/* Ayırıcı çizgi KAPALI: `AccordionItem`in alt kenarlığı ÜST ÜSTE dizili
            maddeleri ayırmak içindir, burada kutucuk başına tek madde var. Kartın
            kendi kenarlığının 12 px üstünde ikinci bir hairline çiziyor ve altında
            ölü bir şerit bırakıyordu — kart iki kez bitmiş gibi okunuyordu. */}
        <AccordionItem value={f.id} className="border-b-0">
          <AccordionTrigger className="min-w-0 px-3">
            {/* `min-w-0`: esnek öğenin varsayılan `min-width:auto`su, içindeki
                nowrap başlığın genişliğinin ALTINA inmeyi ENGELLER — sütun
                kısalmaz, `truncate` hiç devreye girmez ve uzun ad kartın
                dışına taşar (kart `overflow-hidden` olduğu için de üç nokta
                YERİNE sessizce kesilirdi). Ölçüldü: 325 px'lik başlık 288 px'lik
                kartta scrollWidth == clientWidth veriyordu, yani kısaltma yok. */}
            <div className="flex w-full min-w-0 flex-col gap-1 text-left">
              {/* Kalemin yeri SARMALAYICI ile ayrılır, başlığın kendi dolgusuyla
                  DEĞİL: `text-overflow: ellipsis` taşmayı DOLGU kutusunda kırpar,
                  yani `truncate`li bir öğeye verilen `pr-*` yer AYIRMAZ — metin
                  dolgunun içine akıp kalemin ARKASINDAN geçiyordu (denendi, uzun
                  adla görüldü). Sarmalayıcı genişliği daraltınca kısaltma doğru
                  yerde olur. Kalem yüzdüğü için ızgarada kendi yerini kaplamaz. */}
              <div className="pr-8">
                <span className="type-card-title block truncate">
                  {graphName} · {title}
                </span>
              </div>
              <span className="flex flex-wrap items-baseline gap-1">
                <span className="type-kpi">{sayi(f.current)}</span>
                {f.uom && <span className="type-help text-muted-foreground">{f.uom}</span>}
                {/* Ham sayım olduğu açıkça yazılır: 0..255, ölçek çarpanı yok. */}
                {f.rawCounts && (
                  <span className="type-help text-muted-foreground">/ {RAW_MAX} ham</span>
                )}
              </span>
              <span className="flex flex-wrap items-center gap-1">
                {f.statusLabel && (
                  <Badge tone={statusTone(f.statusCode)} dot size="sm">
                    {f.statusLabel}
                  </Badge>
                )}
                <Badge tone={connected && !paused ? "success" : "danger"} dot size="sm">
                  {canliMetin}
                </Badge>
                {unitLabel && (
                  <span className="type-help text-muted-foreground">{unitLabel}</span>
                )}
              </span>
            </div>
          </AccordionTrigger>

          {/* AÇILIŞ NOTU — Grafik BURADA bağlanır; kapalı kutucuk hiç iz
              haritalamaz (bunu Radix yapar, bkz. dosya başı).

              `mzi-akordiyon` (app.css) yüksekliği 0 ↔ ölçülen yükseklik
              arasında oynatır. İZ KOŞULSUZ BASILIR: eskiden burada
              `{expanded && <OzellikIzi/>}` vardı ve KAPANIŞ animasyonunu
              bozuyordu. Radix kapanışta yüksekliği bir layout effect'te ÖLÇÜP
              `--radix-accordion-content-height`e yazar; koşul grafiği aynı
              commit'te söktüğü için ölçülen değer ~260 px yerine yalnız
              üstteki rozet satırının ~40 px'i oluyordu ve kutucuk oradan
              çöküyordu. Koşulun kaldırılması başarımı DEĞİŞTİRMEZ, yalnız
              kapanışın 200 ms'i boyunca grafik ayakta kalır. */}
          <AccordionContent className="mzi-akordiyon px-3">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-1">
                {pct && (
                  <Badge tone={band ? "danger" : "neutral"} size="sm">
                    {pct}
                  </Badge>
                )}
                {/* Hangi sınırın aşıldığı YAZIYLA: renk tek başına bilgi
                    taşımaz ve iki ihlal yönü aynı kırmızıyı kullanıyor. */}
                {band && (
                  <Badge tone="danger" size="sm">
                    {BAND_ETIKETI[band]}
                  </Badge>
                )}
                {/* Yönlendirme yalnız üniteden FAZLASINI söylüyorsa yazılır. */}
                {routing && routing !== unitLabel && (
                  <span className="type-help text-muted-foreground">{routing}</span>
                )}
                {f.samples.length > 0 && f.kind === "trace" && (
                  <span className="type-help text-muted-foreground">
                    {formatNumber(f.samples.length)} örnek
                    {f.minValue != null &&
                      f.maxValue != null &&
                      ` · ${formatNumber(f.minValue)}–${formatNumber(f.maxValue)}`}
                  </span>
                )}
                <ConfidenceTag confidence={f.confidence} />
                {f.truncated && (
                  <Badge tone="warning" dot size="sm">
                    kırpık iz
                  </Badge>
                )}
              </div>
              <OzellikIzi feature={f} title={title} sapma={sapma} altSapma={altSapma} />
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Akordiyondan SONRA: görsel sıra (önce başlık, sonra kalem) ile hem DOM
          hem sekme sırası örtüşsün. Mutlak konum tetikleyicinin üstünde durur;
          iç içe buton doğurmadığı için tıklama kutucuğu açıp kapatmaz. */}
      <div className="absolute right-2 top-2 z-10">
        <AdDuzenle
          graphName={graphName}
          defaultName={defaultName}
          onRename={onRename}
          title={title}
        />
      </div>
    </Card>
  );
}

/** Grafik adını değiştiren Popover — tetikleyiciyle çakışmaz. */
function AdDuzenle({
  graphName,
  defaultName,
  onRename,
  title,
}: {
  graphName: string;
  defaultName: string;
  onRename: (ad: string) => void;
  title: string;
}) {
  const [acik, setAcik] = useState(false);
  const [draft, setDraft] = useState(graphName);

  const kaydet = () => {
    onRename(draft.trim()); // boş ad → varsayılana döner (kabuk hallediyor)
    setAcik(false);
  };

  return (
    <Popover
      open={acik}
      onOpenChange={(v: boolean) => {
        setAcik(v);
        if (v) setDraft(graphName);
      }}
    >
      <PopoverTrigger asChild>
        <IconButton label={`Grafik başlığını değiştir: ${title}`} variant="ghost" size="sm">
          <Pencil size={IKON.sm} />
        </IconButton>
      </PopoverTrigger>
      <PopoverContent>
        <div className="flex w-72 flex-col gap-3">
          <Field label="Grafik adı" hint="Boş bırakılırsa varsayılan ada döner.">
            <Input
              autoFocus
              maxLength={40}
              value={draft}
              placeholder={defaultName}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") kaydet();
                if (e.key === "Escape") setAcik(false);
              }}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={() => setAcik(false)}>
              Vazgeç
            </Button>
            <Button size="sm" iconLeft={<Check size={IKON.sm} />} onClick={kaydet}>
              Kaydet
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Açık kutucuğun grafiği. Ayrı bileşendir ki örnek dizisinin dönüşümü YALNIZ
 * açık kutucuklarda çalışsın.
 */
function OzellikIzi({
  feature: f,
  title,
  sapma,
  altSapma,
}: {
  feature: Feature;
  title: string;
  sapma: number;
  altSapma: number;
}) {
  const data = useMemo(() => f.samples.map((v, i) => ({ i, value: v })), [f.samples]);
  // Eşik iki kaynaktan gelebilir (telden limit / CSV ortalaması + sapma) ve
  // ETİKET HANGİSİ OLDUĞUNU SÖYLER — hesaplanmış bir çizgiyi düz "Limit" diye
  // basmak, onu üreticinin koyduğu eşik gibi okuturdu. Bkz. esik.ts.
  const esikDeger = esik(f, sapma);
  const altEsikDeger = altEsik(f, altSapma);

  return (
    <div className="flex flex-col gap-1">
      <LineChart
        data={data}
        x="i"
        series={[{ key: "value", label: title }]}
        height={IZ_YUKSEKLIGI}
        yTickFormatter={(v) => formatNumber(v)}
        referenceLine={
          esikDeger == null
            ? undefined
            : { value: esikDeger, label: esikEtiketi(f, sapma), tone: "crit" }
        }
      />
      {/* BANT SAYIYLA YAZILIR — ÇİZGİLERE GÜVENİLEMEZ. İki ayrı sebep:

          1. ALT SINIR HİÇ ÇİZİLEMİYOR. Paketin LineChart'ı TEK referans
             çizgisi alır (`referenceLine?: ChartReferenceLine` — dizi DEĞİL),
             yani üst ve alt aynı anda çizilemez. Üst çizilir, alt yalnız
             buradaki sayıda yaşar. Dosya başındaki EKSEN NOTU'nda tasarım
             sistemine açılan istek `yDomain` + `referenceLine[]` idi;
             ikincisi tam olarak budur.
          2. ÜST ÇİZGİ DE KAYBOLABİLİR. `yDomain` yok, eksen veriye göre
             ölçeklenir ve Recharts alanın DIŞINDA kalan çizgiyi sessizce
             ATAR: M08 DEBI'de %10 sapmada çizgi duruyor (246,5), %40'ta
             kayboluyor (313,7) — iz 222–228'de akarken eksen 240'ta bitiyor.

          Kaybolan ya da hiç çizilmeyen sınır "limit yok" diye okunurdu; sayı
          burada durdukça o yanlış okuma olmaz.

          Tek ondalık: değerler HAM SAYIMDIR (0..255 tamsayı) ve ortalamanın
          üçüncü basamağı ("313,675") olmayan bir kesinlik gösterirdi. */}
      {f.baseline != null && esikDeger != null && altEsikDeger != null && (
        <span className="type-help text-muted-foreground">
          {`Bant ${formatNumber(altEsikDeger, 1)} – ${formatNumber(esikDeger, 1)}` +
            ` · ortalama ${formatNumber(f.baseline, 1)} −%${altSapma} / +%${sapma}`}
        </span>
      )}
      {/* Eksen dürüstlüğü: ham iz sabit 0..255'te DEĞİL, otomatik ölçekte
          çiziliyor. Bunu yazmadan bırakmak, sakin bir sinyali salınım gibi
          okutur. Bkz. dosya başındaki EKSEN NOTU. */}
      {f.rawCounts && (
        <span className="type-help text-muted-foreground">
          Otomatik ölçek
          {f.minValue != null && f.maxValue != null
            ? ` · gösterilen aralık ${formatNumber(f.minValue)}–${formatNumber(f.maxValue)}`
            : ""}
          {` · tam ölçek 0–${RAW_MAX} ham`}
        </span>
      )}
    </div>
  );
}

/** İzleme ünitesi kimlik listesi — cihaz, model, sensörler. */
function UniteListesi({ units }: { units: UnitInfo[] }) {
  const columns: Array<CompactListColumn<UnitInfo>> = [
    {
      key: "online",
      header: "Durum",
      type: "badge",
      badge: (u) => ({
        tone: u.online ? "success" : "neutral",
        label: u.online ? "Çevrimiçi" : "Çevrimdışı",
      }),
    },
    { key: "unit", header: "Ünite", type: "code", accessor: (u) => unitTitle(u) },
    { key: "model", header: "Model", accessor: (u) => u.model ?? "—" },
    {
      key: "generation",
      header: "Kuşak",
      accessor: (u) =>
        u.generation == null ? "—" : u.generation === 1 ? "Provis2 (MC_)" : "Promos3 (MC3_)",
    },
    { key: "channelAmount", header: "Kanal", type: "number", accessor: (u) => sayi(u.channelAmount) },
    { key: "firmware", header: "Firmware", type: "code", accessor: (u) => u.firmware ?? "—" },
  ];

  return (
    <CompactList<UnitInfo>
      columns={columns}
      rows={units}
      getRowId={(u) => String(u.unit)}
      rowDetailTitle={(u) => unitTitle(u)}
      rowDetail={(u) => {
        // Sensör özeti: tel üzerinden tanımlayıcı geldiyse onlar, yoksa cihaz
        // kaydındaki MiSensType etiketleri.
        const sensorLabels = u.sensors.length
          ? u.sensors.map((s) => s.typeLabel ?? `Tip ${s.type ?? "?"}`)
          : u.miSensTypeLabels;
        const counted = new Map<string, number>();
        for (const label of sensorLabels) counted.set(label, (counted.get(label) ?? 0) + 1);

        return (
          <KeyValue
            items={[
              { label: "Seri no", value: u.serialNo ?? "—", mono: true },
              {
                label: "GType",
                value:
                  u.gType == null
                    ? "—"
                    : `${hex(u.gType)}${u.gSubType != null ? `/${u.gSubType}` : ""}`,
                mono: true,
              },
              {
                label: "Sensörler",
                value:
                  counted.size > 0
                    ? [...counted].map(([label, n]) => `${n}× ${label}`).join(", ")
                    : "—",
              },
              { label: "Sensör kanalı", value: sayi(u.miSensAmount) },
              { label: "Örnek bölücü", value: sayi(u.sampleDiv) },
              { label: "Reduz limit", value: sayi(u.reduzLim) },
              { label: "Konfig sürümü", value: sayi(u.konfigVersion), mono: true },
            ]}
          />
        );
      }}
    />
  );
}
