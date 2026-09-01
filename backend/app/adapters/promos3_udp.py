"""Prometec CAN-over-UDP giris adaptoru — ADR-0002'nin gercek kaynagi.

Gateway (atolyede 192.168.222.17:1789) her datagramda 36 baytlik CAN kayitlari
yayinlar. Zincir: datagram -> CAN cerceveleri -> unite basina yeniden
birlestirme -> saglama toplamiyla KIMLIKLENDIRME -> govde cozme -> hub.

Bu adaptor SALT OKUYUCUDUR (ADR-0004): sokete hicbir sey yazilmaz, cihaza
komut gonderilmez. Yalniz dinler.

Ayni yol, tezgah olmadan simulatorle beslenir:

    promos3-c\\done\\promos3_sim.exe --stream 127.0.0.1:1789 --period 200

Simulator gercek tel bicimini bayt bayt uretir (kendi --selftest'i bunu
dogrular), bu yuzden burada "simulasyon kipi" diye bir dal YOKTUR: kaynak ister
simulator ister tezgah olsun, cozme yolu birebir aynidir. Eski
tools/mock_gateway.py'nin aksine simulator kendi varsayimlarimizi geri
yansitmaz — dolayisiyla bu yolun dogrulugu artik dairesel degildir.
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from app.hub import LiveHub
from app.promos3.messages import identify_answer
from app.promos3.transport import AnswerReassembler, split_datagram

log = logging.getLogger(__name__)

# Tel sayaclarinin hub'a (dolayisiyla SSE'ye) yazilma araligi. Her datagramda
# yayin yapmak 1789'dan gelen yogun trafikte aboneleri bogar; sayaclar
# periyodik, MESAJLAR ise aninda gider.
COUNTER_FLUSH_S = 1.0


class Promos3Protocol(asyncio.DatagramProtocol):
    """UDP datagramlarini cozup hub'a isleyen protokol.

    Tek olay dongusunde kosar (hub'in varsayimi): datagram_received senkrondur,
    kilit gerekmez.
    """

    def __init__(self, hub: LiveHub) -> None:
        self.hub = hub
        self.reasm = AnswerReassembler()
        self.datagrams = 0
        self.can_frames = 0

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        # "bagli" burada YALNIZCA "soket dinleniyor" demektir. Kaynagin
        # gercekten veri gonderip gondermedigi AYRI BIR SORUDUR ve cevabi
        # hub.data_age_s'tedir (tazelik); WireStats ise tasima teshisidir.
        # Ekran bu ikisini asla birbirinin yerine kullanmamali: PROMOS3_BIND
        # loopback'e cekilmis bir kurulumda soket sonsuza dek "bagli"dir ve
        # tek bayt gelmez.
        #
        # Anahtar hub'in KENDI kaynak kimligidir ("provis" / "promos3-sim"):
        # ikisi ayni teli konusur ama ayni sey degildir, ve status olayindaki
        # `sources` haritasi hangi halkanin kopuk oldugunu ADIYLA soylemeli.
        self.hub.set_source_status(self.hub.source_name, True)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.datagrams += 1
        now = datetime.now(UTC).isoformat()
        try:
            frames = split_datagram(data)
        except ValueError:
            # Kirpik/bozuk datagram: sayaci artmis olur, akis surer.
            log.debug("Promos3: bozuk datagram (%d bayt) %s", len(data), addr)
            return

        self.can_frames += len(frames)
        for frame in frames:
            answer = self.reasm.feed(frame)
            if answer is None:
                continue
            # Kimliklendirilemeyen cevap da hub'a gider: sayaci artar ve ham
            # bas kismi ekranda gorunur (sessizce dusurulmez).
            msg = identify_answer(answer.unit, answer.stripped, frames=answer.frames)
            self.hub.apply_promos3_message(msg, now)

    def error_received(self, exc: Exception) -> None:
        # ICMP port-unreachable gibi durumlar: soketi kapatmaz, loglanir.
        log.debug("Promos3 UDP hatasi: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        self.hub.set_source_status(self.hub.source_name, False)

    def flush_counters(self) -> None:
        """Tasima sayaclarini hub'a yazar (periyodik)."""
        self.hub.set_wire_counters(
            datagrams=self.datagrams,
            can_frames=self.can_frames,
            out_of_range=self.reasm.dropped_out_of_range,
            overflow=self.reasm.dropped_overflow,
            sequence=self.reasm.dropped_sequence,
            orphan=self.reasm.dropped_orphan,
            incomplete=self.reasm.dropped_incomplete,
        )


async def run_promos3_ingest(hub: LiveHub, bind_host: str, port: int) -> None:
    """Surekli gorev: UDP'yi dinle; sokette hata olursa bekleyip yeniden kur.

    Uygulama lifespan'inda baslar, kapaniste iptal edilir.
    """
    loop = asyncio.get_running_loop()
    while True:
        transport = None
        try:
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: Promos3Protocol(hub),
                local_addr=(bind_host, port),
            )
            log.info("Promos3 UDP dinleniyor: %s:%d", bind_host, port)
            # Sayaclari periyodik yaz; soket kapanana dek burada kal.
            while True:
                await asyncio.sleep(COUNTER_FLUSH_S)
                if transport.is_closing():
                    break
                protocol.flush_counters()
        except asyncio.CancelledError:
            raise
        except OSError as exc:
            # En sik: port mesgul (baska bir surec 1789'u tutuyor) ya da adres
            # yok. Gorev OLMEMELI; aralikli yeniden dener.
            log.warning("Promos3 UDP soketi kurulamadi (%s:%d): %s", bind_host, port, exc)
        except Exception:
            log.exception("Promos3 ingest dongusunde beklenmeyen hata")
        finally:
            if transport is not None:
                with contextlib.suppress(Exception):
                    transport.close()
        hub.set_source_status(hub.source_name, False)
        await asyncio.sleep(3.0)
