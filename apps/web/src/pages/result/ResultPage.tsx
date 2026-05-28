import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useTranscriptDetailsQuery } from "@/shared/hooks/useTranscriptDetailsQuery";
import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";
import { Spinner } from "@/shared/ui/Spinner";

type TabKey = "transcript" | "summary" | "subtitles" | "ideas" | "export";

function getTranscriptName(transcript: {
  display_name?: string | null;
  source_file_name?: string | null;
  media_asset?: { original_name?: string | null; stored_name?: string | null } | null;
  id: string;
}): string {
  return (
    transcript.display_name ||
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.id
  );
}


export function ResultPage() {
  const { transcriptId = "" } = useParams();
  const { t } = useI18n();
  const { data: transcript, isLoading } = useTranscriptDetailsQuery(transcriptId);
  const [activeTab, setActiveTab] = useState<TabKey>("transcript");

  const tabs = useMemo(
    () =>
      [
        ["transcript", t.result.transcript],
        ["summary", t.result.summary],
        ["subtitles", t.result.subtitles],
        ["ideas", t.result.contentIdeas],
        ["export", t.result.export],
      ] as const,
    [t],
  );

  if (isLoading) {
    return (
      <div className="flex items-center gap-3 text-slate-500 dark:text-slate-300">
        <Spinner />
        <span>{t.common.loading}</span>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="premium-card p-8">
        <h1 className="text-2xl font-semibold">{t.result.notFound}</h1>
        <Link to="/app/transcriptions" className="mt-4 inline-flex text-cyan-700 dark:text-cyan-300">
          {t.result.backToTranscripts}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="premium-card p-6 md:p-8">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">
            {t.result.title}
          </div>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white md:text-5xl">
            {getTranscriptName(transcript)}
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            {transcript.engine} · {transcript.model_name} · {transcript.language} ·{" "}
            {formatDate(transcript.created_at)}
          </p>
        </div>
      </section>

      <section className="premium-card overflow-hidden">
        <div className="flex flex-wrap gap-2 border-b border-slate-200 p-3 dark:border-white/10">
          {tabs.map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={[
                "rounded-2xl px-4 py-2 text-sm font-semibold transition",
                activeTab === key
                  ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                  : "text-slate-500 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white",
              ].join(" ")}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="p-5 md:p-7">
          {activeTab === "transcript" ? (
            <div className="space-y-4">
              {(transcript.segments || []).length ? (
                transcript.segments?.map((segment) => (
                  <div
                    key={segment.id}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/[0.03]"
                  >
                    <div className="mb-2 text-xs font-semibold text-cyan-700 dark:text-cyan-300">
                      {segment.start_sec}s – {segment.end_sec}s
                    </div>

                    <p className="leading-7 text-slate-700 dark:text-slate-200">{segment.text}</p>
                  </div>
                ))
              ) : (
                <p className="whitespace-pre-wrap leading-8 text-slate-700 dark:text-slate-200">
                  {transcript.full_text}
                </p>
              )}
            </div>
          ) : null}

          {activeTab === "summary" ? <LockedBlock title={t.result.summary} /> : null}
          {activeTab === "subtitles" ? <LockedBlock title={t.result.subtitles} /> : null}
          {activeTab === "ideas" ? <LockedBlock title={t.result.contentIdeas} /> : null}

          {activeTab === "export" ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {(transcript.exports || []).map((artifact) => (
                <a
                  key={artifact.id}
                  href={artifact.download_url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:bg-white hover:shadow-md dark:border-white/10 dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"
                >
                  <div className="text-sm font-semibold uppercase text-slate-950 dark:text-white">
                    {artifact.format}
                  </div>

                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    {t.result.downloadArtifact}
                  </div>
                </a>
              ))}

              <div className="rounded-2xl border border-dashed border-cyan-300 bg-cyan-50 p-4 text-left dark:border-cyan-300/30 dark:bg-cyan-300/10">
                <div className="text-sm font-semibold text-slate-950 dark:text-white">
                  DOCX / PDF {t.result.summary}
                </div>
                <div className="mt-2 text-xs text-cyan-700 dark:text-cyan-200">{t.result.locked}</div>
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function LockedBlock({ title }: { title: string }) {
  const { t } = useI18n();

  return (
    <div className="rounded-[1.5rem] border border-dashed border-cyan-300 bg-cyan-50 p-8 text-center dark:border-cyan-300/30 dark:bg-cyan-300/10">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-xl shadow-sm dark:bg-white/10">
        🔒
      </div>

      <h3 className="mt-4 text-xl font-semibold text-slate-950 dark:text-white">{title}</h3>

      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600 dark:text-cyan-100/80">
        {t.result.upgradeCta}
      </p>
    </div>
  );
}