// Alan modeli — Promos3 TELGRAFININ şekli. backend/app/domain.py ile birebir.
//
// Bu tipler, promos3-c/analysis_jul_28_1_0_0.md'de çözülen GERÇEK veriye göre
// şekillendirilmiştir. Önceki şekil bir log tekrarından türemişti ve tel
// üzerinde var olmayan alanlar taşıyordu (alt/üst limit bandı, kayan pencere).
//
// Bilinmesi gereken dört kural:
//  1. Genlik HAM SAYIMDIR: 0..255, ÖLÇEK ÇARPANI YOK (rapor Part 5).
//     "%" değeri özelliğin limit Level'ına göredir: pct = current/limitLevel*100.
//  2. Canlı iz TEK ÇERÇEVEDİR: 125 × int16 (rapor 4.1), her pakette BÜTÜNÜYLE
//     yenilenir — kayan pencere değil.
//  3. Durum "izleme/alarm" ikilisi değil, 16 kodlu ToolStatus halkasıdır.
//  4. Özellik ADLARI kuruluma özeldir (SKanalRec'ten okunur), koda gömülmez.

/** Alarm durumu (CONTEXT: Alarm — aktif / onaylandı). */
export type AlarmState = "active" | "acknowledged";

/**
 * Çözülmüş bir yüke ne kadar güvenilir.
 *
 * Başlık yerleşimi henüz kalibre edilmediği için (rapor §0.5) tel üzerindeki
 * her şey şu an en iyi durumda "provisional"dır. Ekran bunu ÖN GÖRÜNÜM olarak
 * işaretler; tahmin edilmiş bir ofset asla doğrulanmış veri gibi görünmez.
 */
export type Confidence = "unknown" | "named" | "provisional" | "confirmed";

/**
 * Grafiğin besleme biçimi.
 *  - "trace"  → Promos3 SIGNALVERLAUF: 125 örneklik çerçeve, pakette yenilenir
 *  - "series" → sayaç/ölçüm zaman serisi: kayan pencere (NC kanalı)
 */
export type FeatureKind = "trace" | "series";

/**
 * Limit (CONTEXT: Limit) — tek bir eşik.
 *
 * Promos3'te limit alt+üst BANDI DEĞİL, tipli tek eşiktir (tablo Limits:
 * Limtype, Level, Feat_Num). Level genlikle AYNI ham birimdedir (0..255).
 */
export interface FeatureLimit {
  /** Limtype ham kodu (anlam tablosu doğrulanmadı; kod olduğu gibi taşınır). */
  limType?: number;
  /** Eşik değeri — ham sayım (bu kurulumda görülen aralık 20..170). */
  level: number;
  label?: string;
}

/** Özellik (CONTEXT: Özellik / feature) — kanalda ölçülen karakteristik. */
export interface Feature {
  id: string;
  kind: FeatureKind;
  /** SKanalRec'ten gelen ad (örn. "VIBRATION", "M131 DEBI") — kuruluma özel. */
  name: string;

  // --- Promos3 kimliği (NC serilerinde boş) ---
  /** İzleme ünitesi numarası (CAN-ID − 1280). */
  unitNo?: number;
  /** SIGNALVERLAUF yönlendirme anahtarları (rapor 4.1). */
  toolKey?: number;
  channelKey?: number;
  /** Özellik yuvası / Feat_Num ve SKanalRec maskesi (alt nibble seçme biti). */
  featureNr?: number;
  mask?: number;

  // --- Ölçüm ---
  /** true: değerler HAM SAYIM (0..255), ölçek çarpanı yok (rapor Part 5). */
  rawCounts: boolean;
  /** Birim etiketi; ham sayımda boştur ("" → ekran birim yazmaz). */
  uom: string;
  /** Çizilen değerler: "trace" için ≤125 örnek, "series" için kayan pencere. */
  samples: number[];
  /** O anki değer (izin son örneği / serinin son değeri). */
  current?: number;
  minValue?: number;
  maxValue?: number;

  // --- Limit ve durum ---
  /**
   * Yüzde hesabında kullanılan birincil eşik. GÜVENİLİR limit kaynağı yoksa
   * boştur — uydurma eşik sessizce yanlış yüzde üretirdi.
   */
  limitLevel?: number;
  limits: FeatureLimit[];
  /** pct = current / limitLevel × 100 (rapor Part 5); limit yoksa boş. */
  pct?: number;
  /**
   * Bu özelliğin TÜM CSV değerlerinin ortalaması — YALNIZ CSV kaynağı doldurur,
   * telde her zaman boştur.
   *
   * HAM ORTALAMADIR, EŞİK DEĞİLDİR: eşiği `domain/esik.ts` kurar, çünkü sapma
   * yüzdesi kullanıcının seçimidir ve backend tek durumu bütün abonelere
   * yayınlar. Bu alan doluyken `limitLevel`/`pct` boş gelir.
   */
  baseline?: number;
  /** ToolStatus ham kodu ve etiketi (rapor 6.1). */
  statusCode?: number;
  statusLabel?: string;
  /** Gövde beklenen uzunluğa ulaşmadı: iz gösterilir ama tam değil. */
  truncated: boolean;
  confidence: Confidence;
}

/** Sensör tanımlayıcısı (rapor 4.3) — bu kurulumda 4× PROCUR-S (0x80). */
export interface SensorInfo {
  unitNo: number;
  sensorId: number;
  serial?: string;
  /** Ham SensorType kodu + etiketi (rapor 6.2). */
  type?: number;
  typeLabel?: string;
  subType?: number;
  hwSerial?: number;
  swSerial?: number;
  sensChannels?: number;
  featureCount?: number;
  confidence: Confidence;
}

/**
 * İzleme ünitesi (CONTEXT: İzleme ünitesi / device) — Prometec kutusu.
 * Bu kurulumda iki ünite: SNr 10659 ve 10663, GType 0x44 / SubType 5.
 */
export interface UnitInfo {
  unit: number;
  /** Seri no (10659/10663) — kimlik satırı gelene dek boş. */
  serialNo?: string;
  online: boolean;

  // --- Cihaz kimliği (SGeraetRec / KONFIG) ---
  gType?: number;
  gSubType?: number;
  /** [MonitorTypes] çözümlemesi; indeks tabanı sabitlenmediği için "(?)" taşır. */
  model?: string;
  /** 1 = Provis2/MC_, 2 = Promos3/MC3_ (getTargetType karşılığı). */
  generation?: number;
  channelAmount?: number;
  miSensAmount?: number;
  /** MiSensType[8] ham kodları + etiketleri (0x80 = PROCUR-S). */
  miSensTypes: number[];
  miSensTypeLabels: string[];
  sampleDiv?: number;
  reduzLim?: number;
  /** KONFIG özetindeki sürüm (log: "Version 229"). */
  konfigVersion?: number;
  /** Firmware (örn. "Rtm_V14.5.H86") — akışta gelirse dolar. */
  firmware?: string;
  sensors: SensorInfo[];
}

/**
 * Alarm (CONTEXT: Alarm) — (kanal, çevrim, özellik, limit) dörtlüsüne bağlı.
 * Alanlar hem tel kaydıyla (rapor 4.2) hem saklı `Alarms` tablosuyla aynı.
 */
export interface Alarm {
  id: string;
  time: string; // ISO
  unitNo?: number;
  deviceSerial?: string;

  // --- Tel kaydı ---
  alarmNumber?: number;
  entryId?: number;
  /** Durum baytının alt yarısı = ToolStatus kodu (rapor 6.1). */
  statusCode?: number;
  statusLabel?: string;

  // --- Bağlam (Alarms tablosu kolonları) ---
  channelNr?: number;
  cycleNr?: number;
  featureNr?: number;
  limitNr?: number;
  featureName?: string;
  /** [AlarmNames] yuva etiketi (1=Çarpışma, 2=Kırılma, ...). */
  slotName?: string;
  /** Eşiği aşan tepe ve eşiğin kendisi — ham sayım; kaynak vermiyorsa boş. */
  peak?: number;
  level?: number;
  /** Çevrim başlangıcına göre konum (Alarms.TimeOffset). */
  timeOffset?: number;

  state: AlarmState;
  confidence: Confidence;
}

/** Olay (CONTEXT: Olay / event) — izleme sırasında düşen tek kayıt satırı. */
export interface EventRow {
  id: string;
  time: string; // ISO
  unitNo?: number;

  // --- Promos3 olay kaydı (rapor 4.4) ---
  eventNumber?: number;
  /** EventCode ham kodu + etiketi (rapor 6.5). */
  code?: number;
  codeLabel?: string;
  channelNr?: number;

  // --- Çevrim bağlamı (0x16 im satırları) ---
  // İm satırları çevrim ve iş parçası değişimlerini olay akışına düşürür;
  // NC program adı TELDE YOKTUR.
  workpiece?: string;
  cycleNr?: number;

  confidence: Confidence;
}

/**
 * Taşıma/çözme teşhisi — "veri gelmiyor" ile "geliyor ama çözülmüyor" ayrımı.
 *
 * Başlık yerleşimi kalibre edilmeden gerçek tezgahta ilk bağlantıda en olası
 * durum "çerçeve akıyor, mesaj çözülemiyor"dur. Bu sayaçlar o durumu ekranda
 * GÖRÜNÜR kılar; yoksa arayüz sessizce boş durur.
 */
export interface WireStats {
  datagrams: number;
  canFrames: number;
  messages: number;
  /**
   * Sağlama toplamı TUTAN mesaj sayısı — yani komut kimliği tahmin değil,
   * kanıttır (backend/app/promos3/mc.py).
   */
  parsed: number;
  /** Çerçeveler birleşti ama hiçbir komut sağlamayı tutturamadı. */
  unparsed: number;
  /** CAN-ID tabanın altında / ünite aralığı dışında. */
  droppedOutOfRange: number;
  /** Tamamlanma hiç gelmedi, tampon taştı. */
  droppedOverflow: number;
  /** Sıra numarası atladı: kayıp, yinelenen ya da bozuk çerçeve. */
  droppedSequence: number;
  /** Mesajın ortasından katılındı (ilk seq 0 görülene dek). */
  droppedOrphan: number;
  /** Önceki mesaj bitmeden yenisi başladı. */
  droppedIncomplete: number;
  /** Cihaz "bu komutu yapamıyorum" cevabı verdi — tel sağlıklı. */
  deviceErrors: number;
  /** Son kimliklendirilemeyen mesajın baş kısmı (hex) — teşhisin tek ipucu. */
  lastUnparsedHex?: string;
  /** Son çözülen komutun adı (akışın canlılığını gösterir). */
  lastCommand?: string;
}
