# Bayat veride Alarmlar/Olaylar hala "yok" diyor

Status: open
Role: frontend

`link === "ok"` ama veri BAYAT oldugunda (kaynak susmus, `dataAgeS`
esigi asmis) Alarmlar ekrani hala "Aktif alarm yok", Olaylar ekrani hala
"Henuz olay yok" basiyor.

Neden tam bir yalan degil: liste icerigi GERCEKTEN son alinan durumdur, ve
ayni ekranin ust bari "Veri Yok" diyor - yani ekranin butunu celiskili degil.
Ama bos durumun kendisi, kaynagin o anda sustugunu SOYLEMIYOR.

Bu dalda F3 kapsaminda `baglanti-bosluk.ts` yazildi ve iki ekran artik
`live.link`'i okuyor; bu madde onun BIR ADIM otesi: bagli ama bayat hali.

Yapilacak: bu iki bos duruma "son veri N sn once" niteleyicisi ekle
(`baglanti-bosluk.ts` zaten dogru yer). `dataAgeS` telde mevcut.

Kaynak: 2026-08-11 coklu-kaynak dali, nihai duzeltme dalgasi - uygulayanin
kendi bildirdigi kalinti (b), inceleme "fine to defer, worth tracking" dedi.
