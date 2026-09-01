// Alarmlar — aktif + onaylanmış alarmların listesi (CONTEXT: Alarm, Onay).
//
// Onay MVP'de yalnız kendi DB'mizde "görüldü" damgasıdır (ADR-0004); donanıma
// yazılmaz. Onay tek dokunuş (onay sorusu yok); yanlış dokunuşta aynı satır
// aksiyonu onayı geri alır. Onaylananlar silinmez, "Onaylanmış" görünümünde
// saklanır. Varsayılan görünüm operatörün işi olan "Aktif"tir.
//
// TABLO: DataGrid DEĞİL `DataTable` — yapısı DataTableDesign devrinden gelir
// (istatistik şeridi, arama, bölmeli süzgeç, kolon sürüklemesi, satır detayı,
// numaralı sayfalayıcı), BİÇİMİ uygulamanın kendisinden. İkisi aynı
// `DataTableColumn<T>` sözleşmesini okuduğu için aşağıdaki kolon dizisi
// olduğu gibi taşındı; değişen iki şey var:
//   • Görünüm seçici Tabs'tan tablonun kendi bölmeli süzgecine indi —
//     araç şeridinde durur ve kabuğun sekme çubuğuyla çakışmaz.
//   • Telin taşıdığı ama kolonu olmayan alanlar artık SATIR DETAYINDA
//     görünür (aşağıdaki `detay`). Önceden hiçbir ekranda yoklardı.

import { useMemo, useState } from "react";
import {
  Button,
  DataTable,
  PageShell,
  formatDateTime,
  IKON,
  type DataTableColumn,
  type DataTablePane,
} from "@alp/design-system";
import { Check, ShieldCheck, Undo2, Unplug } from "lucide-react";
import { useIzleme } from "@/app/izleme-baglami";
import type { Alarm, AlarmState } from "@/domain/types";
import { baglantiBoslugu } from "@/domain/baglanti-bosluk";
import ConfidenceTag from "@/domain/ConfidenceTag";
import {
  CONFIDENCE_HINT,
  CONFIDENCE_LABEL,
  alarmTitle,
  deviceTitle,
  peakText,
  sayi,
  statusTone,
} from "@/domain/format";

type Filter = "all" | AlarmState;

/** Detay panosunda boş alan "—" görünür; uydurma değer YAZILMAZ. */
function metin(v: string | null | undefined): string {
  return v == null || v === "" ? "—" : v;
}

export default function AlarmlarRoute() {
  const { alarms, paused, live, onToggleAck, onAckAll } = useIzleme();
  const [filter, setFilter] = useState<Filter>("active");

  // "Aktif alarm yok" bir GÜVENCE cümlesidir ve ancak KAYNAK öyle diyorsa
  // kurulabilir. Zincir kopukken (kaynaksız tezgah, katalog düşmüş, akış
  // kopmuş) liste boş değil BİLİNMEZDİR; yeşil kalkanla "alarm yok" demek,
  // arkasında hiçbir kanıt olmayan bir emniyet iddiasıydı. Metin üç ekranda
  // ortaktır (domain/baglanti-bosluk.ts).
  const bosluk = baglantiBoslugu(live.link, live.source);

  const sayimlar = useMemo(
    () => ({
      active: alarms.filter((a) => a.state === "active").length,
      all: alarms.length,
      acknowledged: alarms.filter((a) => a.state === "acknowledged").length,
    }),
    [alarms],
  );

  const rows = useMemo(
    () => (filter === "all" ? alarms : alarms.filter((a) => a.state === filter)),
    [alarms, filter],
  );

  // Kolonlar Promos3 alarm kaydıyla birebir (rapor 4.2 + Alarms tablosu).
  // Kaynak bir alanı taşımıyorsa "—" görünür; uydurma değer YAZILMAZ.
  const columns: Array<DataTableColumn<Alarm>> = [
    {
      key: "time",
      header: "Zaman",
      mono: true,
      sortable: true,
      render: (a) => formatDateTime(a.time),
      accessor: (a) => a.time,
    },
    {
      key: "state",
      header: "Durum",
      type: "badge",
      badge: (a) =>
        a.state === "active"
          ? { tone: "danger", label: "Aktif" }
          : { tone: "neutral", label: "Onaylandı" },
    },
    { key: "device", header: "Cihaz", type: "code", accessor: (a) => deviceTitle(a) },
    {
      key: "status",
      header: "Sinyal",
      type: "badge",
      badge: (a) => ({ tone: statusTone(a.statusCode), label: a.statusLabel ?? "—" }),
    },
    {
      key: "what",
      header: "Olay",
      // Uzun açıklama kolonun ipucunda yaşar: rozete Tooltip bağlanamaz
      // (paketin Tooltip'i etkileşimli tek çocuk ister) ve yalnız hover'da
      // duran bilgi erişilemez bilgidir. Aynı metin satır detayının not
      // panosunda da tam haliyle durur.
      hint: `Doğrulanmamış kayıtlar "${CONFIDENCE_LABEL.provisional}" olarak işaretlenir. ${CONFIDENCE_HINT.provisional}`,
      render: (a) => (
        <span className="flex flex-wrap items-center gap-2">
          <span>{alarmTitle(a)}</span>
          <ConfidenceTag confidence={a.confidence} />
        </span>
      ),
      accessor: (a) => alarmTitle(a),
    },
    { key: "channelNr", header: "Kanal", type: "number", accessor: (a) => sayi(a.channelNr) },
    { key: "cycleNr", header: "Çevrim", type: "number", accessor: (a) => sayi(a.cycleNr) },
    {
      key: "feature",
      header: "Özellik",
      accessor: (a) => a.featureName ?? (a.featureNr != null ? String(a.featureNr) : "—"),
    },
    { key: "limitNr", header: "Limit", type: "number", accessor: (a) => sayi(a.limitNr) },
    // Tepe/eşik ham sayımdır (0..255, ölçek çarpanı yok — rapor Part 5).
    { key: "peak", header: "Aşım", mono: true, accessor: (a) => peakText(a) ?? "—" },
    {
      key: "islemler",
      header: "İşlem",
      type: "actions",
      exportable: false,
      actions: (a) =>
        a.state === "active"
          ? [
              {
                label: `Görüldü işaretle: ${alarmTitle(a)}`,
                icon: <Check size={IKON.sm} />,
                onSelect: () => onToggleAck(a.id),
              },
            ]
          : [
              {
                label: `Onayı geri al: ${alarmTitle(a)}`,
                icon: <Undo2 size={IKON.sm} />,
                onSelect: () => onToggleAck(a.id),
              },
            ],
    },
  ];

  // Satır detayı — telin TAŞIDIĞI ama kolonu OLMAYAN alanlar. Hiçbiri
  // hesaplanmaz, hepsi kayıttan okunur; boş olan "—" görünür.
  const detay = (a: Alarm): Array<DataTablePane<Alarm>> => [
    { label: "Alarm no", value: () => sayi(a.alarmNumber) },
    { label: "Giriş kimliği", value: () => sayi(a.entryId) },
    { label: "Ünite", value: () => (a.unitNo == null ? "—" : `Ünite ${a.unitNo}`) },
    { label: "Yuva", value: () => metin(a.slotName) },
    // Eşik ham sayımdır (0..255); "ham" yazmadan bir "170" fiziksel bir
    // ölçüm gibi okunurdu.
    { label: "Eşik", value: () => (a.level == null ? "—" : `${sayi(a.level)} ham`) },
    {
      label: "Çevrim ofseti",
      value: () => (a.timeOffset == null ? "—" : `${sayi(a.timeOffset)} ms`),
    },
    { label: "Kayıt kimliği", value: () => a.id },
    { label: "Güven", value: () => CONFIDENCE_LABEL[a.confidence] },
    { label: "Not", wide: true, value: () => CONFIDENCE_HINT[a.confidence] },
  ];

  return (
    <PageShell fullWidth title="Alarmlar" description="Aktif ve onaylanmış alarmlar">
      <DataTable<Alarm>
        kicker="Promos3 · alarm kaydı"
        columns={columns}
        rows={rows}
        // Bölmeli süzgeç kendi görünümünü seçtiği için `rows` süzülmüş gelir;
        // "Toplam" istatistiği SÜZÜLMEMİŞ sayıyı söylemeli.
        total={alarms.length}
        getRowId={(a) => a.id}
        segments={[
          { id: "active", label: "Aktif", count: sayimlar.active },
          { id: "all", label: "Tümü", count: sayimlar.all },
          { id: "acknowledged", label: "Onaylanmış", count: sayimlar.acknowledged },
        ]}
        activeSegment={filter}
        onSegmentChange={(id) => setFilter(id as Filter)}
        searchPlaceholder="Olay, cihaz ya da sinyal ara…"
        detail={detay}
        detailLabel="Alarm ayrıntısı"
        // Opaklık kalıcı hiyerarşi kurmaz (ADR-0039): onaylanmış satır
        // soluklaştırılmaz, semantik ton alır ve okunur kalır.
        rowTone={(a: Alarm) => (a.state === "acknowledged" ? "muted" : "default")}
        stickyHeader
        selectable
        bulkActions={(secili: Alarm[]) =>
          secili.some((a) => a.state === "active") ? (
            <Button size="sm" variant="secondary" onClick={onAckAll}>
              Tümünü görüldü işaretle
            </Button>
          ) : null
        }
        // loading DEĞİL refreshing (ADR-0083): itmeli akışta her zaman veri
        // vardır; iskelet, okunan satırın üstünü örterdi.
        refreshing={!paused && live.connected}
        exportable
        exportFilename="alarmlar.csv"
        columnToggle
        // İkon da ton da değişir: yeşil kalkan "her şey yolunda" der ve zincir
        // kopukken bilinen tek şey hiçbir şey bilmediğimizdir.
        emptyIcon={
          bosluk ? (
            <Unplug size={IKON["2xl"]} aria-hidden />
          ) : (
            <ShieldCheck size={IKON["2xl"]} aria-hidden />
          )
        }
        emptyTitle={bosluk ? bosluk.title : "Aktif alarm yok"}
        emptyBody={
          bosluk
            ? `${bosluk.description} Bu ekran alarm olmadığını SÖYLEMİYOR.`
            : "Onaylanan kayıtlar 'Onaylanmış' görünümünde saklanır."
        }
      />
    </PageShell>
  );
}
