"""Promos3 / Prometec okuma yolu — CAN-over-UDP telgrafini alan modeline cevirir.

Kaynak: promos3-c/analysis_jul_28_1_0_0.md (v2). Bu paket o raporun byte
seviyesindeki bulgularinin TEMIZ ODA Python karsiligidir; promos3-c/src'deki C
okuyucunun ayni tasarimi (guven merdiveni + iki kalibrasyon noktasi) korunur.

Kapsam: yalniz ALMA yolu (cihaz -> uygulama). Bu kurulum bir Provis2 / "MC_"
kutusudur (dagitim grubu 1).

Iki sey RAPORDA DA ACIK UCLU (§0.5) ve burada da oyle isaretlidir:
  1) mesajin toplam uzunlugunun akista nerede durdugu  -> transport.Reassembler
  2) group/command/length alanlarinin TEL uzerindeki yeri -> messages.parse_header
Bunlar bir yakalama (LogCANMessage=1 ya da tek UDP capture) ile netlesir.
Ikisi de tek noktada toplanmistir ki kalibrasyon tek dosya degisikligi olsun.
"""
