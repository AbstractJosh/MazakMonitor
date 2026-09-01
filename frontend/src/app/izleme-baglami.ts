// Kabuk → ekran sözleşmesi.
//
// Akış kabukta yaşar (ekran değişimi bağlantıyı düşürmemeli), ekranlar onu
// yönlendiricinin outlet bağlamından okur. Prop zinciri yerine bağlam: araya
// giren rota bileşenlerinin taşıyıcı olmaktan başka işi olmazdı.

import { useOutletContext } from "react-router-dom";
import type { Alarm, EventRow } from "@/domain/types";
import type { LiveConnection } from "@/domain/useLive";

export interface IzlemeBaglami {
  /** Canlı bağlantı — kaynağı olmayan tezgahta boş durum taşır. */
  live: LiveConnection;
  /**
   * Tezgah katalogunu yeniden çeker.
   *
   * Kabuk katalogu YOKLAMAZ, yani `link === "catalog-down"` kendi kendine
   * düzelmez; ekranın kullanıcıya bir çıkış yolu sunabilmesi için gerekir.
   * Sayfayı yenilemek de düzeltirdi ama onay damgaları istemcide tutulur
   * (ADR-0004) ve yenileme onları silerdi.
   */
  katalogYenile: () => void;
  /** Onay damgası bindirilmiş alarmlar (istemci tarafı "görüldü"). */
  alarms: Alarm[];
  /** Yalnız aktif olanlar — zil sayacı ve sayfa üstü uyarı bunu kullanır. */
  active: Alarm[];
  events: EventRow[];
  paused: boolean;
  /** Aktif ↔ onaylandı arası geçiş; aynı düğme onayı geri de alır. */
  onToggleAck: (id: string) => void;
  onAckAll: () => void;
  /** featureId → kullanıcının verdiği grafik adı. */
  graphTitles: Record<string, string>;
  onRenameGraph: (id: string, name: string) => void;
  /**
   * ÜST limit sapması (%) — karşılama ekranında seçilir, adres çubuğunda
   * taşınır. CSV grafiklerinde üst eşik = ortalama × (1 + sapma/100); telden
   * eşik alan tezgahlarda kullanılmaz. Bkz. domain/esik.ts.
   */
  sapma: number;
  /**
   * ALT limit sapması (%) — alt eşik = ortalama × (1 − altSapma/100).
   * YALNIZ CSV'de anlamlıdır: telde alt sınır diye bir şey yok.
   */
  altSapma: number;
}

export function useIzleme(): IzlemeBaglami {
  return useOutletContext<IzlemeBaglami>();
}
