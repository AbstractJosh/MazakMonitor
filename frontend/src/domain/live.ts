// Canlı durum — ekranların tek veri sözleşmesi.
//
// TEK KAYNAK: backend /api/stream. Backend, Prometec Promos3 telgrafını
// (CAN-over-UDP) çözer ve alan modelini HAZIR yayınlar; ham tel biçimi
// tarayıcıya sızmaz. Bu yüzden burada artık eşleyici yoktur — yalnız şekil.
//
// Eskiden bu dosya MazakFolly log satırlarını tarayıcıda çözerdi (program,
// çevrim, NC nabzı). O kaynak kaldırıldı: taşıdığı alanların tel üzerinde
// karşılığı yoktu, dolayısıyla alanların kendisi de kaldırıldı — hiç
// dolmayacak bir alanı taşımak ekranda kalıcı bir "—" üretmekten başka işe
// yaramaz.
//
// backend/app/domain.py bu dosyanın Python karşılığıdır.

import type { Alarm, EventRow, Feature, UnitInfo, WireStats } from "./types";

// Tezgah adı burada DEĞİLDİR: adlar yapılandırmadır ve backend'den gelen
// tesis/tezgah kataloğunda durur (domain/katalog.ts). Bu dosya yalnız AKIŞTAN
// türeyen şekli tanımlar.

/** Listelerde tutulan en fazla kayıt (en yeniler kalır). */
export const EVENT_LIMIT = 500;

/** Akıştan türetilen canlı durum — ekranların tek veri kaynağı. */
export interface LiveState {
  /** Çevrim numarası (MC_GIVESTATUS / SAMMELMERKMALE im satırları). */
  cycle: number | null;
  /** İş parçası sayacı — im satırı her yeni parçada artar. */
  workpiece: number | null;
  /** PLC giriş/çıkış bit haritaları (MC_GIVEPLCVALUES). */
  plcInputs: number | null;
  plcOutputs: number | null;
  units: UnitInfo[];
  features: Feature[];
  alarms: Alarm[];
  events: EventRow[];
  /** Taşıma/çözme teşhisi — kaynak adaptörü etkinken dolar. */
  wire: WireStats | null;
}

/**
 * Boş başlangıç durumu.
 *
 * ÖNCEDEN TANIMLI GRAFİK YOKTUR: özellikler ve adları TELDEN gelir
 * (MC_GIVEKANAL, +0x4D özellik yuvaları). Yer tutucu grafik açmak, akış
 * gelmeden önce ekranda "veri var" izlenimi verirdi.
 */
export function initialLiveState(): LiveState {
  return {
    cycle: null,
    workpiece: null,
    plcInputs: null,
    plcOutputs: null,
    units: [],
    features: [],
    alarms: [],
    events: [],
    wire: null,
  };
}
