// Yerel @alp/design-system karsiligi — bilesen yuzeyi.
//
// NEDEN VAR: ic Gitea registry'si (10.10.100.220:3000) ALP agi disinda
// erisilemez ve paket public npm'de YOKTUR (dogrulandi: 404). Uygulamanin
// herhangi bir agda kosabilmesi icin paketin KULLANILAN yuzeyi burada yerel
// olarak karsilanir.
//
// KAPSAM: ekranlarin gercekten import ettigi 45 sembol. Paketin tamami DEGIL.
// Kaynak dosyalarin higbiri degistirilmedi; `@alp/design-system` takma adi
// vite.config.ts + tsconfig.json uzerinden buraya baglanir. Paket geri
// geldiginde bu dizin ve o iki takma ad silinir, tek satir ekran kodu
// degismez.
//
// Davranis sozlesmeleri KORUNDU (app.css bunlara yaslanir):
//   data-slot="app-shell-nav"        sol gezinme genislik gecisi
//   data-slot="page-shell"           kabugun kaydirma kipi
//   data-slot="page-shell-content"   asil kaydiran oge + pencere payi
//   data-slot="floating-panel"       cekmece cikis animasyonu
//   data-state="open|closed"         akordiyon + cekmece
//   --radix-accordion-content-height akordiyon yukseklik animasyonu

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactElement,
  type ReactNode,
} from "react";
import { ChevronDown, Download, RotateCcw, Search, Settings2, X } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   Belirtecler ve tipler
   ═══════════════════════════════════════════════════════════════════════ */

/** Ikon olcusu — ekranlar `IKON.md` gibi yazar, ham px gecmez. */
export const IKON = { xs: 12, sm: 16, md: 18, lg: 20, xl: 24, "2xl": 32 } as const;

export type BadgeTone = "neutral" | "success" | "danger" | "warning" | "sky" | "info";
export type AlertTone = "info" | "success" | "warning" | "danger";

export interface ShellNavItem {
  id: string;
  label: string;
  icon?: ReactNode;
}

/** Ton -> sinif. Renk TEK BASINA bilgi tasimaz; her yerde metin de vardir. */
const TON_ROZET: Record<BadgeTone, string> = {
  neutral: "bg-muted text-muted-foreground border-border",
  success: "bg-success-100 text-success-700 border-success-600/30",
  danger: "bg-danger-100 text-danger-700 border-danger-600/30",
  warning: "bg-warning-100 text-warning-700 border-warning-600/30",
  sky: "bg-sky-100 text-sky-700 border-sky-600/30",
  info: "bg-sky-100 text-sky-700 border-sky-600/30",
};

const TON_NOKTA: Record<BadgeTone, string> = {
  neutral: "bg-muted-foreground",
  success: "bg-success-600",
  danger: "bg-danger-600",
  warning: "bg-warning-600",
  sky: "bg-sky-600",
  info: "bg-sky-600",
};

function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/* ═══════════════════════════════════════════════════════════════════════
   Bicimleyiciler
   ═══════════════════════════════════════════════════════════════════════ */

const NF = new Intl.NumberFormat("tr-TR");
const NF1 = new Intl.NumberFormat("tr-TR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** Sayi -> ekran metni. `digits` verilirse o kadar ondalik. */
export function formatNumber(value: number, digits?: number): string {
  if (!Number.isFinite(value)) return "—";
  if (digits === 1) return NF1.format(value);
  if (digits != null) {
    return new Intl.NumberFormat("tr-TR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }
  return NF.format(value);
}

/**
 * "YYYY-MM-DD" TAKVIM GUNUDUR, an DEGIL (ADR-0005).
 *
 * `new Date("2026-08-10")` UTC gece yarisi olarak cozulur ve negatif ofsetli
 * bir tarayicida bir GUN GERI kayar. Parcalari elle ayirmak bunu keser.
 */
function gunAyristir(value: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!m) return null;
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

function anAyristir(value: string | number | Date): Date | null {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") return new Date(value);
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Takvim gunu — yalniz tarih, saat YOK. */
export function formatCalendarDay(day: string | Date): string {
  const d = typeof day === "string" ? (gunAyristir(day) ?? anAyristir(day)) : day;
  if (!d) return String(day);
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** Tam an — tarih + saat (saniye dahil; olay/alarm siralamasi saniyede ayrilir). */
export function formatDateTime(value: string | number | Date): string {
  const d = anAyristir(value);
  if (!d) return "—";
  return d.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/** "3 dk once" — canli listelerde mutlak saatten daha okunur. */
export function formatRelative(value: string | number | Date): string {
  const d = anAyristir(value);
  if (!d) return "—";
  const saniye = Math.round((Date.now() - d.getTime()) / 1000);
  if (saniye < 0) return "az sonra";
  if (saniye < 10) return "az önce";
  if (saniye < 60) return `${saniye} sn önce`;
  const dakika = Math.floor(saniye / 60);
  if (dakika < 60) return `${dakika} dk önce`;
  const saat = Math.floor(dakika / 60);
  if (saat < 24) return `${saat} sa önce`;
  return formatDateTime(d);
}

/* ═══════════════════════════════════════════════════════════════════════
   Temel denetimler
   ═══════════════════════════════════════════════════════════════════════ */

type ButonVariant = "primary" | "secondary" | "ghost";
type Olcu = "sm" | "md";

const BUTON_VARIANT: Record<ButonVariant, string> = {
  primary: "bg-navy-600 text-white border-navy-600 hover:bg-navy-700",
  secondary: "bg-card text-foreground border-border hover:bg-muted",
  ghost: "bg-transparent text-foreground border-transparent hover:bg-muted",
};

const BUTON_OLCU: Record<Olcu, string> = {
  sm: "h-8 px-2.5 text-xs gap-1.5",
  md: "h-10 px-3.5 text-sm gap-2",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  iconLeft,
  disabledReason,
  className,
  ...rest
}: {
  children?: ReactNode;
  variant?: ButonVariant;
  size?: Olcu;
  iconLeft?: ReactNode;
  /**
   * Devre disi birakan SEBEP. Duz `disabled` yerine bunun istenmesi
   * kasitlidir: sebepsiz devre disi bir dugme kullaniciya hicbir sey
   * soylemez; sebep `title` olarak da basilir.
   */
  disabledReason?: string;
  className?: string;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children">) {
  const kapali = disabledReason != null;
  return (
    <button
      type="button"
      disabled={kapali}
      title={disabledReason}
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-[var(--radius)] border font-medium transition-colors",
        BUTON_OLCU[size],
        BUTON_VARIANT[variant],
        kapali && "cursor-not-allowed opacity-50",
        className,
      )}
      {...rest}
    >
      {iconLeft}
      {children}
    </button>
  );
}

export function IconButton({
  label,
  children,
  variant = "ghost",
  size = "md",
  className,
  ...rest
}: {
  /** Erisilebilir ad — ZORUNLU: listede her dugme ayni ikonu tasir. */
  label: string;
  children: ReactNode;
  variant?: ButonVariant;
  size?: Olcu;
  className?: string;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children">) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-[var(--radius)] border transition-colors",
        size === "sm" ? "h-8 w-8" : "h-10 w-10",
        BUTON_VARIANT[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Badge({
  children,
  tone = "neutral",
  dot,
  size = "md",
}: {
  children: ReactNode;
  tone?: BadgeTone;
  dot?: boolean;
  size?: Olcu;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border font-medium",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        TON_ROZET[tone],
      )}
    >
      {dot && <span aria-hidden className={cx("h-1.5 w-1.5 rounded-full", TON_NOKTA[tone])} />}
      {children}
    </span>
  );
}

export function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-2 text-xs">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={cx(
          "relative h-5 w-9 shrink-0 rounded-full border transition-colors",
          checked ? "border-navy-600 bg-navy-600" : "border-border bg-muted",
        )}
      >
        <span
          aria-hidden
          className={cx(
            "absolute top-0.5 h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-[left]",
            checked ? "left-4.5" : "left-0.5",
          )}
          style={{ left: checked ? 18 : 2, transitionDuration: "var(--duration-fast)" }}
        />
      </button>
      <span>{label}</span>
    </label>
  );
}

export function Toggle({
  pressed,
  onPressedChange,
  label,
  children,
  variant = "outline",
  size = "md",
}: {
  pressed: boolean;
  onPressedChange: (v: boolean) => void;
  label: string;
  children?: ReactNode;
  variant?: "outline" | "ghost";
  size?: Olcu;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      aria-label={label}
      title={label}
      onClick={() => onPressedChange(!pressed)}
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-[var(--radius)] border font-medium transition-colors",
        BUTON_OLCU[size],
        pressed
          ? "border-navy-600 bg-navy-600 text-white"
          : variant === "outline"
            ? "border-border bg-card text-foreground hover:bg-muted"
            : "border-transparent bg-transparent text-foreground hover:bg-muted",
      )}
    >
      {children}
    </button>
  );
}

export function ToggleGroup({
  items,
  value,
  onValueChange,
  label,
  size = "md",
}: {
  items: Array<{ value: string; label: string; icon?: ReactNode }>;
  value: string[];
  onValueChange: (v: string[]) => void;
  label: string;
  /** Yalniz "multiple" kullanilir; imza uyumu icin durur. */
  type?: "multiple" | "single";
  variant?: "outline" | "ghost";
  size?: Olcu;
}) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-2">
      {items.map((it) => {
        const acik = value.includes(it.value);
        return (
          <button
            key={it.value}
            type="button"
            aria-pressed={acik}
            onClick={() =>
              onValueChange(
                acik ? value.filter((v) => v !== it.value) : [...value, it.value],
              )
            }
            className={cx(
              "inline-flex items-center gap-1.5 rounded-full border font-medium transition-colors",
              size === "sm" ? "h-7 px-2.5 text-xs" : "h-9 px-3 text-sm",
              acik
                ? "border-navy-600 bg-navy-600 text-white"
                : "border-border bg-card text-muted-foreground hover:bg-muted",
            )}
          >
            {it.icon}
            {it.label}
          </button>
        );
      })}
    </div>
  );
}

export function Input({
  className,
  ...rest
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cx(
        "h-9 w-full rounded-[var(--radius)] border border-border bg-card px-2.5 text-sm text-foreground",
        "placeholder:text-muted-foreground",
        className,
      )}
      {...rest}
    />
  );
}

/**
 * Sayi girdisi. BOS GIRDI `null` VERIR, 0 DEGIL — paket kurali ve karsilama
 * ekrani buna yaslanir: alan bosken ekrana tasinacak bir sayi yoktur ve
 * cagiran varsayilanina duser. 0 dondurmek "sifir sapma" demek olurdu.
 */
export function NumberInput({
  value,
  onChange,
  min,
  max,
  step,
  unit,
  id,
}: {
  value: number | null;
  onChange: (v: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  id?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <input
        id={id}
        type="number"
        inputMode="numeric"
        value={value ?? ""}
        min={min}
        max={max}
        step={step}
        onChange={(e) => {
          const ham = e.target.value;
          if (ham === "") return onChange(null);
          const n = Number(ham);
          onChange(Number.isFinite(n) ? n : null);
        }}
        className="h-9 w-full rounded-[var(--radius)] border border-border bg-card px-2.5 text-sm text-foreground"
      />
      {unit && <span className="shrink-0 text-xs text-muted-foreground">{unit}</span>}
    </div>
  );
}

/** Etiketli alan sarmalayicisi — etiket denetime `htmlFor` ile baglanir. */
export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-medium">
        {label}
      </label>
      <div id={id}>{children}</div>
      {hint && <span className="type-help text-muted-foreground">{hint}</span>}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Kaplar
   ═══════════════════════════════════════════════════════════════════════ */

export function Card({
  children,
  title,
  subtitle,
  className,
}: {
  children?: ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <div
      className={cx(
        // Dolgu 12 px (p-3): grafik kutucugu akordiyonu bunu `-mx-3` ile asip
        // kenara uzanir, tetikleyici `px-3` ile geri verir.
        "overflow-hidden rounded-[var(--radius)] border border-border bg-card p-3",
        className,
      )}
    >
      {(title || subtitle) && (
        <div className="mb-2 flex flex-col gap-0.5">
          {title && <span className="type-card-title">{title}</span>}
          {subtitle && <span className="type-help text-muted-foreground">{subtitle}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Section({
  title,
  count,
  actions,
  children,
}: {
  title: string;
  count?: number;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          {title}
          {count != null && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
              {formatNumber(count)}
            </span>
          )}
        </h2>
        {actions && <div className="flex items-center gap-1">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

export function KPIStrip({
  children,
  banded,
}: {
  children: ReactNode;
  banded?: boolean;
  /** Paket imzasi uyumu; yerelde izgara zaten oto-sigdirir. */
  min?: string;
}) {
  return (
    <div
      className={cx(
        "grid gap-px overflow-hidden rounded-[var(--radius)] border border-border",
        banded ? "bg-border" : "bg-transparent",
      )}
      style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}
    >
      {children}
    </div>
  );
}

export function KPICard({
  label,
  value,
  note,
  deltaTone,
  onClick,
}: {
  label: string;
  value: ReactNode;
  note?: string;
  deltaTone?: "pos" | "neg";
  onClick?: () => void;
}) {
  const govde = (
    <>
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cx(
          "type-kpi",
          deltaTone === "neg" && "text-danger-600",
          deltaTone === "pos" && "text-success-600",
        )}
      >
        {value}
      </span>
      {note && <span className="type-help text-muted-foreground">{note}</span>}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex flex-col gap-1 bg-card p-3 text-left transition-colors hover:bg-muted"
      >
        {govde}
      </button>
    );
  }
  return <div className="flex flex-col gap-1 bg-card p-3">{govde}</div>;
}

export function Alert({
  tone = "info",
  title,
  actions,
  children,
}: {
  tone?: AlertTone;
  title: string;
  actions?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div
      role="status"
      className={cx(
        "flex flex-wrap items-start justify-between gap-3 rounded-[var(--radius)] border p-3",
        TON_ROZET[tone],
      )}
    >
      <div className="flex min-w-0 flex-col gap-1">
        <span className="type-card-title">{title}</span>
        {children && <span className="type-help">{children}</span>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  compact,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div
      className={cx(
        "flex flex-col items-center justify-center gap-2 text-center",
        compact ? "p-4" : "p-10",
      )}
    >
      {icon && <span className="text-muted-foreground">{icon}</span>}
      <span className="type-card-title">{title}</span>
      {description && (
        <span className="type-help max-w-prose text-muted-foreground">{description}</span>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function Skeleton({ style }: { style?: CSSProperties }) {
  return (
    <div
      aria-hidden
      className="animate-pulse rounded-[var(--radius)] bg-muted"
      style={{ height: 16, width: "100%", ...style }}
    />
  );
}

export function ScrollArea({
  children,
  maxHeight,
}: {
  children: ReactNode;
  /** VERILMEZSE hic kaymaz — alarm penceresi buna yaslanir. */
  maxHeight?: number;
}) {
  return (
    <div className="overflow-y-auto" style={maxHeight != null ? { maxHeight } : undefined}>
      {children}
    </div>
  );
}

export function KeyValue({
  items,
}: {
  items: Array<{ label: string; value: ReactNode; mono?: boolean }>;
}) {
  return (
    <dl className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-4 gap-y-2">
      {items.map((it) => (
        <div key={it.label} className="contents">
          <dt className="type-help text-muted-foreground">{it.label}</dt>
          <dd className={cx("type-help m-0 break-words", it.mono && "type-code")}>
            {it.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Toast altyapisi bu uygulamada kullanilmiyor; saglayici gecis noktasidir. */
export function ToasterProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

/* ═══════════════════════════════════════════════════════════════════════
   Sekmeler
   ═══════════════════════════════════════════════════════════════════════ */

export function Tabs({
  tabs,
  active,
  onChange,
  panelId,
}: {
  tabs: Array<{ id: string; label: string; count?: number }>;
  active: string;
  onChange: (id: string) => void;
  /**
   * Panelin DOM kimligi. Verilirse `aria-controls` basilir; DOM'da OLMAYAN bir
   * kimlik ARIA sozlesmesini bozacagi icin cagiran taraf panelin gercekten
   * basildigindan emin olmali (karsilama ekrani bunu ozellikle isaretler).
   */
  panelId?: string;
}) {
  return (
    <div role="tablist" className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map((t) => {
        const secili = t.id === active;
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={secili}
            aria-controls={panelId}
            onClick={() => onChange(t.id)}
            className={cx(
              "-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              secili
                ? "border-navy-600 text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
            {t.count != null && (
              <span className="rounded-full bg-muted px-1.5 py-0.5 text-[11px]">
                {formatNumber(t.count)}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Akordiyon
   ═══════════════════════════════════════════════════════════════════════

   Radix sozlesmesi KORUNUR, cunku app.css ona yaslanir:
     • icerik `data-state="open|closed"` tasir
     • `--radix-accordion-content-height` olculur ve yazilir
     • KAPANISTA icerik HEMEN sokulmez, `animationend` beklenir
     • ACIKKEN cocuklar basilir, KAPALIYKEN HIC basilmaz — canli-route'un
       basarim notu buna dayanir (kapali kutucuk ornek dizisine dokunmaz). */

interface AkordiyonCtx {
  acik: string[];
  degistir: (value: string) => void;
}
const AkordiyonBaglami = createContext<AkordiyonCtx | null>(null);

interface OgeCtx {
  value: string;
  acik: boolean;
  id?: string;
}
const OgeBaglami = createContext<OgeCtx | null>(null);

export function Accordion({
  children,
  value,
  onValueChange,
  className,
}: {
  children: ReactNode;
  value: string[];
  onValueChange: (v: string[]) => void;
  className?: string;
  /** Yalniz "multiple" kullanilir; imza uyumu icin durur. */
  type?: "multiple" | "single";
}) {
  const degistir = useCallback(
    (v: string) =>
      onValueChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]),
    [value, onValueChange],
  );
  const ctx = useMemo(() => ({ acik: value, degistir }), [value, degistir]);
  return (
    <AkordiyonBaglami.Provider value={ctx}>
      <div className={className}>{children}</div>
    </AkordiyonBaglami.Provider>
  );
}

export function AccordionItem({
  children,
  value,
  id,
  className,
}: {
  children: ReactNode;
  value: string;
  id?: string;
  className?: string;
}) {
  const ctx = useContext(AkordiyonBaglami);
  const acik = ctx?.acik.includes(value) ?? false;
  const oge = useMemo(() => ({ value, acik, id }), [value, acik, id]);
  return (
    <OgeBaglami.Provider value={oge}>
      <div id={id} data-state={acik ? "open" : "closed"} className={cx("border-b border-border", className)}>
        {children}
      </div>
    </OgeBaglami.Provider>
  );
}

export function AccordionTrigger({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const ctx = useContext(AkordiyonBaglami);
  const oge = useContext(OgeBaglami);
  if (!ctx || !oge) return null;
  return (
    <button
      type="button"
      aria-expanded={oge.acik}
      onClick={() => ctx.degistir(oge.value)}
      className={cx(
        "flex w-full items-center justify-between gap-2 py-2 text-left transition-colors hover:bg-muted/60",
        className,
      )}
    >
      {children}
      <ChevronDown
        size={IKON.md}
        aria-hidden
        className="shrink-0 text-muted-foreground transition-transform"
        style={{
          transform: oge.acik ? "rotate(180deg)" : "none",
          transitionDuration: "var(--duration-base)",
          transitionTimingFunction: "var(--ease-standard)",
        }}
      />
    </button>
  );
}

export function AccordionContent({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const oge = useContext(OgeBaglami);
  const acik = oge?.acik ?? false;
  // `basili`: DOM'da duruyor mu. Acikken evet; kapanista animasyon bitene dek
  // EVET kalir (yoksa kapanis hic gorunmez), sonra hayir.
  const [basili, setBasili] = useState(acik);
  const disRef = useRef<HTMLDivElement>(null);
  const icRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (acik) setBasili(true);
  }, [acik]);

  // Yukseklik KAPANMADAN ONCE olculur. Radix de bunu bir layout effect'te
  // yapar; olculen deger yanlis cikarsa kutucuk oradan coker.
  useLayoutEffect(() => {
    if (!basili) return;
    const dis = disRef.current;
    const ic = icRef.current;
    if (!dis || !ic) return;
    dis.style.setProperty("--radix-accordion-content-height", `${ic.scrollHeight}px`);
  });

  if (!basili) return null;

  return (
    <div
      ref={disRef}
      data-state={acik ? "open" : "closed"}
      className={className}
      style={{ overflow: "hidden", height: acik ? undefined : 0 }}
      onAnimationEnd={() => {
        if (!acik) setBasili(false);
      }}
    >
      {/* Ic sarmalayici olcum icindir: dis ogenin yuksekligi animasyonla
          oynadigi icin kendi scrollHeight'i guvenilir degil. */}
      <div ref={icRef} className="pb-3">
        {acik ? children : null}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Popover
   ═══════════════════════════════════════════════════════════════════════ */

interface PopoverCtx {
  open: boolean;
  setOpen: (v: boolean) => void;
}
const PopoverBaglami = createContext<PopoverCtx | null>(null);

export function Popover({
  children,
  open,
  onOpenChange,
}: {
  children: ReactNode;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const ctx = useMemo(() => ({ open, setOpen: onOpenChange }), [open, onOpenChange]);
  return (
    <PopoverBaglami.Provider value={ctx}>
      <span className="relative inline-block">{children}</span>
    </PopoverBaglami.Provider>
  );
}

export function PopoverTrigger({
  children,
  asChild,
}: {
  children: ReactElement<{ onClick?: (e: React.MouseEvent) => void }>;
  asChild?: boolean;
}) {
  const ctx = useContext(PopoverBaglami);
  if (!ctx) return null;
  const tikla = (e: React.MouseEvent) => {
    e.stopPropagation();
    ctx.setOpen(!ctx.open);
  };
  // `asChild`: kendi dugmemizi basmayiz, cocuga davranisi takariz — ic ice
  // buton dogurmak tetikleyiciyi erisilemez yapardi.
  if (asChild) {
    const cocuk = children;
    return (
      <span onClick={tikla} className="contents">
        {cocuk}
      </span>
    );
  }
  return (
    <button type="button" onClick={tikla}>
      {children}
    </button>
  );
}

export function PopoverContent({ children }: { children: ReactNode }) {
  const ctx = useContext(PopoverBaglami);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ctx?.open) return;
    const disariTikla = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) ctx.setOpen(false);
    };
    const kacis = (e: KeyboardEvent) => {
      if (e.key === "Escape") ctx.setOpen(false);
    };
    // Bir kare gecikme: aciliş tiklamasinin kendisi "disari tiklama" sayilmasin.
    const t = window.setTimeout(() => document.addEventListener("mousedown", disariTikla), 0);
    document.addEventListener("keydown", kacis);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("mousedown", disariTikla);
      document.removeEventListener("keydown", kacis);
    };
  }, [ctx]);

  if (!ctx?.open) return null;
  return (
    <div
      ref={ref}
      role="dialog"
      className="absolute right-0 top-full z-[var(--layer-nav)] mt-1 rounded-[var(--radius)] border border-border bg-card p-3 shadow-[var(--shadow-lg)]"
    >
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Kabuk
   ═══════════════════════════════════════════════════════════════════════ */

export function AppShell({
  product,
  items,
  activeId,
  onNavigate,
  subtitle,
  topbarActions,
  children,
}: {
  product: string;
  items: ShellNavItem[];
  activeId: string;
  onNavigate: (id: string) => void;
  subtitle?: string;
  /** Paketin Koyu+Kompakt ikilisi; bu uygulamada KAPALI (kabuk kendi basar). */
  themeControls?: boolean;
  topbarActions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex h-full min-h-0 flex-col bg-background text-foreground">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-border bg-card px-4 py-2">
        <div className="flex min-w-0 flex-col">
          <span className="text-sm font-semibold">{product}</span>
          {subtitle && (
            <span className="type-help truncate text-muted-foreground">{subtitle}</span>
          )}
        </div>
        {topbarActions}
      </header>

      <div className="flex min-h-0 flex-1">
        {/* data-slot: app.css genislik gecisini ve `overflow-x: hidden`i
            buradan yakalar. */}
        <aside
          data-slot="app-shell-nav"
          className="hidden w-60 shrink-0 overflow-y-auto border-r border-border bg-card p-2 kabuk:block"
        >
          <nav className="flex flex-col gap-1">
            {items.map((it) => {
              const secili = it.id === activeId;
              return (
                <button
                  key={it.id}
                  type="button"
                  aria-current={secili ? "page" : undefined}
                  onClick={() => onNavigate(it.id)}
                  className={cx(
                    "flex min-w-0 items-center gap-2 rounded-[var(--radius)] px-3 py-2 text-sm font-medium transition-colors",
                    secili
                      ? "bg-navy-600 text-white"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  {it.icon}
                  <span className="min-w-0 flex-1 truncate text-left">{it.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* PageShell'in `flex-1`i ancak DOGRUDAN flex cocugu olunca is gorur;
            araya sade bir div koymak scroller'i olduruyordu (app.css notu). */}
        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>
      </div>

      {/* Dar ekranda gezinme alt seride iner (ADR-0006, 860px kirilimi). */}
      <nav className="flex shrink-0 items-center justify-around border-t border-border bg-card kabuk:hidden">
        {items.map((it) => {
          const secili = it.id === activeId;
          return (
            <button
              key={it.id}
              type="button"
              aria-current={secili ? "page" : undefined}
              onClick={() => onNavigate(it.id)}
              className={cx(
                "flex flex-1 flex-col items-center gap-0.5 py-1.5 text-[11px] font-medium",
                secili ? "text-navy-600" : "text-muted-foreground",
              )}
              style={{ minHeight: "var(--touch-target)" }}
            >
              {it.icon}
              {it.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

export function PageShell({
  title,
  description,
  actions,
  children,
  fullWidth,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <div data-slot="page-shell" className="flex h-full min-h-0 flex-1 flex-col">
      {/* ASIL KAYDIRAN OGE. app.css'teki `.mzi-pencere-payi` alt dolguyu tam
          buraya verir; disarida vermek sayfanin altinda olu serit birakiyordu. */}
      <div data-slot="page-shell-content" className="min-h-0 flex-1 overflow-y-auto p-[var(--space-6)]">
        <div className={cx("mx-auto flex w-full flex-col gap-4", !fullWidth && "max-w-5xl")}>
          <header className="flex flex-wrap items-start justify-between gap-2">
            <div className="flex min-w-0 flex-col gap-0.5">
              <h1 className="text-lg font-semibold">{title}</h1>
              {description && (
                <span className="type-help text-muted-foreground">{description}</span>
              )}
            </div>
            {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
          </header>
          {children}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Tablolar
   ═══════════════════════════════════════════════════════════════════════ */

export interface DataTableColumn<T> {
  key: string;
  header: string;
  /** Ham deger: arama, siralama ve disa aktarma bunu okur. */
  accessor?: (row: T) => string | number | null | undefined;
  /** Ekran gosterimi; verilmezse `accessor` basilir. */
  render?: (row: T) => ReactNode;
  type?: "text" | "code" | "number" | "badge" | "actions";
  mono?: boolean;
  sortable?: boolean;
  filterable?: boolean;
  filterOptions?: string[];
  hint?: string;
  defaultHidden?: boolean;
  exportable?: boolean;
  badge?: (row: T) => { tone: BadgeTone; label: string };
  actions?: (row: T) => Array<{ label: string; icon?: ReactNode; onSelect: () => void }>;
}

function hucreMetni<T>(col: DataTableColumn<T>, row: T): string {
  if (col.badge) return col.badge(row).label;
  const v = col.accessor?.(row);
  if (v == null) return "—";
  return typeof v === "number" ? formatNumber(v) : String(v);
}

function hucreIcerik<T>(col: DataTableColumn<T>, row: T): ReactNode {
  if (col.type === "actions" && col.actions) {
    return (
      <span className="flex items-center gap-1">
        {col.actions(row).map((a) => (
          <IconButton key={a.label} label={a.label} size="sm" variant="ghost" onClick={a.onSelect}>
            {a.icon}
          </IconButton>
        ))}
      </span>
    );
  }
  if (col.badge) {
    const b = col.badge(row);
    return (
      <Badge tone={b.tone} size="sm">
        {b.label}
      </Badge>
    );
  }
  if (col.render) return col.render(row);
  return hucreMetni(col, row);
}

/** CSV kacisi: tirnak ve ayirac tasiyan alan bozulmadan gecmeli. */
function csvAlan(s: string): string {
  return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function DataGrid<T>({
  columns,
  rows,
  getRowId,
  searchable,
  searchPlaceholder,
  pageSize = 25,
  stickyHeader,
  columnToggle,
  exportable,
  exportFilename = "veri.csv",
  refreshing,
  emptyState,
  rowTone,
  selectable,
  bulkActions,
}: {
  columns: Array<DataTableColumn<T>>;
  rows: T[];
  getRowId: (row: T) => string;
  searchable?: boolean;
  searchPlaceholder?: string;
  pageSize?: number;
  stickyHeader?: boolean;
  columnToggle?: boolean;
  exportable?: boolean;
  exportFilename?: string;
  /** `loading` DEGIL: itmeli akista her zaman veri vardir (ADR-0083). */
  refreshing?: boolean;
  emptyState?: ReactNode;
  rowTone?: (row: T) => "default" | "muted";
  selectable?: boolean;
  bulkActions?: (secili: T[]) => ReactNode;
}) {
  const [gizli, setGizli] = useState<ReadonlySet<string>>(
    () => new Set(columns.filter((c) => c.defaultHidden).map((c) => c.key)),
  );
  const [ara, setAra] = useState("");
  const [suzgec, setSuzgec] = useState<Record<string, string>>({});
  const [sira, setSira] = useState<{ key: string; yon: 1 | -1 } | null>(null);
  const [sayfa, setSayfa] = useState(0);
  const [secili, setSecili] = useState<ReadonlySet<string>>(() => new Set());
  const [kolonMenu, setKolonMenu] = useState(false);

  const gorunurKolonlar = columns.filter((c) => !gizli.has(c.key));

  const suzulmus = useMemo(() => {
    let out = rows;
    const q = ara.trim().toLocaleLowerCase("tr");
    if (q) {
      out = out.filter((r) =>
        columns.some((c) => hucreMetni(c, r).toLocaleLowerCase("tr").includes(q)),
      );
    }
    for (const [key, deger] of Object.entries(suzgec)) {
      if (!deger) continue;
      const col = columns.find((c) => c.key === key);
      if (!col) continue;
      out = out.filter((r) => hucreMetni(col, r) === deger);
    }
    if (sira) {
      const col = columns.find((c) => c.key === sira.key);
      if (col) {
        out = [...out].sort((a, b) => {
          const av = col.accessor?.(a) ?? "";
          const bv = col.accessor?.(b) ?? "";
          if (typeof av === "number" && typeof bv === "number") return (av - bv) * sira.yon;
          return String(av).localeCompare(String(bv), "tr") * sira.yon;
        });
      }
    }
    return out;
  }, [rows, columns, ara, suzgec, sira]);

  const sayfaSayisi = Math.max(1, Math.ceil(suzulmus.length / pageSize));
  const aktifSayfa = Math.min(sayfa, sayfaSayisi - 1);
  const dilim = suzulmus.slice(aktifSayfa * pageSize, aktifSayfa * pageSize + pageSize);

  const disaAktar = () => {
    const kolonlar = gorunurKolonlar.filter((c) => c.exportable !== false && c.type !== "actions");
    const satirlar = [
      kolonlar.map((c) => csvAlan(c.header)).join(";"),
      ...suzulmus.map((r) => kolonlar.map((c) => csvAlan(hucreMetni(c, r))).join(";")),
    ];
    // BOM: Excel'in UTF-8'i tanimasi icin sart, yoksa Turkce harfler bozulur.
    const blob = new Blob(["﻿" + satirlar.join("\r\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = exportFilename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const seciliSatirlar = rows.filter((r) => secili.has(getRowId(r)));

  return (
    <div className="flex flex-col gap-3">
      {/* Arac seridi */}
      <div className="flex flex-wrap items-center gap-2">
        {searchable && (
          <label className="relative flex min-w-0 flex-1 items-center">
            <Search
              size={IKON.sm}
              aria-hidden
              className="pointer-events-none absolute left-2 text-muted-foreground"
            />
            <input
              value={ara}
              onChange={(e) => {
                setAra(e.target.value);
                setSayfa(0);
              }}
              placeholder={searchPlaceholder ?? "Ara…"}
              aria-label={searchPlaceholder ?? "Ara"}
              className="h-9 w-full min-w-40 rounded-[var(--radius)] border border-border bg-card pl-8 pr-2.5 text-sm"
            />
          </label>
        )}

        {columns
          .filter((c) => c.filterable && c.filterOptions?.length)
          .map((c) => (
            <select
              key={c.key}
              aria-label={`${c.header} süzgeci`}
              value={suzgec[c.key] ?? ""}
              onChange={(e) => {
                setSuzgec((p) => ({ ...p, [c.key]: e.target.value }));
                setSayfa(0);
              }}
              className="h-9 rounded-[var(--radius)] border border-border bg-card px-2 text-sm"
            >
              <option value="">{c.header}: tümü</option>
              {c.filterOptions?.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          ))}

        {refreshing && (
          <span className="type-help flex items-center gap-1.5 text-muted-foreground">
            <span aria-hidden className="h-1.5 w-1.5 animate-pulse rounded-full bg-success-600" />
            canlı
          </span>
        )}

        <span className="type-help ml-auto text-muted-foreground">
          {formatNumber(suzulmus.length)} kayıt
        </span>

        {columnToggle && (
          <span className="relative">
            <Button
              size="sm"
              variant="secondary"
              iconLeft={<Settings2 size={IKON.sm} />}
              onClick={() => setKolonMenu((v) => !v)}
            >
              Kolonlar
            </Button>
            {kolonMenu && (
              <div className="absolute right-0 top-full z-[var(--layer-nav)] mt-1 flex w-56 flex-col gap-1 rounded-[var(--radius)] border border-border bg-card p-2 shadow-[var(--shadow-lg)]">
                {columns.map((c) => (
                  <label key={c.key} className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={!gizli.has(c.key)}
                      onChange={() =>
                        setGizli((p) => {
                          const n = new Set(p);
                          if (!n.delete(c.key)) n.add(c.key);
                          return n;
                        })
                      }
                    />
                    {c.header}
                  </label>
                ))}
              </div>
            )}
          </span>
        )}

        {exportable && (
          <Button
            size="sm"
            variant="secondary"
            iconLeft={<Download size={IKON.sm} />}
            onClick={disaAktar}
          >
            Dışa aktar
          </Button>
        )}
      </div>

      {selectable && seciliSatirlar.length > 0 && bulkActions && (
        <div className="flex items-center gap-3 rounded-[var(--radius)] border border-border bg-muted p-2">
          <span className="type-help">{formatNumber(seciliSatirlar.length)} seçili</span>
          {bulkActions(seciliSatirlar)}
        </div>
      )}

      {suzulmus.length === 0 ? (
        <div className="rounded-[var(--radius)] border border-border bg-card">{emptyState}</div>
      ) : (
        <div className="overflow-x-auto rounded-[var(--radius)] border border-border bg-card">
          <table className="w-full border-collapse text-sm">
            <thead className={cx(stickyHeader && "sticky top-0 z-10")}>
              <tr className="bg-muted">
                {selectable && (
                  <th className="w-9 px-2 py-2">
                    <input
                      type="checkbox"
                      aria-label="Tümünü seç"
                      checked={dilim.length > 0 && dilim.every((r) => secili.has(getRowId(r)))}
                      onChange={(e) =>
                        setSecili(() =>
                          e.target.checked ? new Set(dilim.map(getRowId)) : new Set(),
                        )
                      }
                    />
                  </th>
                )}
                {gorunurKolonlar.map((c) => (
                  <th
                    key={c.key}
                    title={c.hint}
                    className={cx(
                      "whitespace-nowrap px-3 py-2 text-left text-xs font-semibold text-muted-foreground",
                      c.type === "number" && "text-right",
                    )}
                  >
                    {c.sortable ? (
                      <button
                        type="button"
                        onClick={() =>
                          setSira((p) =>
                            p?.key === c.key
                              ? { key: c.key, yon: p.yon === 1 ? -1 : 1 }
                              : { key: c.key, yon: 1 },
                          )
                        }
                        className="inline-flex items-center gap-1 hover:text-foreground"
                      >
                        {c.header}
                        <span aria-hidden>
                          {sira?.key === c.key ? (sira.yon === 1 ? "▲" : "▼") : "↕"}
                        </span>
                      </button>
                    ) : (
                      c.header
                    )}
                    {c.hint && <span className="sr-only"> — {c.hint}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dilim.map((r) => {
                const id = getRowId(r);
                // Opaklik kalici hiyerarsi kurmaz (ADR-0039): onaylanmis satir
                // soluklastirilmaz, anlamsal ton alir ve OKUNUR kalir.
                const muted = rowTone?.(r) === "muted";
                return (
                  <tr
                    key={id}
                    className={cx("border-t border-border", muted && "bg-muted/40")}
                  >
                    {selectable && (
                      <td className="px-2 py-2">
                        <input
                          type="checkbox"
                          aria-label="Satırı seç"
                          checked={secili.has(id)}
                          onChange={() =>
                            setSecili((p) => {
                              const n = new Set(p);
                              if (!n.delete(id)) n.add(id);
                              return n;
                            })
                          }
                        />
                      </td>
                    )}
                    {gorunurKolonlar.map((c) => (
                      <td
                        key={c.key}
                        className={cx(
                          "px-3 py-2 align-middle",
                          c.type === "number" && "text-right tabular-nums",
                          (c.mono || c.type === "code") && "type-code",
                          muted && "text-muted-foreground",
                        )}
                      >
                        {hucreIcerik(c, r)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {sayfaSayisi > 1 && (
        <div className="flex items-center justify-between gap-2">
          <Button
            size="sm"
            variant="secondary"
            disabledReason={aktifSayfa === 0 ? "İlk sayfadasınız" : undefined}
            onClick={() => setSayfa((p) => Math.max(0, p - 1))}
          >
            Önceki
          </Button>
          <span className="type-help text-muted-foreground">
            {aktifSayfa + 1} / {sayfaSayisi}
          </span>
          <Button
            size="sm"
            variant="secondary"
            disabledReason={aktifSayfa >= sayfaSayisi - 1 ? "Son sayfadasınız" : undefined}
            onClick={() => setSayfa((p) => Math.min(sayfaSayisi - 1, p + 1))}
          >
            Sonraki
          </Button>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   DataTable — DataGrid'in genis kardesi
   ═══════════════════════════════════════════════════════════════════════

   YAPISI DataTableDesign devrinden gelir (github.com/AbstractJosh/
   DataTableDesign): baslik istatistikleri, arama, bolmeli suzgec, kolon
   suruklemesi, satir detay panosu, numarali sayfalayici. BICIMI gelmez —
   devir paketinin Modernist dili (Archivo, 0 yaricap, 2px kural, lacivert
   slab baslik) denendi ve GERI ALINDI: tablo uygulamanin geri kalaninin
   yaninda yabanci duruyordu. Bugun buradaki her kutu uygulamanin KENDI
   ilkellerinden cizilir — Button, IconButton, Badge, EmptyState ve
   DataGrid'in Tailwind siniflarinin AYNISI.

   Devir paketinin kendi kurali da zaten buydu: "tasarim hedef depoda o
   deponun kendi ilkelleriyle YENIDEN kurulur." Tasarimdan alinan sey ekranin
   NE YAPTIGIDIR, nasil gorundugu degil.

   `DataGrid` YERINE GECMEZ, YANINDA DURUR ve ayni `DataTableColumn<T>`
   sozlesmesini okur — ayni kolon dizisi ikisine de verilebilir, hucreleri
   ayni `hucreIcerik` basar. Fark yalnizca CEVREDEDIR: DataGrid'in arac
   seridi + tablo + iki dugmelik sayfalayicisina karsilik burada istatistik
   seridi, bolmeli suzgec, satir detayi ve numarali sayfalayici var.
   Olaylar ekrani DataGrid'de KALDI; gecirmek isteyenin maliyeti tek ad.

   TASARIMDAN BILEREK ALINMAYAN UC SEY (her biri alanin geregi):

   1. SATIR SURUKLEME YOK. Tasarim satirlari da yeniden siralatir; alarm
      kaydi ZAMAN SIRALIDIR, elle siralanmasi anlamsizdir ve tasarimin kendi
      kuralina ("yeniden siralama etkin siralamayi temizler") gore siralamayi
      silerdi. Ilk hucre DURUYOR ama tutamac degil SATIR ACMA sivriucunu
      tasir — tutamacin yeri, onun yerine gecen sey tarafindan dolduruldu.
   2. KAYIT EKLE / SIL / DUZENLE YOK. Alarm uretilir, yazilmaz. Satir
      aksiyonlari cagirandan gelir (Alarmlar'da onay / onayi geri al).
   3. SABIT KOLON GENISLIGI YOK. Tasarim `table-layout: fixed`tir; buradaki
      tablolar icerige gore olcer (DataGrid de oyle) — 10 kolon boylece
      pencereye sigar, yatay kaydirma ancak gercekten gerekince cikar.  */

export interface DataTableSegment {
  id: string;
  label: string;
  count?: number;
}

/** Detay panosunun tek gozu. `wide` olan satirin tamamini kaplar (not). */
export interface DataTablePane<T> {
  label: string;
  value: (row: T) => ReactNode;
  wide?: boolean;
}

/**
 * Satir detayi. Yuksekligini KENDI olcer ve akordiyonun kalibini izler
 * (app.css'teki `mzi-akordiyon`): sabit bir hedef yukseklik surenin cogunu
 * gorunenin otesinde gecirir, egri gozun disinda biter ve hareket "sicrama"
 * gibi okunur.
 *
 * Olcum `useLayoutEffect`tedir — BOYAMADAN once kosar, sinifi ikinci ama yine
 * de boyanmamis bir gecise birakir, yani ilk kare dogru yukseklikle baslar.
 *
 * KAPANIS ANIDIR ve tasarim da boyle der ("collapse is instant — the row
 * unmounts"). Bu, `animationend` beklemeyi ve azaltilmis harekette o olayin
 * HIC gelmemesi tuzagini bastan siler.
 */
function DtDetay({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [acilan, setAcilan] = useState(false);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--dt-detay-h", `${el.scrollHeight}px`);
    setAcilan(true);
  }, []);
  return (
    <div ref={ref} className="dt-detay" data-state={acilan ? "acilan" : undefined}>
      {children}
    </div>
  );
}

/** Sayfalayicinin numara penceresi: bas, son, aktif ve iki komsusu. */
function dtSayfaNumaralari(aktif: number, toplam: number): Array<number | "bosluk"> {
  const out: Array<number | "bosluk"> = [];
  let onceki = -1;
  for (let i = 0; i < toplam; i++) {
    if (i !== 0 && i !== toplam - 1 && Math.abs(i - aktif) > 1) continue;
    if (onceki >= 0 && i - onceki > 1) out.push("bosluk");
    out.push(i);
    onceki = i;
  }
  return out;
}

export function DataTable<T>({
  columns,
  rows,
  getRowId,
  total,
  kicker,
  title,
  segments,
  activeSegment,
  onSegmentChange,
  searchable = true,
  searchPlaceholder,
  pageSize = 25,
  columnToggle,
  exportable,
  exportFilename = "veri.csv",
  detail,
  detailLabel = "Ayrıntı",
  selectable,
  bulkActions,
  rowTone,
  refreshing,
  stickyHeader,
  emptyIcon,
  emptyTitle,
  emptyBody,
}: {
  columns: Array<DataTableColumn<T>>;
  rows: T[];
  getRowId: (row: T) => string;
  /**
   * "Toplam" istatistigi. Verilmezse `rows.length` — cagiran bolmeyle SUZUP
   * gonderiyorsa suzulmemis toplami buradan gecirmelidir.
   */
  total?: number;
  kicker?: string;
  /** Kabuk zaten sayfa basligi basiyorsa BOS BIRAKILIR. */
  title?: string;
  segments?: DataTableSegment[];
  activeSegment?: string;
  onSegmentChange?: (id: string) => void;
  searchable?: boolean;
  searchPlaceholder?: string;
  pageSize?: number;
  columnToggle?: boolean;
  exportable?: boolean;
  exportFilename?: string;
  /** Verilirse satirlar acilir; panolarin dizisi satirdan uretilir. */
  detail?: (row: T) => Array<DataTablePane<T>>;
  detailLabel?: string;
  selectable?: boolean;
  bulkActions?: (secili: T[]) => ReactNode;
  rowTone?: (row: T) => "default" | "muted";
  /** `loading` DEGIL: itmeli akista her zaman veri vardir (ADR-0083). */
  refreshing?: boolean;
  stickyHeader?: boolean;
  emptyIcon?: ReactNode;
  emptyTitle?: string;
  emptyBody?: string;
}) {
  const [gizli, setGizli] = useState<ReadonlySet<string>>(
    () => new Set(columns.filter((c) => c.defaultHidden).map((c) => c.key)),
  );
  // `null` = dogal duzen. Kolon dizisi her cizimde yeniden kuruldugu icin
  // duzen ANAHTAR listesi olarak saklanir, kolon nesnesi olarak degil.
  const [duzen, setDuzen] = useState<string[] | null>(null);
  const [ara, setAra] = useState("");
  const [sira, setSira] = useState<{ key: string; yon: 1 | -1 } | null>(null);
  const [sayfa, setSayfa] = useState(0);
  const [secili, setSecili] = useState<ReadonlySet<string>>(() => new Set());
  const [acik, setAcik] = useState<ReadonlySet<string>>(() => new Set());
  const [kolonMenu, setKolonMenu] = useState(false);
  const [duyuru, setDuyuru] = useState("");
  const [birakma, setBirakma] = useState<{ key: string; taraf: "once" | "sonra" } | null>(null);
  // Suruklenen kolon STATE DEGILDIR: her `dragover` icin yeniden cizmemek
  // gerekir (devir paketinin `dragCol` notu).
  const surukKolon = useRef<string | null>(null);

  const siraliKolonlar = useMemo(() => {
    const harita = new Map(columns.map((c) => [c.key, c]));
    const out: Array<DataTableColumn<T>> = [];
    if (duzen) {
      for (const k of duzen) {
        const c = harita.get(k);
        if (c) {
          out.push(c);
          harita.delete(k);
        }
      }
    }
    // Duzende olmayan (yeni eklenmis) kolonlar dogal yerlerinde kuyruga biner.
    for (const c of columns) if (harita.has(c.key)) out.push(c);
    return out;
  }, [columns, duzen]);

  const gorunur = siraliKolonlar.filter((c) => !gizli.has(c.key));
  // Sivriuc, secim ve ISLEM kolonlari SABITTIR: ne siralanir ne suruklenir.
  const veriKolonlari = gorunur.filter((c) => c.type !== "actions");
  const islemKolonu = gorunur.find((c) => c.type === "actions");

  // Cizim sirasi SABITTIR (tasarim): suz → sirala → sayfala → dilimle.
  const suzulmus = useMemo(() => {
    let out = rows;
    const q = ara.trim().toLocaleLowerCase("tr");
    if (q) {
      out = out.filter((r) =>
        columns.some((c) => hucreMetni(c, r).toLocaleLowerCase("tr").includes(q)),
      );
    }
    if (sira) {
      const col = columns.find((c) => c.key === sira.key);
      if (col) {
        out = [...out].sort((a, b) => {
          const av = col.accessor?.(a) ?? "";
          const bv = col.accessor?.(b) ?? "";
          if (typeof av === "number" && typeof bv === "number") return (av - bv) * sira.yon;
          return String(av).localeCompare(String(bv), "tr") * sira.yon;
        });
      }
    }
    return out;
  }, [rows, columns, ara, sira]);

  const sayfaSayisi = Math.max(1, Math.ceil(suzulmus.length / pageSize));
  const aktifSayfa = Math.min(sayfa, sayfaSayisi - 1);
  const ilk = aktifSayfa * pageSize;
  const dilim = suzulmus.slice(ilk, ilk + pageSize);
  const seciliSatirlar = rows.filter((r) => secili.has(getRowId(r)));
  const sayfaHepsi = dilim.length > 0 && dilim.every((r) => secili.has(getRowId(r)));

  const sayfaya = (n: number) => {
    const hedef = Math.max(0, Math.min(sayfaSayisi - 1, n));
    setSayfa(hedef);
    setDuyuru(`Sayfa ${hedef + 1} / ${sayfaSayisi}`);
  };

  const siralamaCevir = (key: string) => {
    // artan → azalan → siralamasiz (tasarim: ucuncu tiklama temizler).
    setSira((p) => (p?.key !== key ? { key, yon: 1 } : p.yon === 1 ? { key, yon: -1 } : null));
    setSayfa(0);
  };

  const kolonuTasi = (key: string, hedefKey: string, taraf: "once" | "sonra") => {
    if (key === hedefKey) return;
    const yeni = siraliKolonlar.map((c) => c.key);
    const from = yeni.indexOf(key);
    if (from < 0) return;
    yeni.splice(from, 1);
    let to = yeni.indexOf(hedefKey);
    if (to < 0) return;
    if (taraf === "sonra") to += 1;
    yeni.splice(to, 0, key);
    setDuzen(yeni);
    const ad = columns.find((c) => c.key === key)?.header ?? key;
    const kalan = veriKolonlari.filter((c) => c.key !== key);
    const yer = kalan.findIndex((c) => c.key === hedefKey) + (taraf === "sonra" ? 2 : 1);
    setDuyuru(`${ad} kolonu ${yer}. sıraya taşındı`);
  };

  const klavyeyleTasi = (key: string, yon: -1 | 1) => {
    const anahtarlar = veriKolonlari.map((c) => c.key);
    const i = anahtarlar.indexOf(key);
    const j = i + yon;
    if (i < 0 || j < 0 || j >= anahtarlar.length) return;
    kolonuTasi(key, anahtarlar[j], yon === 1 ? "sonra" : "once");
  };

  const duzeniSifirla = () => {
    setDuzen(null);
    setSira(null);
    setDuyuru("Kolon düzeni ve sıralama sıfırlandı");
  };

  const disaAktar = () => {
    const kolonlar = gorunur.filter((c) => c.exportable !== false && c.type !== "actions");
    const satirlar = [
      kolonlar.map((c) => csvAlan(c.header)).join(";"),
      ...suzulmus.map((r) => kolonlar.map((c) => csvAlan(hucreMetni(c, r))).join(";")),
    ];
    // BOM: Excel'in UTF-8'i tanimasi icin sart, yoksa Turkce harfler bozulur.
    const blob = new Blob(["﻿" + satirlar.join("\r\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = exportFilename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const sutunSayisi = 1 + (selectable ? 1 : 0) + veriKolonlari.length + (islemKolonu ? 1 : 0);

  // `type-kpi` DEGIL: o 24px'tir ve kabugun 18px'lik sayfa basligini gecerek
  // hiyerarsiyi ters cevirir. Bunlar sayfanin KPI'lari degil, tablonun yan
  // okumasidir; basligin bir kademe altinda dururlar.
  const istatistik = (etiket: string, deger: number) => (
    <div>
      <dt className="type-help text-muted-foreground">{etiket}</dt>
      <dd className="m-0 text-base font-semibold tabular-nums">{formatNumber(deger)}</dd>
    </div>
  );

  return (
    <div className="flex flex-col gap-3">
      {/* Yeniden siralama ve sayfa degisimi GORULMEYEN degisikliklerdir;
          ekran okuyucuya soylenmesi tasarimin erisilebilirlik sartidir. */}
      <p className="sr-only" role="status" aria-live="polite">
        {duyuru}
      </p>

      {/* Baslik seridi — kunye + (istege bagli) baslik + uc sayim. */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-3">
        <div className="flex min-w-0 flex-col gap-0.5">
          {kicker && <span className="type-help text-muted-foreground">{kicker}</span>}
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
        </div>
        <dl className="m-0 flex flex-wrap gap-6">
          {istatistik("Toplam", total ?? rows.length)}
          {istatistik("Eşleşen", suzulmus.length)}
          {istatistik("Seçili", seciliSatirlar.length)}
        </dl>
      </div>

      {/* Arac seridi — DataGrid'inkiyle ayni olcu ve ayni siniflar. */}
      <div className="flex flex-wrap items-center gap-2">
        {searchable && (
          <label className="relative flex min-w-0 flex-1 items-center">
            <Search
              size={IKON.sm}
              aria-hidden
              className="pointer-events-none absolute left-2 text-muted-foreground"
            />
            <input
              value={ara}
              onChange={(e) => {
                setAra(e.target.value);
                setSayfa(0);
              }}
              placeholder={searchPlaceholder ?? "Ara…"}
              aria-label={searchPlaceholder ?? "Ara"}
              className="h-9 w-full min-w-40 rounded-[var(--radius)] border border-border bg-card pl-8 pr-2.5 text-sm"
            />
          </label>
        )}

        {/* Bolmeli suzgec. Bicimi paketin `ToggleGroup`unun aynisidir (yuvarlak
            hap, secili olan lacivert dolgulu); sayim cipi `Tabs`inkidir. Tek
            secimli oldugu icin ToggleGroup'un kendisi KULLANILAMAZ — o coklu
            secim tasir ve `aria-pressed` yerine radyo anlambilimi gerekir. */}
        {segments && segments.length > 0 && (
          <div role="group" aria-label="Görünüm" className="flex flex-wrap gap-1.5">
            {segments.map((s) => {
              const on = s.id === activeSegment;
              return (
                <button
                  key={s.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => {
                    onSegmentChange?.(s.id);
                    setSayfa(0);
                  }}
                  className={cx(
                    "inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-xs font-medium transition-colors",
                    on
                      ? "border-navy-600 bg-navy-600 text-white"
                      : "border-border bg-card text-muted-foreground hover:bg-muted",
                  )}
                >
                  {s.label}
                  {s.count != null && (
                    <span
                      className={cx(
                        "rounded-full px-1.5 py-0.5 text-[11px]",
                        on ? "bg-white/20" : "bg-muted",
                      )}
                    >
                      {formatNumber(s.count)}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {refreshing && (
          <span className="type-help flex items-center gap-1.5 text-muted-foreground">
            <span aria-hidden className="h-1.5 w-1.5 animate-pulse rounded-full bg-success-600" />
            canlı
          </span>
        )}

        <span className="ml-auto flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            iconLeft={<RotateCcw size={IKON.sm} />}
            disabledReason={
              duzen === null && sira === null ? "Kolon düzeni zaten varsayılan" : undefined
            }
            onClick={duzeniSifirla}
          >
            Düzeni sıfırla
          </Button>

          {columnToggle && (
            <span className="relative">
              <Button
                size="sm"
                variant="secondary"
                aria-expanded={kolonMenu}
                iconLeft={<Settings2 size={IKON.sm} />}
                onClick={() => setKolonMenu((v) => !v)}
              >
                Kolonlar
              </Button>
              {kolonMenu && (
                <div className="absolute right-0 top-full z-[var(--layer-nav)] mt-1 flex w-56 flex-col gap-1 rounded-[var(--radius)] border border-border bg-card p-2 shadow-[var(--shadow-lg)]">
                  {siraliKolonlar
                    .filter((c) => c.type !== "actions")
                    .map((c) => (
                      <label key={c.key} className="flex items-center gap-2 text-xs">
                        <input
                          type="checkbox"
                          checked={!gizli.has(c.key)}
                          onChange={() =>
                            setGizli((p) => {
                              const n = new Set(p);
                              if (!n.delete(c.key)) n.add(c.key);
                              return n;
                            })
                          }
                        />
                        {c.header}
                      </label>
                    ))}
                </div>
              )}
            </span>
          )}

          {exportable && (
            <Button
              size="sm"
              variant="secondary"
              iconLeft={<Download size={IKON.sm} />}
              onClick={disaAktar}
            >
              Dışa aktar
            </Button>
          )}
        </span>
      </div>

      {selectable && seciliSatirlar.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-[var(--radius)] border border-border bg-muted p-2">
          <span className="type-help">{formatNumber(seciliSatirlar.length)} seçili</span>
          {bulkActions?.(seciliSatirlar)}
          <Button size="sm" variant="ghost" onClick={() => setSecili(new Set())}>
            Temizle
          </Button>
        </div>
      )}

      {suzulmus.length === 0 ? (
        <div className="rounded-[var(--radius)] border border-border bg-card">
          <EmptyState
            icon={emptyIcon}
            title={emptyTitle ?? "Eşleşen kayıt yok"}
            description={emptyBody}
          />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-[var(--radius)] border border-border bg-card">
            <table className="w-full border-collapse text-sm">
              <thead className={cx(stickyHeader && "sticky top-0 z-10")}>
                <tr className="bg-muted">
                  <th className="w-9 px-2 py-2">
                    <span className="sr-only">{detailLabel}</span>
                  </th>
                  {selectable && (
                    <th className="w-9 px-2 py-2">
                      <input
                        type="checkbox"
                        aria-label="Sayfadaki tümünü seç"
                        checked={sayfaHepsi}
                        onChange={() =>
                          setSecili((p) => {
                            const n = new Set(p);
                            for (const r of dilim) {
                              if (sayfaHepsi) n.delete(getRowId(r));
                              else n.add(getRowId(r));
                            }
                            return n;
                          })
                        }
                      />
                    </th>
                  )}
                  {veriKolonlari.map((c) => (
                    <th
                      key={c.key}
                      title={c.hint}
                      className={cx(
                        "group whitespace-nowrap px-3 py-2 text-left text-xs font-semibold text-muted-foreground",
                        c.type === "number" && "text-right",
                        surukKolon.current === c.key && "opacity-50",
                        // Birakma isareti: 2px lacivert ic golge. `border` DEGIL
                        // — border-collapse altinda kolon kenarligi komsunun
                        // yerini oynatir, ic golge yerlesime hic dokunmaz.
                        birakma?.key === c.key &&
                          (birakma.taraf === "once"
                            ? "shadow-[inset_2px_0_0_var(--color-navy-600)]"
                            : "shadow-[inset_-2px_0_0_var(--color-navy-600)]"),
                      )}
                      onDragOver={(e) => {
                        if (!surukKolon.current) return;
                        e.preventDefault();
                        e.dataTransfer.dropEffect = "move";
                        const k = e.currentTarget.getBoundingClientRect();
                        setBirakma({
                          key: c.key,
                          taraf: e.clientX < k.left + k.width / 2 ? "once" : "sonra",
                        });
                      }}
                      onDragLeave={() => setBirakma((p) => (p?.key === c.key ? null : p))}
                      onDrop={(e) => {
                        e.preventDefault();
                        const kaynak = surukKolon.current;
                        const taraf = birakma?.taraf ?? "once";
                        surukKolon.current = null;
                        setBirakma(null);
                        if (kaynak) kolonuTasi(kaynak, c.key, taraf);
                      }}
                    >
                      <span
                        className={cx(
                          "flex select-none items-center gap-1.5",
                          c.type === "number" && "justify-end",
                        )}
                      >
                        {/* Tutamac U+283F Braille glifi, ikon DEGIL. Suruklenebilir
                            olan YALNIZ odur; prototipte tum <th> suruklenirdi ve o
                            zaman siralama tiklamasi kazayla surukleme baslatiyordu.
                            <button> olmasi klavye yolunu acar — prototipte yeniden
                            siralamanin klavye karsiligi HIC YOKTU. */}
                        <button
                          type="button"
                          draggable
                          aria-label={`${c.header} kolonunu taşı`}
                          title={`${c.header} kolonunu taşı — Alt + ok tuşları`}
                          // Uygulamanin baslik satiri sade: her kolonun onunde
                          // duran kalici bir glif etiketle yarisirdi. Tutamac
                          // BASLIGA GELINCE cikar; klavyeyle gelen icin
                          // `focus-visible` ayni isi yapar, yani ozellik fare
                          // disinda da bulunabilir kalir.
                          className={cx(
                            "cursor-grab leading-none opacity-0 transition-opacity",
                            "hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100",
                            "active:cursor-grabbing",
                            surukKolon.current === c.key && "opacity-100",
                          )}
                          onDragStart={(e) => {
                            surukKolon.current = c.key;
                            e.dataTransfer.effectAllowed = "move";
                            // Firefox suruklemeyi ancak veri yazilirsa baslatir.
                            e.dataTransfer.setData("text/plain", c.key);
                          }}
                          onDragEnd={() => {
                            surukKolon.current = null;
                            setBirakma(null);
                          }}
                          onKeyDown={(e) => {
                            if (!e.altKey) return;
                            if (e.key === "ArrowLeft") {
                              e.preventDefault();
                              klavyeyleTasi(c.key, -1);
                            } else if (e.key === "ArrowRight") {
                              e.preventDefault();
                              klavyeyleTasi(c.key, 1);
                            }
                          }}
                        >
                          <span aria-hidden>⠿</span>
                        </button>
                        {c.sortable ? (
                          <button
                            type="button"
                            onClick={() => siralamaCevir(c.key)}
                            className="inline-flex items-center gap-1 hover:text-foreground"
                          >
                            {c.header}
                            <span aria-hidden>
                              {sira?.key === c.key ? (sira.yon === 1 ? "▲" : "▼") : "↕"}
                            </span>
                          </button>
                        ) : (
                          c.header
                        )}
                      </span>
                      {c.hint && <span className="sr-only"> — {c.hint}</span>}
                    </th>
                  ))}
                  {islemKolonu && (
                    <th className="whitespace-nowrap px-3 py-2 text-left text-xs font-semibold text-muted-foreground">
                      {islemKolonu.header}
                    </th>
                  )}
                </tr>
              </thead>

              {/* Her kayit KENDI <tbody>si: detay satiri kardes <tr> olmali. */}
              {dilim.map((r) => {
                const id = getRowId(r);
                const acikMi = acik.has(id);
                const seciliMi = secili.has(id);
                // Opaklik kalici hiyerarsi KURMAZ (ADR-0039): onaylanmis satir
                // soluklastirilmaz, anlamsal ton alir ve OKUNUR kalir.
                const muted = rowTone?.(r) === "muted";
                const panolar = acikMi ? detail?.(r) : undefined;
                return (
                  <tbody key={id}>
                    <tr
                      className={cx(
                        "border-t border-border",
                        muted && "bg-muted/40",
                        // Secim isareti kenarligin YERINE ic golge: satir
                        // kenarligi border-collapse altinda tabloyu tasirip
                        // kalici bir yatay kaydirma cubugu doguruyor.
                        seciliMi && "bg-sky-100/40",
                      )}
                    >
                      <td
                        className={cx(
                          "px-2 py-2 text-center",
                          seciliMi && "shadow-[inset_2px_0_0_var(--color-navy-600)]",
                        )}
                      >
                        {detail && (
                          <IconButton
                            label={detailLabel}
                            size="sm"
                            variant="ghost"
                            aria-expanded={acikMi}
                            className={cx("h-7 w-7", acikMi && "text-navy-600")}
                            onClick={() =>
                              setAcik((p) => {
                                const n = new Set(p);
                                if (!n.delete(id)) n.add(id);
                                return n;
                              })
                            }
                          >
                            <ChevronDown
                              size={IKON.sm}
                              className={cx(
                                "transition-transform duration-[var(--duration-base)] ease-[var(--ease-standard)]",
                                acikMi && "rotate-180",
                              )}
                            />
                          </IconButton>
                        )}
                      </td>
                      {selectable && (
                        <td className="px-2 py-2 text-center">
                          <input
                            type="checkbox"
                            aria-label="Satırı seç"
                            checked={seciliMi}
                            onChange={() =>
                              setSecili((p) => {
                                const n = new Set(p);
                                if (!n.delete(id)) n.add(id);
                                return n;
                              })
                            }
                          />
                        </td>
                      )}
                      {veriKolonlari.map((c) => (
                        <td
                          key={c.key}
                          className={cx(
                            "px-3 py-2 align-middle",
                            c.type === "number" && "text-right tabular-nums",
                            (c.mono || c.type === "code") && "type-code",
                            muted && "text-muted-foreground",
                          )}
                        >
                          {hucreIcerik(c, r)}
                        </td>
                      ))}
                      {islemKolonu && (
                        <td className="px-3 py-2 align-middle">{hucreIcerik(islemKolonu, r)}</td>
                      )}
                    </tr>
                    {panolar && panolar.length > 0 && (
                      <tr className={cx(seciliMi && "bg-sky-100/40")}>
                        <td className="bg-muted/40 p-0" colSpan={sutunSayisi}>
                          <DtDetay>
                            {/* TEK kart, icinde `KeyValue` kaliminda etiket/deger
                                ciftleri. Once `KPIStrip`in kil cizgi izgarasi
                                denendi (`gap-px` + kenarlik renginde zemin) ve
                                BIRAKILDI: goz sayisi sutun sayisini tutmadiginda
                                son siranin artigi bos KALIYOR ve zemin oradan
                                sizarak yanlis boyanmis bir pano gibi okunuyordu.
                                Tasarim bunu her gozu basarak cozer, ama o ancak
                                sutun sayisi SABITKEN yapilabilir; burada izgara
                                `auto-fit`tir ve pencereyle degisir. */}
                            <div className="p-3">
                              <div className="rounded-[var(--radius)] border border-border bg-card p-3">
                                {/* <dl>: `dt`/`dd` ancak tanim listesi icinde
                                    gecerlidir; araya giren `div` HTML5'te
                                    izinlidir ve izgaranin gozu odur. */}
                                <dl
                                  className="m-0 grid gap-x-6 gap-y-3"
                                  style={{
                                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                                  }}
                                >
                                  {panolar.map((p) => (
                                    <div key={p.label} className={cx(p.wide && "col-span-full")}>
                                      <dt className="type-help text-muted-foreground">{p.label}</dt>
                                      <dd className="type-help m-0 mt-0.5 break-words">
                                        {p.value(r)}
                                      </dd>
                                    </div>
                                  ))}
                                </dl>
                              </div>
                            </div>
                          </DtDetay>
                        </td>
                      </tr>
                    )}
                  </tbody>
                );
              })}
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="type-help text-muted-foreground">
              Gösterilen{" "}
              <span className="font-semibold text-foreground">
                {formatNumber(ilk + 1)}–{formatNumber(ilk + dilim.length)}
              </span>{" "}
              / {formatNumber(suzulmus.length)} kayıt
            </span>
            {sayfaSayisi > 1 && (
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="secondary"
                  disabledReason={aktifSayfa === 0 ? "İlk sayfadasınız" : undefined}
                  onClick={() => sayfaya(aktifSayfa - 1)}
                >
                  Önceki
                </Button>
                {dtSayfaNumaralari(aktifSayfa, sayfaSayisi).map((n, k) =>
                  n === "bosluk" ? (
                    <span key={`b${k}`} aria-hidden className="px-1 text-xs text-muted-foreground">
                      …
                    </span>
                  ) : (
                    <button
                      key={n}
                      type="button"
                      aria-current={n === aktifSayfa ? "page" : undefined}
                      aria-label={`Sayfa ${n + 1}`}
                      onClick={() => sayfaya(n)}
                      className={cx(
                        "inline-flex h-8 min-w-8 items-center justify-center rounded-[var(--radius)] border px-2 text-xs font-medium transition-colors",
                        n === aktifSayfa
                          ? "border-navy-600 bg-navy-600 text-white"
                          : "border-border bg-card text-foreground hover:bg-muted",
                      )}
                    >
                      {formatNumber(n + 1)}
                    </button>
                  ),
                )}
                <Button
                  size="sm"
                  variant="secondary"
                  disabledReason={aktifSayfa >= sayfaSayisi - 1 ? "Son sayfadasınız" : undefined}
                  onClick={() => sayfaya(aktifSayfa + 1)}
                >
                  Sonraki
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   CompactList — satir + sag cekmece detayi
   ═══════════════════════════════════════════════════════════════════════ */

export type CompactListColumn<T> = DataTableColumn<T>;

export function CompactList<T>({
  columns,
  rows,
  getRowId,
  rowDetailTitle,
  rowDetail,
}: {
  columns: Array<CompactListColumn<T>>;
  rows: T[];
  getRowId: (row: T) => string;
  rowDetailTitle?: (row: T) => string;
  rowDetail?: (row: T) => ReactNode;
}) {
  const [acikId, setAcikId] = useState<string | null>(null);
  // Cekmece CIKIS animasyonu icin kapanista bir kare daha basili kalir
  // (app.css: `[data-slot=floating-panel][data-state=closed]`).
  const [basili, setBasili] = useState<string | null>(null);

  useEffect(() => {
    if (acikId) setBasili(acikId);
  }, [acikId]);

  const acikSatir = rows.find((r) => getRowId(r) === (acikId ?? basili));

  return (
    <div className="overflow-x-auto rounded-[var(--radius)] border border-border bg-card">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-muted">
            {columns.map((c) => (
              <th
                key={c.key}
                className={cx(
                  "whitespace-nowrap px-3 py-2 text-left text-xs font-semibold text-muted-foreground",
                  c.type === "number" && "text-right",
                )}
              >
                {c.header}
              </th>
            ))}
            {rowDetail && <th className="w-9" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const id = getRowId(r);
            return (
              <tr key={id} className="border-t border-border">
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cx(
                      "px-3 py-2 align-middle",
                      c.type === "number" && "text-right tabular-nums",
                      (c.mono || c.type === "code") && "type-code",
                    )}
                  >
                    {hucreIcerik(c, r)}
                  </td>
                ))}
                {rowDetail && (
                  <td className="px-2 py-2">
                    <IconButton
                      label={`Ayrıntı: ${rowDetailTitle?.(r) ?? id}`}
                      size="sm"
                      variant="ghost"
                      onClick={() => setAcikId(id)}
                    >
                      <ChevronDown size={IKON.sm} className="-rotate-90" />
                    </IconButton>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>

      {rowDetail && acikSatir && basili && (
        <>
          <div
            className="fixed inset-0 z-[var(--layer-nav)] bg-black/30"
            onClick={() => setAcikId(null)}
          />
          <div
            data-slot="floating-panel"
            data-side="right"
            data-state={acikId ? "open" : "closed"}
            onAnimationEnd={() => {
              if (!acikId) setBasili(null);
            }}
            className="fixed right-0 top-0 z-[var(--layer-nav)] flex h-full w-96 max-w-full flex-col gap-3 overflow-y-auto border-l border-border bg-card p-4 shadow-[var(--shadow-lg)]"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="type-card-title">{rowDetailTitle?.(acikSatir)}</span>
              <IconButton label="Kapat" size="sm" variant="ghost" onClick={() => setAcikId(null)}>
                <X size={IKON.sm} />
              </IconButton>
            </div>
            {rowDetail(acikSatir)}
          </div>
        </>
      )}
    </div>
  );
}
