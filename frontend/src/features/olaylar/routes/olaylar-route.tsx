// Olaylar — izleme sırasında düşen kayıt satırları (CONTEXT: Olay / event).
// Geçmiş ve raporların ham malzemesi.
//
// Satırların kaynağı Promos3 telgrafıdır:
//   • Ölçüm bloğundaki im satırları (0x16) → yeni çevrim / yeni iş parçası
//   • Prometec olay kaydı (rapor 4.4) → eventNumber + EventCode + kanal
// Filtre seçenekleri akışta GERÇEKTEN görülen değerlerden üretilir; sabit liste
// yoktur (uydurulmuş sütun/seçenek bu ekranın baştan beri kaçındığı hatadır).

import { useMemo } from "react";
import {
  DataGrid,
  EmptyState,
  PageShell,
  formatDateTime,
  IKON,
  type DataTableColumn,
} from "@alp/design-system";
import { FileSearch, Unplug } from "lucide-react";
import { useIzleme } from "@/app/izleme-baglami";
import type { EventRow } from "@/domain/types";
import { baglantiBoslugu } from "@/domain/baglanti-bosluk";
import { CONFIDENCE_HINT, CONFIDENCE_LABEL, eventTitle, hex, sayi } from "@/domain/format";

export default function OlaylarRoute() {
  const { events, paused, live } = useIzleme();

  // "Henüz olay yok" cümlesi bir GÖZLEMDİR ve gözleyecek bir akış olmasını
  // gerektirir. Zincir kopukken (kaynaksız tezgah, katalog düşmüş, akış
  // kopmuş) geçmiş boş değil BİLİNMEZDİR — "henüz" demek, birazdan geleceğini
  // ima ederek olmayan bir akış vaat ediyordu. Metin üç ekranda ortaktır
  // (domain/baglanti-bosluk.ts).
  const bosluk = baglantiBoslugu(live.link, live.source);

  // Süzgeç seçenekleri akışta görülen değerlerden; sıra sabit olsun diye
  // sıralanır (kolon menüsü her karede yeniden dizilmesin).
  const olaySecenekleri = useMemo(() => {
    const seen = new Map<number, string>();
    for (const e of events) {
      if (e.code != null && !seen.has(e.code)) seen.set(e.code, eventTitle(e));
    }
    return [...seen].sort((a, b) => a[0] - b[0]).map(([, label]) => label);
  }, [events]);

  const uniteSecenekleri = useMemo(
    () =>
      Array.from(new Set(events.map((e) => e.unitNo).filter((u): u is number => u != null)))
        .sort((a, b) => a - b)
        .map((u) => `Ünite ${u}`),
    [events],
  );

  const columns: Array<DataTableColumn<EventRow>> = [
    {
      key: "time",
      header: "Zaman",
      mono: true,
      sortable: true,
      render: (e) => formatDateTime(e.time),
      accessor: (e) => e.time,
    },
    {
      key: "what",
      header: "Olay",
      filterable: true,
      filterOptions: olaySecenekleri,
      hint: `Doğrulanmamış kayıtlar "${CONFIDENCE_LABEL.provisional}" olarak işaretlenir. ${CONFIDENCE_HINT.provisional}`,
      accessor: (e) => eventTitle(e),
    },
    {
      // Hex kod yalnız hem kod hem etiket varken anlamlıdır: etiketsiz ham kod
      // kanıttır, karar sütunu değil — bu yüzden varsayılan KAPALI (ADR-0071).
      key: "code",
      header: "Kod",
      type: "code",
      defaultHidden: true,
      accessor: (e) => (e.code != null && e.codeLabel ? hex(e.code) : "—"),
    },
    {
      key: "unitNo",
      header: "Ünite",
      filterable: true,
      filterOptions: uniteSecenekleri,
      accessor: (e) => (e.unitNo != null ? `Ünite ${e.unitNo}` : "—"),
    },
    { key: "channelNr", header: "Kanal", type: "number", accessor: (e) => sayi(e.channelNr) },
    {
      key: "eventNumber",
      header: "Olay No",
      type: "number",
      accessor: (e) => sayi(e.eventNumber),
    },
    {
      key: "workpiece",
      header: "İş Parçası",
      type: "code",
      accessor: (e) => e.workpiece ?? "—",
    },
    {
      key: "cycleNr",
      header: "Çevrim",
      type: "number",
      defaultHidden: true,
      accessor: (e) => sayi(e.cycleNr),
    },
  ];

  return (
    <PageShell
      fullWidth
      title="Olaylar"
      description="İzleme geçmişi — raporların ham malzemesi"
    >
      <DataGrid<EventRow>
        columns={columns}
        rows={events}
        getRowId={(e) => e.id}
        searchable
        searchPlaceholder="Olay ya da iş parçası ara…"
        pageSize={25}
        stickyHeader
        columnToggle
        exportable
        exportFilename="olaylar.csv"
        refreshing={!paused && live.connected}
        emptyState={
          bosluk ? (
            <EmptyState
              icon={<Unplug size={IKON["2xl"]} />}
              title={bosluk.title}
              description={`${bosluk.description} Bu ekran olay yaşanmadığını SÖYLEMİYOR.`}
            />
          ) : (
            <EmptyState
              icon={<FileSearch size={IKON["2xl"]} />}
              title="Henüz olay yok"
              description="Akıştan olay kaydı geldikçe burada listelenir."
            />
          )
        }
      />
    </PageShell>
  );
}
