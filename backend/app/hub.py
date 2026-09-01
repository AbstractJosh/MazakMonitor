"""Canli durum merkezi — adaptorlerden gelen olaylari duruma isler, SSE
abonelerine dagitir.

Dagitim "son durum kazanir" (latest-wins) yaklasimiyla yapilir: her aboneye
ara olaylar degil, uyandiginda gecerli olan TAM anlik goruntu gider. Tam
goruntu idempotenttir — kopup yeniden baglanan tuketici seq/tekrar derdi
yasamaz.

Es zamanlilik: her sey tek uvicorn olay dongusunde kosar; yazarlar (adaptor)
await icermeyen senkron metotlar kullanir, bu yuzden kilit gerekmez. Aboneler
surum sayacini asyncio.Event ile bekler.
"""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

from app.csv_live import apply_measurement as _apply_measurement
from app.domain import LiveState, WireStats
from app.live import apply_promos3_message, initial_live_state
from app.promos3.messages import Promos3Message
from app.sim.baselines import Baselines
from app.sim.csv_reader import MeasurementRecord

# Sessiz baglantiyi canli tutan nabiz araligi.
PING_INTERVAL_S = 15.0

# Verinin "TAZE" sayildigi en buyuk yas (saniye).
#
# NEDEN BU SAYI: esik "kaynak sustu mu" sorusunu cevaplar ve burada YANLIS
# POZITIF pahalidir — yavas ama saglikli bir kaynagi olu ilan etmek ekrani
# yalancilastirir, ki bu tam da kacindigimiz sey. Bilinen kadanslar esigin cok
# altinda kalir (simulator 200 ms, CSV tekrar oynatmasi 1000 ms); gercek
# gateway'in kadansi ise BILINMIYOR — saha kurulumuna gore degisir. Bu yuzden
# cimri degil comert bir sayi secildi.
#
# NEDEN NABZIN KATI: tazelik sessizlikte NABIZLA tasinir (bkz. sse_frames) —
# veri akmazken "state" cercevesi dogmaz, yasi istemciye nabiz goturur. Esik
# nabza esit olsaydi tek bir gec kalmis nabiz bile durumu dusururdu. Uc kat,
# ust uste UC nabiz penceresi bos gecmeden "veri yok" denmemesini garanti eder;
# rozet saglikli bir kaynakta iki durum arasinda gidip gelmez.
DATA_STALE_AFTER_S = 3 * PING_INTERVAL_S

# Kimliklendirilemeyen mesajdan ekrana tasinan bas kismin uzunlugu (bayt).
# Teshis icin bas kisim yeter; tum govdeyi tasimak SSE cercevesini gereksiz
# sisirir.
UNPARSED_PREVIEW_BYTES = 32


def sse_frame(event: str, data: Any) -> str:
    """Tek bir SSE cercevesi. json.dumps tek satir uretir; data alani bolunmez."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class LiveHub:
    def __init__(
        self, source_name: str = "promos3", feature_names: dict[int, str] | None = None
    ) -> None:
        self.source_name = source_name
        # Ozellik adlari KURULUMA OZELDIR (rapor 7.2) — koda gomulmez. Asil
        # kaynak TELDIR (MC_GIVEKANAL +0x4D); bu yalnizca yedek gecersiz kilma.
        self.feature_names = feature_names
        # CSV taban ortalamalari — `set_baselines` ile acilista dolar, tel
        # kaynaklarinda bos kalir (Promos3 esigi TELDEN gelir, turetilmez).
        self.baselines: Baselines = {}
        self.state: LiveState = initial_live_state()
        # Baglanti durumu KAYNAK BASINA tutulur: birden cok adaptor eklendiginde
        # biri digerinin durumunu ezmesin ve ekran hangi halkanin kopuk oldugunu
        # tam soyleyebilsin.
        self._sources: dict[str, bool] = {}
        # Tel/cozme teshisi — Promos3 adaptoru doldurur.
        self.wire: WireStats | None = None
        # Uygulanan yuk sayisi — KAYNAKTAN BAGIMSIZ canlilik olcusu.
        # `wire.parsed` yalnizca Promos3 tasimasini sayar ve CSV tezgahinda
        # hep 0 kalirdi; ekran "bagli ama veri yok" ile "veri akiyor"u ayirt
        # edebilmek zorunda.
        #
        # DIKKAT: `frames` "HIC geldi mi" sorusunu cevaplar, "SU AN geliyor mu"
        # sorusunu DEGIL — bir kez artti mi bir daha azalmaz. Ikincisinin
        # cevabi asagidaki `last_frame_at`tir.
        self.frames = 0
        # Son uygulanan yukun ANI — time.monotonic, duvar saati DEGIL: yas
        # hesabi saat ayarindan/yaz saatinden etkilenmemeli. None = bu hub'a
        # hic veri gelmedi.
        #
        # "BAGLI" ILE "VERI GELIYOR" AYRI SORULARDIR: soket baglanmis
        # (set_source_status True) ve tek bayt gelmemis olabilir — kurulumun
        # PROMOS3_BIND=127.0.0.1 oldugu bu makinede A/1 tam olarak boyledir.
        # Ikisini tek bayrakta toplamak, ekranin sessiz bir kaynagi yesil
        # gostermesi demekti.
        self.last_frame_at: float | None = None
        self._state_ver = 0
        self._status_ver = 0
        self._subscribers: set[asyncio.Event] = set()

    # --- yazar tarafi (adaptorler) ---

    def apply_promos3_message(self, msg: Promos3Message, time_iso: str) -> None:
        """Promos3 mesajini duruma isler ve tel istatistiklerini guncellerken
        KIMLIKLENDIRILEMEYEN mesaji da kaydeder.

        Kimligi cikmayan mesaj sessizce dusmez: sayaci artar ve bas kismi hex
        olarak tasinir. Arayuzun bunu SOYLEMESI gerekir — yoksa "veri yok" ile
        "veri cozulemedi" ayni goruntuyu verir.
        """
        stats = self.wire or WireStats()
        stats.messages += 1
        if msg.device_error:
            # Cihaz "bu komutu yapamiyorum" dedi: tel saglikli, veri yok.
            stats.device_errors += 1
        elif msg.parsed:
            stats.parsed += 1
            stats.last_command = msg.name
        else:
            stats.unparsed += 1
            stats.last_unparsed_hex = msg.raw[:UNPARSED_PREVIEW_BYTES].hex(" ")
        self.wire = stats

        new_state = apply_promos3_message(self.state, msg, time_iso, self.feature_names)
        self.state = new_state
        self._mark_frame()
        # Istatistikler her mesajda degisir; durum degismese de aboneler
        # sayaclari gormeli (akisin canliligi buradan okunuyor).
        self._bump(state=True)

    def set_baselines(self, baselines: Baselines) -> None:
        """CSV taban ortalamalarini kurar (ingest gorevi acilista bir kez cagirir).

        `feature_names` ile ayni cinsten bir yapilandirmadir ama kurucuya
        giremez: dosyalarin TAMAMI okunmadan hesaplanamaz ve o okuma hub
        kurulduktan sonra, ingest gorevi baslarken olur.
        """
        self.baselines = baselines

    def apply_measurement(self, rec: MeasurementRecord, time_iso: str) -> None:
        """CSV olcum satirini duruma isler.

        TEL ISTATISTIGI URETMEZ (`self.wire` None kalir): WireStats
        Promos3 tasima teshisidir (datagram/CAN cerceve sayaclari) ve
        CSV'nin teli yoktur. Canlilik `frames` ile olculur.
        """
        self.state = _apply_measurement(self.state, rec, time_iso, self.baselines)
        self._mark_frame()
        self._bump(state=True)

    def _mark_frame(self) -> None:
        """Uygulanan yuku sayar VE tazelik damgasini atar.

        Iki adaptorun da tek gecmesi gereken kapi: damgayi yalniz birinde
        atmak, oteki kaynagi kalici "bayat" gosterirdi.
        """
        self.frames += 1
        self.last_frame_at = time.monotonic()

    # --- tazelik ---

    @property
    def data_age_s(self) -> float | None:
        """Son uygulanan yukun uzerinden gecen saniye; hic veri gelmediyse None.

        SUNUCUDA hesaplanir. Istemciye mutlak bir an gonderip karsilastirmayi
        ona birakmak, tarayici saatiyle sunucu saatinin tutmadigi bir makinede
        tazeligi uydurmak olurdu.
        """
        if self.last_frame_at is None:
            return None
        # round: telde uc ondalik yeter; ayrica JSON'da gereksiz basamak
        # tasimaz. max(0.0, ...) monotonic'in geri gitmeyecegini varsaymaz.
        return round(max(0.0, time.monotonic() - self.last_frame_at), 3)

    @property
    def data_fresh(self) -> bool:
        """Veri SU AN akiyor mu — "hic akti mi" degil (bkz. `frames`)."""
        age = self.data_age_s
        return age is not None and age <= DATA_STALE_AFTER_S

    def set_wire_counters(
        self,
        datagrams: int,
        can_frames: int,
        out_of_range: int,
        overflow: int,
        sequence: int = 0,
        orphan: int = 0,
        incomplete: int = 0,
    ) -> None:
        """Tasima sayaclarini adaptorden alir (cerceve duzeyi; mesaj olusmasa da artar).

        Adaptor bunu saniyede bir cagirir. DEGISMEDIYSE abone uyandirilmaz:
        sessiz bir telde her saniye cerceve yayinlamak, hicbir sey olmazken tum
        SSE istemcilerini saniyede bir uyandirmak olurdu.
        """
        stats = self.wire or WireStats()
        unchanged = (
            stats.datagrams == datagrams
            and stats.can_frames == can_frames
            and stats.dropped_out_of_range == out_of_range
            and stats.dropped_overflow == overflow
            and stats.dropped_sequence == sequence
            and stats.dropped_orphan == orphan
            and stats.dropped_incomplete == incomplete
        )
        if unchanged and self.wire is not None:
            return
        stats.datagrams = datagrams
        stats.can_frames = can_frames
        stats.dropped_out_of_range = out_of_range
        stats.dropped_overflow = overflow
        stats.dropped_sequence = sequence
        stats.dropped_orphan = orphan
        stats.dropped_incomplete = incomplete
        self.wire = stats
        self._bump(state=True)

    @property
    def upstream_connected(self) -> bool:
        """Herhangi bir kaynak bagli mi (toplu gorunum)."""
        return any(self._sources.values())

    def set_source_status(self, source: str, connected: bool) -> None:
        """Tek bir kaynagin baglanti durumunu yazar.

        Her adaptor YALNIZ kendi durumunu bildirir; birbirlerinin durumunu
        ezmezler.
        """
        if self._sources.get(source) == connected:
            return
        self._sources[source] = connected
        self._bump(status=True)

    def reset_run(self) -> None:
        """Durumu sifirlar: eski kosunun degerleri "guncel veri" gibi kalmasin."""
        self.state = initial_live_state()
        self._bump(state=True)

    def _bump(self, state: bool = False, status: bool = False) -> None:
        if state:
            self._state_ver += 1
        if status:
            self._status_ver += 1
        for ev in self._subscribers:
            ev.set()

    # --- okuyucu tarafi (API) ---

    def state_wire(self) -> dict[str, Any]:
        """Anlik goruntu, tel biciminde (camelCase).

        exclude_none: bos opsiyoneller (serialNo, limitLevel, cevrim...) telde
        HIC gorunmez — frontend tipleri bunlari `alan?:` (undefined) ilan eder;
        null gonderilseydi "deger yok" ile "deger null" ayni sekle duserdi.
        """
        snap = self.state.model_copy(update={"wire": self.wire})
        return snap.model_dump(by_alias=True, exclude_none=True)

    def status_wire(self) -> dict[str, Any]:
        """Backend'in kaynak baglantisi: hangi kaynak, bagli mi."""
        return {
            "source": self.source_name,
            "connected": self.upstream_connected,
            # Kaynak basina durum: ekran hangi halkanin kopuk oldugunu tam
            # soyleyebilsin (toplu "connected" tek basina bunu gizler).
            "sources": dict(sorted(self._sources.items())),
        }

    async def sse_frames(self) -> AsyncIterator[str]:
        """Bir SSE abonesinin cerceve akisi.

        Baglanista status+state hemen gider; sonra hangisi degistiyse o gider,
        sessizlikte ping. Surum karsilastirmasi uyanma ile gonderme arasindaki
        degisiklikleri de yakalar (kacan guncelleme olmaz).
        """
        wake = asyncio.Event()
        self._subscribers.add(wake)
        state_ver = status_ver = -1
        try:
            while True:
                if status_ver != self._status_ver:
                    status_ver = self._status_ver
                    yield sse_frame("status", self.status_wire())
                if state_ver != self._state_ver:
                    state_ver = self._state_ver
                    yield sse_frame(
                        "state",
                        {
                            "seq": state_ver,
                            "frames": self.frames,
                            # Tazelik zarfin icinde, `frames`in YANINDA:
                            # "hic geldi mi" ile "su an geliyor mu" ayri
                            # sorulardir ve ekran ikisini de sormak zorunda.
                            "dataAgeS": self.data_age_s,
                            # Esik de birlikte gider: sayinin tek sahibi
                            # backend'dir, arayuz onu tekrar yazmaz.
                            "stalenessS": DATA_STALE_AFTER_S,
                            "state": self.state_wire(),
                        },
                    )
                try:
                    await asyncio.wait_for(wake.wait(), PING_INTERVAL_S)
                    wake.clear()
                except TimeoutError:
                    # NABIZ TAZELIGI DE TASIR. Kaynak sustugunda "state"
                    # cercevesi HIC dogmaz; istemci son gordugu yasla kalir ve
                    # "Veri Akisi Aktif" kalicilasirdi. Yasi buraya bindirmek
                    # yeni bir arka plan zamanlayicisi GEREKTIRMEZ — nabiz
                    # zaten tam da sessizlikte atiyor.
                    yield sse_frame(
                        "ping",
                        {"tMs": int(time.time() * 1000), "dataAgeS": self.data_age_s},
                    )
        finally:
            self._subscribers.discard(wake)
