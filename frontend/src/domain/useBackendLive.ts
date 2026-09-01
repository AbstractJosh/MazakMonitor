// Backend canlı akış kancası — /api/stream (SSE) tüketicisi.
//
// Backend tam anlık görüntü yayınladığı (delta yok) için bu kanca useLive'daki
// seq/koşu korumalarına muhtaç değildir: her "state" olayı idempotenttir,
// kopup yeniden bağlanınca gelen ilk görüntü zaten günceldir. Koşu sıfırlama
// da backend'de yapılır (adaptör startedAt'i izler).
//
// Yeniden bağlanma: EventSource yalnız AĞ hatasında kendi kendine yeniden
// dener; 200-olmayan HTTP yanıtta (backend kapalıyken dev'de Vite proxy 500,
// prod'da IIS 502/503 döner) spec gereği KALICI kapanır (readyState=CLOSED)
// ve bir daha denemez. Kiosk ekranı sayfa yenilenmeden kendine gelsin diye
// kapalı bağlantı burada zamanlayıcıyla yeniden kurulur.

import { useEffect, useState } from "react";
import { initialLiveState, type LiveState } from "./live";
import {
  liveStateFromWire,
  type BackendPingEvent,
  type BackendStateEvent,
  type BackendStatusEvent,
} from "./backend";
import type { LiveConnection, LiveLink } from "./useLive";

// Kalıcı kapanan (CLOSED) bağlantıyı yeniden kurma aralığı.
const RETRY_MS = 5_000;

/**
 * Tazelik: yaş da eşik de BACKEND'DEN gelir.
 *
 * Burada ne bir sayı sabitlenir ne de `Date.now()` ile bir karşılaştırma
 * yapılır — tarayıcı saatiyle sunucu saati tutmayabilir ve eşiğin ikinci bir
 * kopyası sessizce ayrışırdı. Yaşı sessizlikte nabız taşır (bkz. `ping`),
 * yani kaynak sustuğunda bu değer kendi kendine büyür.
 */
function tazeMi(dataAgeS: number | null, stalenessS: number | null): boolean {
  if (dataAgeS == null || stalenessS == null) return false;
  return dataAgeS <= stalenessS;
}

/**
 * `machineId` null ise akış HİÇ kurulmaz (duraklatma ve kaynaksız tezgah böyle
 * söylenir); doluysa o tezgahın akışına bağlanılır. Aynı origin: dev'de Vite
 * /api'yi backend'e (8001) proxyler (vite.config.ts), prod'da frontend'i zaten
 * backend servis eder.
 */
export function useBackendLive(machineId: string | null): LiveConnection {
  const [state, setState] = useState<LiveState>(initialLiveState);
  const [esOpen, setEsOpen] = useState(false);
  const [status, setStatus] = useState<BackendStatusEvent | null>(null);
  const [frames, setFrames] = useState(0);
  const [dataAgeS, setDataAgeS] = useState<number | null>(null);
  const [stalenessS, setStalenessS] = useState<number | null>(null);

  useEffect(() => {
    if (!machineId) return;
    let es: EventSource | null = null;
    let retryId: number | null = null;
    let disposed = false;

    const connect = () => {
      es = new EventSource(`/api/stream?tezgah=${encodeURIComponent(machineId)}`);
      es.onopen = () => setEsOpen(true);
      es.onerror = () => {
        setEsOpen(false);
        // CONNECTING ise tarayıcı kendisi yeniden deniyordur; CLOSED ise
        // (200-olmayan yanıt) bir daha denemez — biz kurarız.
        if (!disposed && es?.readyState === EventSource.CLOSED) {
          retryId = window.setTimeout(connect, RETRY_MS);
        }
      };
      es.addEventListener("state", (e) => {
        const ev = JSON.parse((e as MessageEvent<string>).data) as BackendStateEvent;
        setState(liveStateFromWire(ev.state));
        setFrames(ev.frames);
        setDataAgeS(ev.dataAgeS);
        setStalenessS(ev.stalenessS);
      });
      es.addEventListener("status", (e) => {
        setStatus(JSON.parse((e as MessageEvent<string>).data) as BackendStatusEvent);
      });
      // Nabız yalnız "bağlantı ayakta" demez, YAŞI da taşır. Kaynak
      // sustuğunda "state" çerçevesi hiç doğmaz; bu dinleyici olmasaydı üst
      // bardaki "Veri Akışı Aktif" ilk kareden sonra sonsuza dek kalırdı.
      es.addEventListener("ping", (e) => {
        const ev = JSON.parse((e as MessageEvent<string>).data) as BackendPingEvent;
        setDataAgeS(ev.dataAgeS);
      });
    };

    connect();
    return () => {
      disposed = true;
      if (retryId !== null) window.clearTimeout(retryId);
      es?.close();
      setEsOpen(false);
      setStatus(null);
      // Tezgah değişince önceki tezgahın sayaçları taşınmasın: canlılık ölçüsü
      // tezgaha aittir, kancaya değil.
      setFrames(0);
      setDataAgeS(null);
      setStalenessS(null);
    };
  }, [machineId]);

  // İki halka ayrı raporlanır ki hata mesajı doğru halkayı suçlasın:
  // akış (tarayıcı↔backend SSE) ve kaynak (backend↔ağ geçidi / simülatör /
  // CSV okuma görevi).
  const link: LiveLink = !esOpen
    ? "stream-down"
    : status?.connected
      ? "ok"
      : "source-down";

  return {
    connected: link === "ok",
    link,
    // Kaynak kimliği status olayından gelir; henüz gelmediyse null (kabuk onu
    // katalogdan tamamlar — bkz. uygulama-kabugu).
    source: status?.source ?? null,
    frames,
    dataAgeS,
    dataFresh: tazeMi(dataAgeS, stalenessS),
    state,
  };
}
