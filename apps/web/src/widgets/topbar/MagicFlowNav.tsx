import { Link, useLocation } from "react-router-dom";

import { useI18n } from "@/shared/i18n";

type SourceKind = "files" | "downloads";

type MagicFlowStep = {
  key: string;
  labelKey: "source" | "processing" | "text" | "subtitles" | "content";
  href?: string | ((location: ReturnType<typeof useLocation>) => string);
  disabled?: boolean;
  match: (pathname: string) => boolean;
};

const SOURCE_STORAGE_KEY = "vatranscribe:last-source";

function isSourceKind(value: string | null): value is SourceKind {
  return value === "files" || value === "downloads";
}

function getStoredSource(): SourceKind | null {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.sessionStorage.getItem(SOURCE_STORAGE_KEY);

  return isSourceKind(value) ? value : null;
}

function rememberSource(source: SourceKind) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(SOURCE_STORAGE_KEY, source);
}

function getSourceHref(location: ReturnType<typeof useLocation>): string {
  const pathname = location.pathname;
  const params = new URLSearchParams(location.search);
  const sourceFromUrl = params.get("source");

  if (pathname.includes("/downloads")) {
    rememberSource("downloads");
    return "/app/downloads";
  }

  if (pathname.includes("/files")) {
    rememberSource("files");
    return "/app/files";
  }

  if (isSourceKind(sourceFromUrl)) {
    rememberSource(sourceFromUrl);
    return `/app/${sourceFromUrl}`;
  }

  const storedSource = getStoredSource();

  if (storedSource) {
    return `/app/${storedSource}`;
  }

  return "/app/files";
}

const steps: MagicFlowStep[] = [
  {
    key: "source",
    labelKey: "source",
    href: getSourceHref,
    match: (pathname) =>
      pathname === "/app" ||
      pathname.includes("/dashboard") ||
      pathname.includes("/downloads") ||
      pathname.includes("/files"),
  },
  {
    key: "processing",
    labelKey: "processing",
    href: "/app/jobs",
    match: (pathname) => pathname.includes("/jobs"),
  },
  {
    key: "text",
    labelKey: "text",
    href: "/app/transcriptions",
    match: (pathname) =>
      pathname.includes("/transcriptions") ||
      pathname.includes("/transcripts") ||
      pathname.includes("/result"),
  },
  {
    key: "subtitles",
    labelKey: "subtitles",
    href: "/app/transcriptions",
    match: (pathname) =>
      pathname.includes("/transcriptions") ||
      pathname.includes("/transcripts") ||
      pathname.includes("/result"),
  },
  {
    key: "content",
    labelKey: "content",
    disabled: true,
    match: () => false,
  },
];

export function MagicFlowNav() {
  const { t } = useI18n();
  const location = useLocation();
  const pathname = location.pathname;

  return (
    <nav
      className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-300"
      aria-label="VATranscribe workflow navigation"
    >
      {steps.map((step, index) => {
        const isActive = step.match(pathname);
        const href = typeof step.href === "function" ? step.href(location) : step.href;
        const label = t.flow[step.labelKey];

        return (
          <span key={step.key} className="inline-flex items-center gap-2">
            {step.disabled || !href ? (
              <span
                aria-disabled="true"
                title={t.flow.comingSoon}
                className="cursor-not-allowed rounded-lg px-2 py-1 text-slate-500 opacity-70"
              >
                {label}
              </span>
            ) : (
              <Link
                to={href}
                aria-label={`${t.flow.goToStep}: ${label}`}
                className={[
                  "rounded-lg px-2 py-1 transition",
                  isActive
                    ? "bg-cyan-400/10 text-cyan-300"
                    : "text-slate-200 hover:bg-white/10 hover:text-white",
                ].join(" ")}
              >
                {label}
              </Link>
            )}

            {index < steps.length - 1 ? (
              <span className="select-none text-slate-500" aria-hidden="true">
                →
              </span>
            ) : null}
          </span>
        );
      })}
    </nav>
  );
}
