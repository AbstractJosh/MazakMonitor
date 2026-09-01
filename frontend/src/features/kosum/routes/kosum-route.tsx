// Tam Koşum — CSV korpusunun TAMAMI, tek grafikte.
//
// NEDEN AYRI BİR EKRAN: Canlı İzleme aynı CSV'den beslenir ama KAYAN BİR
// PENCERE gösterir (backend live.WINDOW = 120 örnek) ve koşumda 131 an var —
// yani canlı ekran koşumun tamamını hiçbir zaman göstermez, tur başa sardıkça
// pencerenin başından dökülür. Burası dosyaları baştan sona okur.
//
// CANLI YOLA DOKUNULMAZ: bu ekran `/api/kosum` dışında hiçbir şey çağırmaz;
// akış, hub ve SSE olduğu gibi kalır.
//
// EŞİK ÇİZGİSİ YOK ve bu bilinçli. Paketin `LineChart`ı TEK `referenceLine`
// alır (dizi değil, bkz. canli-route.tsx'teki aynı not); yedi serinin ortak
// bir sınırı olmadığı için çizilecek tek çizgi, hepsinin limitiymiş gibi
// okunurdu. Ortalamalar bunun yerine grafiğin altında SAYIYLA yazılır.
//
// EKSEN NOTU: değerler ham sayımdır ve eksen veriye göre ölçeklenir (paketin
// LineChart'ında `yDomain` prop'u yok). İki ünite iki farklı seviyede akar
// (10660 ~110, 10665 ~220); ortak eksen bunları ayrı bantlar olarak okutur,
// ama otomatik ölçek olduğu AÇIKÇA yazılır — canli-route.tsx ile aynı kural.

import { useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  Alert,
  Button,
  Card,
  EmptyState,
  PageShell,
  Skeleton,
  ToggleGroup,
  formatCalendarDay,
  formatNumber,
  IKON,
} from "@alp/design-system";
import { CHART_COLORS, CHART_OTHER, LineChart } from "@alp/design-system/charts";
import { FileClock, RotateCcw } from "lucide-react";
import {
  tekGun,
  useKosum,
  type Kosum,
  type KosumDurum,
  type KosumHata,
  type KosumRow,
} from "@/domain/kosum";

/** Tek büyük grafiğin yüksekliği — kutucuk izinden (180) belirgin biçimde uzun. */
const GRAFIK_YUKSEKLIGI = 440;

/** X ekseninin veri anahtarı. Satır değerleri seri KİMLİĞİYLE anahtarlanır,
 *  yani bu adın onlarla çakışması mümkün değil (`csv:...` öneki). */
const X_ANAHTARI = "t";

export default function KosumRoute() {
  const [params] = useSearchParams();
  // Tezgah kabukla AYNI yerden okunur (`?tezgah=`): bağlam onu taşımıyor ve
  // ikinci bir kopyasını bağlama eklemek aynı bilgiyi iki yerde tutmak olurdu.
  const machineId = params.get("tezgah") ?? "";
  const { kosum, durum, hata, yenile } = useKosum(machineId);

  return (
    <PageShell fullWidth title="Tam Koşum" description={aciklama(kosum, durum)}>
      {durum === "loading" ? (
        <Card>
          <Skeleton style={{ height: GRAFIK_YUKSEKLIGI }} />
        </Card>
      ) : durum === "yok" ? (
        <KayitYok />
      ) : durum === "error" ? (
        <Alert
          tone="danger"
          title={hata?.cevapVerdi ? "Koşum kaydı okunamadı" : "Backend'e ulaşılamadı"}
          actions={
            <Button
              size="sm"
              variant="secondary"
              iconLeft={<RotateCcw size={IKON.sm} />}
              onClick={yenile}
            >
              Tekrar dene
            </Button>
          }
        >
          {hataMetni(hata)}
          {/* Sunucunun HAM tanısı — ayrı satırda ve olduğu gibi. Cümlenin
              içine gömülmez: backend metinleri ASCII yazılır ("CSV kaynagi
              okunamadi") ve aksanlı arayüz nesrinin ortasında bozuk bir
              cümle gibi okunur; ayrıca iki cümle nokta olmadan birbirine
              yapışırdı. Ayrı satırda ise ne olduğu bellidir: makinenin
              söylediği, alıntı. Yol uzundur, `break-all` taşmayı keser. */}
          {hata?.detay && (
            <div className="type-help mt-2 break-all">{hata.detay}</div>
          )}
        </Alert>
      ) : kosum && kosum.series.length > 0 ? (
        <KosumGrafigi kosum={kosum} />
      ) : (
        <EmptyState
          icon={<FileClock size={IKON["2xl"]} />}
          title="Kayıtta çizilecek seri yok"
          description="CSV korpusu okundu ama değeri olan bir özellik yuvası bulunamadı."
        />
      )}
    </PageShell>
  );
}

/**
 * Hata metni SUÇLUYU DOĞRU ADLANDIRIR.
 *
 * Sunucu cevap verdiyse (503) ağı suçlamak kullanıcıyı yanlış yere baktırır —
 * `veri/`si eksik deploy edilmiş bir kurulumda sorun sunucuda değil
 * dosyalardadır (bkz. domain/kosum.ts `KosumHata`).
 *
 * Burası YALNIZ nesri kurar; sunucunun ham `detail`i Alert gövdesinde ayrı
 * satırda basılır. Gömseydik ASCII backend metni aksanlı cümlenin ortasına
 * düşer, üstelik iki cümle nokta olmadan yapışırdı.
 *
 * Her iki dalda da SON CÜMLE aynı kalır: bu ekran koşumun boş olduğunu
 * iddia etmiyor — hata ile boş kayıt ayrı şeylerdir.
 */
function hataMetni(hata: KosumHata | null): string {
  const kuyruk = "Bu ekran koşumun boş olduğunu SÖYLEMİYOR.";
  if (!hata?.cevapVerdi) return `Backend'e ulaşılamadı. ${kuyruk}`;
  return `Sunucu CSV kaynağını okuyamadı. ${kuyruk}`;
}

/** Başlık altındaki tek satır: tarih + saat aralığı + an sayısı. */
function aciklama(kosum: Kosum | null, durum: KosumDurum): string {
  if (durum === "loading") return "CSV kaydı okunuyor…";
  if (durum === "yok") return "Bu tezgahın kayıtlı koşumu yok";
  if (!kosum || kosum.count === 0) return "CSV kaydı";
  return `${zamanAraligi(kosum)} · ${formatNumber(kosum.count)} an · CSV kaydı`;
}

/**
 * Koşumun tarih/saat aralığı.
 *
 * Tarih pakete BİÇİMLETİLİR (`formatCalendarDay`), saat OLDUĞU GİBİ basılır.
 * İkisi telde de ayrı gelir ve bu kasıtlıdır: CSV'nin zamanı duvar saatidir,
 * bir UTC anı değil — `formatDateTime`den geçirmek onu gösterim dilimine
 * çevirir ve tarayıcı saati sunucununkiyle tutmayan her makinede koşum
 * saatlerini kaydırırdı (ADR-0005: an ile takvim günü ayrı kavramlar).
 */
function zamanAraligi(k: Kosum): string {
  if (!k.startDay || !k.endDay) return "CSV kaydı";
  if (tekGun(k)) {
    return `${formatCalendarDay(k.startDay)} · ${k.startTime}–${k.endTime}`;
  }
  return `${formatCalendarDay(k.startDay)} ${k.startTime} – ${formatCalendarDay(k.endDay)} ${k.endTime}`;
}

/** Kaynağı CSV olmayan tezgah — arıza değil, yapılandırma. */
function KayitYok() {
  const navigate = useNavigate();
  const { search } = useLocation();

  return (
    <EmptyState
      icon={<FileClock size={IKON["2xl"]} />}
      title="Bu tezgahın kayıtlı koşumu yok"
      description="Koşum kaydı CSV kaynaklı tezgaha aittir. Bu bir arıza değil, yapılandırmadır."
      action={
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate({ pathname: "/", search })}
        >
          Tezgah değiştir
        </Button>
      }
    />
  );
}

/**
 * Tek büyük grafik + seri çipleri.
 *
 * Ayrı bileşendir ki satır dönüşümü (131 an × 7 seri) yalnız kayıt GELDİĞİNDE
 * kurulsun; yükleme/hata dallarında hiç koşmasın.
 */
function KosumGrafigi({ kosum }: { kosum: Kosum }) {
  // GİZLİ tutulur, açık değil: varsayılan "hepsi görünür" böylece bir başlangıç
  // effect'i gerektirmez ve kayıt yeniden çekilince seçim bozulmaz.
  const [gizli, setGizli] = useState<ReadonlySet<string>>(() => new Set());

  // KİMLİK SABİTLENİR, HER ÇİZİMDE YENİ DİZİ ÜRETİLMEZ. Radix'in denetimli
  // değeri REFERANSLA izlemesi yüzünden bu bir başarım ayarı değil DOĞRULUK
  // şartıdır: `value`ya her çizimde yeni bir dizi verildiğinde Radix değeri
  // değişmiş sayıp `onValueChange`i çağırıyor, o da durumu yazıyor, o da yeni
  // bir dizi doğuruyordu — sonsuz döngü. Ölçüldü: bir çipe tek tıklama
  // sekmeyi tamamen donduruyordu (CDP ekran görüntüsü 30 sn'de zaman aşımına
  // uğradı). Aşağıdaki `setGizli` de aynı döngüyü kendi ucundan kırar.
  const gorunur = useMemo(
    () => kosum.series.filter((s) => !gizli.has(s.id)),
    [kosum.series, gizli],
  );
  const gorunurIds = useMemo(() => gorunur.map((s) => s.id), [gorunur]);

  // RENK SERİNİN KİMLİĞİNE BAĞLIDIR, SIRASINA DEĞİL — paketin `CHART_COLORS`
  // sözleşmesi bunu açıkça söyler. `LineChart` rengi kendisine verilen dizinin
  // SIRASINDAN dağıttığı için, bir seri gizlenince kalanlar yeniden boyanırdı;
  // `colors` bunu sabit indekse geri bağlar.
  //
  // 9. SERİ BAŞA SARMAZ, `CHART_OTHER`A KATLANIR. Paletin sözleşmesi bunu
  // harfiyen söyler: "9. seri yeni bir renk değildir". Modulo ile sarmak 9.
  // seriye 1.nin rengini verirdi — yani tek işi yedi çizgiyi birbirinden
  // ayırmak olan bir grafikte İKİ FARKLI sinyal aynı renge boyanırdı, üstelik
  // sessizce. Bugün 7 seri var (2 ünite × 4 yuva − 1 boş yuva); sınır bir
  // ünite ya da bir yuva eklendiğinde geçilir, o yüzden şimdiden kapalı.
  const renkler = useMemo(
    () =>
      new Map(
        kosum.series.map((s, i) => [
          s.id,
          i < CHART_COLORS.length ? CHART_COLORS[i] : CHART_OTHER,
        ]),
      ),
    [kosum.series],
  );

  // Satırlar GÖRÜNÜRLÜKTEN BAĞIMSIZ kurulur: çip açılıp kapandıkça 131 satırı
  // yeniden üretmenin anlamı yok, recharts kullanılmayan anahtarı zaten
  // görmezden gelir.
  const gunlu = !tekGun(kosum);
  const data = useMemo(
    () => kosum.rows.map((r) => ({ [X_ANAHTARI]: xEtiketi(r, gunlu), ...r.values })),
    [kosum.rows, gunlu],
  );

  return (
    <Card>
      <div className="flex flex-col gap-3">
        {gorunur.length === 0 ? (
          <div
            className="flex items-center justify-center"
            style={{ height: GRAFIK_YUKSEKLIGI }}
          >
            <EmptyState
              compact
              title="Bütün seriler gizli"
              description="Aşağıdaki çiplerden en az birini aç."
            />
          </div>
        ) : (
          <LineChart
            data={data}
            x={X_ANAHTARI}
            series={gorunur.map((s) => ({ key: s.id, label: s.name }))}
            colors={gorunur.map((s) => renkler.get(s.id) ?? CHART_OTHER)}
            height={GRAFIK_YUKSEKLIGI}
            yTickFormatter={(v) => formatNumber(v)}
          />
        )}

        <ToggleGroup
          type="multiple"
          label="Grafikte gösterilecek seriler"
          variant="outline"
          size="sm"
          value={gorunurIds}
          onValueChange={(acikIds: string[]) =>
            setGizli((onceki) => {
              const yeni = new Set(
                kosum.series.map((s) => s.id).filter((id) => !acikIds.includes(id)),
              );
              // AYNI SEÇİM YENİ NESNE ÜRETMEZ. Değişmemiş bir seçim için yeni
              // bir Set döndürmek durumu "değişti" saydırır ve yukarıdaki
              // döngüyü tek başına ayakta tutmaya yeter — çağrı idempotent
              // olmak zorunda.
              return esitKume(onceki, yeni) ? onceki : yeni;
            })
          }
          items={kosum.series.map((s) => ({
            value: s.id,
            label: s.name,
            // Çipin rengi grafikteki çizgisiyle aynı: ad tek başına hangi
            // çizginin kime ait olduğunu söylemiyordu.
            //
            // HALKA `ring-current`: basılı çipin zemini marka mavisidir ve
            // paletin İLK rengi de mavidir — SPINDEL'in noktası zeminde
            // TAMAMEN kayboluyordu (ölçüldü, ekranda hiç görünmüyordu).
            // `currentColor` çipin kendi yazı rengidir, yani basılıyken beyaz
            // basılı değilken koyu: hangi durumda olursa olsun zeminden
            // ayrıldığı GARANTİ olan tek renk. Sabit bir renk seçmek iki
            // durumdan birinde aynı sorunu geri getirirdi.
            icon: (
              <span
                aria-hidden
                className="inline-block h-2 w-2 rounded-full ring-1 ring-current"
                style={{ background: renkler.get(s.id) ?? CHART_OTHER }}
              />
            ),
          }))}
        />

        {/* ORTALAMALAR SAYIYLA — çizgi olarak çizilemedikleri için (dosya
            başındaki EŞİK ÇİZGİSİ notu). Yalnız görünen seriler yazılır;
            gizlenmiş bir serinin sayısı grafikte karşılığı olmayan bir
            bağlam olurdu. */}
        {gorunur.length > 0 && (
          <span className="type-help text-muted-foreground">
            {gorunur
              .map((s) => `${s.name} ortalama ${formatNumber(s.baseline, 1)}`)
              .join(" · ")}
          </span>
        )}

        {/* Eksen dürüstlüğü: ham sayım, otomatik ölçek, gösterilen aralık.
            canli-route.tsx ile aynı cümle kurgusu. */}
        {gorunur.length > 0 && (
          <span className="type-help text-muted-foreground">
            {`Ham sayım · otomatik ölçek · gösterilen aralık ${formatNumber(
              Math.min(...gorunur.map((s) => s.minValue)),
            )}–${formatNumber(Math.max(...gorunur.map((s) => s.maxValue)))}`}
            {` · ${formatNumber(kosum.count)} an, eksende gün içi saat`}
          </span>
        )}

        {/* Kopuk iz açıkça söylenir: bir seri koşumun her anında okunmadıysa
            çizgisindeki boşluk veriden gelir, çizimden değil. */}
        {gorunur.some((s) => s.count < kosum.count) && (
          <span className="type-help text-muted-foreground">
            {gorunur
              .filter((s) => s.count < kosum.count)
              .map((s) => `${s.name}: ${formatNumber(s.count)}/${formatNumber(kosum.count)} anda okundu`)
              .join(" · ")}
          </span>
        )}
      </div>
    </Card>
  );
}

/** İki kümenin aynı üyeleri taşıyıp taşımadığı — seçim değişti mi kararı. */
function esitKume(a: ReadonlySet<string>, b: ReadonlySet<string>): boolean {
  if (a.size !== b.size) return false;
  for (const v of a) if (!b.has(v)) return false;
  return true;
}

/**
 * Eksen etiketi. Tek günlük koşumda yalnız saat; birden fazla güne yayılan bir
 * korpusta saat tek başına belirsizdir (aynı etiket iki kez geçerdi), o yüzden
 * gün de yazılır — tarih yine pakete biçimletilir.
 */
function xEtiketi(r: KosumRow, gunlu: boolean): string {
  return gunlu ? `${formatCalendarDay(r.day)} ${r.time}` : r.time;
}
