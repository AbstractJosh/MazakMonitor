from app.config import Settings
from app.hub import DATA_STALE_AFTER_S
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
    assert "dataAgeS" in govde["facilities"][0]["machines"][0]
    assert govde["stalenessS"] == DATA_STALE_AFTER_S


def test_catalog_wire_BAGLI_ama_sessiz_kaynagi_ayirt_eder():
    """Halka ayakta + veri yok, halkanin kendisiyle AYNI SEY DEGILDIR.

    Karsilama ekraninin dorduncu hali ("Veri bekleniyor") tam da bu ikilinin
    farkindan dogar: `connected` True iken `dataAgeS` None olabilir ve o
    tezgah yesil gorunmemelidir.
    """
    catalog = build_catalog(_acik())
    out = catalog_wire(
        catalog,
        connected_ids={"tesis-a/tezgah-1", "tesis-a/tezgah-3"},
        data_age_s={"tesis-a/tezgah-1": None, "tesis-a/tezgah-3": 0.4},
    )
    tezgahlar = {m.id: m for f in out.facilities for m in f.machines}

    # Soketi bagli, tek bayt gelmemis (PROMOS3_BIND=127.0.0.1 hali).
    assert tezgahlar["tesis-a/tezgah-1"].connected is True
    assert tezgahlar["tesis-a/tezgah-1"].data_age_s is None
    # Gercekten akan kaynak.
    assert tezgahlar["tesis-a/tezgah-3"].data_age_s == 0.4
    # Kaynagi hic olmayan tezgahta yas da yoktur.
    assert tezgahlar["tesis-a/tezgah-4"].data_age_s is None


def test_catalog_wire_yas_verilmezse_hepsi_bilinmez():
    """Cagiran yas gecmediyse "0 saniye once" uydurulmaz."""
    catalog = build_catalog(_acik())
    out = catalog_wire(catalog, connected_ids={"tesis-a/tezgah-1"})
    tezgahlar = {m.id: m for f in out.facilities for m in f.machines}
    assert tezgahlar["tesis-a/tezgah-1"].data_age_s is None
