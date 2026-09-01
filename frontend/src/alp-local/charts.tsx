// Yerel @alp/design-system/charts karsiligi — recharts uzerine.
//
// SOZLESME KORUNUR: renk SERININ KIMLIGINE baglanabilsin diye `colors`
// disaridan verilebilir (kosum ekrani bunu yapar; sirayla dagitilan renk bir
// seri gizlendiginde kalanlari yeniden boyardi).
//
// 9. SERI YENI BIR RENK DEGILDIR: palet 8 rengte biter ve sonrasi
// `CHART_OTHER`a katlanir. Modulo ile basa sarmak IKI FARKLI sinyali ayni
// renge boyardi — tek isi cizgileri birbirinden ayirmak olan bir grafikte
// sessiz bir yalan.

import {
  CartesianGrid,
  Line,
  LineChart as RCLineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/** Kategorik palet — 8 ayirt edilebilir renk. */
export const CHART_COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#d97706",
  "#7c3aed",
  "#0891b2",
  "#db2777",
  "#65a30d",
] as const;

/** Paletin disinda kalan her sey. Yeni bir renk DEGIL, "diger"dir. */
export const CHART_OTHER = "#94a3b8";

export interface ChartSeries {
  key: string;
  label: string;
}

export interface ChartReferenceLine {
  value: number;
  label?: string;
  tone?: "crit" | "warn" | "info";
}

const REF_RENK: Record<string, string> = {
  crit: "#dc2626",
  warn: "#d97706",
  info: "#0284c7",
};

export function LineChart({
  data,
  x,
  series,
  colors,
  height = 240,
  yTickFormatter,
  referenceLine,
}: {
  data: Array<Record<string, unknown>>;
  x: string;
  series: ChartSeries[];
  colors?: readonly string[];
  height?: number;
  yTickFormatter?: (v: number) => string;
  /**
   * TEKIL — dizi DEGIL. Ekranlar bu sinirin bilincinde yazildi: alt sinir
   * cizilemedigi icin sayiyla yaziliyor (canli-route ve kosum-route notlari).
   */
  referenceLine?: ChartReferenceLine;
}) {
  return (
    <div style={{ height, width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <RCLineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--mzi-border)" />
          <XAxis
            dataKey={x}
            tick={{ fontSize: 11, fill: "var(--mzi-muted-fg)" }}
            stroke="var(--mzi-border)"
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--mzi-muted-fg)" }}
            stroke="var(--mzi-border)"
            tickFormatter={yTickFormatter}
            width={48}
          />
          <Tooltip
            contentStyle={{
              background: "var(--mzi-card)",
              border: "1px solid var(--mzi-border)",
              borderRadius: "var(--radius)",
              fontSize: 12,
              color: "var(--mzi-fg)",
            }}
            labelStyle={{ color: "var(--mzi-muted-fg)" }}
          />
          {referenceLine && (
            <ReferenceLine
              y={referenceLine.value}
              stroke={REF_RENK[referenceLine.tone ?? "info"]}
              strokeDasharray="4 4"
              label={{
                value: referenceLine.label,
                position: "insideTopRight",
                fontSize: 11,
                fill: REF_RENK[referenceLine.tone ?? "info"],
              }}
            />
          )}
          {series.map((s, i) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={colors?.[i] ?? CHART_COLORS[i] ?? CHART_OTHER}
              strokeWidth={1.75}
              dot={false}
              isAnimationActive={false}
              connectNulls={false}
            />
          ))}
        </RCLineChart>
      </ResponsiveContainer>
    </div>
  );
}
