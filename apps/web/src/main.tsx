import React from "react";
import ReactDOM from "react-dom/client";

import { AppProviders } from "@/app/providers/AppProviders";
import { initConsentAwareAnalytics } from "@/shared/analytics";
import { initCoreWebVitals } from "@/shared/core-web-vitals";
import { initFrontendObservability } from "@/shared/observability/sentry";
import { ErrorBoundary } from "@/shared/ui/ErrorBoundary";
import "@/app/styles/index.css";

initFrontendObservability();
initConsentAwareAnalytics();
initCoreWebVitals();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AppProviders />
    </ErrorBoundary>
  </React.StrictMode>,
);
