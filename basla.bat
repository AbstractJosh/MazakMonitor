@echo off
rem ===========================================================================
rem  Mazak Monitor - gelistirme baslaticisi
rem
rem  KULLANIM (bu makinede ".\" oneki ZORUNLU):
rem
rem    Explorer'da cift tiklamak calisir. Terminalden cagirirken ".\" yazin;
rem    duz "basla.bat" CALISMAZ. Nedeni bu makinede
rem    NoDefaultCurrentDirectoryInExePath=1 olmasi (kurumsal sertlestirme):
rem    cmd, program ararken calisma dizinini KULLANMAZ ve dosya yerinde olsa
rem    bile "is not recognized" der.
rem
rem    ILK KURULUM: bagimliliklar bir kez  .\kur.bat  ile kurulur; bu betik
rem    kurulum yapmaz, eksikse kur.bat'a yonlendirir.
rem
rem      .\basla.bat            Backend + arayuz + simulator. Uc kaynak da
rem                             ayri tezgahlara baglidir:
rem                               Tesis A / Tezgah 1  PROVIS   (UDP 1789)
rem                               Tesis A / Tezgah 2  SIM      (UDP 1790)
rem                               Tesis A / Tezgah 3  CSV      (surec ici)
rem                             Hangi tezgahin yayin yaptigi karsilama
rem                             ekraninda yazar.
rem
rem      .\basla.bat dur        Baslatilan her seyi durdurur.
rem
rem  ---------------------------------------------------------------------------
rem  Bedeli odenmis ayrintilar (her biri bir hatadan ogrenildi):
rem
rem  1) Vite'a --host VERILMEK ZORUNDA. Varsayilanda yalniz IPv6 ([::1]:5173)
rem     dinler; tarayici IPv4 denedigi icin HATA SAYFASI gosterir. ("localhost"
rem     ile curl calisir ama tarayici calismaz - kafa karistirir.)
rem     Verilen deger 127.0.0.1 DEGIL 0.0.0.0'dir; nedeni madde 8.
rem
rem  2) Uc kaynak bayragi da ACIKCA yazilir (PROMOS3_ENABLED, PROMOS3_SIM_ENABLED,
rem     CSV_REPLAY_ENABLED = true); "bos deger" ile kapatilmaya CALISILMAZ.
rem     Windows'ta bos deger ATAMAK IMKANSIZ: cmd'de "set X=" degiskeni SILER,
rem     PowerShell'de "$env:X=''" de siler. Ikisinde de pydantic varsayilana
rem     doner ve adaptor sessizce kosar ya da sessizce KAPANIR.
rem     (Regresyon: backend/tests/test_machines.py::test_kapali_bayrak_kaynagi_KATALOGDAN_dusurur
rem     - acikca kapatilan bir bayragin ilgili tezgahi katalogdan tumden dusurdugunu dogrular.)
rem
rem  3) Ortam degiskenleri BU BETIGIN ortamina yazilir; alt pencereler miras
rem     alir. Onceki surum uzun bir PowerShell tek-satirini "start" icine
rem     gomuyordu; ic tirnaklar yenildigi icin PROMOS3_FEATURE_NAMES hic
rem     ulasmiyor, grafikler sessizce "Kanal N" kaliyordu. Calisma dizini artik
rem     ":baslat"in -WorkingDirectory bagimsizindan gelir; ic ice tirnak yine
rem     gerekmez (madde 11).
rem
rem  4) SIMULATORUN DINLEDIGI PORT YOKTUR (--stream yalniz gonderir). Bu yuzden
rem     "dur" onu porta gore bulamaz; pencere basligi da tutmazsa SAG KALIR ve
rem     bir sonraki kosumda sentetik veriyi gercek gibi gosterir (mock gateway
rem     ile aynen boyle oldu). Artik surec adina gore de oldurulur (dur), ayrica
rem     kendi surecimizi baslatmadan once onceden kosan her kopya temizlenir
rem     (madde 6) - artik "reddet" degil "temizle ve devam et" stratejisi
rem     gecerlidir, cunku PROVIS ile SIM ayni kosumda birlikte calisir.
rem
rem  5) Ozellik adlari (VIBRATION vb.) ARTIK YAPILANDIRMADAN VERILMEZ: TELDEN
rem     gelirler. MC_GIVEKANAL (0x0E) cevabi SKanalRecV40'tir ve operatorun
rem     verdigi etiketler +0x4D'deki 4 yuvada durur. PROMOS3_FEATURE_NAMES
rem     yalnizca yedek gecersiz kilmadir; hicbir kipte set edilmesi gerekmez.
rem
rem  6) SIMULATOR MUTLAKA --stream ILE KOSAR. promos3_sim.exe'nin VARSAYILAN
rem     kipi --serve'dur: UDP 1789'u BAGLAR ve yalniz GELEN ISTEKLERI cevaplar.
rem     Backend ise SALT OKUYUCUDUR (ADR-0004) - sokete hicbir sey yazmaz,
rem     dolayisiyla hicbir zaman istek SORMAZ. Sonuc: exe'yi cift tiklamak
rem     "serving : UDP :1789" yazar, saglikli GORUNUR, ama tek bayt gondermez
rem     ve ekran bos kalir. Ustelik --serve'un 0.0.0.0:1789 bagi PROVIS'in
rem     gercek gateway dinleyicisiyle CAKISIR (SO_REUSEADDR ile son baglanan
rem     datagramlari kapar), yani gercek kaynak bile susturulabilir.
rem     Teshis: /api/live -> wire.datagrams 0'da takiliysa paket hic ULASMIYOR;
rem     >0 ama parsed 0 ise ulasiyor ama COZULMUYOR (iki ayri sorun).
rem     Bu yuzden kendi --stream surecimizi baslatmadan once ONCEDEN kosan her
rem     simulatoru temizler (asagida). Kendi surecimiz artik 1790'a gonderir
rem     (PROVIS'in 1789'u ile cakismaz), yani bu artik bir "kilit" degil bir
rem     "temizlik"tir.
rem
rem  7) Bu betikte echo edilen DEGISKENLERIN ICINDE ">" OLMAZ. "set" tirnakli
rem     oldugu icin atama sirasinda sorun cikmaz, ama "echo ... %VAR% ..."
rem     satirinda kabuk onu YONLENDIRME sanir: "SIM - ... -> UDP 1789" degeri
rem     [1/3] satirini ekrana degil "UDP" ADLI DOSYAYA yazdi (depo kokunde
rem     bulundu). Ok isareti gerekiyorsa "=>" degil, hic kullanmayin.
rem
rem  8) ARAYUZ LAN IP'SINDEN ACILIR, loopback'ten DEGIL. Bu makinede Chrome
rem     trafigi Websense/Forcepoint DLP eklentisinden geciyor ve loopback'i
rem     ATLAMIYOR: 127.0.0.1:5173 tarayicida hata sayfasi verir. Ayirt edici
rem     isaret sudur - ayni anda "curl 127.0.0.1:5173" CALISIR. Yani sunucu
rem     saglamdir, engelleyen tarayicidir; Vite loglarinda hicbir iz kalmaz.
rem
rem     Cozum: --host 0.0.0.0. Hem loopback'i hem LAN arayuzunu dinler, ve LAN
rem     IP'si DLP eklentisinden GECER (olculdu: 10.x uzerinden ekran acildi).
rem     Madde 1'in sarti da karsilanir - asil kural "IPv6-only birakma"dir,
rem     0.0.0.0 bunu zaten saglar.
rem
rem     DISARI ACILAN YALNIZ VITE'DIR; backend 127.0.0.1:8001'de KALIR. LAN'daki
rem     istemci /api'ye Vite'in kendi vekili uzerinden ulasir (vite.config.ts
rem     "proxy"), yani API'yi ayrica disari acmaya gerek YOK.
rem
rem     IP SABITLENMEZ: ag degisince (kablo/Wi-Fi/VPN) degisir, bu yuzden her
rem     kosumda yeniden bulunur. Bulunamazsa 127.0.0.1'e duser - betik yine
rem     calisir, yalnizca tarayici yine engellenebilir.
rem ===========================================================================

setlocal
cd /d "%~dp0"

if /i "%~1"=="dur" goto :durdur

where uv >nul 2>nul || goto :yok_uv
where npm >nul 2>nul || goto :yok_npm
if not exist "frontend\node_modules" goto :yok_kurulum
rem Klasorun VARLIGI yetmez, DOSYAYA kadar bakilir: temizlenmis ya da yarim
rem kalmis bir kurulumda node_modules VARDIR ama ICI BOSTUR, ve arayuz o halde
rem ACILMAZ. Olculdu: bos bir node_modules ile eski kapi GECIYOR, hata Vite
rem loglarina gomuluyor, betik ise mutlu mesut "acildi" diyordu.
if not exist "frontend\node_modules\vite" goto :eksik_kurulum

rem --- Ortam: alt pencereler bunlari miras alir ------------------------------
rem Uc kaynak bayragi da HER kosumda ACIKCA yazilir; varsayilana birakmak
rem madde 2'de anlatilan sessiz-varsayilan tuzagina davetiyedir.
rem
rem PROVIS ile SIM ayni tel bicimini (Promos3 CAN-over-UDP) konusur, tek fark
rem PORTTUR: PROVIS 1789'u, kendi surecimiz 1790'i dinler/gonderir - backend'de
rem "simulasyon kipi" YOKTUR, iki ayri kaynak vardir.
set "VITE_LIVE_SOURCE=backend"
set "PROMOS3_ENABLED=true"
set "PROMOS3_BIND=127.0.0.1"
set "PROMOS3_PORT=1789"
set "PROMOS3_SIM_ENABLED=true"
set "PROMOS3_SIM_PORT=1790"
set "CSV_REPLAY_ENABLED=true"

rem --- Hazirlik: iki disarida kalan bagimlilik + iki portsuz sag kalan --------
if not exist "promos3-c\done\promos3_sim.exe" goto :yok_sim

rem Klasorun VARLIGI yetmez, DOSYAYA kadar bakilir. IKI unite de kontrol
rem edilir: yalniz 10660'a bakan kapi, 10665 eksik/bos bir checkout'ta GECER
rem ve replay 262 yerine 131 satir/tur yazar - kullanici bunun yarisi eksik
rem oldugunu banner'dan anlayamaz. Asagidaki hata mesaji (:yok_veri) zaten
rem ikisini birden sayiyordu.
if not exist "veri\10660\*.csv" goto :yok_veri
if not exist "veri\10665\*.csv" goto :yok_veri

rem Madde 6: elle cift tiklanan bir simulator VARSAYILAN --serve kipindedir
rem ve 0.0.0.0:1789'u baglar - yani GERCEK PROVIS'in datagramlarini calar.
rem Kendi --stream surecimiz hicbir port baglamaz, ama onceden kosan bir
rem kopya bu riski hala tasir. Baslamadan once temizlenir.
call :sahte_var
if not errorlevel 1 (
    echo       Onceden kosan simulator bulundu, durduruluyor ^(madde 6^).
    call :sahte_oldur
)

rem Madde 4'un ariza sinifi CSV SIM ICIN DE gecerli: portsuzdur, yani
rem :port_kontrol onu GOREMEZ. Kullanici pencereleri elle kapatip "dur"
rem demediyse elle baslatilmis eski bir "python -m app.sim.replay" hayatta
rem kalabilir ve SQLite kilidini tutup asagidaki alembic adimini yaniltici
rem bir hatayla dusurebilir. ALEMBIC'TEN ONCE olmasi bunun icin onemli.
echo.
echo       Onceden kosan CSV sim (varsa) durduruluyor (portsuzdur, port kontrolu gormez).
call :csv_sim_oldur

rem CSV adaptoru artik surec ici oldugu ve HER kosumda yazdigi icin sema HER
rem kosumda guncel olmak zorunda - eskiden bu adim yalniz CSV kipinde kosardi.
echo       Veritabani semasi guncelleniyor (alembic upgrade head)...
pushd backend
uv run alembic upgrade head
set "ALEMBIC_RC=%ERRORLEVEL%"
popd
if not "%ALEMBIC_RC%"=="0" goto :migration_hatasi

:port_kontrol
netstat -ano | findstr LISTENING | findstr ":8001" >nul 2>nul && goto :port_mesgul
netstat -ano | findstr LISTENING | findstr ":5173" >nul 2>nul && goto :port_mesgul

echo.
echo [1/3] Backend baslatiliyor (127.0.0.1:8001, uc kaynak da acik)...
call :baslat "ALP Backend" "%CD%\backend" "uv run uvicorn app.main:app --host 127.0.0.1 --port 8001"

rem Madde 8: 0.0.0.0 = loopback + LAN. Adres asagida, banner'dan once bulunur.
rem npm bir EXE degil, npm.cmd yani BAT'tir: bir .bat govdesinde oneksiz
rem cagrilirsa denetim bir daha DONMEZ, kalan satirlar sessizce kosmaz -
rem "call npm ..." gerekir. Burada gerekmez, cunku komut ":baslat"in actigi
rem YEPYENI bir cmd icinde en ustte kosuyor. Bu satiri :baslat'in disina
rem tasiyan olursa basina "call" koymak ZORUNDA. ("--" npm 7+ surumlerinde
rem bayraklari vite'a gecirir; npm 11 kurulu, ayirici KALIR.)
echo [2/3] Arayuz baslatiliyor (0.0.0.0:5173, kaynak=backend)...
call :baslat "ALP Frontend" "%CD%\frontend" "npm run dev -- --host 0.0.0.0"

echo       backend bekleniyor...
set /a TRY=0
:bekle
set /a TRY+=1
curl -s -o nul http://127.0.0.1:8001/api/health && goto :hazir
if %TRY% GEQ 30 goto :backend_gelmedi
call :bir_saniye
goto :bekle

:hazir
echo       backend hazir.

echo.
echo [3/3] SIMULATOR baslatiliyor...
echo       ####################################################################
echo       #  DIKKAT: A/2 (Tesis A / Tezgah 2) tezgahindaki TUM degerler      #
echo       #  SENTETIKTIR. Tezgahtan gelmiyor; promos3_sim.exe uretiyor.      #
echo       ####################################################################
rem Madde 10: ".\" oneki ZORUNLU - betigin kendi basligindaki kuralin aynisi.
rem Bu makinede NoDefaultCurrentDirectoryInExePath=1 (ortam degiskeni olarak
rem kurulu), yani cmd program ararken CALISMA DIZININI KULLANMAZ; "/D" ile
rem dogru klasore girmek YETMEZ. Oneksiz bicim "promos3_sim.exe is not
rem recognized" der. Bu sessiz bir arizaydi: hata yalniz "ALP Simulator"
rem penceresinde kalir, baslatici pencere [3/3]'u basip normal devam eder ve
rem A/2 sebepsizce BOS durur (/api/live -> wire.datagrams 0'da takilir).
rem Port 1790: PROVIS'in gercek gateway'i 1789'u kullanir; ayni portu iki
rem dinleyici baglayamaz (madde 6).
call :baslat "ALP Simulator" "%CD%\promos3-c\done" ".\promos3_sim.exe --stream 127.0.0.1:1790 --period 200"

:arayuz_bekle
set /a TRY=0
:bekle2
set /a TRY+=1
curl -s -o nul http://127.0.0.1:5173/ && goto :ac
if %TRY% GEQ 40 goto :vite_gelmedi
call :bir_saniye
goto :bekle2

:ac
rem --- Madde 8: LAN IP'yi bul (her kosumda yeniden) --------------------------
rem Loopback arayuzu ve APIPA (169.254.*, "kablo takili degil" adresi) elenir;
rem birden fazla arayuz varsa isletim sisteminin tercih ettigi yol secilir
rem (en dusuk InterfaceMetric) - VPN/sanal adaptor varken dogrusu budur.
rem
rem Cikti DOSYAYA yazilir, "for /f" ile YAKALANMAZ: for /f ('...') komutu tek
rem tirnakla sarar ve PowerShell filtresindeki tek tirnaklar ('Loopback') onu
rem erkenden kapatir. Cift tirnak icinde tek tirnak ise sorunsuz (madde 3'teki
rem "ic tirnak kacisi guvenilmez" notunun kabul ettigi bicim budur).
set "LANIP="
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notlike '169.254.*' } | Sort-Object InterfaceMetric | Select-Object -First 1 -ExpandProperty IPAddress" > "%TEMP%\alp_lanip.txt" 2>nul
set /p LANIP=<"%TEMP%\alp_lanip.txt"
del "%TEMP%\alp_lanip.txt" >nul 2>nul
if not defined LANIP set "LANIP=127.0.0.1"

echo.
echo ===========================================================================
echo   Arayuz:  http://%LANIP%:5173/
echo   API   :  http://127.0.0.1:8001/api/live
echo.
if not "%LANIP%"=="127.0.0.1" echo   NOT: Adres bilerek LAN IP'sidir. Bu makinede Chrome trafigi Websense/
if not "%LANIP%"=="127.0.0.1" echo   Forcepoint DLP eklentisinden geciyor ve loopback'i ATLAMIYOR; 127.0.0.1
if not "%LANIP%"=="127.0.0.1" echo   ve "localhost" tarayicida hata sayfasi verir - ama curl ile calisir.
if not "%LANIP%"=="127.0.0.1" echo   Sunucu saglam, engelleyen tarayici. Ayrintisi: madde 8.
if "%LANIP%"=="127.0.0.1" echo   UYARI: LAN IP bulunamadi, loopback'e dusuldu. Tarayici hata sayfasi
if "%LANIP%"=="127.0.0.1" echo   gosterirse nedeni DLP eklentisidir (madde 8); agi/VPN'i kontrol edin.
echo.
rem Madde 7: bu iki satirin icinde ">" YOK.
echo   Tezgahlar:  A/1 PROVIS 1789  .  A/2 SIM 1790  .  A/3 CSV
echo   A/2 SENTETIKTIR - o tezgahtaki hicbir sayi olcum degildir.
echo.
echo   Durdurmak icin:  .\basla.bat dur
echo ===========================================================================
rem Tarayici da madde 11'e tabidir: "start" ile acilan tarayici betigin STDOUT
rem tutamagini miras alir ve cagirici EOF'u tarayici KAPANANA kadar gormez -
rem sunucular bir yana, tek basina bu bile kosumu asmaya yeter.
powershell -NoProfile -Command "Start-Process 'http://%LANIP%:5173/'" >nul 2>nul
goto :son

rem --- Durdurma ------------------------------------------------------------
:durdur
echo Durduruluyor...
taskkill /FI "WINDOWTITLE eq ALP Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq ALP Frontend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq ALP Simulator*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq ALP CSV Sim*" /T /F >nul 2>nul
rem Porta gore temizlik.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr ":8001"') do taskkill /F /PID %%p >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr ":5173"') do taskkill /F /PID %%p >nul 2>nul
rem SIMULATORUN portu YOK: surec adina gore oldur (madde 4).
call :sahte_oldur
rem CLI CSV sim (python -m app.sim.replay) artik basla.bat tarafindan hic
rem baslatilmiyor, ama elle calistirilmis olabilir - o da portsuzdur, yani
rem madde 4'un ariza sinifi ONUN ICIN DE gecerli. Baslik filtresi etkilesimsiz
rem kosumda (ajan/CI) TUTMAZ: "start" o zaman pencere basligi atamaz ve sim
rem SAG KALIR. Sag kalan yazici DB'ye yazmayi surdurur, ustelik SQLite
rem kilidini tutup bir sonraki kosumun alembic adimini yaniltici bir hatayla
rem dusurebilir.
call :csv_sim_oldur
echo Durduruldu.
goto :son

rem --- Yardimcilar ---------------------------------------------------------
rem Madde 11: PENCERELER "start" ILE ACILMAZ. "start ... cmd /k" ile acilan
rem pencere cagiriciya IKI BAGLA baglidir ve ikisi de yalnizca ETKILESIMSIZ
rem kosumda isirir (ajan, CI, ciktisi boruya alinan kosum):
rem
rem   a) Betigin STDOUT tutamagini MIRAS ALIR. Cikti bir boruya okunuyorsa o
rem      boru sunucular olene kadar kapanmaz: basla.bat kendisi bitmis olsa
rem      bile cagirici EOF bekler ve ASILIR. Olculdu: cikti bir boruya
rem      verildiginde kosum 300 sn'de donmedi - oysa uc sunucu da ayaktaydi,
rem      yani "acilmadi" degil "hic bitmedi" arizasidir.
rem
rem   b) Betigin SUREC AGACINDA kalir. Cagirici bitince arta kalan agaci
rem      toplayan bir ortamda ucu birden sessizce olur: banner yazilir, betik
rem      "acildi" der, saniyeler sonra 8001 de 5173 de kapalidir. Hata yok.
rem
rem Explorer'dan cift tiklarken ikisi de gorunmez (ortada ne boru ne toplayici
rem vardir) - madde 4 ve 9 ile ayni sinif: elle kosarken TUTMAYAN ariza.
rem
rem Start-Process ile acilan surec cagiranin borusunu miras ALMAZ ve onun
rem agacinda DEGILDIR; iki bag da kopar. (Olculdu: pencere her iki bicimde de
rem sag kalabiliyor, ama cagirici yalnizca bu bicimde HEMEN donuyor.)
rem
rem -ArgumentList TEK BIR DIZGEDIR, dizi DEGIL. Dizi verilirse PowerShell
rem parcalari tirnaklar; cmd.exe'ye "/k" ardindan TIRNAKLI bir dizge gider ve
rem dizgenin icinde "&" oldugu icin cmd dis tirnaklari SOYMAZ - tum dizgeyi
rem program adi sanip "is not recognized" der. Tek dizgede hic tirnak yoktur;
rem "&" cmd'ye dogrudan ulasir ve baslik komutunu asil komuta zincirler.
rem
rem "^&" YAZILMAZ: cift tirnak icinde "^" harfi harfidir, yani cmd'ye "^&"
rem ulasir ve oradaki kacis "&"i AYIRICI olmaktan cikarir - ampersan baslik
rem yazisinin parcasi olur ve asil komut HIC KOSMAZ.
rem
rem Baslik "title" ile verilir; start'in "TITLE" bagimsizinin yerini o tutar.
rem Ama ACIK OLSUN: baslik INSAN icindir, :durdur icin DEGIL. Olculdu - bu
rem makinede varsayilan konsol Windows Terminal oldugu icin pencere
rem WindowsTerminal.exe'ye aittir ve cmd.exe'nin kendi penceresi YOKTUR:
rem "tasklist /FI WINDOWTITLE eq ALP Backend*" UCUNDE DE bos doner. Bu
rem :baslat ile gelen bir gerileme DEGILDIR (start ile acilan pencere de ayni
rem terminale dusuyordu); :durdur'u gercekte yurutenler port suzgeci ile
rem surec adi yedekleridir - baslik suzgeci yalnizca eski bir yoldur.
rem
rem %~1 = pencere basligi, %~2 = calisma dizini, %~3 = calistirilacak komut.
:baslat
powershell -NoProfile -Command "Start-Process -FilePath cmd.exe -ArgumentList '/k title %~1 & %~3' -WorkingDirectory '%~2'" >nul 2>nul
exit /b 0

rem Madde 9: bekleme "timeout" ILE YAPILMAZ. timeout stdin YONLENDIRILMISSE
rem "ERROR: Input redirection is not supported" deyip ANINDA doner; o zaman
rem bekleme dongusu bir anda 30/40 turu bitirir ve sunucu saglikliyken bile
rem "ayaga kalkmadi" hatasi verir. Elle cift tiklarken sorun cikmaz - betigi
rem BASKA bir surec cagirdiginda (ajan, CI, PowerShell ciktisi yakalama)
rem stdin yonlendirilmis olur. "ping -n 2 127.0.0.1" iki durumda da ~1 sn
rem bekler ve stdin'e hic dokunmaz.
:bir_saniye
ping -n 2 127.0.0.1 >nul 2>nul
exit /b 0

rem Simulator kosuyor mu? errorlevel 0 = kosuyor, 1 = kosmuyor.
rem Ic tirnak YOK: bat -> powershell aktariminda "\" kacisi guvenilmez.
rem
rem Surec ADINA bakilir, komut satirina DEGIL: yalniz CommandLine'a bakan bir
rem sorgu KENDINI de bulurdu (sorguyu kosturan powershell'in komut satirinda da
rem 'promos3_sim' gecer) ve betik, simulator kapaliyken bile temizlik adimini
rem yanlis calistirirdi. UDP'yi gonderen surec promos3_sim.exe'dir; olculecek
rem olan o.
:sahte_var
powershell -NoProfile -Command "if (Get-Process -Name promos3_sim -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
exit /b %errorlevel%

rem Tek gecis YETMEZ: simulator  cmd -> promos3_sim.exe  zinciridir; ustteki
rem cmd'yi oldurmek altakini yetim birakir ama SUSTURMAZ. Bu yuzden hicbiri
rem kalmayana dek (en fazla 5 gecis) tekrarlanir.
:sahte_oldur
powershell -NoProfile -Command "1..5 | ForEach-Object { $p = Get-Process -Name promos3_sim -ErrorAction SilentlyContinue; if (-not $p) { return }; $p | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }; Start-Sleep -Milliseconds 300 }" >nul 2>nul
exit /b 0

rem CSV SIM'i komut satirina gore oldur (baslik filtresinin yedegi).
rem Surec ADI ayirt edici DEGILDIR ("python.exe"); ayirt eden sey komut
rem satiridir. Yine de ad suzgeci ZORUNLUDUR: yalniz CommandLine'a bakan bir
rem sorgu KENDINI de bulurdu (sorguyu kosturan powershell'in komut satirinda
rem da "app.sim.replay" gecer) - :sahte_var'daki tuzagin aynisi.
rem Zincir cmd -> uv.exe -> python.exe'dir ve UCU DE ayni gecisde alinir:
rem yazan surec python'dur, ama baslik filtresi tutmadiginda geride kalan
rem cmd/uv kabuklari da temizlenmezse her kosumda bir tane birikir.
rem Get-Process kullanilmaz: CommandLine ozelligi PowerShell 7'de vardir, bu
rem satirin kosturdugu "powershell" ise 5.1'dir (orada deger bos gelir).
:csv_sim_oldur
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { @('python.exe','uv.exe','cmd.exe') -contains $_.Name -and $_.CommandLine -like '*app.sim.replay*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>nul
exit /b 0

rem --- Hatalar -------------------------------------------------------------
:port_mesgul
echo HATA: 8001 ya da 5173 zaten kullanimda - baska bir kosum acik olabilir.
echo       Once durdurun:  .\basla.bat dur
goto :son

:yok_sim
echo HATA: promos3-c\done\promos3_sim.exe yok (A/2 tezgahi bunu kullanir,
echo       her kosumda gerekir - artik ayri bir "sim kipi" yok).
echo       Derlemek icin (gcc/MinGW gerekir):
echo         cd promos3-c\done
echo         gcc -std=c11 -O2 -Wall -Wextra promos3_sim.c -o promos3_sim.exe -lws2_32
echo       Ayrintilar: promos3-c\done\done_run.txt
goto :son

:yok_veri
echo HATA: veri\10660 klasorunde CSV yok (A/3 tezgahi bunu okur, her kosumda
echo       gerekir - artik ayri bir "csv kipi" yok).
echo       262 olcum CSV'si depoda veri\10660 ve veri\10665 altinda durur.
echo       Eksikse depoyu guncelleyin:  git pull
goto :son

:migration_hatasi
echo HATA: "alembic upgrade head" basarisiz (cikis kodu %ALEMBIC_RC%).
echo       Elle calistirip hatayi okuyun:
echo         cd backend
echo         uv run alembic upgrade head
goto :son

:yok_uv
echo HATA: "uv" bulunamadi. Kurulum: https://docs.astral.sh/uv/
goto :son

:yok_npm
echo HATA: "npm" bulunamadi. Arayuz bagimliliklari npm ile kurulur ve kosar;
echo       npm Node.js ile birlikte gelir.
echo       Kurulum: https://nodejs.org/  (winget install OpenJS.NodeJS.LTS)
goto :son

:yok_kurulum
echo HATA: arayuz bagimliliklari kurulu degil (frontend\node_modules yok).
echo       Once kurulumu calistirin:  .\kur.bat
goto :kurulum_notu

:eksik_kurulum
echo HATA: arayuz bagimliliklari EKSIK - node_modules var ama ici bos.
echo       Yarim kalmis ya da temizlenmis bir kurulum; arayuz bu haliyle acilmaz.
goto :kurulum_notu

rem Kurulum ARTIK HER AGDA tamamlanir: arayuzun ic registry bagimliligi
rem (@alp/design-system) kaldirildi ve yerini depo icindeki src/alp-local/
rem aldi. Yani bu nota dusen biri gercekten kurulumu kosmamistir - eskisi
rem gibi "ag disindasin, yapacak bir sey yok" durumu KALMADI.
:kurulum_notu
echo.
echo       Kurulum:  .\kur.bat
echo       Herhangi bir agda calisir; ALP LAN/VPN gerekmez.
echo.
echo       Backend BUNDAN BAGIMSIZDIR ve tek basina kosar:
echo         cd backend ^&^& uv run uvicorn app.main:app --reload --port 8001
echo       Saglama:  curl http://127.0.0.1:8001/api/health
goto :son

:backend_gelmedi
echo HATA: backend 30 saniyede ayaga kalkmadi. "ALP Backend" penceresindeki
echo       hatayi okuyun (en sik: 8001 mesgul ya da UDP 1789/1790 baska surecte).
goto :son

:vite_gelmedi
echo HATA: arayuz 40 saniyede ayaga kalkmadi. "ALP Frontend" penceresine bakin
echo       (en sik: bagimliliklar kurulu degil - once .\kur.bat calistirin).
goto :son

:son
endlocal
