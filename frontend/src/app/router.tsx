// Rotalar. Seçili tezgah URL'de taşınır (`?tezgah=tesis-a/tezgah-1`) — yenileme
// ve tarayıcı geri tuşu çalışır, kiosk ekranı doğrudan adreslenebilir.

import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { SplashScreen } from "@alp/design-system/screens";
import UygulamaKabugu from "./uygulama-kabugu";
import { URUN_ADI } from "./urun";

const CanliRoute = lazy(() => import("@/features/canli/routes/canli-route"));
const AlarmlarRoute = lazy(() => import("@/features/alarmlar/routes/alarmlar-route"));
const OlaylarRoute = lazy(() => import("@/features/olaylar/routes/olaylar-route"));
const KosumRoute = lazy(() => import("@/features/kosum/routes/kosum-route"));
const KarsilamaRoute = lazy(() => import("@/features/karsilama/routes/karsilama-route"));

/** Tembel rota çözülürken duran açılış ekranı — paketten, çatallanmadan. */
function Yukleniyor() {
  return <SplashScreen product={URUN_ADI} />;
}

function sarmala(el: React.ReactNode) {
  return <Suspense fallback={<Yukleniyor />}>{el}</Suspense>;
}

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
      // Rota HER tezgah için çözülür, nav maddesi ise yalnız CSV kaynaklı
      // tezgahta basılır (bkz. uygulama-kabugu.tsx MENU). Rotayı da gizlemek
      // elle yazılmış bir adresi sessizce karşılamaya atardı; ekran bunun
      // yerine kaydın neden olmadığını SÖYLER.
      { path: "kosum", element: sarmala(<KosumRoute />) },
    ],
  },
  // Varsayılan tezgah YOK: bilinmeyen yol seçime döner.
  { path: "*", element: <Navigate to="/" replace /> },
]);
