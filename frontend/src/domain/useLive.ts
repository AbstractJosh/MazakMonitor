// Canlı akış kancası — ekranların tek giriş kapısı.
//
// Tek kaynak vardır: backend /api/stream (SSE). Backend, Prometec Promos3
// telgrafını çözüp alan modelini hazır yayınlar. Eskiden burada ikinci bir
// kaynak (MazakFolly'ye doğrudan 9001 bağlantısı) ve onu seçen bir
// yapılandırma anahtarı (VITE_LIVE_SOURCE) vardı; ikisi de kaldırıldı.

import type { LiveState } from "./live";
import type { SourceKind } from "./katalog";
export { useBackendLive as useLive } from "./useBackendLive";

/**
 * Akış zincirinin durumu — hata mesajı doğru halkayı suçlayabilsin diye
 * "bağlı değil" tek bayrağa indirgenmez:
 *   "ok"          → zincir sağlam;
 *   "stream-down" → tarayıcı /api/stream'e ulaşamıyor (backend kapalı?);
 *   "source-down" → akış açık ama backend kendi kaynağına (Promos3 gateway /
 *                   simülatör) ulaşamıyor;
 *   "no-source"   → seçilen tezgahın arkasında kaynak YOK (arıza değil,
 *                   yapılandırma: katalogdan gelir, bkz. domain/katalog.ts).
 *                   Bu hâlde akış hiç kurulmaz ve ekrana BOŞ durum verilir —
 *                   başka bir tezgahın son karesi bu tezgahın adı altında
 *                   görünmesin;
 *   "catalog-loading" → katalog HENÜZ gelmedi, yani bu tezgahın kaynağı olup
 *                   olmadığı BİLİNMİYOR. "no-source" ile karıştırılmaz: biri
 *                   yapılandırma İDDİASI, öbürü bilgisizliktir ve ikisini tek
 *                   duruma indirmek ekrana bilmediği bir şeyi söyletirdi;
 *   "catalog-down" → katalog alınamadı (GET /api/machines). Kaynak bağlaması
 *                   öğrenilemediği için akış hiç kurulmaz. Kabuk katalogu
 *                   YOKLAMAZ (bkz. useKatalog `pollMs`), yani bu durum kendi
 *                   kendine düzelmez — ekran tekrar denemeyi SUNMAK zorundadır.
 */
export type LiveLink =
  | "ok"
  | "stream-down"
  | "source-down"
  | "no-source"
  | "catalog-loading"
  | "catalog-down";

/** Canlı bağlantı — ekranlar yalnız bunu görür. */
export interface LiveConnection {
  /** Akış zinciri sağlam mı (link === "ok" kısayolu). */
  connected: boolean;
  /** Zincirin hangi halkası kopuk (hata mesajları için). */
  link: LiveLink;
  /**
   * Bu akışın arkasındaki kaynağın kimliği; bilinmiyorsa null.
   *
   * Hata metni doğru kaynağı ADLANDIRABİLSİN diye taşınır: "Promos3 ağ
   * geçidinden veri gelmiyor" cümlesi A/3'te (CSV) ve A/2'de (simülatör)
   * olmayan bir cihazı suçluyordu.
   */
  source: SourceKind | null;
  /**
   * Backend'in uyguladığı yük sayısı; 0 ise henüz HİÇ veri gelmemiş.
   *
   * "ŞU AN veri geliyor mu" sorusunun cevabı DEĞİLDİR (geri saymaz) — o
   * `dataFresh`tir.
   */
  frames: number;
  /** Son verinin yaşı (saniye), backend'de hesaplanır; null = hiç gelmedi. */
  dataAgeS: number | null;
  /**
   * Veri ŞU AN akıyor mu — backend'in eşiğine göre (telden gelir, istemci
   * kendi saatiyle kıyaslamaz).
   */
  dataFresh: boolean;
  /** Akıştan türetilen canlı durum. */
  state: LiveState;
}
