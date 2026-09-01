// Tesis / tezgah kataloğu — backend'den gelir (`GET /api/machines`).
//
// Katalog ARTIK BURADA DOĞMAZ (eski `facilities.ts` onu üretiyordu): üç
// kaynak geldiğinde tezgah→kaynak bağlaması zaten backend'de olmak zorunda,
// ve katalogu burada da tutmak aynı bağlamayı iki yerde tutmak olurdu.
//
// Backend ekran METNİ göndermez, kaynak KİMLİĞİ gönderir; okunur karşılığı
// aşağıdaki `KAYNAK_ADI` haritasındadır.

import { useCallback, useEffect, useState } from "react";

/** Kaynak kimliği — `provis` ile `promos3-sim` aynı teli konuşur, aynı şey değildir. */
export type SourceKind = "provis" | "promos3-sim" | "csv";

export interface Machine {
  id: string;
  name: string;
  /**
   * Makine modeli, biliniyorsa.
   *
   * Katalog ucu akış ucundan FARKLI davranır: `/api/stream` boş opsiyonelleri
   * telde hiç göndermez (exclude_none, bkz. backend.ts), `/api/machines` ise
   * `null` gönderir. Ölçüldü — `model: null` gelir, alan eksik gelmez.
   */
  model: string | null;
  /** Kaynak yoksa null — bu bir arıza değil, yapılandırmadır. */
  source: SourceKind | null;
  sourcePort: number | null;
  /**
   * Kaynak adaptörünün HALKASI ayakta mı: UDP soketi bağlı / CSV okuma
   * görevi koşuyor.
   *
   * "VERİ GELİYOR" DEMEK DEĞİLDİR. `PROMOS3_BIND=127.0.0.1` ile koşan bu
   * makinede A/1'in soketi sonsuza dek bağlıdır ve gerçek ağ geçidinden tek
   * bayt gelmez. Yeşil rozetin ölçütü bu alan değil `dataAgeS`tir.
   */
  connected: boolean;
  /**
   * Son verinin yaşı (saniye), BACKEND'DE hesaplanır; null = hiç veri
   * gelmedi.
   *
   * Mutlak an değil YAŞ gelir: tarayıcı saatiyle sunucu saati tutmayabilir,
   * istemci tazeliği kendi saatinden tahmin etmemeli. Eşik `Katalog.stalenessS`.
   */
  dataAgeS: number | null;
}

export interface Facility {
  id: string;
  name: string;
  machines: Machine[];
}

export interface Katalog {
  facilities: Facility[];
  /**
   * Verinin "taze" sayıldığı en büyük yaş (saniye) — backend'in eşiği
   * (hub.DATA_STALE_AFTER_S). Sayının tek sahibi backend'dir; burada
   * kopyalanmaz, telden okunur.
   */
  stalenessS: number;
}

/** Kaynağın okunur adı (kart etiketi). Arayüz metni arayüzün işidir. */
export const KAYNAK_ADI: Record<SourceKind, string> = {
  provis: "PROVIS ağ geçidi",
  "promos3-sim": "Simülatör — değerler sentetiktir",
  csv: "CSV tekrar oynatma",
};

/**
 * Kaynağın CÜMLE İÇİNDEKİ adı — "… kuramadı" gibi metinlerde geçer.
 *
 * `KAYNAK_ADI` bir ETİKETTİR ve cümleye girmez: "Simülatör — değerler
 * sentetiktir dinleyicisi kurulmadı" okunmaz bir cümle olurdu. Hata metninin
 * doğru kaynağı adlandırması bu projede pazarlık konusu değil (aynı ekran
 * daha önce CSV tezgahındaki bir kesintiyi Promos3 ağ geçidine yıkıyordu),
 * o yüzden iki biçim de ayrı ayrı tutulur.
 */
export const KAYNAK_CUMLEDE: Record<SourceKind, string> = {
  provis: "PROVIS ağ geçidi",
  "promos3-sim": "simülatör",
  csv: "CSV tekrar oynatması",
};

/**
 * Veri ŞU AN akıyor mu — "hiç aktı mı" değil.
 *
 * Yaş da eşik de backend'den gelir; burada ne bir sayı sabitlenir ne de
 * `Date.now()` ile karşılaştırma yapılır (tarayıcı saatiyle sunucu saati
 * tutmayabilir). `Number.isFinite` eşiği hiç gelmeyen bir cevaba karşı
 * KAPALI tarafa düşer: bilinmeyen eşikle "canlı" demektense "veri bekleniyor"
 * demek yeğdir.
 */
export function veriTaze(m: Machine, stalenessS: number): boolean {
  return m.dataAgeS != null && Number.isFinite(stalenessS) && m.dataAgeS <= stalenessS;
}

export type KatalogDurum = "loading" | "ready" | "error";

/**
 * Katalog kancası.
 *
 * `pollMs` verilirse `connected` tazeliği için düzenli yeniden çekilir —
 * karşılama ekranı bunu kullanır. İzleme ekranlarında gerekmez: oradaki
 * bağlantı durumunu SSE `status` olayı zaten taşır.
 */
export function useKatalog(pollMs?: number) {
  const [katalog, setKatalog] = useState<Katalog | null>(null);
  const [durum, setDurum] = useState<KatalogDurum>("loading");

  const cek = useCallback(async (signal?: AbortSignal) => {
    try {
      const r = await fetch("/api/machines", { signal });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setKatalog((await r.json()) as Katalog);
      setDurum("ready");
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      // Boş katalogla devam ETMEK yanlış olurdu: "hiç tezgah yok" diye
      // okunurdu. Hata durumu ayrı taşınır.
      setDurum("error");
    }
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    void cek(ac.signal);
    if (!pollMs) return () => ac.abort();
    const id = window.setInterval(() => void cek(ac.signal), pollMs);
    return () => {
      ac.abort();
      window.clearInterval(id);
    };
  }, [cek, pollMs]);

  return { katalog, durum, yenile: () => void cek() };
}

export function findFacility(k: Katalog | null, id: string): Facility | undefined {
  return k?.facilities.find((f) => f.id === id);
}

export function findMachine(k: Katalog | null, id: string): Machine | undefined {
  for (const f of k?.facilities ?? []) {
    const m = f.machines.find((x) => x.id === id);
    if (m) return m;
  }
  return undefined;
}

/** Başlıklarda kullanılan tam ad: "Tesis A · Tezgah 1". */
export function machineTitle(facility: Facility, machine: Machine): string {
  return `${facility.name} · ${machine.name}`;
}
