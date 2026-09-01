// Yerel @alp/design-system/screens karsiligi.
//
// Tembel rota cozulurken duran acilis ekrani. Router bunu `Suspense`in
// `fallback`i olarak basar, yani cogu gecişte bir kareden kisa gorunur —
// bu yuzden yanip sonen bir ilerleme cubugu YOK: kisa bekleyisde o, olmayan
// bir sorunu varmis gibi gosterirdi.

export function SplashScreen({ product }: { product: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex h-full min-h-0 flex-1 flex-col items-center justify-center gap-3 bg-background p-10 text-foreground"
    >
      <span className="text-base font-semibold">{product}</span>
      <span
        aria-hidden
        className="h-1 w-32 overflow-hidden rounded-full bg-muted"
      >
        <span
          className="block h-full w-1/3 rounded-full bg-navy-600"
          style={{
            animation: "mzi-splash 1.1s var(--ease-standard) infinite",
          }}
        />
      </span>
      <span className="type-help text-muted-foreground">Yükleniyor…</span>

      <style>{`
        @keyframes mzi-splash {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
        @media (prefers-reduced-motion: reduce) {
          [role="status"] span[aria-hidden] > span { animation: none; }
        }
      `}</style>
    </div>
  );
}
