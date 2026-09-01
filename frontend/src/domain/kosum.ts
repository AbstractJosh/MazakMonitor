// Tam koşum kaydı — CSV korpusunun TAMAMI (`GET /api/kosum`).
//
// CANLI YOLLA İLGİSİ YOKTUR ve ona dokunmaz: canlı ekran hub'dan SSE ile
// beslenir ve KAYAN BİR PENCERE gösterir (120 örnek), bu uç ise dosyaları
// baştan sona okur — koşumda 131 an var, yani canlı ekran koşumun tamamını
// hiçbir zaman göstermez. Kaydın kendisi statiktir: bir kez çekilir, yoklanmaz.

import { useCallback, useEffect, useState } from "react";

export interface KosumSeries {
  /** Backend `csv_live.csv_feature_id` ile AYNI kimlik: `csv:10660:1`. */
  id: string;
  unitNo: number;
  slot: number;
  /** CSV kolon başlığından gelir (kuruluma özel), koda gömülmez. */
  name: string;
  /** Yuvanın KOŞUM BOYU ortalaması (backend/app/sim/baselines.py ile aynı tanım). */
  baseline: number;
  minValue: number;
  maxValue: number;
  /** Kaç anda okundu — `Kosum.count`tan küçükse iz kopukludur. */
  count: number;
}

export interface KosumRow {
  /** Takvim günü `YYYY-MM-DD` — AN DEĞİL (ADR-0005). */
  day: string;
  /** Günün saati `HH:MM:SS` — duvar saati, saat dilimi taşımaz. */
  time: string;
  /**
   * Seri kimliği → değer.
   *
   * OKUNMAYAN YUVA ANAHTARSIZDIR: 0 yazmak, hiç ölçülmemiş bir yuvayı sıfır
   * ölçülmüş gibi çizerdi.
   */
  values: Record<string, number>;
}

export interface Kosum {
  /** Koşumun ilk/son anı. Boş korpusta hepsi null; ekran bir şey iddia etmez. */
  startDay: string | null;
  startTime: string | null;
  endDay: string | null;
  endTime: string | null;
  /** Gerçekten okunabilen an sayısı. */
  count: number;
  series: KosumSeries[];
  rows: KosumRow[];
}

/**
 * `yok` ARIZA DEĞİLDİR: bu tezgahın kaynağı CSV değil, yani kayıtlı koşumu da
 * yoktur (yapılandırma). `error`la aynı sepete koymak "tekrar dene" dedirtirdi
 * — kabuktaki `no-source` ile aynı ayrım.
 */
export type KosumDurum = "loading" | "ready" | "yok" | "error";

/**
 * Hatanın KİMDEN geldiği.
 *
 * Backend `/api/kosum`ta iki ayrı arızayı ayırır: ağ/sunucu hiç cevap vermez,
 * ya da sunucu cevap verip "CSV kaynağı okunamadı" der (503). İkisini tek
 * metne indirmek — "Backend'e ulaşılamadı" — `veri/`si eksik deploy edilmiş
 * bir kurulumda YANLIŞ SUÇLAMADIR ve kullanıcıyı sunucuya baktırırken sorun
 * dosyalarda durur.
 *
 * Bu projede hata metninin doğru kaynağı adlandırması pazarlık konusu değil:
 * aynı ekran daha önce CSV tezgahındaki bir kesintiyi Promos3 ağ geçidine
 * yıkmıştı (bkz. katalog.ts `KAYNAK_CUMLEDE`).
 */
export interface KosumHata {
  /** Sunucu CEVAP VERDİ mi — verdiyse suçlu ağ değil, kaynaktır. */
  cevapVerdi: boolean;
  /** Sunucunun kendi açıklaması (`detail`); okunamadıysa null. */
  detay: string | null;
}

/** Koşum kancası — tek atışlık, yoklama yok (kayıt süreç boyunca değişmez). */
export function useKosum(machineId: string) {
  const [kosum, setKosum] = useState<Kosum | null>(null);
  const [durum, setDurum] = useState<KosumDurum>("loading");
  const [hata, setHata] = useState<KosumHata | null>(null);

  const cek = useCallback(
    async (signal?: AbortSignal) => {
      setDurum("loading");
      try {
        const r = await fetch(`/api/kosum?tezgah=${encodeURIComponent(machineId)}`, {
          signal,
        });
        if (r.status === 404) {
          setDurum("yok");
          return;
        }
        if (!r.ok) {
          // Sunucu CEVAP VERDİ; gövdesindeki `detail` neyin okunamadığını
          // söyler. Gövde okunamazsa da suçlu yine sunucu değil kaynaktır —
          // `cevapVerdi` cevabın kendisinden bilinir, gövdesinden değil.
          setHata({ cevapVerdi: true, detay: await detayOku(r) });
          setDurum("error");
          return;
        }
        setKosum((await r.json()) as Kosum);
        setDurum("ready");
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        // Boş koşumla devam ETMEK yanlış olurdu: "kayıt boşmuş" diye
        // okunurdu. Hata durumu ayrı taşınır (katalog.ts ile aynı kural).
        setHata({ cevapVerdi: false, detay: null });
        setDurum("error");
      }
    },
    [machineId],
  );

  useEffect(() => {
    const ac = new AbortController();
    void cek(ac.signal);
    return () => ac.abort();
  }, [cek]);

  return { kosum, durum, hata, yenile: () => void cek() };
}

/** Hata gövdesindeki `detail` — okunamazsa null, çünkü uydurulmuş bir açıklama
 *  hiç açıklama olmamasından kötüdür. */
async function detayOku(r: Response): Promise<string | null> {
  try {
    const govde: unknown = await r.json();
    const detay = (govde as { detail?: unknown }).detail;
    return typeof detay === "string" ? detay : null;
  } catch {
    return null;
  }
}

/** Koşum tek gün mü sürdü — eksen etiketinin tarih taşıyıp taşımayacağını belirler. */
export function tekGun(k: Kosum): boolean {
  return k.startDay != null && k.startDay === k.endDay;
}
