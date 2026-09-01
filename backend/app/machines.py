"""Tesis/tezgah katalogu ve tezgah->kaynak baglamasi — TEK DOGRULUK KAYNAGI.

Adlar YAPILANDIRMADIR, telden gelmez: Promos3 telgrafinda tesis/tezgah
kavrami yoktur (izleme unitesi, kanal, ozellik vardir — bkz. CONTEXT.md).
Bu yuzden burada durur.

Katalog frontend'de degil BURADA durur (ADR-0006 madde 1'i gunceller):
uc kaynak geldiginde tezgah->kaynak baglamasi zaten backend'de olmak
zorundadir, ve katalog frontend'de kalsaydi ayni baglama iki yerde
tutulurdu — uyusmazliklari da sessiz olurdu.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from app.config import Settings
from app.domain import CamelModel
from app.hub import DATA_STALE_AFTER_S

# Uc kaynak, uc ayri kimlik. "provis" ile "promos3-sim" ayni TASIMAYI
# (Promos3 CAN-over-UDP) kullanir ama ayni SEY DEGILDIR: biri tezgahtan
# gelir, oteki uretir. Tek bir "promos3" kimligi ikisini ayirt edilemez
# kilardi ve karsilama ekrani sentetik veriyi gercek gibi etiketlerdi.
SourceKind = Literal["provis", "promos3-sim", "csv"]

FACILITY_LETTERS = ("A", "B", "C", "D")
MACHINES_PER_FACILITY = 4

# Gosterim baglamasi. Sahada bu tablo tezgah basina gercek gateway'lere
# doner; bugun uc farkli kaynagin ayni anda, birbirine karismadan
# calistigini gostermek icin vardir.
PROVIS_MACHINE_ID = "tesis-a/tezgah-1"
SIM_MACHINE_ID = "tesis-a/tezgah-2"
CSV_MACHINE_ID = "tesis-a/tezgah-3"

# Sahadaki gercek tezgahin modeli — yalniz onunki bilinir.
_MODELS = {PROVIS_MACHINE_ID: "Mazak Integrex"}


@dataclass(frozen=True)
class SourceSpec:
    kind: SourceKind
    # Yalniz Promos3 tasimasi icin; CSV'de None.
    port: int | None = None


@dataclass(frozen=True)
class MachineDef:
    id: str
    name: str
    model: str | None = None
    source: SourceSpec | None = None


@dataclass(frozen=True)
class FacilityDef:
    id: str
    name: str
    machines: tuple[MachineDef, ...]


def _sources(s: Settings) -> dict[str, SourceSpec]:
    """Etkin tezgah->kaynak baglamasi.

    KAPALI bayrak baglamayi HIC uretmez. Bunun sonucu katalogda gorunur:
    o tezgah "kaynak yok" olur, "kaynagi var ama bagli degil" olmaz.
    Dinleyici kurulmadigi icin veri gelmesi imkansizdir; ikincisi ekranda
    beklemeye deger bir sey varmis izlenimi verirdi.
    """
    out: dict[str, SourceSpec] = {}
    if s.promos3_enabled:
        out[PROVIS_MACHINE_ID] = SourceSpec(kind="provis", port=s.promos3_port)
    if s.promos3_sim_enabled:
        out[SIM_MACHINE_ID] = SourceSpec(kind="promos3-sim", port=s.promos3_sim_port)
    if s.csv_replay_enabled:
        out[CSV_MACHINE_ID] = SourceSpec(kind="csv", port=None)
    return out


def build_catalog(s: Settings) -> tuple[FacilityDef, ...]:
    """4 tesis x 4 tezgah; kaynaklar ayarlardan baglanir."""
    sources = _sources(s)
    facilities: list[FacilityDef] = []
    for letter in FACILITY_LETTERS:
        facility_id = f"tesis-{letter.lower()}"
        machines = tuple(
            MachineDef(
                id=(mid := f"{facility_id}/tezgah-{i + 1}"),
                name=f"Tezgah {i + 1}",
                model=_MODELS.get(mid),
                source=sources.get(mid),
            )
            for i in range(MACHINES_PER_FACILITY)
        )
        facilities.append(
            FacilityDef(id=facility_id, name=f"Tesis {letter}", machines=machines)
        )
    return tuple(facilities)


def find_machine(
    catalog: Iterable[FacilityDef], machine_id: str
) -> MachineDef | None:
    for f in catalog:
        for m in f.machines:
            if m.id == machine_id:
                return m
    return None


def machines_with_source(catalog: Iterable[FacilityDef]) -> list[MachineDef]:
    return [m for f in catalog for m in f.machines if m.source is not None]


# --- Tel bicimi (GET /api/machines) ---
#
# Backend EKRAN METNI gondermez, kaynak KIMLIGI gonderir. Okunur karsilik
# ("Simulator — degerler sentetiktir" gibi) frontend'de tek bir haritada
# durur: frontend kimligi zaten AYRICA bilmek zorundadir (rozet tonu ve
# uyari dili ona gore degisir), etiketi de gondermek ayni bilgiyi iki
# bicimde tasimak olurdu.
#
# NOT: promos3/rings.py'nin Turkce etiket gondermesi bununla celismez —
# orada backend TELDEN COZULEN bir kodun karsiligini bilir (ToolStatus ->
# statusLabel), yani metnin tek sahibi odur.


class MachineOut(CamelModel):
    id: str
    name: str
    model: str | None = None
    source: SourceKind | None = None
    source_port: int | None = None
    # Kaynak adaptorunun HALKASI ayakta mi: UDP soketi bagli / CSV ingest
    # kosuyor. "Veri geliyor" DEMEK DEGILDIR — onu `data_age_s` soyler.
    connected: bool = False
    # Son verinin yasi (saniye), SUNUCUDA hesaplanir; None = hic veri gelmedi.
    # Mutlak an degil YAS gonderilir: tarayici saatiyle sunucu saati
    # tutmayabilir, istemci tazeligi tahmin etmek zorunda kalmasin.
    data_age_s: float | None = None


class FacilityOut(CamelModel):
    id: str
    name: str
    machines: list[MachineOut]


class CatalogOut(CamelModel):
    facilities: list[FacilityOut]
    # Tazelik esigi TELDE gider: sayinin tek sahibi hub.py'dir (gerekcesi
    # orada yazar), arayuz onu ikinci kez yazmaz.
    staleness_s: float = DATA_STALE_AFTER_S


def catalog_wire(
    catalog: Iterable[FacilityDef],
    connected_ids: set[str],
    data_age_s: dict[str, float | None] | None = None,
) -> CatalogOut:
    """Katalogu tel bicimine cevirir.

    `connected_ids` O ANDA halkasi ayakta olan tezgahlar, `data_age_s` ise
    tezgah basina son verinin yasidir. IKISI AYRI SORUDUR ve ayri tasinir:
    soketi bagli ama sessiz bir kaynak "bagli"dir, "canli" DEGILDIR.
    """
    ages = data_age_s or {}
    return CatalogOut(
        facilities=[
            FacilityOut(
                id=f.id,
                name=f.name,
                machines=[
                    MachineOut(
                        id=m.id,
                        name=m.name,
                        model=m.model,
                        source=m.source.kind if m.source else None,
                        source_port=m.source.port if m.source else None,
                        connected=m.id in connected_ids,
                        data_age_s=ages.get(m.id),
                    )
                    for m in f.machines
                ],
            )
            for f in catalog
        ]
    )
