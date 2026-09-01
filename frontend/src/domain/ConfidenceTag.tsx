// Güven rozeti — doğrulanmamış her değerin yanında durur.
//
// "confirmed" HİÇ işaret taşımaz: doğrulanmış veri normaldir, işaretlenmesi
// gereken sapma değildir. Geri kalan üçü ön görünümdür (rapor §0.5).
//
// Açıklama metni (CONFIDENCE_HINT) buraya Tooltip olarak BAĞLANMAZ: paketin
// Tooltip'i etkileşimli tek bir çocuk ister, rozet etkileşimli değildir; ayrıca
// yalnız hover'da duran bilgi erişilemez bilgidir. Uzun açıklama tablo kolonunun
// `hint`inde ve satır detayında (KeyValue) yaşar.

import { Badge } from "@alp/design-system";
import { CONFIDENCE_LABEL, isProvisional } from "./format";
import type { Confidence } from "./types";

export default function ConfidenceTag({ confidence }: { confidence: Confidence }) {
  if (!isProvisional(confidence)) return null;
  return (
    <Badge tone="warning" dot size="sm">
      {CONFIDENCE_LABEL[confidence]}
    </Badge>
  );
}
