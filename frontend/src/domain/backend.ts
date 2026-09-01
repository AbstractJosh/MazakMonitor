// Backend /api/stream sözleşmesi — tel tipleri + saf eşleme.
//
// Backend, alan modelini (types.ts sözleşmesi) hazır halde yayınlar; ham kaynak
// biçimi (Prometec CAN-over-UDP telgrafı) buraya SIZMAZ — çözme backend'de
// yapılır (backend/app/promos3/*).

import type { Alarm, EventRow, Feature, UnitInfo, WireStats } from "./types";
import type { LiveState } from "./live";
import type { SourceKind } from "./katalog";

/** /api/stream "state" olayının verisi: sürüm sayacı + akış canlılığı + tam anlık görüntü. */
export interface BackendStateEvent {
  seq: number;
  /**
   * Backend'in uyguladığı yük sayısı — KAYNAKTAN BAĞIMSIZ canlılık ölçüsü.
   *
   * `wire.parsed` yalnız Promos3 taşımasını sayar; CSV tezgahının teli
   * olmadığı için orada hep 0 kalır ve üst bar kusursuz akan bir tezgahta
   * "Veri Yok" yazardı.
   *
   * DİKKAT: bu sayaç "HİÇ geldi mi" sorusunu cevaplar, "ŞU AN geliyor mu"
   * sorusunu DEĞİL — bir kez arttı mı bir daha azalmaz. İkincisi `dataAgeS`.
   */
  frames: number;
  /**
   * Son uygulanan yükün üzerinden geçen saniye, BACKEND'DE hesaplanır;
   * null = bu tezgaha hiç veri gelmedi.
   *
   * Mutlak an değil YAŞ gelir: tarayıcı saatiyle sunucu saati tutmayabilir.
   */
  dataAgeS: number | null;
  /** Tazelik eşiği (saniye) — backend'in `hub.DATA_STALE_AFTER_S` sabiti. */
  stalenessS: number;
  state: WireLiveState;
}

/**
 * /api/stream "ping" olayı — sessizliği canlı tutan nabız.
 *
 * YAŞI DA TAŞIR: kaynak sustuğunda "state" çerçevesi hiç doğmaz, yani
 * istemci son gördüğü yaşla kalır ve "Veri Akışı Aktif" kalıcılaşırdı.
 */
export interface BackendPingEvent {
  /** Sunucu saati (ms) — teşhis için; tazelik hesabına GİRMEZ. */
  tMs: number;
  dataAgeS: number | null;
}

/**
 * LiveState'in tel biçimi (backend domain.LiveState, camelCase).
 *
 * Backend boş opsiyonelleri telde HİÇ göndermez (exclude_none): serialNo,
 * limitLevel, statusCode ve buradaki boş alanlar undefined olarak gelir —
 * "değer yok" ile "değer null" aynı şekle düşmesin diye.
 */
export interface WireLiveState {
  cycle?: number;
  workpiece?: number;
  plcInputs?: number;
  plcOutputs?: number;
  units: UnitInfo[];
  features: Feature[];
  alarms: Alarm[];
  events: EventRow[];
  /** Taşıma/çözme teşhisi — yalnız kaynak adaptörü etkinken gelir. */
  wire?: WireStats;
}

/** /api/stream "status" olayı: backend'in kaynak bağlantısı. */
export interface BackendStatusEvent {
  /**
   * Bu tezgahın kaynağının KİMLİĞİ — backend katalogdaki `source.kind`ı
   * gönderir (machines.py `SourceKind`), yani katalog.ts'in ilan ettiği üç
   * kimliğin aynısı.
   *
   * Eskiden burada `string` yazıyordu ve yorum "promos3 ya da none" diyordu;
   * ikisi de yanlıştı. Tip bunu söylemediği için hata metinleri kaynağı
   * adlandıramıyor, CSV tezgahındaki bir kesinti "Promos3 ağ geçidi" diye
   * raporlanıyordu.
   */
  source: SourceKind;
  /**
   * Kaynak adaptörünün halkası ayakta mı (soket bağlı / okuma görevi
   * koşuyor). "Veri geliyor" demek DEĞİLDİR — onu `dataAgeS` söyler.
   */
  connected: boolean;
  /** Kaynak başına bağlantı durumu — hangi halkanın kopuk olduğunu söyler. */
  sources?: Record<string, boolean>;
}

/** Tel durumunu ekran durumuna çevirir (undefined → null). */
export function liveStateFromWire(wire: WireLiveState): LiveState {
  return {
    cycle: wire.cycle ?? null,
    workpiece: wire.workpiece ?? null,
    plcInputs: wire.plcInputs ?? null,
    plcOutputs: wire.plcOutputs ?? null,
    units: wire.units,
    features: wire.features,
    // exclude_none boş listeleri değil yalnız None'ları atar; yine de eski bir
    // backend sürümü alanı hiç göndermezse ekran çökmesin.
    alarms: wire.alarms ?? [],
    events: wire.events ?? [],
    wire: wire.wire ?? null,
  };
}
