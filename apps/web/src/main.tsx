import React from "react";
import ReactDOM from "react-dom/client";

import { AppProviders } from "@/app/providers/AppProviders";
import { ErrorBoundary } from "@/shared/ui/ErrorBoundary";
import "@/app/styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AppProviders />
    </ErrorBoundary>
  </React.StrictMode>,
);
