// Alarm penceresi — ekranın sağ altında duran, açılıp kapanan yerleşik panel.
//
// NEDEN GEZİNMEDE DEĞİL: alarm bir EKRANIN değil TEZGAHIN durumudur. Sekme
// olduğunda ancak oraya GİDİLDİĞİNDE görünüyordu; burada Canlı ve Olaylar
// ekranlarının ikisinde de sürekli durur.
//
// TRİYAJ ARACI DEĞİLDİR: 11 kolonlu ızgara, dışa aktarma, kolon seçici,
// sıralama ve toplu onay `/alarmlar`da KALIR (rota duruyor, yalnız gezinmeden
// çıktı). Bu pencere farkındalık verir — ne oldu, kaç tane, tek dokunuşla
// onayla — ve gerisi için tam ekrana yollar.
//
// PAKET DIŞI BİLEŞEN YOK: Card + Accordion + ScrollArea + Badge + IconButton.
// Desen `canli-route.tsx`teki `OzellikKutucugu`nun birebir aynısı ve açılış
// animasyonu app.css'teki MEVCUT `mzi-akordiyon` yamasıdır — HAREKET bloğuna
// dördüncü bir kural eklemek, zaten kapatılmış bir boşluğu ikinci kez
// yamamak olurdu.

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Badge,
  Button,
  Card,
  IconButton,
  ScrollArea,
  formatNumber,
  formatRelative,
  IKON,
} from "@alp/design-system";
import { AlertTriangle, Check, ShieldCheck, Unplug } from "lucide-react";
import type { Alarm } from "@/domain/types";
import type { BaglantiBoslugu } from "@/domain/baglanti-bosluk";
import { alarmContext, alarmTitle, deviceTitle } from "@/domain/format";

/** Accordion tek öğelidir; değer sabit ve DOM kimliğiyle aynı olmak zorunda. */
const PENCERE_ID = "mzi-alarm-penceresi";

/** Liste bu yükseklikten sonra kayar. `maxHeight` VERİLMEZSE hiç kaymaz. */
const LISTE_YUKSEKLIGI = 280;

export { PENCERE_ID };

export default function AlarmPenceresi({
  active,
  bosluk,
  acik,
  onToggle,
  onToggleAck,
  onTumunuGor,
}: {
  /** Yalnız aktif alarmlar — onaylananlar tam ekrandaki "Onaylanmış"ta yaşar. */
  active: Alarm[];
  /** Zincir kopuksa boşluğun tarifi; sağlamsa null. */
  bosluk: BaglantiBoslugu | null;
  acik: boolean;
  onToggle: () => void;
  onToggleAck: (id: string) => void;
  onTumunuGor: () => void;
}) {
  return (
    <div
      // KIRILIM `kabuk`, `sm` DEĞİL: paket Tailwind'in sm..2xl ölçeğini SİLER
      // (theme-olcek.css: `--breakpoint-*: initial`) ve tek kırılım bırakır —
      // 860px, sol gezinmenin alt tab bar'a döndüğü yer (ADR-0006). `sm:`
      // yazmak sessizce HİÇBİR kural üretmez; ölçüldü, pencere tam genişlikte
      // kaldı.
      //
      // Dar ekranda alt kenar ALT TAB BAR'IN: pencere onun üstüne çıkar
      // (`--touch-target` + bir birim boşluk), yoksa gezinmenin üstüne oturur.
      // Sol/sağ AYRI verilir (`inset-x-*` DEĞİL): kısayol ile `right-4` aynı
      // özelliği farklı yollardan yazar ve hangisinin kazandığı üretilen CSS
      // sırasına kalır.
      className="fixed left-4 right-4 bottom-[calc(var(--touch-target)+var(--space-4))] z-[var(--layer-nav)] kabuk:left-auto kabuk:bottom-4 kabuk:w-96"
      // Landmark: sürekli duran bir bölge, ekran okuyucuda adıyla bulunabilmeli.
      role="region"
      aria-label="Alarm penceresi"
    >
      <Card className="shadow-[var(--shadow-lg)]">
        <Accordion
          className="-mx-3"
          type="multiple"
          value={acik ? [PENCERE_ID] : []}
          onValueChange={(v: string[]) => {
            if (v.includes(PENCERE_ID) !== acik) onToggle();
          }}
        >
          {/* Kart kendi kenarlığını zaten çiziyor; ayırıcı ikinci hairline
              olurdu (OzellikKutucugu ile aynı gerekçe). */}
          <AccordionItem value={PENCERE_ID} id={PENCERE_ID} className="border-b-0">
            <AccordionTrigger className="min-w-0 px-3">
              <span className="flex min-w-0 items-center gap-2">
                <AlertTriangle size={IKON.md} />
                <span className="type-card-title truncate">Alarmlar</span>
                <Sayac active={active} bosluk={bosluk} />
              </span>
            </AccordionTrigger>

            {/* İÇERİK KOŞULSUZ BASILIR: Radix kapanışta yüksekliği bir layout
                effect'te ÖLÇER; `{acik && ...}` koşulu ölçülen değeri bozar ve
                kapanış animasyonu çöker (canli-route.tsx'teki AÇILIŞ NOTU). */}
            <AccordionContent className="mzi-akordiyon px-3">
              <div className="flex flex-col gap-3">
                {bosluk ? (
                  <Bosluk bosluk={bosluk} />
                ) : active.length === 0 ? (
                  <span className="flex items-center gap-2 type-help text-muted-foreground">
                    <ShieldCheck size={IKON.md} />
                    Aktif alarm yok.
                  </span>
                ) : (
                  <ScrollArea maxHeight={LISTE_YUKSEKLIGI}>
                    <ul className="flex flex-col gap-2">
                      {active.map((a) => (
                        <Satir key={a.id} alarm={a} onAck={() => onToggleAck(a.id)} />
                      ))}
                    </ul>
                  </ScrollArea>
                )}

                {/* Triaj tam ekranda: sıralama, dışa aktarma, kolon seçici ve
                    "Onaylanmış" geçmişi orada yaşar. */}
                <Button size="sm" variant="ghost" onClick={onTumunuGor}>
                  Tümünü gör →
                </Button>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </div>
  );
}

/**
 * Kapalı şeritteki sayı.
 *
 * ZİNCİR KOPUKKEN SAYI BASILMAZ: "0" bir GÜVENCE cümlesidir ve arkasında
 * hiçbir kanıt yoktur. Bu pencere her ekranda sürekli durduğu için o farkı
 * yutmanın en pahalı olduğu yer burasıdır (bkz. domain/baglanti-bosluk.ts).
 */
function Sayac({ active, bosluk }: { active: Alarm[]; bosluk: BaglantiBoslugu | null }) {
  if (bosluk) {
    return (
      <Badge tone="neutral" size="sm">
        bilinmiyor
      </Badge>
    );
  }
  return (
    <Badge tone={active.length > 0 ? "danger" : "success"} size="sm" dot>
      {formatNumber(active.length)}
    </Badge>
  );
}

/** Zincir kopuk — ne bilinmediği yazılır, alarm yokluğu İDDİA EDİLMEZ. */
function Bosluk({ bosluk }: { bosluk: BaglantiBoslugu }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="flex items-center gap-2 type-card-title">
        <Unplug size={IKON.md} />
        {bosluk.title}
      </span>
      <span className="type-help text-muted-foreground">
        {bosluk.description} Bu pencere alarm olmadığını SÖYLEMİYOR.
      </span>
    </div>
  );
}

/** Tek alarm satırı — ne, ne zaman, hangi cihaz + tek dokunuş onay. */
function Satir({ alarm: a, onAck }: { alarm: Alarm; onAck: () => void }) {
  return (
    <li className="flex items-center justify-between gap-2">
      <div className="flex min-w-0 flex-col">
        <span className="type-card-title truncate">{alarmTitle(a)}</span>
        <span className="type-help truncate text-muted-foreground">
          {formatRelative(a.time)}
          {` · ${deviceTitle(a)}`}
          {alarmContext(a) && ` · ${alarmContext(a)}`}
        </span>
      </div>
      {/* Erişilebilir ad hangi alarm olduğunu SÖYLEMELİ: listede her düğme
          aynı ikonu taşır ve ekran okuyucu bunları ayırt edemezdi. */}
      <IconButton label={`Alarmı görüldü işaretle: ${alarmTitle(a)}`} variant="ghost" size="sm" onClick={onAck}>
        <Check size={IKON.sm} />
      </IconButton>
    </li>
  );
}
