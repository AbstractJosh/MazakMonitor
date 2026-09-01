# Gercek kaynak adaptoru (Prometec UDP / NC koprusu)

Status: open
Role: backend

MazakFolly adaptoru (app/adapters/folly.py) gelistirme icindir; gercek veri
icin ADR-0002'nin onunu acmak gerekiyor:

- Tezgah basinda Wireshark ile UDP cerceve/telegram formatini dogrula
  (192.168.222.17:1789). Dogrulanirsa ADR-0002 accepted'a cekilir.
- Format cozulunce `app/adapters/` altina ayni `LiveHub`'a yazan ikinci
  adaptor eklenir; API sozlesmesi (domain.LiveState) degismez.
- Alarm/limit verisi ancak bu kaynakla gelir; `/api/alarms` o zaman dolar
  (frontend'in alarm panosu hazir bekliyor).

Bu is atolye tarafinda planlama gerektirir (tezgaha erisim).
