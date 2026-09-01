# Tesis/tezgah seçimi arayüzde; katalog backend'de, kaynak tezgah başına

Arayüz **karşılama → tezgah seçimi → izleme** akışıyla açılıyor. Seçim
iki kademeli: önce **tesis**, sonra o tesisteki **tezgah** (katalog: 4 tesis
× 4 tezgah). Seçilen tezgah topbar'da her zaman yazar ve "Değiştir" ile
yeniden seçilir.

Bu, ADR-0005'in "çoklu-tezgah UI/orkestrasyonu MVP'de yok" maddesini
**arayüz tarafında** günceller. ADR-0005'in asıl kararı (veri modeli
tezgah-bağımsız, Tezgah birinci sınıf) aynen geçerlidir — zaten bu değişikliği
ucuz kılan da odur.

## Kararlar

1. **Katalog yapılandırmadır ve backend'de durur.** Tesis/tezgah adları
   `backend/app/machines.py` içinde durur, telden gelmez: Promos3 telgrafında
   tesis/tezgah kavramı yoktur (izleme ünitesi, kanal, özellik vardır).
   Backend'e tesis/tezgah alanı yine EKLENMEDİ — `app/machines.py` kod içi
   bir yapılandırma dosyasıdır, veri modelinin parçası değildir.

   Bu ADR'nin önceki sürümünde katalog `frontend/src/domain/facilities.ts`
   içindeydi. Adların yapılandırma olduğu gerekçe aynen geçerli; değişen
   yalnız nerede durduğu. Taşınma sebebi: üç kaynakla tezgah→kaynak bağlaması
   zaten backend'de olmak zorunda, ve katalog frontend'de kalsaydı aynı
   bağlama iki yerde tutulur, iki yer arasındaki uyuşmazlıklar da sessiz
   olurdu.

2. **Canlı kaynak artık tek değil, tezgah başınadır.** Üç kaynak üç ayrı
   tezgaha bağlıdır: `provis` (gerçek PROVIS ağ geçidi, Promos3 UDP 1789) →
   `tesis-a/tezgah-1`; `promos3-sim` (`promos3_sim.exe --stream`, Promos3 UDP
   1790) → `tesis-a/tezgah-2`; `csv` (CSV tekrar oynatma, artık **süreç
   içi**) → `tesis-a/tezgah-3`. Kalan 13 tezgahın kaynağı yok. Katalogdaki
   `hasLiveSource` bayrağı ve `LIVE_MACHINE_ID` sabiti kalktı; yerini tezgah
   başına `SourceSpec` aldı (`app/machines.py`).

   Bu bir **gösterim (demo) bağlamasıdır**: amaç dört tesisi de doldurmak
   değil, üç farklı kaynağın aynı anda, birbirine karışmadan, ayrı tezgahlar
   altında göründüğünü göstermektir.

3. **Kaynağı olmayan tezgahta ekran dürüstçe boştur — aynen geçerli.** Akış
   hiç kurulmaz ve ekrana boş durum verilir; bağlantı durumu `no-source`'tur.
   Bu bir arıza DEĞİLDİR ve öyle gösterilmez — hangi tezgahın yayın yaptığı
   daha SEÇİM ekranında yazar.

   Üstüne bir kademe eklendi: "kaynak yok" ile "kaynak var ama bağlı değil"
   karşılama ekranında **ayrı** gösterilir (boş nokta / dolu-ama-`warning`
   nokta) — kartın bağlantı durumu `GET /api/machines`'in `connected`
   alanından, yani o anki **gerçek** durumdan gelir. Yapılandırılmış ama
   düşmüş bir kaynağı yeşil göstermek, kaçınılması gereken hatanın ta
   kendisidir.

   Kritik ayrıntı aynen geçerli: kancayı kapatmak tek başına yetmez, `useLive`
   kapatılınca son kareyi elinde tutar (duraklatmanın istenen davranışı
   budur). Bu yüzden kaynaksız tezgaha ayrı bir boş durum verilir; yoksa bir
   tezgahın verisi başka bir tezgahın adı altında görünürdü — projenin
   baştan beri kaçındığı hata (bkz. `basla.bat` başlığındaki madde 4 ve 6).

4. **Tezgah değişince kabuk baştan kurulur — aynen geçerli**
   (`key={machineId}`). Alarm onay damgaları, grafik adları ve duraklatma
   tezgaha özeldir; taşınsalardı bir tezgahın onayı başka tezgahın alarmına
   düşerdi.

5. **Karşılama ekranı artık gerçek bir kapıdır.** `/` her zaman karşılamayı
   gösterir, `/tezgah` `/`'a yönlenir (tek seçici kalsın diye), ve `?tezgah`
   olmadan `/canli`'ye gelen istek de `/`'a döner. Tezgah seçilmeden izleme
   ekranına girilemez.

   Bu ADR'nin önceki sürümü açılış cümlesinde zaten "karşılama → tezgah
   seçimi → izleme" yazıyordu, ama kod bunu karşılamıyordu: `/` doğrudan
   `/canli`'ye yönleniyor, ve `?tezgah` verilmeyince kabuk sessizce
   `DEFAULT_MACHINE_ID`'ye düşüyordu — yani uygulama sormadan A/1'i izlemeye
   başlıyordu. `DEFAULT_MACHINE_ID` kalktı; bu dal o boşluğu kapattı.

## Sonra ne gelir

Katalog hâlâ kod içi yapılandırmadır (`app/machines.py`); DB'ye taşınması
ayrı bir fazdır. Kaynak artık tezgah başına ayrışmış olsa da üçü de bir
gösterim bağlamasıdır — kalan 13 tezgaha gerçek bir gateway bağlanması
(tezgah başına ayrı Promos3 ağ geçidi/port ya da tezgah kimliği taşıyan tek
bir akış) henüz yapılmadı. Bu ADR bunlardan biri gerçekleştiğinde yine
güncellenmelidir.
