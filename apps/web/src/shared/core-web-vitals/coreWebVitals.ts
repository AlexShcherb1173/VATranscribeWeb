import { env } from "@/shared/config/env";
import { hasConsentFor } from "@/shared/cookies/consent";
import { trackAnalyticsEvent } from "@/shared/analytics";

type WebVitalName = "LCP" | "INP" | "CLS" | "TTFB";

type WebVitalMetric = {
  name: WebVitalName;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
};

function rateMetric(name: WebVitalName, value: number): WebVitalMetric["rating"] {
  if (name === "LCP") {
    return value <= env.coreWebVitalsTargets.lcp ? "good" : value <= 4000 ? "needs-improvement" : "poor";
  }
  if (name === "INP") {
    return value <= env.coreWebVitalsTargets.inp ? "good" : value <= 500 ? "needs-improvement" : "poor";
  }
  if (name === "CLS") {
    return value <= env.coreWebVitalsTargets.cls ? "good" : value <= 0.25 ? "needs-improvement" : "poor";
  }
  return "good";
}

function reportMetric(metric: WebVitalMetric): void {
  if (!hasConsentFor("analytics")) {
    return;
  }

  if (env.coreWebVitalsReportMode === "console" && import.meta.env.DEV) {
    console.info("[core-web-vitals]", metric);
  }

  if (env.coreWebVitalsReportMode === "analytics") {
    trackAnalyticsEvent("core_web_vital", metric);
  }
}

function observeEntryType(type: string, callback: (entries: PerformanceEntry[]) => void): void {
  if (typeof PerformanceObserver === "undefined") {
    return;
  }

  try {
    const observer = new PerformanceObserver((list) => callback(list.getEntries()));
    observer.observe({ type, buffered: true });
  } catch {
    // Some browsers do not support every entry type. Ignore unsupported metrics.
  }
}

export function initCoreWebVitals(): void {
  if (!env.coreWebVitalsEnabled || typeof window === "undefined") {
    return;
  }

  observeEntryType("largest-contentful-paint", (entries) => {
    const last = entries[entries.length - 1];
    if (last) {
      reportMetric({ name: "LCP", value: last.startTime, rating: rateMetric("LCP", last.startTime) });
    }
  });

  observeEntryType("layout-shift", (entries) => {
    const cls = entries.reduce((sum, entry) => {
      const layoutShift = entry as PerformanceEntry & { value?: number; hadRecentInput?: boolean };
      return layoutShift.hadRecentInput ? sum : sum + Number(layoutShift.value || 0);
    }, 0);
    reportMetric({ name: "CLS", value: cls, rating: rateMetric("CLS", cls) });
  });

  observeEntryType("event", (entries) => {
    const maxDuration = entries.reduce((max, entry) => Math.max(max, entry.duration || 0), 0);
    if (maxDuration > 0) {
      reportMetric({ name: "INP", value: maxDuration, rating: rateMetric("INP", maxDuration) });
    }
  });
}

if (typeof window !== "undefined") {
  window.addEventListener("vatranscribe:cookie-consent-updated", () => {
    initCoreWebVitals();
  });
}
