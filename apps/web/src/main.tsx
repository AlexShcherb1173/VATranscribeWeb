import React from "react";
import ReactDOM from "react-dom/client";

import { AppProviders } from "@/app/providers/AppProviders";
import { initFrontendObservability } from "@/shared/observability/sentry";
import { ErrorBoundary } from "@/shared/ui/ErrorBoundary";
import "@/app/styles/index.css";

initFrontendObservability();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AppProviders />
    </ErrorBoundary>
  </React.StrictMode>,
);
