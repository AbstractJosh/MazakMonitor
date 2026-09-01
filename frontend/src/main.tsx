import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { ToasterProvider } from "@alp/design-system";

// SIRA YÜK TAŞIR: önce paketin derlenmiş CSS'i (token değerleri + fontlar +
// bileşen stilleri), sonra uygulamanın Tailwind girişi (token köprüsü orada).
// Ters çevrilirse köprü token'ları bulamaz ve marka renkleri sessizce düşer.
import "@alp/design-system/styles.css";
import "./app/app.css";

import { router } from "./app/router";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ToasterProvider>
      <RouterProvider router={router} />
    </ToasterProvider>
  </React.StrictMode>,
);
