---
status: proposed
---

# Prometec izleme = UDP gateway (PCAN kartı değil)

Prometec izleme üniteleriyle (10659/10663) haberleşmeyi, mevcut kurulumdaki
**CAN→Ethernet gateway üzerinden düz UDP** ile yapıyoruz (`192.168.222.17:1789`,
`PROVISsettings.ini [CAN] PCANGateway=1`), yerel PEAK/PCAN kartı + `CanApi2.dll`
yolunu kullanmıyoruz.

Sonuç: ekstra donanım gerekmez ve CAN tarafındaki 32-bit zorunluluğu kalkar —
64-bit backend gateway'e doğrudan UDP soketiyle bağlanabilir.

## Status

**proposed** — UDP çerçeve/telegram formatı henüz tezgah başında Wireshark ile
canlı doğrulanmadı; doğrulanınca **accepted**'a çekilecek. Doğrulama başarısız
olursa PCAN kartı yoluna dönmek gerekebilir (bu yüzden ADR).
