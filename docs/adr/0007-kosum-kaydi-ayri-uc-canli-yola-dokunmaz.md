# Koşum kaydı ayrı bir uçtan gelir; canlı yola dokunmaz

Arayüzde üçüncü bir sekme var: **Tam Koşum** — CSV korpusunun TAMAMI tek bir
grafikte. Canlı İzleme aynı CSV'den beslenir ama koşumun tamamını hiçbir zaman
gösteremez, ve bu bir eksiklik değil canlı akışın tanımıdır.

Bu ADR, ADR-0006'nın tezgah→kaynak bağlamasını **okuma tarafında** genişletir;
oradaki kararların hiçbirini değiştirmez.

## Neden ayrı bir yol gerekti

Canlı ekran KAYAN BİR PENCERE gösterir (`live.WINDOW` = 120 örnek) ama ünite
başına 131 an vardır. Tur başa sardıkça pencerenin başından dökülür, yani
koşumun tamamı canlı yoldan GÖRÜLEMEZ. Pencereyi büyütmek yanlış çözüm
olurdu: pencere canlı izlemenin bir parametresidir, arşiv okumanın değil.

## Kararlar

1. **Koşum kaydı `GET /api/kosum`tan gelir ve dosyaları baştan sona okur.**
   Kurucu `backend/app/kosum.py`'dir; hub'a, SSE akışına ve DB'ye HİÇ
   dokunmaz. Canlı yolun bozulmaması bir dikkat meselesi değil, yapının
   sonucudur — `csv_replay.py` aynı 131 anı döngüyle hub'a beslemeye aynen
   devam eder.

2. **`/api/measurements` bu iş için KULLANILMADI.** O uç CSV sim'in yazdığı
   SQLite tablosunu okur: tablo budanır (varsayılan 60 dk), 500 satırda
   kırpılır ve tekrar döngüsünün turları iç içe girer. Tek ve temiz bir koşum
   oradan çıkarılamaz. İki uç ayrı sorular sorar ve ayrı kalır.

3. **Kayıt TEK GEÇİŞTE kurulur; taban ortalaması da aynı okumadan çıkar.**
   `compute_baselines`i ayrıca çağırmak 262 dosyayı ikinci kez okumak ve
   ortalamanın tanımını iki yerde tutmak olurdu. Tanımın aynı kaldığı testle
   bağlanmıştır (`test_kosum.py`) — ayrılsalardı canlı eşik ile koşum
   grafiğinin altındaki ortalama aynı veriden iki farklı sayı gösterirdi.

4. **Kayıt süreç boyunca değişmez, o yüzden bir kez kurulup saklanır.**
   `veri/` altındaki 262 dosya statiktir ve tekrar oynatma onları yalnızca
   OKUR. Kuruluş `asyncio.to_thread` + kilit ile yapılır: ~0,5 sn'lik okuma
   olay döngüsünü bloke etmesin, iki eş zamanlı ilk istek de aynı işi iki kez
   yapmasın.

5. **Sekme YALNIZ CSV kaynaklı tezgahta basılır.** Koşum kaydı `veri/`
   altındaki korpustur ve o korpus TEK BİR tezgaha bağlıdır (ADR-0006 madde
   2). Sekme her tezgahta dursaydı, gerçek PROVIS tezgahının navigasyonu
   BAŞKA bir tezgahın ölçümlerini vaat ederdi — projenin baştan beri
   kaçındığı hata. Backend aynı kuralı uygular: kaynağı CSV olmayan tezgahta
   `/api/kosum` 404 döner. Kural iki yerde de aynıdır ve tek cümleyle
   söylenir: **koşum kaydı CSV kaynağının özelliğidir, her tezgahın değil.**

   Rota yine de her tezgah için çözülür ve ekran kaydın neden olmadığını
   SÖYLER. Elle yazılmış bir adresi sessizce karşılamaya atmak, ADR-0006
   madde 3'ün "dürüstçe boş" kuralının tersiydi.

6. **Telde AN GÖNDERİLMEZ: takvim günü ve günün saati AYRI gider.** CSV'nin
   zamanı duvar saatidir (tezgahın dışa aktardığı yerel an), bir UTC zaman
   noktası değil. Naif bir ISO an gönderilseydi arayüz onu tarayıcı diliminde
   çözer, tasarım sisteminin `formatDateTime`i İstanbul'a çevirir ve iki dilim
   tutmayan her makinede koşum saatleri KAYARDI. Tasarım sistemi ADR-0005 de
   aynı ayrımı koyar: an ile takvim günü ayrı kavramlardır. Tarih pakete
   `formatCalendarDay` ile biçimletilir, saat olduğu gibi basılır.

7. **Yedi serinin ortak eşik çizgisi ÇİZİLMEZ.** Paketin `LineChart`ı tek
   `referenceLine` alır (dizi değil — canli-route.tsx'teki aynı not) ve
   yedi serinin ortak bir sınırı yoktur; çizilecek tek çizgi hepsinin
   limitiymiş gibi okunurdu. Ortalamalar grafiğin altında SAYIYLA yazılır.
   Eksenin otomatik ölçekli olduğu ve gösterilen aralık da açıkça basılır —
   canli-route.tsx'in EKSEN NOTU'yla aynı kural.

8. **"Kayıt YOK" ile "kayıt OKUNAMADI" ayrı cevaplardır (404 / 503) ve ekran
   suçluyu doğru adlandırır.** 404 yapılandırmadır (madde 5: kaynağı CSV
   olmayan tezgah), 503 arızadır: katalog CSV kaynağını VAAT ETMİŞTİR ama
   korpus yerinde değildir. İkisi tek koda düşseydi `veri/`si eksik deploy
   edilmiş bir kurulum ekranda "bu tezgahın koşumu yok" derdi — yanlış,
   üstelik kimseyi dosyalara bakmaya göndermeyen bir cümle.

   Arayüz de aynı ayrımı taşır (`KosumHata.cevapVerdi`): sunucu cevap
   verdiyse suçlanan ağ değil KAYNAKTIR. Her hatayı "Backend'e ulaşılamadı"
   diye basmak, bu projenin bir kez düştüğü hatanın aynısıydı — o zaman da
   CSV tezgahındaki bir kesinti Promos3 ağ geçidine yıkılmıştı (ADR-0006,
   `katalog.ts` `KAYNAK_CUMLEDE`). Sunucunun ham `detail`i AYRI SATIRDA
   basılır: backend metinleri ASCII yazılır ve aksanlı arayüz nesrinin
   ortasına gömülünce bozuk bir cümle gibi okunur.

9. **Palette 9. seri BAŞA SARMAZ, `CHART_OTHER`a katlanır.** Paketin
   `CHART_COLORS` sözleşmesi bunu harfiyen söyler. Modulo ile sarmak 9. seriye
   1.nin rengini verirdi: tek işi çizgileri birbirinden ayırmak olan bir
   grafikte iki farklı sinyal SESSİZCE aynı renge boyanırdı. Bugün 7 seri var
   (2 ünite × 4 yuva − 1 boş yuva), yani sınır bir ünite ya da bir yuva
   eklendiğinde geçilir.

## Sonra ne gelir

Kayıtta CSV'nin `Alarm` kolonu var ama grafikte İŞARETLENMİYOR; koşum
üzerinde alarm anlarını göstermek ayrı bir adımdır. Ham satır tablosu da
bilerek eklenmedi — ekran tek bir soruyu cevaplıyor ("koşum boyunca ne oldu"),
kanıt satırları `/api/measurements`te duruyor.

Tasarım sistemine açılmış `yDomain` + `referenceLine[]` isteği (bkz.
canli-route.tsx) gelirse madde 7 yeniden değerlendirilmelidir.
