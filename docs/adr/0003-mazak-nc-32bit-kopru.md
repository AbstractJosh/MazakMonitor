# Mazak NC = ayrı 32-bit köprü süreci

Mazak NC verisini (çalışan program, güncel takım, parça sayısı, spindle/eksen
yükü) **`NTIFDLL.dll` üzerinden** okuyoruz. Bu DLL **32-bit** olduğu için, onu
yükleyen süreç de 32-bit olmak zorunda; bu yüzden **ayrı bir 32-bit "cihaz
köprüsü" süreci** kuruyoruz. Köprü NTIFDLL ile konuşur ve localhost üzerinden
64-bit backend'e temiz bir yerel API (REST/WebSocket) sunar.

Böylece backend ve UI **64-bit** kalabilir; 32-bit zorunluluğu tek, izole bir
sürece hapsedilir.

## Consequences

- Aynı köprü süreci, gerekiyorsa Prometec UDP gateway'ini de taşıyabilir; ama
  UDP tarafı 64-bit'ten de erişilebildiği için (bkz. ADR-0002) 32-bit zorunluluğu
  yalnız NTIFDLL yüzündendir.
- Mazak API vendor code + password ister (`referans/Provis3/Data/mazak.lic`);
  TCP port 57400.
