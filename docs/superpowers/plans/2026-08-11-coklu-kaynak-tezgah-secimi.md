# Çoklu kaynak + karşılama ekranı — uygulama planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Üç veri kaynağını (PROVIS / promos3_sim / CSV) aynı anda üç ayrı tezgaha bağlamak ve uygulamayı, kullanıcının tesis + tezgah seçtiği bir karşılama ekranından açmak.

**Architecture:** Backend tezgah→kaynak bağlamasının ve tesis/tezgah kataloğunun sahibi olur (`app/machines.py`, `GET /api/machines`). Kaynağı olan her tezgah kendi `LiveHub` örneğini alır; `/api/stream` gibi uçlar `?tezgah=` ile hub seçer. CSV tekrar-oynatma ayrı bir süreç olmaktan çıkıp süreç içi bir ingest adaptörüne dönüşür ve hub'ı besler, böylece üç tezgah da aynı Canlı/Alarmlar/Olaylar ekranlarını kullanır.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (uv), React + TypeScript + Vite (bun), `@alp/design-system`, pytest.

**Spec:** `docs/superpowers/specs/2026-08-11-coklu-kaynak-tezgah-secimi-design.md`

## Global Constraints

Her görevin gereksinimlerine **örtük olarak** bunlar dahildir:

- **Bun, Node değil.** `bun install`, `bun run lint`. `npm`/`pnpm`/`node` kullanılmaz.
- **Python: `uv`.** `cd backend && uv run pytest`, `uv run alembic ...`.
- **UI yalnız `@alp/design-system`'den.** Elle bileşen yazmak yasak. Paket adı `@alp/ui` DEĞİL.
- **Ekran yazmadan önce oku:** `frontend/node_modules/@alp/design-system/COMPONENTS.md`, `docs/design-language.md`, `blocks/`. (Paketin `CLAUDE.md`'si ve skill'i npm `files` listesinde YOK — kurulu pakette aramayın.)
- **Ham hex/px yasak, arbitrary Tailwind yasak** (paketin `adherence` lint kuralı error verir). Token ve `.type-*` rolleri kullanılır.
- **Emoji ve unicode glif ikon olarak kullanılmaz.** İkon = `lucide-react`, boy `IKON`, kontur `KONTUR` sabitinden.
- **Başlıklar cümle düzeni.** BÜYÜK HARF yalnız 11px mikro etiket ailesinde (eyebrow/badge).
- **Renk tek başına bilgi taşımaz** — durum noktası her zaman metin etiketiyle gelir.
- **Animasyon** `--duration-*` / `--ease-*` token'larından; uygulamaya ait olanlar YALNIZ `frontend/src/app/app.css` içindeki `HAREKET` bloğunda, `mzi-` öneki ile. `alp-` paketin ad alanıdır, oraya yazılmaz.
- **Frontend'de birim test altyapısı YOKTUR.** Frontend doğrulaması = `cd frontend && bun run lint` (eslint + `tsc --noEmit`) + elle bakma. Frontend görevlerinde "testi yaz" adımı bilerek yoktur; yerine tip + lint + gözle doğrulama vardır.
- **Backend Python yorumları ASCII yazılır** (mevcut dosyaların baskın biçimi). Kullanıcıya giden Türkçe dizeler diakritik taşıyabilir — `promos3/rings.py` ve `live.py` böyle yapar.
- **Dosya sonu:** `.bat` dosyaları CRLF.
- **Git:** çalışma dalı `coklu-kaynak-tezgah-secimi`. Her görev sonunda commit.

---

### Task 1: Backend katalog + `Settings` + `GET /api/machines`

**Files:**
- Create: `backend/app/machines.py`
- Modify: `backend/app/config.py` (Settings'e üç alan)
- Modify: `backend/app/main.py` (yeni uç)
- Modify: `backend/tests/conftest.py` (üç bayrağı da kapat)
- Test: `backend/tests/test_machines.py` (yeni)

**Interfaces:**
- Consumes: `app.config.Settings`, `app.domain.CamelModel`
- Produces:
  - `SourceKind = Literal["provis", "promos3-sim", "csv"]`
  - `SourceSpec(kind: SourceKind, port: int | None)`
  - `MachineDef(id: str, name: str, model: str | None, source: SourceSpec | None)`
  - `FacilityDef(id: str, name: str, machines: tuple[MachineDef, ...])`
  - `build_catalog(s: Settings) -> tuple[FacilityDef, ...]`
  - `find_machine(catalog, machine_id: str) -> MachineDef | None`
  - `machines_with_source(catalog) -> list[MachineDef]`
  - `catalog_wire(catalog, connected_ids: set[str]) -> CatalogOut`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_machines.py`:

```python
from app.config import Settings
from app.machines import (
    build_catalog,
    catalog_wire,
    find_machine,
    machines_with_source,
)


def _acik() -> Settings:
    """Uc kaynagin da acik oldugu ayarlar (basla.bat'in yazdigi hal)."""
    return Settings(
        promos3_enabled=True,
        promos3_port=1789,
        promos3_sim_enabled=True,
        promos3_sim_port=1790,
        csv_replay_enabled=True,
    )


def test_katalog_dort_tesis_dort_tezgah():
    catalog = build_catalog(_acik())
    assert [f.id for f in catalog] == ["tesis-a", "tesis-b", "tesis-c", "tesis-d"]
    assert [f.name for f in catalog] == ["Tesis A", "Tesis B", "Tesis C", "Tesis D"]
    assert all(len(f.machines) == 4 for f in catalog)
    assert catalog[0].machines[0].id == "tesis-a/tezgah-1"
    assert catalog[0].machines[0].name == "Tezgah 1"


def test_uc_kaynak_uc_ayri_tezgaha_baglanir():
    catalog = build_catalog(_acik())
    baglilar = {m.id: m.source for m in machines_with_source(catalog)}
    assert set(baglilar) == {
        "tesis-a/tezgah-1",
        "tesis-a/tezgah-2",
        "tesis-a/tezgah-3",
    }
    assert baglilar["tesis-a/tezgah-1"].kind == "provis"
    assert baglilar["tesis-a/tezgah-1"].port == 1789
    assert baglilar["tesis-a/tezgah-2"].kind == "promos3-sim"
    assert baglilar["tesis-a/tezgah-2"].port == 1790
    assert baglilar["tesis-a/tezgah-3"].kind == "csv"
    assert baglilar["tesis-a/tezgah-3"].port is None


def test_kalan_on_uc_tezgah_kaynaksizdir():
    catalog = build_catalog(_acik())
    kaynaksiz = [m for f in catalog for m in f.machines if m.source is None]
    assert len(kaynaksiz) == 13


def test_kapali_bayrak_kaynagi_KATALOGDAN_dusurur():
    """Kapali kaynak "bagli degil" DEGIL, "kaynak yok"tur.

    Dinleyici hic kurulmadigi icin o tezgaha veri gelmesi imkansizdir;
    "tanimli ama dusmus" gostermek ekranda yanlis bir umut uretirdi.
    """
    s = _acik()
    s.promos3_sim_enabled = False
    catalog = build_catalog(s)
    assert find_machine(catalog, "tesis-a/tezgah-2").source is None
    assert len(machines_with_source(catalog)) == 2


def test_yalniz_gercek_tezgahin_modeli_bilinir():
    catalog = build_catalog(_acik())
    assert find_machine(catalog, "tesis-a/tezgah-1").model == "Mazak Integrex"
    assert find_machine(catalog, "tesis-a/tezgah-2").model is None


def test_find_machine_bilinmeyen_kimlikte_none_doner():
    catalog = build_catalog(_acik())
    assert find_machine(catalog, "tesis-z/tezgah-9") is None


def test_catalog_wire_bagli_kimlikleri_isaretler():
    catalog = build_catalog(_acik())
    out = catalog_wire(catalog, connected_ids={"tesis-a/tezgah-1"})

    tezgahlar = {m.id: m for f in out.facilities for m in f.machines}
    assert tezgahlar["tesis-a/tezgah-1"].connected is True
    assert tezgahlar["tesis-a/tezgah-1"].source == "provis"
    assert tezgahlar["tesis-a/tezgah-1"].source_port == 1789
    # Kaynagi var ama bagli degil.
    assert tezgahlar["tesis-a/tezgah-2"].connected is False
    assert tezgahlar["tesis-a/tezgah-2"].source == "promos3-sim"
    # Kaynagi hic yok.
    assert tezgahlar["tesis-a/tezgah-4"].connected is False
    assert tezgahlar["tesis-a/tezgah-4"].source is None
    assert tezgahlar["tesis-a/tezgah-4"].source_port is None


def test_catalog_wire_camelcase_uretir():
    catalog = build_catalog(_acik())
    out = catalog_wire(catalog, connected_ids=set())
    govde = out.model_dump(by_alias=True)
    assert "sourcePort" in govde["facilities"][0]["machines"][0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_machines.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.machines'`

- [ ] **Step 3: Add the three settings fields**

`backend/app/config.py` — `promos3_port` tanımının hemen altına ekleyin:

```python
    # --- Promos3 SIMULATORU (promos3_sim.exe --stream) — AYRI TEZGAH ---
    #
    # Gercek gateway ile AYNI tel bicimini konusur, bu yuzden ayni adaptor
    # okur; ayirt eden tek sey PORTTUR. Ayri port sart: ayni portu iki
    # dinleyici baglayamaz ve baglayabilseydi sentetik veri gercek tezgahin
    # ekranina karisirdi.
    #
    # Ad neden "promos3_sim_*": "sim_*" oneki BU DOSYADA ZATEN CSV sim'indir
    # (sim_csv_dir / sim_period_ms / sim_retention_minutes). "sim_enabled"
    # demek iki farkli simulatoru tek ada toplardi.
    promos3_sim_enabled: bool = True
    promos3_sim_port: int = 1790

    # --- CSV tekrar-oynatma: surec ICI ingest adaptoru ---
    #
    # Kapaliyken adaptor hic kurulmaz ve ilgili tezgah katalogda KAYNAKSIZ
    # gorunur ("bagli degil" degil) — bkz. machines.build_catalog.
    csv_replay_enabled: bool = True
```

- [ ] **Step 4: Write `backend/app/machines.py`**

```python
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
    connected: bool = False


class FacilityOut(CamelModel):
    id: str
    name: str
    machines: list[MachineOut]


class CatalogOut(CamelModel):
    facilities: list[FacilityOut]


def catalog_wire(
    catalog: Iterable[FacilityDef], connected_ids: set[str]
) -> CatalogOut:
    """Katalogu tel bicimine cevirir; `connected_ids` O ANDA bagli olanlardir."""
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
                    )
                    for m in f.machines
                ],
            )
            for f in catalog
        ]
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_machines.py -v`
Expected: PASS (8 test)

- [ ] **Step 6: Close all three source flags in conftest**

`backend/tests/conftest.py` — `os.environ["PROMOS3_ENABLED"] = "false"` satırını şununla değiştirin:

```python
# UC KAYNAGIN DA kapatilmasi gerekir. Yalniz PROMOS3_ENABLED'i kapatmak
# artik yetmez: lifespan ayrica 1790'i dinleyen ikinci bir Promos3
# adaptoru ve GECICI DB'ye yazan bir CSV adaptoru kurardi.
os.environ["PROMOS3_ENABLED"] = "false"
os.environ["PROMOS3_SIM_ENABLED"] = "false"
os.environ["CSV_REPLAY_ENABLED"] = "false"
```

- [ ] **Step 7: Add the endpoint**

`backend/app/main.py` — import satırlarına ekleyin:

```python
from app.machines import CatalogOut, build_catalog, catalog_wire
```

Modül düzeyinde `hub = LiveHub(...)` satırının **üstüne**:

```python
# Katalog acilista BIR KEZ kurulur: ayarlar surec omru boyunca degismez.
CATALOG = build_catalog(settings)
```

`/api/health`'in altına:

```python
@app.get("/api/machines")
def machines() -> CatalogOut:
    """Tesis/tezgah katalogu + her tezgahin kaynagi ve O ANKI baglantisi.

    Karsilama ekraninin tek kaynagi. `connected` yapilandirmayi degil
    GERCEGI soyler: tanimli ama dusmus bir kaynak yesil gorunmez.
    """
    # Task 2'de HUBS gelene dek bos kume; o gorevde baglanir.
    return catalog_wire(CATALOG, connected_ids=set())
```

- [ ] **Step 8: Run the whole backend suite**

Run: `cd backend && uv run pytest -q`
Expected: PASS — mevcut testlerin hiçbiri kırılmamalı.

- [ ] **Step 9: Commit**

```bash
git add backend/app/machines.py backend/app/config.py backend/app/main.py backend/tests/conftest.py backend/tests/test_machines.py
git commit -m "Katalog ve tezgah->kaynak baglamasi backend'e tasindi (/api/machines)"
```

---

### Task 2: Hub başına tezgah + `?tezgah=` + `frames` sayacı

**Files:**
- Modify: `backend/app/hub.py` (frames sayacı)
- Modify: `backend/app/main.py` (HUBS, uçlara parametre)
- Test: `backend/tests/test_hub.py` (ekleme), `backend/tests/test_api.py` (değişiklik + ekleme)

**Interfaces:**
- Consumes: Task 1'in `CATALOG`, `machines_with_source`, `find_machine`, `catalog_wire`
- Produces:
  - `LiveHub.frames: int` — uygulanan yük sayısı (kaynaktan bağımsız)
  - `state` SSE olayının zarfı: `{"seq": int, "frames": int, "state": {...}}`
  - `main.HUBS: dict[str, LiveHub]`
  - `main._hub_for(tezgah: str) -> LiveHub` (404 fırlatır)

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_hub.py` sonuna ekleyin (dosyanın mevcut `TIME` ve `identify_answer` yardımcılarını kullanır):

```python
def test_frames_uygulanan_yuk_basina_artar():
    """`frames` KAYNAKTAN BAGIMSIZ canlilik olcusudur.

    `wire.parsed` yalnizca Promos3 tasimasini sayar; CSV tezgahinin teli
    olmadigi icin orada hep 0 kalir ve ust bar kusursuz akan bir tezgahta
    "Veri Yok" yazardi. Bu sayac o soruyu her kaynak icin cevaplar.
    """
    hub = LiveHub()
    assert hub.frames == 0
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    assert hub.frames == 1
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    assert hub.frames == 2


@pytest.mark.anyio
async def test_state_cercevesi_frames_tasir():
    hub = LiveHub()
    gen = hub.sse_frames()
    await gen.__anext__()  # status
    cerceve = await gen.__anext__()  # state
    assert '"frames": 0' in cerceve

    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    cerceve = await gen.__anext__()
    assert '"frames": 1' in cerceve
```

`backend/tests/test_api.py` sonuna ekleyin:

```python
def test_stream_bilinmeyen_tezgahta_404():
    r = client.get("/api/live", params={"tezgah": "tesis-z/tezgah-9"})
    assert r.status_code == 404
    assert "api/machines" in r.json()["detail"]


def test_stream_kaynaksiz_tezgahta_404():
    """Kaynaksiz tezgah bos bir akis DEGIL, 404 verir.

    Frontend o tezgah icin akisi HIC kurmaz (bos durum verir); bu uc
    yalnizca elle/teshis amacli cagrilar icin bir bekcidir.
    """
    r = client.get("/api/live", params={"tezgah": "tesis-d/tezgah-4"})
    assert r.status_code == 404


def test_machines_ucu_katalogu_doner():
    body = client.get("/api/machines").json()
    assert len(body["facilities"]) == 4
    assert all(len(f["machines"]) == 4 for f in body["facilities"])
    # conftest uc bayragi da kapatir -> hicbir tezgahin kaynagi yok.
    hepsi = [m for f in body["facilities"] for m in f["machines"]]
    assert all(m["source"] is None for m in hepsi)
    assert all(m["connected"] is False for m in hepsi)
```

`backend/tests/test_api.py` içindeki **mevcut** `/api/live` çağrısı (satır ~15) `?tezgah=` almalı. conftest üç kaynağı da kapattığı için `HUBS` boştur ve o uç artık 404 döner — testi bu gerçeğe göre güncelleyin (aşağıda Step 4).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_hub.py tests/test_api.py -v`
Expected: FAIL — `AttributeError: 'LiveHub' object has no attribute 'frames'` ve `/api/machines` 404.

- [ ] **Step 3: Add the counter to `LiveHub`**

`backend/app/hub.py`, `__init__` içinde `self._state_ver = 0` satırının üstüne:

```python
        # Uygulanan yuk sayisi — KAYNAKTAN BAGIMSIZ canlilik olcusu.
        # `wire.parsed` yalnizca Promos3 tasimasini sayar ve CSV tezgahinda
        # hep 0 kalirdi; ekran "bagli ama veri yok" ile "veri akiyor"u ayirt
        # edebilmek zorunda.
        self.frames = 0
```

`apply_promos3_message` içinde `self.state = new_state` satırının hemen altına:

```python
        self.frames += 1
```

`sse_frames` içindeki state çerçevesini değiştirin:

```python
                    yield sse_frame(
                        "state",
                        {"seq": state_ver, "frames": self.frames, "state": self.state_wire()},
                    )
```

- [ ] **Step 4: Wire per-machine hubs in `main.py`**

`backend/app/main.py` — önce Task 1'de eklenen importa `machines_with_source`'u ekleyin:

```python
from app.machines import CatalogOut, build_catalog, catalog_wire, machines_with_source
```

Sonra `_source_name()` ve tekil `hub = LiveHub(...)` satırlarını **silin**, yerine:

```python
# Kaynagi olan her tezgahin KENDI hub'i vardir. Tek hub, uc kaynagin
# durumunu tek durumda toplardi: uc tezgah da ayni cevrimi, ayni alarmlari
# gosterirdi.
#
# Tek process/tek worker varsayimi (IIS HttpPlatformHandler standardi):
# uvicorn --workers N kullanilirsa her worker AYRI hub takimi + AYRI
# dinleyiciler + AYRI CSV yazicisi kurar (ikinci UDP bagi da catisir) —
# kullanma.
HUBS: dict[str, LiveHub] = {
    m.id: LiveHub(source_name=m.source.kind, feature_names=settings.feature_names())
    for m in machines_with_source(CATALOG)
}


def _hub_for(tezgah: str) -> LiveHub:
    """Tezgahin hub'i; yoksa NE YAPILACAGINI soyleyen 404.

    Ciplak 404 yerine yonlendirme: kaynaksiz bir tezgahi elle cagiran biri
    hangi tezgahlarin yayin yaptigini bir istekte ogrenebilmeli.
    """
    hub = HUBS.get(tezgah)
    if hub is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"bilinmeyen ya da kaynaksiz tezgah: {tezgah}; "
                "yayin yapan tezgahlar: GET /api/machines"
            ),
        )
    return hub
```

`/api/machines` gövdesini gerçek bağlantı durumuna bağlayın:

```python
@app.get("/api/machines")
def machines() -> CatalogOut:
    """Tesis/tezgah katalogu + her tezgahin kaynagi ve O ANKI baglantisi.

    Karsilama ekraninin tek kaynagi. `connected` yapilandirmayi degil
    GERCEGI soyler: tanimli ama dusmus bir kaynak yesil gorunmez.
    """
    bagli = {mid for mid, h in HUBS.items() if h.upstream_connected}
    return catalog_wire(CATALOG, connected_ids=bagli)
```

Dört akış ucunu parametreye bağlayın:

```python
@app.get("/api/stream")
def stream(tezgah: str) -> StreamingResponse:
    """Secilen tezgahin canli durum akisi (SSE)."""
    return StreamingResponse(
        _hub_for(tezgah).sse_frames(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/live")
def live(tezgah: str) -> dict:
    """Anlik goruntu (REST) — /api/stream'in tek seferlik hali; test/teshis icin."""
    hub = _hub_for(tezgah)
    return {"status": hub.status_wire(), "state": hub.state_wire()}


@app.get("/api/events")
def events(tezgah: str) -> list[EventRow]:
    """Olay gecmisi (son EVENT_LIMIT kayit, en yeni basta)."""
    return _hub_for(tezgah).state.events


@app.get("/api/alarms")
def alarms(tezgah: str) -> list[Alarm]:
    """Alarm listesi (en yeni basta)."""
    return _hub_for(tezgah).state.alarms
```

`lifespan` içindeki tek görev kurulumunu şimdilik hub başına yapın (CSV Task 4'te gelir):

```python
    tasks: list[asyncio.Task[None]] = []
    for m in machines_with_source(CATALOG):
        hub = HUBS[m.id]
        if m.source.kind in ("provis", "promos3-sim"):
            tasks.append(
                asyncio.create_task(
                    run_promos3_ingest(hub, settings.promos3_bind, m.source.port)
                )
            )
```

- [ ] **Step 5: Fix the existing `/api/live` test**

`backend/tests/test_api.py` — mevcut testi güncelleyin. conftest üç kaynağı da kapattığı için `HUBS` boştur:

```python
def test_live_kaynaksiz_kurulumda_404_doner():
    """conftest uc bayragi da kapatir: hicbir tezgahin hub'i yoktur.

    Eskiden bu test tekil hub'in bos durumunu okuyordu; hub artik tezgaha
    aittir ve kaynaksiz tezgahin hub'i HIC kurulmaz.
    """
    r = client.get("/api/live", params={"tezgah": "tesis-a/tezgah-1"})
    assert r.status_code == 404
```

- [ ] **Step 6: Run the whole backend suite**

Run: `cd backend && uv run pytest -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/hub.py backend/app/main.py backend/tests/test_hub.py backend/tests/test_api.py
git commit -m "Hub basina tezgah, uclarda ?tezgah= ve kaynaktan bagimsiz frames sayaci"
```

---

### Task 3: `csv_live.py` — ölçüm satırı → `LiveState` (saf eşleyici)

**Files:**
- Create: `backend/app/csv_live.py`
- Test: `backend/tests/test_csv_live.py` (yeni)

**Interfaces:**
- Consumes: `app.sim.csv_reader.MeasurementRecord/FeatureValue/LimitValue`, `app.domain.LiveState`, `app.live.WINDOW`
- Produces: `apply_measurement(state: LiveState, rec: MeasurementRecord, time_iso: str) -> LiveState`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_csv_live.py`:

```python
from datetime import datetime

from app.csv_live import apply_measurement
from app.domain import LiveState
from app.live import WINDOW
from app.sim.csv_reader import FeatureValue, LimitValue, MeasurementRecord

TIME = "2026-08-10T11:23:02"


def _rec(**patch) -> MeasurementRecord:
    base = dict(
        unit_no=10660,
        source_time=datetime(2026, 8, 10, 11, 23, 2),
        channel_nr=1,
        tool_nr=11,
        program_nr=0,
        cut_nr=0,
        workpiece=None,
        alarm=None,
        alarm_limit=None,
        source_file="000_01_00011_000_260810_112302.csv",
        features=[
            FeatureValue(slot=1, name="SPINDEL", value=115.0, work_value=87.0),
            FeatureValue(slot=2, name="VIBRATION", value=None, work_value=None),
        ],
        limits=[LimitValue(limit_nr=1, level=230.0, lim_type=2, feature_nr=1)],
    )
    base.update(patch)
    return MeasurementRecord(**base)


def test_unite_online_isaretlenir():
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert [u.unit for u in out.units] == [10660]
    assert out.units[0].online is True
    assert out.units[0].serial_no == "10660"


def test_ozellik_seri_olarak_kurulur():
    out = apply_measurement(LiveState(), _rec(), TIME)
    ozellikler = {f.name: f for f in out.features}
    assert "SPINDEL" in ozellikler
    f = ozellikler["SPINDEL"]
    assert f.id == "csv:10660:1"
    assert f.kind == "series"
    assert f.unit_no == 10660
    assert f.samples == [115.0]
    assert f.current == 115.0
    assert f.raw_counts is True


def test_degeri_olmayan_yuva_ozellik_URETMEZ():
    """VIBRATION kolonu 10665'te 131/131 bostur.

    Hic dolmayacak bir ozellik ekranda kalici bir "—" uretmekten baska ise
    yaramaz (domain.py'nin NC alanlarini kaldirma gerekcesinin aynisi).
    """
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert all(f.name != "VIBRATION" for f in out.features)


def test_ornekler_birikir_ve_pencere_kayar():
    state = LiveState()
    for i in range(WINDOW + 10):
        state = apply_measurement(
            state,
            _rec(features=[FeatureValue(slot=1, name="SPINDEL", value=float(i), work_value=None)]),
            TIME,
        )
    f = next(f for f in state.features if f.name == "SPINDEL")
    assert len(f.samples) == WINDOW
    assert f.samples[-1] == float(WINDOW + 9)
    assert f.current == float(WINDOW + 9)
    assert f.min_value == float(10)
    assert f.max_value == float(WINDOW + 9)


def test_limit_yuzdeyi_besler():
    out = apply_measurement(LiveState(), _rec(), TIME)
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.limit_level == 230.0
    assert f.pct == 50.0
    assert [lim.level for lim in f.limits] == [230.0]


def test_limitsiz_ozellikte_yuzde_BOS_kalir():
    """Uydurma esikle yanlis yuzde uretmektense yuzde hic gosterilmez."""
    out = apply_measurement(LiveState(), _rec(limits=[]), TIME)
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.limit_level is None
    assert f.pct is None


def test_alarm_biti_alarm_uretir():
    out = apply_measurement(LiveState(), _rec(alarm=1, alarm_limit=230), TIME)
    assert len(out.alarms) == 1
    a = out.alarms[0]
    assert a.unit_no == 10660
    assert a.channel_nr == 1
    assert a.level == 230.0
    assert a.state == "active"


def test_alarmsiz_satir_alarm_URETMEZ():
    assert apply_measurement(LiveState(), _rec(alarm=0), TIME).alarms == []
    assert apply_measurement(LiveState(), _rec(alarm=None), TIME).alarms == []


def test_uydurulmayanlar_bos_kalir():
    """CSV'de karsiligi olmayan alan DOLDURULMAZ.

    workpiece: Workpiece ID kolonu 262/262 dosyada bostur.
    wire: CSV'nin teli yoktur (tasima teshisi Promos3'e ozeldir).
    """
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert out.workpiece is None
    assert out.wire is None
    assert out.plc_inputs is None
    assert out.events == []


def test_cevrim_cut_nr_den_gelir():
    out = apply_measurement(LiveState(), _rec(cut_nr=7), TIME)
    assert out.cycle == 7


def test_iki_unite_ayri_ozellik_uretir():
    state = apply_measurement(LiveState(), _rec(unit_no=10660), TIME)
    state = apply_measurement(state, _rec(unit_no=10665), TIME)
    assert {f.id for f in state.features} == {"csv:10660:1", "csv:10665:1"}
    assert [u.unit for u in state.units] == [10660, 10665]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_csv_live.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.csv_live'`

- [ ] **Step 3: Write `backend/app/csv_live.py`**

```python
"""Provis olcum satiri -> canli durum: SAF esleyici.

live.py'nin (Promos3 telgrafi -> LiveState) CSV karsiligidir ve ayni
kurallara uyar: saatsiz (an damgasi cagirandan gelir), saf, tek basina
test edilebilir.

CSV kaynagi neden ayni ekrani besler: veri/ altindaki dosyalar OLCUM
SATIRLARIDIR ve Promos3'un 0x16 SAMMELMERKMALE bloguyla ayni seyi tasir
(ozellik basina deger + limit + alarm biti). Bu yuzden ayni "series"
grafiklerine dusurler ve CSV tezgahi ayri bir ekran turu gerektirmez.

DOLDURULMAYANLAR bilerek bostur: CSV'de karsiligi olmayan alan (is parcasi
sayaci, PLC haritasi, tel istatistikleri, cihaz kimligi) uydurulmaz —
ekranda kalici bir "—" uretmekten baska ise yaramaz.
"""

from app.domain import Alarm, Feature, FeatureLimit, LiveState, UnitInfo
from app.live import WINDOW, _upsert_feature, _upsert_unit
from app.sim.csv_reader import MeasurementRecord


def _feature_id(unit_no: int, slot: int) -> str:
    return f"csv:{unit_no}:{slot}"


def apply_measurement(
    state: LiveState, rec: MeasurementRecord, time_iso: str
) -> LiveState:
    """Bir olcum satirini duruma isler ve YENI durumu doner."""
    units = _upsert_unit(
        state.units,
        rec.unit_no,
        # Klasor adi (10660/10665) oldugu gibi tasinir. CONTEXT.md telde
        # iki uniteyi 10659/10663 SERI NUMARALARIYLA anar; ikisi ayni sey
        # degildir, o yuzden CAN turevi bir unite indisiymis gibi
        # gosterilmez.
        serial_no=str(rec.unit_no),
        online=True,
    )

    features = state.features
    for fv in rec.features:
        # Degeri olmayan yuva ozellik URETMEZ: 10665'in VIBRATION kolonu
        # 131/131 bostur ve hic dolmayacak bir grafik acmak, ekranda
        # kalici bir "—"den baska bir sey vermez.
        if fv.value is None:
            continue

        fid = _feature_id(rec.unit_no, fv.slot)
        previous = next((f for f in features if f.id == fid), None)

        base = previous.samples if previous else []
        samples = [*base, fv.value][-WINDOW:]
        current = samples[-1]

        # Bu yuvaya ait limitler; birincisi yuzdenin paydasidir.
        limits = [
            FeatureLimit(lim_type=lv.lim_type, level=lv.level)
            for lv in rec.limits
            if lv.feature_nr == fv.slot
        ]
        limit_level = limits[0].level if limits else None
        pct = (
            None
            if not limit_level
            else round(current / limit_level * 100, 1)
        )

        features = _upsert_feature(
            features,
            Feature(
                id=fid,
                kind="series",
                # Ad CSV kolon basligindan gelir (kuruluma ozel, koda
                # gomulmez). Baslik bossa live.py ile ayni yedek kullanilir.
                name=fv.name or f"Özellik {fv.slot}",
                unit_no=rec.unit_no,
                feature_nr=fv.slot,
                # Provis degerleri ham sayimdir; olcek carpani yok.
                raw_counts=True,
                uom="",
                samples=samples,
                current=current,
                min_value=min(samples),
                max_value=max(samples),
                limit_level=limit_level,
                limits=limits,
                pct=pct,
                # Degerler kalibre edilmemis bir baslik yerlesiminden degil,
                # belgelenmis bir Provis disa aktarimindan gelir ve
                # csv_reader kolon hizasini dosya basina dogrular.
                confidence="confirmed",
            ),
        )

    alarms = state.alarms
    if rec.alarm:
        alarms = [
            Alarm(
                id=f"csv:{rec.unit_no}:{rec.source_file}",
                time=time_iso,
                unit_no=rec.unit_no,
                device_serial=str(rec.unit_no),
                channel_nr=rec.channel_nr,
                cycle_nr=rec.cut_nr,
                alarm_number=rec.alarm,
                level=float(rec.alarm_limit) if rec.alarm_limit is not None else None,
                state="active",
                confidence="confirmed",
            ),
            *alarms,
        ]

    return state.model_copy(
        update={
            "units": units,
            "features": features,
            "alarms": alarms,
            # Bu veride Cut 262/262 dosyada 0'dir; yine de GERCEK cevrim
            # numarasidir ve oldugu gibi tasinir.
            "cycle": rec.cut_nr,
        }
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_csv_live.py -v`
Expected: PASS (11 test)

- [ ] **Step 5: Commit**

```bash
git add backend/app/csv_live.py backend/tests/test_csv_live.py
git commit -m "csv_live: olcum satirini canli duruma ceviren saf esleyici"
```

---

### Task 4: CSV ingest adaptörü (süreç içi) + `lifespan` bağlanması

**Files:**
- Create: `backend/app/adapters/csv_replay.py`
- Modify: `backend/app/hub.py` (`apply_measurement`)
- Modify: `backend/app/main.py` (lifespan'a CSV dalı)
- Test: `backend/tests/test_csv_ingest.py` (yeni)

**Interfaces:**
- Consumes: Task 3'ün `apply_measurement`, `app.sim.replay.write_moment/prune/_with_lock_retry`, `app.sim.csv_reader.read_moments/read_measurement`
- Produces:
  - `LiveHub.apply_measurement(rec: MeasurementRecord, time_iso: str) -> None`
  - `run_csv_ingest(hub: LiveHub, csv_dir: Path, period_ms: int, retention_min: int) -> None` (async, sonsuz)

- [ ] **Step 1: Write the failing test**

`backend/tests/test_csv_ingest.py`:

```python
import asyncio

import pytest

from app.adapters.csv_replay import run_csv_ingest
from app.config import settings
from app.hub import LiveHub
from app.sim.csv_reader import FeatureValue, LimitValue, MeasurementRecord
from datetime import datetime


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _rec() -> MeasurementRecord:
    return MeasurementRecord(
        unit_no=10660,
        source_time=datetime(2026, 8, 10, 11, 23, 2),
        channel_nr=1,
        tool_nr=11,
        program_nr=0,
        cut_nr=0,
        workpiece=None,
        alarm=None,
        alarm_limit=None,
        source_file="x.csv",
        features=[FeatureValue(slot=1, name="SPINDEL", value=115.0, work_value=None)],
        limits=[LimitValue(limit_nr=1, level=230.0, lim_type=2, feature_nr=1)],
    )


def test_hub_olcumu_uygular_ve_frames_artirir():
    hub = LiveHub(source_name="csv")
    hub.apply_measurement(_rec(), "2026-08-10T11:23:02")
    assert hub.frames == 1
    assert [f.name for f in hub.state.features] == ["SPINDEL"]
    # Tel istatistigi URETILMEZ: CSV'nin teli yoktur.
    assert hub.wire is None


@pytest.mark.anyio
async def test_ingest_hubi_besler_ve_baglantiyi_bildirir(db_bos):
    """Adaptor gercek veri/ klasorunu okur (conftest SIM_CSV_DIR'i sabitler)."""
    hub = LiveHub(source_name="csv")
    task = asyncio.create_task(
        run_csv_ingest(
            hub,
            csv_dir=settings.csv_dir(),
            period_ms=0,
            retention_min=60,
        )
    )
    # Birkac anin islenmesine izin ver, sonra iptal et.
    for _ in range(200):
        if hub.frames > 0 and hub.upstream_connected:
            break
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert hub.frames > 0
    assert hub.upstream_connected is True
    assert hub.state.features, "ozellik uretilmedi"


@pytest.mark.anyio
async def test_csv_koku_yoksa_baglanti_dusuk_bildirilir(tmp_path):
    """Eksik klasor sessizce bos donmez: durum "bagli degil" olur."""
    hub = LiveHub(source_name="csv")
    await run_csv_ingest(hub, csv_dir=tmp_path, period_ms=0, retention_min=60)
    assert hub.upstream_connected is False
    assert hub.frames == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_csv_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.adapters.csv_replay'`

- [ ] **Step 3: Add `apply_measurement` to `LiveHub`**

`backend/app/hub.py` — importlara ekleyin:

```python
from app.csv_live import apply_measurement as _apply_measurement
from app.sim.csv_reader import MeasurementRecord
```

`set_wire_counters`'ın üstüne:

```python
    def apply_measurement(self, rec: MeasurementRecord, time_iso: str) -> None:
        """CSV olcum satirini duruma isler.

        TEL ISTATISTIGI URETMEZ (`self.wire` None kalir): WireStats
        Promos3 tasima teshisidir (datagram/CAN cerceve sayaclari) ve
        CSV'nin teli yoktur. Canlilik `frames` ile olculur.
        """
        self.state = _apply_measurement(self.state, rec, time_iso)
        self.frames += 1
        self._bump(state=True)
```

- [ ] **Step 4: Write `backend/app/adapters/csv_replay.py`**

```python
"""CSV tekrar-oynatma ingest adaptoru — SUREC ICI.

run_promos3_ingest ile ayni sozlesme: sonsuz async gorev, iptal edilebilir,
kendi durumunu hub'a bildirir.

NEDEN SUREC ICI: bu adaptor hub'i besler, yani ekranin gordugu canli durumu
uretir. Ayri bir surec (eski `python -m app.sim.replay`) bunu ancak IPC ile
yapabilirdi. CLI hala durur ve DB'ye yazmayi surdurur; bu adaptor ayni
yardimcilari cagirir, kopyalamaz.

DB YAZMASI SURUYOR: /api/measurements ve test_replay.py bozulmaz.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.exc import OperationalError

from app.db import SessionLocal
from app.hub import LiveHub
from app.sim.csv_reader import Moment, read_measurement, read_moments
from app.sim.replay import _prune_with_retry, _to_row, _with_lock_retry

log = logging.getLogger("app.adapters.csv_replay")

SOURCE = "csv"


def _read_and_write(session, moment: Moment, now: datetime) -> list:
    """Bir anin kayitlarini okur, DB'ye yazar ve KAYITLARI doner.

    write_moment yalnizca SAYI donuyordu; hub'i beslemek icin kayitlarin
    kendisi gerekiyor. Okuma+yazma tek yerde kaliyor ki dosya iki kez
    okunmasin.
    """
    records = []
    for unit_no, path in moment.files:
        record = read_measurement(path, unit_no)
        if record is None:
            continue  # bozuk dosya TUM ani dusurmez
        session.add(_to_row(record, now))
        records.append(record)
    session.commit()
    return records


async def run_csv_ingest(
    hub: LiveHub, csv_dir: Path, period_ms: int, retention_min: int
) -> None:
    """CSV'leri DONGUSEL okur: DB'ye yazar ve hub'i besler."""
    try:
        moments = await asyncio.to_thread(read_moments, csv_dir)
    except FileNotFoundError as exc:
        # Sessizce bos donmek "calisiyor ama hicbir sey yazmiyor" demekti.
        log.error("CSV kaynagi okunamadi: %s", exc)
        hub.set_source_status(SOURCE, False)
        return

    log.info("CSV SIM  -  uretilen her satir CSV'DEN gelir, canli olcum DEGILDIR")
    log.info("  kaynak: %s   an sayisi: %d", csv_dir, len(moments))

    with SessionLocal() as session:
        while True:
            try:
                for moment in moments:
                    now = datetime.now(UTC).replace(tzinfo=None)
                    records = await asyncio.to_thread(
                        _with_lock_retry,
                        session,
                        moment.name,
                        lambda: _read_and_write(session, moment, now),
                    )
                    # Hub yazmalari OLAY DONGUSUNDE kalir: hub kilitsizdir
                    # ve tek dongu varsayar (bkz. hub.py basligi).
                    for rec in records or []:
                        hub.apply_measurement(rec, now.isoformat())
                    if records:
                        hub.set_source_status(SOURCE, True)
                    if period_ms > 0:
                        await asyncio.sleep(period_ms / 1000)

                await asyncio.to_thread(
                    _prune_with_retry,
                    session,
                    datetime.now(UTC).replace(tzinfo=None)
                    - timedelta(minutes=retention_min),
                )
            except OperationalError as exc:
                # Kalici bir DB arizasi sessizce sifir-satir turlara
                # donusmez; acikca durur ve durumu dusuk bildirir.
                log.error("Kalici veritabani hatasi, CSV ingest duruyor: %s", exc)
                hub.set_source_status(SOURCE, False)
                return

            # Tur sonu tabani: `period_ms=0` verildiginde serbest kosmasin.
            await asyncio.sleep(0.2)
```

**Not:** `_with_lock_retry` ve `_prune_with_retry` `app/sim/replay.py`'de zaten var; `_to_row` da öyle. Bunlar `_` ile başlıyor ama modül içi değil paket içi paylaşımdır — kopyalamak yerine içe aktarın.

- [ ] **Step 5: Wire it into `lifespan`**

`backend/app/main.py` — importa ekleyin:

```python
from app.adapters.csv_replay import run_csv_ingest
```

`lifespan` döngüsündeki `if` zincirini tamamlayın:

```python
        elif m.source.kind == "csv":
            tasks.append(
                asyncio.create_task(
                    run_csv_ingest(
                        hub,
                        csv_dir=settings.csv_dir(),
                        period_ms=settings.sim_period_ms,
                        retention_min=settings.sim_retention_minutes,
                    )
                )
            )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_csv_ingest.py -v`
Expected: PASS (3 test)

- [ ] **Step 7: Run the whole backend suite**

Run: `cd backend && uv run pytest -q`
Expected: PASS — özellikle `test_replay.py` ve `test_csv_reader.py` bozulmamalı.

- [ ] **Step 8: Commit**

```bash
git add backend/app/adapters/csv_replay.py backend/app/hub.py backend/app/main.py backend/tests/test_csv_ingest.py
git commit -m "CSV sim surec ici ingest adaptorune donustu; hub'i besler, DB'ye yazmayi surdurur"
```

---

### Task 5: Frontend — katalog istemcisi, akış kancası, `dataLive` düzeltmesi ve karşılama ekranı

> **Neden tek görev:** katalogu backend'e taşımak `facilities.ts`'i siler, ve o dosyayı
> `tezgah-route.tsx` içe aktarır. İkisini ayrı görevlere bölmek, ilkini `tsc` HATA
> VEREREK biten — yani tek başına doğrulanamayan — bir görev yapardı. Frontend
> değişikliği tek bir doğrulanabilir birimdir.

**Files:**
- Create: `frontend/src/domain/katalog.ts`
- Create: `frontend/src/features/karsilama/routes/karsilama-route.tsx`
- Delete: `frontend/src/domain/facilities.ts`
- Delete: `frontend/src/features/tezgah/routes/tezgah-route.tsx`
- Modify: `frontend/src/domain/backend.ts`, `frontend/src/domain/useLive.ts`, `frontend/src/domain/useBackendLive.ts`
- Modify: `frontend/src/app/uygulama-kabugu.tsx`, `frontend/src/app/router.tsx`

**Interfaces:**
- Consumes: Task 1–2'nin `/api/machines` ve `/api/stream?tezgah=`
- Produces:
  - `SourceKind`, `Machine`, `Facility`, `Katalog` tipleri
  - `useKatalog(pollMs?: number): { katalog, durum, yenile }`
  - `findMachine(k, id)`, `findFacility(k, id)`, `machineTitle(f, m)`
  - `KAYNAK_ADI: Record<SourceKind, string>`
  - `useLive(machineId: string | null): LiveConnection` (`frames` alanı ile)
  - `/` rotasında karşılama ekranı; seçim `→ /canli?tezgah=<id>`

**ÖNCE OKUYUN** (CLAUDE.md kuralı, Step 7'den önce): `frontend/node_modules/@alp/design-system/COMPONENTS.md` (Card · Section · Tabs · Badge · Alert · Skeleton · PageShell · Button) ve `docs/design-language.md`.

- [ ] **Step 1: Write `frontend/src/domain/katalog.ts`**

```ts
// Tesis / tezgah kataloğu — backend'den gelir (`GET /api/machines`).
//
// Katalog ARTIK BURADA DOĞMAZ (eski `facilities.ts` onu üretiyordu): üç
// kaynak geldiğinde tezgah→kaynak bağlaması zaten backend'de olmak zorunda,
// ve katalogu burada da tutmak aynı bağlamayı iki yerde tutmak olurdu.
//
// Backend ekran METNİ göndermez, kaynak KİMLİĞİ gönderir; okunur karşılığı
// aşağıdaki `KAYNAK_ADI` haritasındadır.

import { useCallback, useEffect, useState } from "react";

/** Kaynak kimliği — `provis` ile `promos3-sim` aynı teli konuşur, aynı şey değildir. */
export type SourceKind = "provis" | "promos3-sim" | "csv";

export interface Machine {
  id: string;
  name: string;
  model?: string;
  /** Kaynak yoksa null — bu bir arıza değil, yapılandırmadır. */
  source: SourceKind | null;
  sourcePort: number | null;
  /** Kaynağın ŞU ANKİ durumu; yapılandırma değil gerçek. */
  connected: boolean;
}

export interface Facility {
  id: string;
  name: string;
  machines: Machine[];
}

export interface Katalog {
  facilities: Facility[];
}

/** Kaynağın okunur adı. Arayüz metni arayüzün işidir. */
export const KAYNAK_ADI: Record<SourceKind, string> = {
  provis: "PROVIS ağ geçidi",
  "promos3-sim": "Simülatör — değerler sentetiktir",
  csv: "CSV tekrar oynatma",
};

export type KatalogDurum = "loading" | "ready" | "error";

/**
 * Katalog kancası.
 *
 * `pollMs` verilirse `connected` tazeliği için düzenli yeniden çekilir —
 * karşılama ekranı bunu kullanır. İzleme ekranlarında gerekmez: oradaki
 * bağlantı durumunu SSE `status` olayı zaten taşır.
 */
export function useKatalog(pollMs?: number) {
  const [katalog, setKatalog] = useState<Katalog | null>(null);
  const [durum, setDurum] = useState<KatalogDurum>("loading");

  const cek = useCallback(async (signal?: AbortSignal) => {
    try {
      const r = await fetch("/api/machines", { signal });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setKatalog((await r.json()) as Katalog);
      setDurum("ready");
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      // Boş katalogla devam ETMEK yanlış olurdu: "hiç tezgah yok" diye
      // okunurdu. Hata durumu ayrı taşınır.
      setDurum("error");
    }
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    void cek(ac.signal);
    if (!pollMs) return () => ac.abort();
    const id = window.setInterval(() => void cek(ac.signal), pollMs);
    return () => {
      ac.abort();
      window.clearInterval(id);
    };
  }, [cek, pollMs]);

  return { katalog, durum, yenile: () => void cek() };
}

export function findFacility(k: Katalog | null, id: string): Facility | undefined {
  return k?.facilities.find((f) => f.id === id);
}

export function findMachine(k: Katalog | null, id: string): Machine | undefined {
  for (const f of k?.facilities ?? []) {
    const m = f.machines.find((x) => x.id === id);
    if (m) return m;
  }
  return undefined;
}

/** Başlıklarda kullanılan tam ad: "Tesis A · Tezgah 1". */
export function machineTitle(facility: Facility, machine: Machine): string {
  return `${facility.name} · ${machine.name}`;
}
```

- [ ] **Step 2: Delete the old catalog**

```bash
git rm frontend/src/domain/facilities.ts
```

- [ ] **Step 3: Carry `frames` through the stream contract**

`frontend/src/domain/backend.ts` — `BackendStateEvent`'i güncelleyin:

```ts
/** /api/stream "state" olayının verisi: sürüm sayacı + akış canlılığı + tam anlık görüntü. */
export interface BackendStateEvent {
  seq: number;
  /**
   * Backend'in uyguladığı yük sayısı — KAYNAKTAN BAĞIMSIZ canlılık ölçüsü.
   *
   * `wire.parsed` yalnız Promos3 taşımasını sayar; CSV tezgahının teli
   * olmadığı için orada hep 0 kalır ve üst bar kusursuz akan bir tezgahta
   * "Veri Yok" yazardı.
   */
  frames: number;
  state: WireLiveState;
}
```

`frontend/src/domain/useLive.ts` — `LiveConnection`'a ekleyin:

```ts
  /** Backend'in uyguladığı yük sayısı; 0 ise henüz veri gelmemiş. */
  frames: number;
```

Ve kancanın imzasını güncelleyin (dosya `useBackendLive`'ı yeniden dışa aktarır; imza değişikliği oradadır).

`frontend/src/domain/useBackendLive.ts`:
- `const STREAM_URL = "/api/stream";` satırını **silin**.
- İmzayı `export function useBackendLive(machineId: string | null): LiveConnection {` yapın.
- `const [frames, setFrames] = useState(0);` ekleyin.
- `useEffect` gövdesinin başındaki `if (!enabled) return;` yerine `if (!machineId) return;`.
- `new EventSource(STREAM_URL)` yerine:

```ts
      es = new EventSource(`/api/stream?tezgah=${encodeURIComponent(machineId)}`);
```

- `state` dinleyicisine `setFrames(ev.frames);` ekleyin.
- `useEffect` bağımlılığını `[machineId]` yapın ve temizlikte `setFrames(0)` çağırın (tezgah değişince önceki tezgahın sayacı taşınmasın).
- Dönüşe `frames` ekleyin.

- [ ] **Step 4: Update the app shell**

`frontend/src/app/uygulama-kabugu.tsx`:

- İmportu değiştirin: `facilities` yerine
  ```ts
  import { findFacility, findMachine, machineTitle, useKatalog } from "@/domain/katalog";
  ```
- `UygulamaKabugu` içinde varsayılana düşmeyi **kaldırın**:

```ts
export default function UygulamaKabugu() {
  const [params] = useSearchParams();
  const machineId = params.get("tezgah");

  // Tezgah SEÇİLMEDİYSE varsayılana düşülmez — kullanıcı seçsin diye
  // karşılama ekranı var. Sessiz varsayılan, bu işin tam tersiydi.
  if (!machineId) return <Navigate to="/" replace />;

  // key={machineId}: tezgah değişince kabuk BAŞTAN kurulur (ADR-0006/4).
  return <KabukIc key={machineId} machineId={machineId} />;
}
```

- `KabukIc` içinde katalogu kullanın:

```ts
  const { katalog } = useKatalog();
  const machine = findMachine(katalog, machineId);
  const facility = findFacility(katalog, machineId.split("/")[0] ?? "");
  // Katalog gelene dek ham kimlik gösterilir: ad uydurmaktansa dürüst.
  const baslik = facility && machine ? machineTitle(facility, machine) : machineId;
  const hasSource = machine?.source != null;
```

- `useLive` çağrısını değiştirin:

```ts
  const streamed = useLive(hasSource && !paused ? machineId : null);
```

- Kaynaksız boş bağlantıya `frames` ekleyin:

```ts
  const live: LiveConnection = hasSource
    ? streamed
    : { connected: false, link: "no-source", frames: 0, state: NO_SOURCE_STATE };
```

- **Hatanın düzeltildiği satır:**

```ts
  // Veri canli mi: zincir saglam VE backend gercekten yuk uygulamis.
  //
  // ESKIDEN `wire.parsed > 0` bakiliyordu. `wire` PROMOS3 TASIMA
  // teshisidir (datagram/CAN cerceve sayaclari); CSV tezgahinin teli
  // yoktur, yani kusursuz akan bir tezgahta bu satir "Veri Yok" yazardi.
  const dataLive = live.connected && live.frames > 0;
```

- "Değiştir" düğmesini karşılamaya yönlendirin:

```tsx
          <Button
            size="sm"
            variant="secondary"
            onClick={() => navigate(`/?tezgah=${encodeURIComponent(machineId)}`)}
          >
            Değiştir
          </Button>
```

- `Navigate`'i `react-router-dom` importuna ekleyin.

Bu aşamada `tezgah-route.tsx` hâlâ `facilities.ts`'i içe aktardığı için proje tip
kontrolünden GEÇMEZ; Step 5–6 onu değiştirir. Doğrulama Step 7'dedir.

Karşılama ekranında kilitlenmiş tasarım kararları — hepsi pakete karşı doğrulandı:

| Karar | Gerekçe |
|---|---|
| Dış çerçeve `PageShell` (AppShell YOK) | Karşılama kabuğun dışındadır (henüz tezgah seçilmedi, nav anlamsız olurdu). `PageShell` başlığı, `--container-max` genişliğini ve dolguyu getirir; elle çerçeve yazmak yasak. |
| Kart ızgarası `alp-oto-izgara` | Paketin kendi yardımcı sınıfı (`dist/styles.css`'te doğrulandı). Elle `grid-template-columns` yazılmaz. |
| Kart içinde `Button`, kart kendisi tıklanabilir DEĞİL | `CardProps` `onClick` **almaz** (`dist/index.d.ts`: prop'lar açıkça destructure edilir, native attr yayılmaz). `interactive` verip tıklanmayan bir kart yanıltıcı bir affordance olurdu. |
| Kart düğmeleri `variant="secondary"` | Bir ekranda tek `primary` kuralı; dört kartın dördü de primary olamaz. |
| Durum noktası + METİN | "Renk tek başına bilgi taşımaz" (tasarım dili). |
| Kaynaksız kart da seçilebilir | ADR-0006 madde 3: boş ekran doğru davranıştır ve kullanıcı bunu **seçmeden önce** okur. |
| Dört durum karşılanır | yükleme = `Skeleton` (spinner değil), hata = `Alert tone="danger"` + tekrar dene. |

- [ ] **Step 5: Write the welcome screen**

`frontend/src/features/karsilama/routes/karsilama-route.tsx`:

```tsx
// Karşılama — tesis ve tezgah seçimi. Uygulamanın giriş kapısı.
//
// DÜRÜSTLÜK KURALI: hangi tezgahın arkasında gerçek kaynak olduğu SEÇERKEN
// söylenir, seçtikten sonra boş ekranla değil. Üç durum ayrı ayrı görünür —
// "kaynak yok", "kaynak var ama düşmüş" ve "veri akıyor" üç ayrı şeydir ve
// ikincisini yeşil göstermek operatörü boş bir ekrana hazırlıksız yollardı.
//
// Kabuğun DIŞINDADIR: tezgah henüz seçilmediği için AppShell'in gezinmesi
// (Canlı/Alarmlar/Olaylar) anlamsız olurdu.

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Alert,
  Badge,
  Button,
  Card,
  PageShell,
  Section,
  Skeleton,
  Tabs,
  type BadgeTone,
} from "@alp/design-system";
import {
  KAYNAK_ADI,
  findFacility,
  useKatalog,
  type Machine,
} from "@/domain/katalog";
import { URUN_ADI } from "@/app/urun";

// `connected` tazeliği için yeniden çekme aralığı. Karşılama ekranı açıkken
// bir kaynak düşerse kart bunu söylemeli.
const YENILEME_MS = 5_000;

/** Üç durum, üç ayrı rozet. Renk tek başına bilgi taşımaz — metin hep var. */
function rozet(m: Machine): { tone: BadgeTone; label: string } {
  if (m.source == null) return { tone: "neutral", label: "Kaynak yok" };
  if (!m.connected) return { tone: "warning", label: "Kaynak bağlı değil" };
  return { tone: "success", label: "Canlı" };
}

export default function KarsilamaRoute() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // "Değiştir" ile gelindiyse mevcut tezgah taşınır: doğru tesis seçili açılır
  // ve vazgeçilebilir olur.
  const mevcut = params.get("tezgah");

  const { katalog, durum, yenile } = useKatalog(YENILEME_MS);
  const [tesisId, setTesisId] = useState<string | null>(null);

  const secili =
    tesisId ?? mevcut?.split("/")[0] ?? katalog?.facilities[0]?.id ?? null;
  const tesis = secili ? findFacility(katalog, secili) : undefined;

  const izle = (id: string) =>
    navigate(`/canli?tezgah=${encodeURIComponent(id)}`);

  return (
    <PageShell
      title={URUN_ADI}
      description="İzlemek istediğiniz tesisi ve tezgahı seçin."
      actions={
        mevcut ? (
          <Button size="sm" variant="secondary" onClick={() => izle(mevcut)}>
            Vazgeç
          </Button>
        ) : undefined
      }
    >
      {durum === "error" && (
        <Alert
          tone="danger"
          title="Tezgah listesi alınamadı"
          actions={
            <Button size="sm" onClick={yenile}>
              Tekrar dene
            </Button>
          }
        >
          Backend'e ulaşılamıyor. Liste boş değil, BİLİNMİYOR — çalışan
          tezgahlar olabilir.
        </Alert>
      )}

      {durum === "loading" && (
        <div aria-busy="true" className="flex flex-col gap-3">
          <Skeleton style={{ width: 240 }} />
          <Skeleton />
          <Skeleton />
        </div>
      )}

      {katalog && (
        <>
          <Tabs
            tabs={katalog.facilities.map((f) => ({ id: f.id, label: f.name }))}
            active={secili ?? ""}
            onChange={setTesisId}
            panelId="tezgah-listesi"
          />

          {tesis && (
            <div
              id="tezgah-listesi"
              role="tabpanel"
              aria-label={`${tesis.name} tezgahları`}
            >
              <Section title={tesis.name} count={tesis.machines.length}>
                <div className="alp-oto-izgara">
                  {tesis.machines.map((m) => {
                    const r = rozet(m);
                    return (
                      <Card key={m.id} title={m.name} subtitle={m.model}>
                        <div className="flex flex-col items-start gap-3">
                          <Badge tone={r.tone} dot>
                            {r.label}
                          </Badge>
                          <span className="type-help text-muted-foreground">
                            {m.source
                              ? KAYNAK_ADI[m.source]
                              : "Bu tezgaha kaynak tanımlanmamış — ekran boş kalacak."}
                          </span>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => izle(m.id)}
                          >
                            İzle
                          </Button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </Section>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
```

- [ ] **Step 6: Delete the old picker and rewire the router**

```bash
git rm frontend/src/features/tezgah/routes/tezgah-route.tsx
```

`frontend/src/app/router.tsx` — `TezgahRoute` lazy importunu silin, şunu ekleyin:

```tsx
const KarsilamaRoute = lazy(() => import("@/features/karsilama/routes/karsilama-route"));
```

Ve rota ağacını değiştirin:

```tsx
export const router = createBrowserRouter([
  // Karşılama kabuğun DIŞINDADIR: tezgah seçilmeden nav anlamsız olurdu.
  { path: "/", element: sarmala(<KarsilamaRoute />) },
  // Eski seçim ekranı karşılamaya taşındı; tek seçici kalsın.
  { path: "/tezgah", element: <Navigate to="/" replace /> },
  {
    element: <UygulamaKabugu />,
    children: [
      { path: "canli", element: sarmala(<CanliRoute />) },
      { path: "alarmlar", element: sarmala(<AlarmlarRoute />) },
      { path: "olaylar", element: sarmala(<OlaylarRoute />) },
    ],
  },
  // Varsayılan tezgah YOK: bilinmeyen yol seçime döner.
  { path: "*", element: <Navigate to="/" replace /> },
]);
```

- [ ] **Step 7: Type-check and lint**

Run: `cd frontend && bun run lint`
Expected: PASS (0 hata). `facilities.ts` ve `tezgah-route.tsx` artık silinmiş olmalı;
bu adım o iki silmenin de temiz olduğunun kanıtıdır.

- [ ] **Step 8: Look at it**

Run: `.\basla.bat provis` (tek kip Task 6'da gelir), sonra banner'daki **LAN IP** adresini açın (`127.0.0.1` bu makinede tarayıcıda AÇILMAZ — DLP eklentisi; bkz. CLAUDE.md).

Bu kipte yalnız A/1'in kaynağı açıktır; A/2 ve A/3 "Kaynak bağlı değil" görünür — bu
doğru davranıştır ve üç kaynağın birden koştuğu doğrulama Task 6'dadır.

Kontrol listesi:
- Karşılama açılıyor, dört tesis sekmesi var.
- Tesis A'da dört kart; A/1–A/3 kaynak adı yazıyor, A/4 "Kaynak yok".
- Koyu tema (`data-theme="dark"`) bozulmuyor.
- Klavyeyle sekmeler ok tuşlarıyla, kartlar Tab ile gezilebiliyor; odak halkası görünür.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/domain/katalog.ts frontend/src/domain/backend.ts \
        frontend/src/domain/useLive.ts frontend/src/domain/useBackendLive.ts \
        frontend/src/app/uygulama-kabugu.tsx frontend/src/app/router.tsx \
        frontend/src/features/karsilama
git commit -m "Frontend: katalog backend'den, akis tezgaha bagli, karsilama ekrani giris kapisi"
```

(Silinen `facilities.ts` ve `tezgah-route.tsx` Step 2/6'daki `git rm` ile zaten
sahnelenmiştir.)

---

### Task 6: `basla.bat` — tek kip

**Files:**
- Modify: `basla.bat`

- [ ] **Step 1: Rewrite the mode logic**

Değişiklikler:

1. **Başlık bloğu (madde 1–11) yeniden yazılır.** Kip menüsü anlatan satırlar çıkar; şu maddeler KORUNUR ve güncellenir: 1 (Vite `--host`), 2 (bayrak açıkça yazılır), 3 (env miras), 4 (portsuz süreç sağ kalır), 6 (`--serve` tuzağı), 7 (`>` yazma), 8 (LAN IP / DLP), 9 (`timeout` yerine `ping`), 10 (`.\` öneki). Madde 11 (CSV kipinde kök açılmaz) **kalkar** — artık tek kip var ve uygulama kökü her zaman açılır.
2. **Kullanım bölümü:**

```
rem      .\basla.bat            Backend + arayuz + simulator. Uc kaynak da
rem                             ayri tezgahlara baglidir:
rem                               Tesis A / Tezgah 1  PROVIS   (UDP 1789)
rem                               Tesis A / Tezgah 2  SIM      (UDP 1790)
rem                               Tesis A / Tezgah 3  CSV      (surec ici)
rem                             Hangi tezgahin yayin yaptigi karsilama
rem                             ekraninda yazar.
rem
rem      .\basla.bat dur        Baslatilan her seyi durdurur.
```

3. **`MODE` çözümlemesi, `:kaynak_sor` menüsü, `choice` çağrısı ve `:bilinmeyen_kip` etiketi silinir.** `dur` kontrolü kalır.
4. **Ortam bloğu** üç bayrağı da açıkça yazar (madde 2):

```bat
set "VITE_LIVE_SOURCE=backend"
set "PROMOS3_ENABLED=true"
set "PROMOS3_BIND=127.0.0.1"
set "PROMOS3_PORT=1789"
set "PROMOS3_SIM_ENABLED=true"
set "PROMOS3_SIM_PORT=1790"
set "CSV_REPLAY_ENABLED=true"
```

5. **`:sahte_acik` dalı (başlamayı reddetme) silinir**, ama `:sahte_hazirlik` temizliği KALIR:

```bat
rem Madde 6: elle cift tiklanan bir simulator VARSAYILAN --serve kipindedir
rem ve 0.0.0.0:1789'u baglar - yani GERCEK PROVIS'in datagramlarini calar.
rem Kendi --stream surecimiz hicbir port baglamaz, ama onceden kosan bir
rem kopya bu riski hala tasir. Baslamadan once temizlenir.
call :sahte_var
if not errorlevel 1 (
    echo       Onceden kosan simulator bulundu, durduruluyor ^(madde 6^).
    call :sahte_oldur
)
```

6. **`alembic upgrade head` HER koşumda** (CSV artık her koşumda yazar). `:csv_hazirlik`'teki `veri\10660` + `veri\10665` kontrolü ve `:yok_veri` hatası KORUNUR. `call :csv_sim_oldur` çağrısı burada KALIR (elle başlatılmış `python -m app.sim.replay` kopyası SQLite kilidini tutup alembic'i yanıltıcı bir hatayla düşürebilir).
7. **Simülatör 1790'a gönderir:**

```bat
start "ALP Simulator" /D "%CD%\promos3-c\done" cmd /k .\promos3_sim.exe --stream 127.0.0.1:1790 --period 200
```

8. **`[3/3]` CSV penceresi silinir** (`:csv_baslat` etiketi ve `start "ALP CSV Sim" ...`). Adım numaraları `[1/3]`/`[2/3]`/`[3/3]` olarak kalır (backend / arayüz / simülatör).
9. **Banner** kip satırlarını kaybeder, şunu kazanır:

```bat
echo   Tezgahlar:  A/1 PROVIS 1789  .  A/2 SIM 1790  .  A/3 CSV
echo   A/2 SENTETIKTIR - o tezgahtaki hicbir sayi olcum degildir.
```

(Madde 7: bu satırların içinde `>` OLMAZ.)
10. **`:durdur`** aynen kalır — `ALP CSV Sim` başlık filtresi ve `call :csv_sim_oldur` dahil (CLI hâlâ duruyor).

- [ ] **Step 2: Verify CRLF line endings**

Run: `file basla.bat` (ya da `git diff --stat`)
Expected: "CRLF line terminators". `.bat` dosyaları CRLF olmak zorunda.

- [ ] **Step 3: Run it end to end**

Run: `.\basla.bat`
Expected: üç pencere (Backend / Frontend / Simulator), banner LAN IP basar, tarayıcı karşılama ekranında açılır.

Doğrulayın:
- A/1 kartı: gerçek gateway yoksa "Kaynak bağlı değil" (doğru davranış).
- A/2 kartı: "Canlı" + "Simülatör — değerler sentetiktir".
- A/3 kartı: "Canlı" + "CSV tekrar oynatma".
- A/2 seçilince grafikler akar; üst bar **"Veri Akışı Aktif"** yazar.
- A/3 seçilince grafikler akar ve üst bar yine **"Veri Akışı Aktif"** yazar (bu `frames` düzeltmesinin kanıtıdır — eski kodda "Veri Yok" yazardı).
- A/4 seçilince ekran boş, üst barda "bu tezgah için canlı kaynak tanımlı değil".
- `curl "http://127.0.0.1:8001/api/machines"` üç kaynağı da gösterir.

Sonra: `.\basla.bat dur` — üç pencere de kapanır, `promos3_sim` süreci kalmaz.

- [ ] **Step 4: Commit**

```bash
git add basla.bat
git commit -m "basla.bat tek kip: uc kaynak birden, sim 1790'a, CSV surec ici"
```

---

### Task 7: ADR-0006 ve CLAUDE.md güncellemesi

**Files:**
- Modify: `docs/adr/0006-tesis-tezgah-secimi-katalog-statik-kaynak-tek.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update ADR-0006**

ADR kendi "Sonra ne gelir" maddesinde bunu **öngörmüştü**; o öngörü gerçekleşti. Başlığı ve kararları güncelleyin:

- Başlık: `# Tesis/tezgah seçimi arayüzde; katalog backend'de, kaynak tezgah başına`
- **Madde 1 değişir:** katalog `frontend/src/domain/facilities.ts`'ten `backend/app/machines.py`'ye taşındı. Adların yapılandırma olduğu gerekçesi AYNEN geçerli; değişen yalnız nerede durduğu. Sebep: üç kaynakla tezgah→kaynak bağlaması zaten backend'de olmak zorunda ve iki yerde tutulmuş bir bağlamanın uyuşmazlıkları sessiz olurdu.
- **Madde 2 değişir:** canlı kaynak artık tek değil. Üç kaynak üç ayrı tezgaha bağlıdır (`provis` 1789 / `promos3-sim` 1790 / `csv` süreç içi); `hasLiveSource` bayrağı yerini tezgah başına `SourceSpec`e bıraktı ve `LIVE_MACHINE_ID` kalktı.
- **Madde 3 aynen geçerli** (kaynaksız tezgahta ekran dürüstçe boş) — üstüne bir kademe eklendi: "kaynak yok" ile "kaynak var ama bağlı değil" karşılama ekranında **ayrı** gösterilir.
- **Madde 4 aynen geçerli** (`key={machineId}`).
- **Yeni madde:** karşılama ekranı artık gerçek bir kapıdır. Önceki sürümde "karşılama → seçim → izleme" yazıyordu ama kodda `/` doğrudan `/canli`'ye gidiyor ve seçilmemiş tezgah `DEFAULT_MACHINE_ID`'ye düşüyordu; o boşluk kapandı.
- **"Sonra ne gelir"i yenileyin:** katalogun DB'ye taşınması ve tezgah başına gerçek gateway bağlanması hâlâ ileride.

- [ ] **Step 2: Update CLAUDE.md**

`## Calistirma` bölümünde:
- `.\basla.bat` artık kip almaz — menü/`provis`/`sim`/`csv` argümanlarını anlatan satırlar çıkar.
- Yerine tezgah bağlaması tablosu ve şu not girer: CSV sim artık **süreç içidir** ve hub'ı besler; `promos3_sim.exe` ile karıştırılmaz (biri TEL biçimi üretir, öteki ÖLÇÜM SATIRI — ama artık ikisi de ekranı besler, farklı tezgahlarda).
- `PROMOS3_ENABLED=false` olan CSV kipi anlatımı çıkar (artık öyle bir kip yok).
- LAN IP / DLP maddesi AYNEN kalır.

- [ ] **Step 3: Verify nothing else references the removed things**

Run:
```bash
grep -rn "facilities\.ts\|LIVE_MACHINE_ID\|DEFAULT_MACHINE_ID\|hasLiveSource\|basla.bat sim\|basla.bat csv\|basla.bat provis" --include=*.ts --include=*.tsx --include=*.py --include=*.md --include=*.bat . | grep -v node_modules | grep -v docs/superpowers | grep -v docs/adr/0006
```
Expected: çıktı boş. (Spec ve eski ADR metni hariç tutulur; spec tarihsel kayıttır.)

- [ ] **Step 4: Full verification**

Run:
```bash
cd backend && uv run pytest -q
cd ../frontend && bun run lint
```
Expected: ikisi de PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/adr/0006-tesis-tezgah-secimi-katalog-statik-kaynak-tek.md CLAUDE.md
git commit -m "ADR-0006 ve CLAUDE.md coklu kaynak gercegine guncellendi"
```

---

## Doğrulama özeti

| Ne | Komut |
|---|---|
| Backend testleri | `cd backend && uv run pytest` |
| Frontend tip + lint | `cd frontend && bun run lint` |
| Şema | `cd backend && uv run alembic upgrade head` |
| Uçtan uca | `.\basla.bat`, LAN IP'den aç, A/1–A/4'ü sırayla seç |

**Kanıt olarak bakılacak tek satır:** A/3 (CSV) seçiliyken üst bar "Veri Akışı Aktif" yazmalı. Eski kodda "Veri Yok" yazardı ve bu, planın düzelttiği sessiz hatanın ta kendisidir.
