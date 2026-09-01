@echo off
rem ===========================================================================
rem  Mazak Monitor - tek seferlik kurulum
rem
rem  KULLANIM (bu makinede ".\" oneki ZORUNLU, bkz. basla.bat basligi):
rem
rem      .\kur.bat
rem
rem  Ne yapar: backend (uv sync) ve arayuz (npm ci) bagimliliklarini indirir.
rem
rem  HERHANGI BIR AGDA KOSAR: ALP LAN'inda, evde, VPN'siz, vekilsiz. ALP'e ozel
rem  hicbir adim artik SART DEGILDIR; hepsi ya kosullu ya da olumcul olmayan
rem  bir denemedir. Onceki surum bunlari sart kosuyordu ve ALP disindaki bir
rem  makinede daha ilk adimda duruyordu.
rem
rem  ON KOSUL: uv ve Node.js kurulu olmali; npm Node ile birlikte gelir.
rem  Kurulu degilse asagidaki hata mesajlari adresleri verir. Baska HICBIR
rem  sey gerekmez (bun ARTIK KULLANILMAZ; Python'u uv kendisi indirir).
rem
rem  ---------------------------------------------------------------------------
rem  Bedeli odenmis ayrintilar:
rem
rem  1) ALP aginda dis dunyaya dogrudan cikis KAPALI; trafik phantom-wcg
rem     vekilinden gecer ve vekil TLS'i kendi sertifikasiyla ACIP yeniden
rem     imzalar. curl/uv Windows sertifika deposunu okudugu icin calisir ama
rem     Node - dolayisiyla npm - o depoyu OKUMAZ, kendi gomulu kok listesini
rem     kullanir; vekilin imzaladigi zinciri "UNABLE_TO_GET_ISSUER_CERT
rem     _LOCALLY" ile reddeder. Cozum: Windows deposundaki kokleri PEM'e
rem     disari alip NODE_EXTRA_CA_CERTS ile Node'a vermek.
rem
rem  2) PEM'e YALNIZ suresi gecmemis sertifikalar alinir. Depoda 1997'den
rem     kalma suresi dolmus kokler de durur; hepsi paketlenirse TLS
rem     kutuphanesi zinciri suresi dolmus kokten kurup CERT_HAS_EXPIRED
rem     verebiliyor (aynen boyle oldu).
rem
rem  3) npm ci / npm install ilk seferde EPERM ile dusebilir - "operation not
rem     permitted, rename ...": virus taramasi yeni acilan dosyayi kilitliyor,
rem     npm da onu yerine tasiyamiyor. Indirilen paketler kaybolmaz; HEMEN
rem     tekrar denemek yeter. Bu betik bir kez otomatik tekrar dener.
rem
rem  --- Agdan bagimsiz kosmak icin degisenler --------------------------------
rem
rem  4) IC REGISTRY BAGIMLILIGI KALKTI. Arayuz eskiden @alp/design-system'i
rem     10.10.100.220:3000 uzerindeki ic Gitea registry'sinden cekiyordu. O
rem     adres yalniz ALP LAN'inda vardir ve paket PUBLIC NPM'DE YOKTUR
rem     (dogrulandi: 404) - yani ag disindaki bir makinede arayuz HICBIR
rem     BETIKLE kurulamiyordu. Paketin kullanilan yuzeyi depo icine alindi
rem     (frontend/src/alp-local/, vite+tsconfig takma adlariyla baglanir),
rem     boylece "npm ci" artik yalniz public npm'e gider.
rem
rem     Ekran dosyalarinin import satirlari DEGISMEDI: hepsi hala
rem     "@alp/design-system"den okur. Paket bir gun yeniden erisilebilir
rem     olursa src/alp-local/ ve o takma adlar silinir, package.json'a
rem     bagimlilik geri eklenir; tek satir ekran kodu degismez.
rem
rem     frontend/.npmrc'deki @alp kapsam yonlendirmesi BILEREK DURUYOR: bugun
rem     hicbir paket o kapsami kullanmadigi icin npm o adrese HIC gitmez, ama
rem     paket geri geldiginde ek ayar gerekmez.
rem
rem  5) SERTIFIKA ADIMI OLUMCUL DEGIL. Madde 1'deki PEM yalnizca TLS'i ACAN
rem     bir vekil VARSA gerekir; ALP disinda vekil yoktur ve adim anlamsizdir.
rem     Eskiden yine de ":sertifika_hata" ile kurulumu BITIRIYORDU. Artik
rem     denenir, olmazsa UYARI verilip gecilir. PEM uretilemediginde
rem     NODE_EXTRA_CA_CERTS hic set EDILMEZ - var olmayan bir yola isaret eden
rem     bu degisken Node'da butun TLS'i cokertir, yani YANLIS degisken HIC
rem     degiskenden KOTUDUR.
rem
rem  6) BACKEND ONCE KURULUR. Ikisi bagimsizdir ve backend public PyPI'dan
rem     gelir; arayuz herhangi bir sebeple duserse backend calisir kalsin.
rem ===========================================================================

setlocal EnableExtensions
cd /d "%~dp0"

where uv >nul 2>nul || goto :yok_uv
where npm >nul 2>nul || goto :yok_npm

rem --- [1/3] Kok sertifika paketi -------------------------------------------
rem Madde 5: denenir, olumcul DEGILDIR.
echo.
echo [1/3] Kok sertifika paketi hazirlaniyor (vekil TLS'i icin, madde 1-2)...
set "CA_PEM=%USERPROFILE%\.alp-kok-ca.pem"
rem Cert: PSDrive KULLANILMAZ: bu makinelerde modul otomatik yuklemesi kapali
rem oldugundan "Cannot find drive 'Cert'" verir. .NET X509Store dogrudan calisir.
powershell -NoProfile -Command "$now = Get-Date; $all = @(); foreach ($n in 'Root','CA') { $s = New-Object System.Security.Cryptography.X509Certificates.X509Store($n, 'LocalMachine'); $s.Open('ReadOnly'); $all += $s.Certificates; $s.Close() }; $ok = $all | Where-Object { $_.NotAfter -gt $now -and $_.NotBefore -lt $now }; $p = foreach ($x in $ok) { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($x.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----' }; $p | Set-Content $env:USERPROFILE\.alp-kok-ca.pem -Encoding ascii" 2>nul

if exist "%CA_PEM%" (
    set "NODE_EXTRA_CA_CERTS=%CA_PEM%"
    echo       Hazir.
) else (
    echo       UYARI: sertifika paketi uretilemedi.
    echo       Vekil arkasinda DEGILSENIZ bu normaldir; kurulum devam ediyor.
    echo       TLS hatasi alirsaniz madde 1-2'ye bakin.
)

rem Vekil muafiyeti. Bugun hicbir bagimlilik LAN'daki registry'den gelmiyor
rem (madde 4), yani bu satir bir sey DUZELTMIYOR; paket geri geldiginde
rem gerekecegi icin duruyor ve hicbir agda zarari yok.
rem "if defined" SART: NO_PROXY tanimsizsa duz "%NO_PROXY%,10.10..." yazimi
rem degiskene "%NO_PROXY%" metnini OLDUGU GIBI koyar (cmd cozemedigi yuzdeyi
rem silmez, birakir) ve npm onu ana adi sanir.
if defined NO_PROXY (set "NO_PROXY=%NO_PROXY%,10.10.100.220") else (set "NO_PROXY=10.10.100.220")
set "no_proxy=%NO_PROXY%"

rem --- [2/3] Backend --------------------------------------------------------
echo.
echo [2/3] Backend bagimliliklari kuruluyor (uv sync)...
uv sync --directory backend || goto :backend_hata
echo       Tamam.

rem --- [3/3] Arayuz ---------------------------------------------------------
echo.
echo [3/3] Arayuz bagimliliklari kuruluyor (npm ci)...
rem DIKKAT: if-blogu icindeki echo'larda parantez KULLANMA - kapatan ")" blogu
rem echo ortasinda bitirir ve cmd "... was unexpected at this time" ile duser.
rem DIKKAT: Windows'ta npm bir EXE degil, npm.cmd yani BAT dosyasidir. Baska bir
rem bat icinden "call"suz cagrilirsa denetim ona GECER ve GERI DONMEZ - betigin
rem kalani sessizce hic calismaz. Her npm cagrisi "call" ile.
rem Tek seferlik kurulumda dogru komut "npm ci"dir: package-lock.json'i birebir
rem uygular, surumleri yeniden cozmez. Ama npm ci kilit dosyasi yoksa ya da
rem package.json ile uyusmuyorsa kesin hata verir; o durumda da, madde 3'teki
rem tarama kilidinde de yedek deneme "npm install" olur.
rem
rem "--no-audit --no-fund": ikisi de registry'ye EK istek atar ve kisitli agda
rem kurulumu bagimsiz bir nedenden dusurebilir. Kurulum icin gereksizdirler.
pushd frontend
call npm ci --no-audit --no-fund
if errorlevel 1 (
    echo       Ilk deneme dusdu; npm install ile tekrar deneniyor - kilit uyumsuzlugu ya da virus taramasi kilidi, madde 3...
    call npm install --no-audit --no-fund || goto :frontend_hata
)
popd
echo       Tamam.

echo.
echo ===========================================================================
echo   Kurulum tamam.
echo.
echo   Calistirmak icin:      .\basla.bat          (tek kip; A/2 SENTETIKTIR)
echo   Testler icin:          cd backend ^&^& uv run pytest
echo                          cd frontend ^&^& npm run lint
echo ===========================================================================
goto :son

rem --- Hatalar -------------------------------------------------------------
:yok_uv
echo HATA: "uv" bulunamadi. Kurulum: https://docs.astral.sh/uv/
echo       (winget install astral-sh.uv)
echo       DIKKAT: winget PATH'i gunceller ama ACIK olan kabuk bunu GORMEZ;
echo       kurulumdan sonra YENI bir terminal acin.
goto :son

:yok_npm
echo HATA: "npm" bulunamadi. npm, Node.js ile birlikte kurulur.
echo       Kurulum: https://nodejs.org/  (winget install OpenJS.NodeJS.LTS)
goto :son

:backend_hata
echo HATA: "uv sync" dusdu. Cikti yukarida; en sik neden ag/vekil sorunudur.
goto :son

:frontend_hata
popd
echo HATA: arayuz kurulumu iki denemede de dusdu. Cikti yukarida.
echo.
echo       Once HATA KODUNU okuyun, hepsi ayri bir sey soyler:
echo         UNABLE_TO_GET_ISSUER_CERT_LOCALLY  sertifika, madde 1-2
echo         E403 / E407 Tunnel or SSL Forbidden  vekil, madde 1
echo         EPERM / rename                       tarama kilidi, madde 3
echo.
echo       Elle sinamak icin - bu satiri once kosun, yoksa asagidaki komut
echo       kendi ortami olmadigi icin ILGISIZ hata verir. Betigin setlocal'i
echo       bitince ayar kaybolur, o yuzden tekrar gerekir:
echo         set "NODE_EXTRA_CA_CERTS=%%USERPROFILE%%\.alp-kok-ca.pem"
echo.
echo         npm ping --registry https://registry.npmjs.org/
goto :son

:son
endlocal
