// Bağlantı boşluğu — "veri yok" ile "bilmiyoruz" arasındaki farkın TEK yeri.
//
// NEDEN VAR: Canlı İzleme zincirin hangi halkasının koptuğunu söylemeyi
// öğrenmişti; Alarmlar ve Olaylar öğrenmemişti. O iki ekran `live.link`e hiç
// bakmadan "Aktif alarm yok" (yeşil kalkanla) ve "Henüz olay yok" basıyordu.
// Kaynaksız bir tezgahta, katalog düşmüşken ya da akış kopmuşken bu bir GÜVENCE
// cümlesidir ve arkasında hiçbir kanıt yoktur. Yeni karşılama ekranından 16
// tezgahın 13'ü tek tıkla oraya varıyor.
//
// NEDEN KABUĞA TAŞINMADI (banner'ı üç ekranda tekrarlamak yerine): iki neden.
//   1) İki ekranın sorunu banner DEĞİL, DataGrid'in BOŞ DURUMUDUR. Üstte
//      "bağlantı yok" bandı basıp altta ızgaranın içinde "Aktif alarm yok"
//      demek aynı yalanı biraz daha aşağıda söylemek olurdu; boş durumun
//      METNİ değişmek zorunda ve onu kabuk basamaz.
//   2) Canlı İzleme'nin banner yuvası pano yasasına bağlıdır (bağlam → müdahale
//      → ölçüm) ve müdahale bandı KPI şeridinin ALTINDADIR. Kabuğa taşımak onu
//      sayfa başlığının da üstüne çıkarır, yani düzeni bozar.
// Tekrarlanan şey artık kod değil ÇAĞRI: metin burada tek nüsha durur.

import type { AlertTone } from "@alp/design-system";
import { KAYNAK_CUMLEDE, type SourceKind } from "./katalog";
import type { LiveLink } from "./useLive";

export interface BaglantiBoslugu {
  /** Banner tonu; boş durumlarda kullanılmaz (ikon + metin taşır). */
  tone: AlertTone;
  title: string;
  description: string;
}

/**
 * Zincir kopuksa boşluğu tarif eder, sağlamsa null döner.
 *
 * null dönmesi ekranın kendi olumlu cümlesini ("Aktif alarm yok") kurmakta
 * SERBEST olduğu anlamına gelir: o cümle ancak kaynak öyle dediğinde doğrudur.
 *
 * `kaynak` bilinmiyorsa metin genel kalır — olmayan bir cihazı suçlamaktansa
 * az şey söylemek yeğdir.
 */
export function baglantiBoslugu(
  link: LiveLink,
  kaynak: SourceKind | null,
): BaglantiBoslugu | null {
  switch (link) {
    case "ok":
      return null;
    case "catalog-loading":
      return {
        tone: "info",
        title: "Tezgah bilgisi yükleniyor",
        description:
          "Bu tezgahın kaynağı henüz bilinmiyor. Ekranın boş olması tezgah hakkında bir şey SÖYLEMİYOR.",
      };
    case "catalog-down":
      return {
        tone: "danger",
        title: "Tezgah listesi alınamadı",
        description:
          "Bu tezgahın kaynağı öğrenilemediği için akış kurulmadı. Ekranın boş olması tezgah hakkında bir şey SÖYLEMİYOR.",
      };
    case "no-source":
      return {
        tone: "warning",
        title: "Bu tezgah için canlı kaynak tanımlı değil",
        description: "Ekran boş kalacak. Bu bir arıza değil, yapılandırmadır.",
      };
    case "stream-down":
      return {
        tone: "danger",
        title: "Backend akışına bağlanılamıyor",
        description:
          "Bağlantı yeniden kurulmaya çalışılıyor. Liste boş değil, BİLİNMİYOR.",
      };
    case "source-down":
      return kaynakDustu(kaynak);
  }
}

/**
 * Kaynak halkası kopuk — ve HANGİ kaynak olduğu söylenir.
 *
 * Eskiden burada tek bir cümle vardı: "Akış açık ama Promos3 ağ geçidinden
 * veri gelmiyor." O cümle A/3'te (CSV; klasör yoksa, kalıcı veritabanı
 * hatasında ve her açılışın ilk ~1 sn'sinde buraya düşülür) hiç var olmayan
 * bir cihazı, A/2'de ise simülatörü "ağ geçidi" diye suçluyordu.
 *
 * Suçlanan şey de doğru olmak zorunda: bu hâl backend'in KENDİ halkasını
 * kuramamasıdır (UDP dinleyicisi ayakta değil / CSV okuma görevi durdu),
 * karşı taraftaki cihazın susması DEĞİL. Susan ama dinleyicisi ayakta bir
 * kaynak `link === "ok"` kalır ve üst bar "Veri Yok" der.
 */
function kaynakDustu(kaynak: SourceKind | null): BaglantiBoslugu {
  if (kaynak === "csv") {
    return {
      tone: "warning",
      title: "CSV tekrar oynatması durdu",
      description:
        "Akış açık ama backend CSV okumayı sürdüremiyor (klasör bulunamadı ya da kalıcı bir veritabanı hatası). Ekran boş kalacak.",
    };
  }
  if (kaynak === "provis" || kaynak === "promos3-sim") {
    return {
      tone: "warning",
      title: `${KAYNAK_CUMLEDE[kaynak]} dinleyicisi kurulmadı`,
      description: `Akış açık ama backend ${KAYNAK_CUMLEDE[kaynak]} için UDP dinleyicisini kuramadı (port başka bir süreçte olabilir). Ekran boş kalacak.`,
    };
  }
  return {
    tone: "warning",
    title: "Backend kaynağa ulaşamıyor",
    description:
      "Akış açık ama backend bu tezgahın kaynağını kuramadı. Hangi kaynak olduğu henüz bilinmiyor.",
  };
}
