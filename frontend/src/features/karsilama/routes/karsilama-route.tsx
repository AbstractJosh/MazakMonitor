// Karşılama — tesis ve tezgah seçimi. Uygulamanın giriş kapısı.
//
// DÜRÜSTLÜK KURALI: hangi tezgahın arkasında gerçek kaynak olduğu SEÇERKEN
// söylenir, seçtikten sonra boş ekranla değil. DÖRT durum ayrı ayrı görünür:
//
//   Kaynak yok        yapılandırmada bu tezgaha kaynak bağlanmamış (13 tezgah).
//   Kaynak bağlı değil  kaynak tanımlı ama adaptörün halkası ayakta değil.
//   Veri bekleniyor   halka ayakta, veri AKMIYOR. Arıza değil: sessiz bir ağ
//                     geçidi bozuk değildir, sadece susuyordur.
//   Canlı             veri ŞU AN akıyor (backend'in yaş damgasına göre).
//
// DÖRDÜNCÜSÜ NEDEN VAR: "bağlı" ile "veri geliyor" ayrı sorulardır ve eskiden
// rozet birincisine bakıyordu. Ölçüldü — ağ geçidi hiç takılı değilken A/1
// `connected: true`, `datagrams=0, parsed=0` diyordu ve bu ekran yeşil "Canlı"
// basıyordu; aynı anda o tezgahın izleme ekranı "Veri Yok / Gösterilecek
// grafik yok" diyordu. Bu makinede PROMOS3_BIND=127.0.0.1 olduğu için (bkz.
// basla.bat) A/1'e gerçek gateway trafiği HİÇ ulaşamaz, yani o yeşil rozet
// kalıcıydı.
//
// Kabuğun DIŞINDADIR: tezgah henüz seçilmediği için AppShell'in gezinmesi
// (Canlı/Alarmlar/Olaylar) anlamsız olurdu.

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  Field,
  NumberInput,
  PageShell,
  Section,
  Skeleton,
  Tabs,
  type BadgeTone,
} from "@alp/design-system";
import {
  KAYNAK_ADI,
  findFacility,
  useKatalog,
  veriTaze,
  type Machine,
} from "@/domain/katalog";
import {
  ALT_SAPMA_VARSAYILAN,
  SAPMA_MAX,
  SAPMA_MIN,
  SAPMA_VARSAYILAN,
  sapmaOku,
} from "@/domain/esik";
import { URUN_ADI } from "@/app/urun";

// Durum tazeliği için yeniden çekme aralığı. Karşılama ekranı açıkken bir
// kaynak düşerse ya da susarsa kart bunu söylemeli. Yaş BACKEND'DE hesaplanır,
// yani her yoklama taze bir cevap getirir — istemcinin kendi saatiyle bir şey
// hesaplaması gerekmez.
const YENILEME_MS = 5_000;

/**
 * Dört durum, dört ayrı rozet. Renk tek başına bilgi taşımaz — metin hep var.
 *
 * `bilinmiyor`: SON yoklama düştü. O hâlde canlılık iddiası ÖNCEKİ yoklamanın
 * kalıntısıdır ve basılmaz — backend kesintisi sırasında ekran hâlâ yeşil
 * "Canlı" tezgahlar reklam ediyordu. Kaynağın VARLIĞI yine de söylenir: o
 * yapılandırmadır (süreç ömrü boyunca değişmez), bu ekranın zaten gösterdiği
 * tezgah adlarıyla aynı yaştadır ve onu da gizlemek bilgi kazandırmazdı.
 */
function rozet(
  m: Machine,
  esikS: number,
  bilinmiyor: boolean,
): { tone: BadgeTone; label: string } {
  if (m.source == null) return { tone: "neutral", label: "Kaynak yok" };
  if (bilinmiyor) return { tone: "neutral", label: "Durum bilinmiyor" };
  if (!m.connected) return { tone: "warning", label: "Kaynak bağlı değil" };
  // Yeşilin ölçütü `connected` DEĞİL yaştır: soketi bağlı ama sessiz bir
  // kaynak "Canlı" olamaz.
  if (!veriTaze(m, esikS)) return { tone: "sky", label: "Veri bekleniyor" };
  return { tone: "success", label: "Canlı" };
}

/** Rozetin altındaki açıklama — rozetin İDDİASINI dayanağıyla birlikte verir. */
function aciklama(m: Machine, esikS: number, bilinmiyor: boolean): string {
  if (m.source == null) return "Bu tezgaha kaynak tanımlanmamış — ekran boş kalacak.";
  const kaynak = KAYNAK_ADI[m.source];
  if (bilinmiyor) return `${kaynak} · son durum alınamadı.`;
  if (!m.connected) return `${kaynak} · backend bu kaynağı kuramadı.`;
  if (veriTaze(m, esikS)) return kaynak;
  if (m.dataAgeS == null) return `${kaynak} · kaynak dinleniyor, henüz veri gelmedi.`;
  // Sayı yaşın KENDİSİDİR, uydurma değil: "ne kadar süredir sessiz" sorusunun
  // cevabı operatörün ilk soracağı şeydir. Rozet bundan ETKİLENMEZ (eşiğin
  // üstünde tek bir durum vardır), yani yazı akarken rozet titremez.
  return `${kaynak} · son veri ${Math.round(m.dataAgeS)} sn önce.`;
}

export default function KarsilamaRoute() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // "Değiştir" ile gelindiyse mevcut tezgah taşınır: doğru tesis seçili açılır
  // ve vazgeçilebilir olur.
  const mevcut = params.get("tezgah");

  const { katalog, durum, yenile } = useKatalog(YENILEME_MS);
  const [tesisId, setTesisId] = useState<string | null>(null);

  // Limit sapması. "Değiştir" ile gelindiyse kullanıcının az önce seçtiği
  // yüzde adres çubuğunda taşınır ve alan onunla açılır — varsayılana dönmek,
  // seçimi sessizce geri almak olurdu.
  //
  // NumberInput boş girdide `null` verir (0 DEĞİL, paket kuralı): alan boşken
  // ekrana taşınacak bir sayı yoktur, o yüzden `izle` varsayılana düşer.
  const [sapma, setSapma] = useState<number | null>(() => sapmaOku(params.get("sapma")));
  const [altSapma, setAltSapma] = useState<number | null>(() =>
    sapmaOku(params.get("altSapma"), ALT_SAPMA_VARSAYILAN),
  );

  // SON yoklama düştü mü. Kartlar kalır (adlar ve kaynak bağlaması hâlâ
  // geçerli) ama CANLILIK iddiası düşer: kesinti sırasında eski yoklamanın
  // yeşil rozetlerini basmaya devam etmek, tam da bu ekranın önlemek için
  // yazıldığı yalandı.
  const bilinmiyor = durum === "error";

  // Sekme seçimi: elle seçilen > "Değiştir" ile taşınan > ilk tesis.
  const istenen = tesisId ?? mevcut?.split("/")[0] ?? null;
  // Katalogda OLMAYAN bir tesise düşülmez (elle yazılmış URL): o hâlde hiçbir
  // sekme seçili kalmaz ve `panelId` DOM'da bulunmayan bir öğeyi işaret ederdi
  // — paket bunu açıkça yasaklar (Tabs `panelId`: kırık `aria-controls` ARIA
  // sözleşmesini bozar).
  const tesis =
    (istenen ? findFacility(katalog, istenen) : undefined) ?? katalog?.facilities[0];
  const secili = tesis?.id ?? null;

  const izle = (id: string) =>
    navigate(
      `/canli?tezgah=${encodeURIComponent(id)}` +
        `&sapma=${sapma ?? SAPMA_VARSAYILAN}` +
        `&altSapma=${altSapma ?? ALT_SAPMA_VARSAYILAN}`,
    );

  return (
    <PageShell
      title={URUN_ADI}
      description="İzlemek istediğiniz tesisi ve tezgahı seçin."
      actions={
        mevcut ? (
          <Button size="sm" variant="secondary" onClick={() => izle(mevcut)}>
            Vazgeç
          </Button>
        ) : undefined
      }
    >
      {durum === "error" && (
        <Alert
          tone="danger"
          title="Tezgah listesi alınamadı"
          actions={
            <Button size="sm" onClick={yenile}>
              Tekrar dene
            </Button>
          }
        >
          Backend'e ulaşılamıyor. Liste boş değil, BİLİNMİYOR — çalışan tezgahlar
          olabilir. Aşağıdaki kartlar son başarılı yoklamadan kalmadır; canlılık
          rozetleri "Durum bilinmiyor"a çekildi.
        </Alert>
      )}

      {durum === "loading" && (
        <div aria-busy="true" className="flex flex-col gap-3">
          <Skeleton style={{ width: 240 }} />
          <Skeleton />
          <Skeleton />
        </div>
      )}

      {katalog && (
        <>
          {/* Sekmelerin ÜSTÜNDE: sapma her tezgah için geçerlidir, bir tesise
              ait değil — tesis panelinin içine girseydi kapsamı yanlış
              okunurdu. İpucu KİMİ ETKİLEDİĞİNİ söyler: telden gerçek eşik alan
              tezgahlarda bu sayının hiçbir karşılığı yoktur ve sessizce
              etkisiz kalması "ayarım çalışmıyor" diye okunurdu. */}
          <div className="flex flex-wrap gap-4">
            <div className="max-w-xs">
              <Field
                label="Üst limit sapması"
                hint="Ortalamanın bu kadar ÜSTÜ. Aşan değer 'üst limit üstünde' işaretlenir."
              >
                <NumberInput
                  value={sapma}
                  onChange={setSapma}
                  min={SAPMA_MIN}
                  max={SAPMA_MAX}
                  step={5}
                  unit="%"
                />
              </Field>
            </div>
            <div className="max-w-xs">
              <Field
                label="Alt limit sapması"
                hint="Ortalamanın bu kadar ALTI (%20 → ortalamanın %80'i). Altına düşen değer 'alt limit altında' işaretlenir."
              >
                <NumberInput
                  value={altSapma}
                  onChange={setAltSapma}
                  min={SAPMA_MIN}
                  max={SAPMA_MAX}
                  step={5}
                  unit="%"
                />
              </Field>
            </div>
          </div>
          {/* Kapsam bir kez, iki alanın ALTINDA yazılır: aynı cümleyi iki
              ipucunda tekrarlamak, ikisinin ayrı kuralları olduğunu ima
              ederdi. */}
          <span className="type-help text-muted-foreground">
            İkisi de yalnız CSV kaynaklı tezgahlarda geçerlidir: sınırlar o
            grafiğin tüm CSV değerlerinin ortalamasından türer. Telden eşik alan
            tezgahlar etkilenmez — telde alt sınır diye bir şey yoktur.
          </span>

          <Tabs
            tabs={katalog.facilities.map((f) => ({ id: f.id, label: f.name }))}
            active={secili ?? ""}
            onChange={setTesisId}
            panelId="tezgah-listesi"
          />

          {tesis && (
            <div id="tezgah-listesi" role="tabpanel" aria-label={`${tesis.name} tezgahları`}>
              <Section title={tesis.name} count={tesis.machines.length}>
                <div className="alp-oto-izgara">
                  {tesis.machines.map((m) => {
                    const r = rozet(m, katalog.stalenessS, bilinmiyor);
                    return (
                      <Card key={m.id} title={m.name} subtitle={m.model ?? undefined}>
                        <div className="flex flex-col items-start gap-3">
                          <Badge tone={r.tone} dot>
                            {r.label}
                          </Badge>
                          <span className="type-help text-muted-foreground">
                            {aciklama(m, katalog.stalenessS, bilinmiyor)}
                          </span>
                          {/* Erişilebilir ad hangi tezgah olduğunu SÖYLEMELİ:
                              ızgarada dört düğme de "İzle" yazar ve ekran
                              okuyucu bunları ayırt edemezdi (paket aynı tuzağı
                              `Tag.removeLabel` için de işaretler). */}
                          <Button
                            size="sm"
                            variant="secondary"
                            aria-label={`${m.name} tezgahını izle`}
                            onClick={() => izle(m.id)}
                          >
                            İzle
                          </Button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </Section>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
