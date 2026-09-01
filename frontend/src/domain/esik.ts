// Eşik: çizilen limit çizgisi ve yüzde rozeti TEK yerden hesaplanır.
//
// İKİ AYRI EŞİK KAYNAĞI VAR ve karıştırılmaz:
//
//   Promos3 (provis / promos3-sim)  eşik TELDEN gelir → `limitLevel`.
//                                   Üreticinin koyduğu gerçek eşiktir,
//                                   dokunulmaz.
//   CSV (csv)                       tel yok. Backend o özelliğin TÜM CSV
//                                   değerlerinin ortalamasını yollar
//                                   (`baseline`), BANDI bu ekran kurar:
//                                   üst = ortalama × (1 + sapma/100)
//                                   alt = ortalama × (1 − altSapma/100)
//
// BANDIN ALT UCU YALNIZ CSV'DE VARDIR. Telde limit ALT+ÜST bandı değil, tipli
// TEK eşiktir; oradan bir alt sınır türetmek telin söylemediğini söylemek olur.
//
// SAPMA NEDEN İSTEMCİDE: backend'in hub'ı tek durumu BÜTÜN abonelere yayınlar.
// Yüzde sunucuda tutulsaydı bir kullanıcının seçimi diğerlerinin ekranını
// değiştirirdi. Backend olguyu (ortalama) yollar, tercih burada uygulanır.
//
// CSV'NİN KENDİ LİMİTİ NEDEN KULLANILMIYOR: ölçüldü — 10665 ünitesinde CSV'nin
// `Limit` kolonu izin dörtte biri kadar (M08 DEBI: limit 50, ortalama 224,1).
// Çizgi grafiğin tabanına yapışıyor, rozet kalıcı olarak %448 okuyordu.
// Gerekçenin tamamı backend/app/sim/baselines.py'de.

import type { Feature } from "@/domain/types";

/** ÜST limit sapması — ortalamanın bu kadar ÜSTÜ. Karşılamadan değiştirilir. */
export const SAPMA_VARSAYILAN = 10;
/** ALT limit sapması — ortalamanın bu kadar ALTI (varsayılan %20 → ort. ×0,80). */
export const ALT_SAPMA_VARSAYILAN = 20;
export const SAPMA_MIN = 0;
export const SAPMA_MAX = 100;

/**
 * Adres çubuğundan gelen sapmayı okur.
 *
 * Elle yazılmış/bozuk değer SESSİZCE 0 OLMAZ: `Number("")` sıfır döner ve
 * sıfır sapma "eşik = ortalama" demektir — yani okunamayan bir girdi, izin tam
 * ortasından geçen bir limit çizgisi üretirdi. Okunamayan her hâl varsayılana
 * düşer.
 */
export function sapmaOku(raw: string | null, varsayilan = SAPMA_VARSAYILAN): number {
  if (raw == null || raw.trim() === "") return varsayilan;
  const n = Number(raw);
  if (!Number.isFinite(n)) return varsayilan;
  return Math.min(SAPMA_MAX, Math.max(SAPMA_MIN, n));
}

/** ÜST eşik: CSV'de ortalama + sapma, telde limit Level. Yoksa null. */
export function esik(f: Feature, sapmaPct: number): number | null {
  if (f.baseline != null) return f.baseline * (1 + sapmaPct / 100);
  return f.limitLevel ?? null;
}

/**
 * ALT eşik: ortalama − sapma. YALNIZ tabanı olan (CSV) özellikte vardır.
 *
 * TELDE ALT LİMİT YOKTUR ve uydurulmaz: Promos3'te limit ALT+ÜST BANDI DEĞİL,
 * tipli TEK eşiktir (domain.py'deki FeatureLimit notu — Limits tablosu
 * Limtype/Level/Feat_Num). Oradaki tek sayıdan bir alt sınır türetmek, telin
 * söylemediği bir şeyi söylemek olurdu.
 */
export function altEsik(f: Feature, altSapmaPct: number): number | null {
  if (f.baseline == null) return null;
  return f.baseline * (1 - altSapmaPct / 100);
}

/** Bandın dışına çıkıldıysa HANGİ yönde; içerideyse (ya da eşik yoksa) null. */
export type BandDurumu = "ustunde" | "altinda";

/**
 * Değer bandın dışında mı.
 *
 * Sınıra DEĞMEK de ihlaldir (`>=` / `<=`): eski davranış `pct >= 100` idi,
 * yani tam eşikteki değer zaten kırmızıydı ve alt sınır da simetrik olmalı.
 *
 * Telden beslenen özellikte `alt` null olduğu için yalnız "ustunde" çıkabilir —
 * bugünkü davranışın aynısı.
 */
export function bandDurumu(
  f: Feature,
  sapmaPct: number,
  altSapmaPct: number,
): BandDurumu | null {
  if (f.current == null) return null;
  const ust = esik(f, sapmaPct);
  const alt = altEsik(f, altSapmaPct);
  if (ust != null && f.current >= ust) return "ustunde";
  if (alt != null && f.current <= alt) return "altinda";
  return null;
}

/** Rozet metni — hangi sınırın aşıldığını AÇIKÇA yazar. */
export const BAND_ETIKETI: Record<BandDurumu, string> = {
  ustunde: "üst limit üstünde",
  altinda: "alt limit altında",
};

/**
 * Yüzde: o anki değer / eşik × 100.
 *
 * Eşik yoksa yüzde de YOKTUR — uydurma eşikle yanlış yüzde üretmeyiz
 * (backend'in `pct`'yi boş bırakma kuralının aynısı). Sıfır eşik de yüzde
 * üretmez: bölme sonsuza giderdi.
 */
export function yuzde(f: Feature, sapmaPct: number): number | null {
  const e = esik(f, sapmaPct);
  if (e == null || e === 0 || f.current == null) return null;
  return Math.round((f.current / e) * 100 * 10) / 10;
}

/**
 * Eşik çizgisinin etiketi.
 *
 * TÜRETİLMİŞ ÇİZGİ ÖYLE OLDUĞUNU SÖYLER: yalnız "Limit" yazmak, hesaplanmış
 * bir çizgiyi üreticinin koyduğu eşik gibi okuturdu. Karşılama ekranındaki
 * dört durumlu rozetin izlediği kuralın aynısı.
 */
export function esikEtiketi(f: Feature, sapmaPct: number): string {
  return f.baseline != null ? `Limit (ort. +%${sapmaPct})` : "Limit";
}
