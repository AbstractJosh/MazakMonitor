from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Depo koku: <depo>/backend/app/config.py -> parents[2] = <depo>
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # PostgreSQL baglantisi. GERCEK deger her zaman .env'den gelir.
    # Asagidaki bos varsayilan, .env yokken acik bir hata almak icindir;
    # buraya parola/kullanici YAZILMAZ (bkz. .env.example).
    database_url: str = ""

    # --- Prometec CAN-over-UDP adaptoru (ADR-0002) — TEK CANLI KAYNAK ---
    #
    # Ayni yol hem atolyedeki gercek gateway'i hem de tezgah olmadan
    # promos3-c/done/promos3_sim.exe --stream'i dinler; tel bicimi aynidir.
    #
    # VARSAYILAN ACIK: uygulamanin tek veri kaynagi budur, kapali bir varsayilan
    # "calisiyor ama hicbir sey gostermiyor" backend'i normal hale getirirdi.
    # Testler bunu acikca kapatir (conftest.py: PROMOS3_ENABLED=false).
    promos3_enabled: bool = True
    # Dinlenecek arayuz. Gateway datagramlarini alan arayuzun adresi verilir;
    # "0.0.0.0" tum arayuzleri dinler.
    promos3_bind: str = "0.0.0.0"
    # PROVISsettings.ini [CAN] GatewayPort.
    promos3_port: int = 1789

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

    # Ozellik adlari — KURULUMA OZELDIR (rapor 7.2), koda gomulmez.
    #
    # ARTIK NORMALDE GEREKSIZDIR: adlar TELDEN gelir. MC_GIVEKANAL (0x0E)
    # cevabi SKanalRecV40'tir ve operatorun verdigi etiketler +0x4D'deki 4
    # yuvada durur (bu kurulumda VIBRATION / M131 DEBI / M131BASINC /
    # M08 DEBI, maskeler 0x01/0x02/0x04/0x08); live.py onlari oradan okur.
    #
    # Bu ayar yalnizca YEDEKTIR: kanal kaydi henuz gelmemisse ya da bir yuva
    # adsizsa devreye girer. Bicim: "maske=Ad", virgulle ayrilmis.
    #
    # Verilmezse arayuz yuva sirasini gosterir ("Özellik 1") — uydurma ad
    # YAZILMAZ.
    promos3_feature_names: str = ""

    # --- CSV tekrar-oynatma simulatoru (app/sim/replay.py) ---
    #
    # Bu simulator promos3_sim.exe DEGILDIR: o TEL bicimini uretir (UDP 1789),
    # bu ise OLCUM SATIRI uretir (CSV -> SQLite). Ikisi birbirine dokunmaz.

    # CSV kokü; bos ise depodaki veri/ kullanilir.
    sim_csv_dir: str = ""
    # Anlar arasi bekleme. 131 an x 1000 ms = tam tur ~2 dk 11 sn.
    sim_period_ms: int = 1000
    # Budama esigi. Sinirsiz buyuyen bir dosya, geceyi acik geciren bir
    # kosumda gigabaytlara cikar (1 sn periyotta saniyede 18 satir duser).
    sim_retention_minutes: int = 60

    def feature_names(self) -> dict[int, str]:
        """promos3_feature_names ayarini {kanalAnahtari: ad} sozlugune cevirir.

        Bozuk girisler (sayi olmayan anahtar, "=" icermeyen parca) SESSIZCE
        atlanir: yanlis yazilmis tek bir ad yuzunden backend acilmamamali.
        """
        out: dict[int, str] = {}
        for part in self.promos3_feature_names.split(","):
            key, sep, name = part.partition("=")
            if not sep:
                continue
            key, name = key.strip(), name.strip()
            if not name:
                continue
            try:
                # 0x01 gibi onekli yazim da kabul edilir (maske gosterimi).
                out[int(key, 0)] = name
            except ValueError:
                continue
        return out

    def db_url(self) -> str:
        """Etkin veritabani URL'i.

        .env'de DATABASE_URL verilmisse O kazanir (.env.example'daki niyet);
        verilmemisse yerel SQLite dosyasina dusulur. Boylece kurulumsuz bir
        makinede .bat cift tiklanabilir kalir.

        Yol MUTLAKTIR: sim backend/ icinden, testler baska bir dizinden kosar
        - goreli bir yol iki AYRI dosya acar ve "yazdim ama gorunmuyor"
        seklinde ortaya cikardi.
        """
        if self.database_url:
            return self.database_url
        return f"sqlite+pysqlite:///{(_REPO_ROOT / 'veri' / 'mazak.db').as_posix()}"

    def csv_dir(self) -> Path:
        """CSV kokü (icinde unite numarali klasorler)."""
        return Path(self.sim_csv_dir) if self.sim_csv_dir else _REPO_ROOT / "veri"


settings = Settings()