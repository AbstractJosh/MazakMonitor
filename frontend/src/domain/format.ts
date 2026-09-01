// Görüntüleme yardımcıları — kod → ekran metni. Üç ekran da bunları kullanır
// ki ham sayım, ToolStatus ve güven düzeyi her yerde AYNI dille anlatılsın.

import { formatNumber, type BadgeTone } from "@alp/design-system";
import type { Alarm, Confidence, EventRow, Feature } from "./types";

/** Ham genlik tam ölçeği: 0..255, ölçek çarpanı yok (rapor Part 5). */
export const RAW_MIN = 0;
export const RAW_MAX = 255;

/**
 * Güven düzeyinin operatöre söylediği şey.
 *
 * "confirmed" dışındaki her şey ÖN GÖRÜNÜMDÜR: değer tel üzerinden okundu ama
 * bayt yerleşimi henüz bir yakalamayla doğrulanmadı (rapor §0.5). Bunu
 * saklamak, tahmini veriyi ölçüm gibi göstermek olurdu.
 */
export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  confirmed: "Doğrulanmış",
  provisional: "Ön görünüm",
  named: "Çözülmedi",
  unknown: "Bilinmiyor",
};

export const CONFIDENCE_HINT: Record<Confidence, string> = {
  confirmed: "Bayt yerleşimi doğrulandı; değerler ölçümdür.",
  provisional:
    "Değer tel üzerinden okundu ama başlık/gövde yerleşimi henüz bir yakalamayla doğrulanmadı — sayıları ölçüm olarak kullanmayın.",
  named: "Komut tanınıyor ama gövdesi çözülmüyor; yalnız ham bayt var.",
  unknown: "Komut tanınmıyor; yalnız ham bayt var.",
};

/** Ön görünüm mü (doğrulanmamış her şey). */
export function isProvisional(c: Confidence): boolean {
  return c !== "confirmed";
}

/**
 * ToolStatus kodunun tonu (rapor 6.1).
 *
 * Kırmızı yalnız gerçekten yük/takım sorunudur; kesme başı/sonu ve temas
 * bildirimleri izlemenin NORMAL işaretleridir — onları kırmızıya boyamak
 * operatörü alarm körlüğüne iter.
 *
 * Bu bir PROTOKOL KODU → ANLAM haritasıdır, elle renk seçimi DEĞİLDİR: eşiğe
 * bakarak ton üretmek gerektiğinde araç `thresholdTone`dur. Kodun anlamı
 * eşikten türetilemez, tablodan gelir.
 *
 * Dönüş tipi paketin `BadgeTone`udur: yanlış bir değer çalışma anında sessizce
 * nötr rozet değil, DERLEME hatası olsun diye.
 */
export function statusTone(code: number | undefined): BadgeTone {
  if (code == null) return "neutral";
  switch (code) {
    case 0x1: // Aşırı yük
    case 0x2: // Düşük yük
    case 0x4: // Takım yok
    case 0xf: // Takım aşınması
      return "danger";
    case 0x5: // Çalışma üstü
    case 0x6: // Çalışma altı
    case 0x9: // Dinamik üst
    case 0xa: // Dinamik alt
    case 0xb: // Örüntü üst
    case 0xc: // Örüntü alt
      return "warning";
    case 0x3: // Temas
    case 0x7: // Kesme başlangıcı
    case 0x8: // Kesme sonu
    case 0xd: // ACF temas
    case 0xe: // Kesme algılama teması
      return "sky";
    default:
      return "neutral";
  }
}

/**
 * Sayı → ekran metni; boş değer "—".
 *
 * `null → "—"` kuralı her tabloda ve her kutucukta yük taşır: eksik bir ölçüm
 * asla 0 gibi okunmamalıdır. Biçimleme paketin `formatNumber`ıdır (elle nokta/
 * virgül yazılmaz).
 */
export function sayi(v: number | null | undefined): string {
  return v == null ? "—" : formatNumber(v);
}

/** Ham kod gösterimi — her yerde AYNI biçim: 0x03, 0x1B (iki hane, büyük harf). */
export function hex(n: number): string {
  return `0x${n.toString(16).toUpperCase().padStart(2, "0")}`;
}

/**
 * Özellik/kanal adı.
 *
 * Ad TELDEN gelir (MC_GIVEKANAL, +0x4D özellik yuvaları) ve zorunlu doludur;
 * yuva adsızsa backend yuva sırasını yazar. `id` yalnız savunma amaçlı son
 * çaredir.
 */
export function featureTitle(f: Feature): string {
  return f.name || f.id;
}

/** Özelliğin kimlik satırı: hangi ünite / takım / kanal anahtarı. */
export function featureRouting(f: Feature): string | null {
  if (f.unitNo == null) return null;
  const parts = [`Ünite ${f.unitNo}`];
  if (f.toolKey != null) parts.push(`takım ${f.toolKey}`);
  if (f.channelKey != null) parts.push(`kanal ${f.channelKey}`);
  return parts.join(" · ");
}

/**
 * Yüzde metni. Eşik yoksa yüzde YOKTUR — uydurma eşikle yanlış yüzde üretmeyiz.
 *
 * `Feature` DEĞİL SAYI alır: yüzdenin paydası kaynağa göre değişir (telde
 * `limitLevel`, CSV'de ortalama + kullanıcının sapması) ve o seçim `esik.ts`in
 * işidir. Biçimleyicinin hangi eşiğin geçerli olduğunu bilmesi gerekmez.
 */
export function pctText(pct: number | null | undefined): string | null {
  return pct == null ? null : `%${formatNumber(pct)}`;
}

/**
 * Alarmın "nerede"si — hangi özellik. Yoğun satırda (Canlı İzleme paneli)
 * "ne oldu" zaten durum çipinde yazdığı için başlık yalnız bunu gösterir;
 * `alarmTitle` ikisini birleştirir.
 */
export function alarmWhere(a: Alarm): string | null {
  return a.featureName ?? (a.featureNr != null ? `Özellik ${a.featureNr}` : null);
}

/** Alarmın tek satırlık başlığı: hangi özellik, ne oldu. */
export function alarmTitle(a: Alarm): string {
  const what = a.statusLabel ?? (a.statusCode != null ? `Durum ${hex(a.statusCode)}` : "Alarm");
  const where = alarmWhere(a);
  return where ? `${where} — ${what}` : what;
}

/**
 * Aşım metni: tepe / eşik. Ham sayım olduğu YAZILIR (0..255, ölçek çarpanı
 * yok) — birimsiz bir "204" fiziksel bir ölçüm gibi okunurdu.
 * Kaynak tepe değeri vermiyorsa null.
 */
export function peakText(a: Alarm): string | null {
  if (a.peak == null) return null;
  const peak = formatNumber(a.peak);
  return a.level == null ? `${peak} ham` : `${peak} / ${formatNumber(a.level)} ham`;
}

/**
 * Alarmın bağlam satırı: kanal/çevrim/limit — yalnız DOLU alanlar.
 * Cihaz kimliği burada YOK: onu `deviceTitle` tek bir dille söyler, yoksa aynı
 * kutu satır içinde iki farklı adla görünürdü.
 */
export function alarmContext(a: Alarm): string {
  const parts: string[] = [];
  if (a.channelNr != null) parts.push(`kanal ${a.channelNr}`);
  if (a.cycleNr != null) parts.push(`çevrim ${a.cycleNr}`);
  if (a.limitNr != null) parts.push(`limit ${a.limitNr}`);
  if (a.slotName) parts.push(a.slotName);
  return parts.join(" · ");
}

/** Olay satırının okunur açıklaması. */
export function eventTitle(e: EventRow): string {
  if (e.codeLabel) return e.codeLabel;
  if (e.code != null) return `Olay ${hex(e.code)}`;
  if (e.workpiece) return `İş parçası ${e.workpiece}`;
  return "—";
}

/**
 * Bir izleme ünitesinin/kutunun adı — TEK dil.
 *
 * Seri no varsa "SNr 10659", yoksa "Ünite 1". Alarm satırı, ünite şeridi ve
 * tablo kolonu aynı kutuya aynı adı verir.
 */
export function deviceTitle(d: {
  unit?: number;
  unitNo?: number;
  serialNo?: string;
  /** Alarm kaydı seri numarasını BU adla taşır (types.ts: Alarm.deviceSerial). */
  deviceSerial?: string;
}): string {
  // İki ad da okunur: UnitInfo `serialNo`, Alarm `deviceSerial` taşır. Yalnız
  // `serialNo` okunduğu için alarm satırlarında "SNr …" HİÇ görünmemişti.
  const serial = d.serialNo ?? d.deviceSerial;
  if (serial) return `SNr ${serial}`;
  const no = d.unit ?? d.unitNo;
  return no == null ? "—" : `Ünite ${no}`;
}

/** Ünite başlığı (UnitInfo için `deviceTitle` kısayolu). */
export function unitTitle(unit: { unit: number; serialNo?: string }): string {
  return deviceTitle(unit);
}
