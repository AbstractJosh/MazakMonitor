# Veri modeli tezgah-bağımsız, MVP tek-tezgah deploy

Veri modelini **Tezgah birinci sınıf varlık** olacak şekilde kuruyoruz (bir
tezgah, altında bir veya çok izleme ünitesi/kanal); ama MVP'yi **yalnız bu tek
Mazak'a** kurup test ediyoruz. Çoklu-tezgah UI/orkestrasyonu (filo panosu,
tezgah bazlı yönetim) MVP'de **yok**.

Neden: Bu tek tezgahta zaten iki izleme ünitesi var, yani model "bir tezgah +
çok cihaz"ı hâlâ taşımak zorunda; "Tezgah"ı birinci sınıf yapmak şimdi neredeyse
bedava, ama şemaya "tek tezgah" varsayımı gömülürse ikinci tezgah geldiğinde
yeniden şekillendirme acı verir. İleride başka tezgah gelmesi somut bir olasılık.
