# Web + kiosk kabuğu, tümü offline LAN

Uygulamayı **web tabanlı** (FastAPI + Vite/React) kurup operatöre **tam ekran
kiosk kabuğu** ile "exe gibi" sunuyoruz; her şey tezgah PC'sinde ve atölye
ağında **internetsiz (offline)** çalışır. Web ≠ internet: LAN'daki ofis PC'leri
de aynı arayüzü tarayıcıyla açar, böylece "ofisten görünürlük" bedava gelir.

## Considered Options

- **Native masaüstü uygulaması** (eski Provis3 gibi Qt): tek makineye kilitli,
  ofis görünürlüğü için ayrı iş gerekir.
- **Web + kiosk (seçilen):** tek kod tabanı hem tezgah başı dokunmatik hem ofis
  tarayıcısı; ALP standart stack'iyle (FastAPI + Vite + @alp/ui) uyumlu.

Neden kaydedildi: Tek-tezgah, offline bir araç için "neden native değil de web?"
sorusunu ileride soran olur — cevap ofis görünürlüğü + tek kod tabanı.
