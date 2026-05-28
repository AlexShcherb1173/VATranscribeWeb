import { useEffect, useState, type MouseEvent } from "react";
import { createPortal } from "react-dom";

import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";
import {
  getJobStatusClass,
  mapJobStatus,
  mapJobType,
} from "@/shared/lib/job-mappers";

type JobLike = {
  id: string;
  title?: string | null;
  type?: string | null;
  status?: string | null;
  requested_format?: string | null;
  mp4_mode?: string | null;
  input_url?: string | null;
  created_at?: string | null;
  finished_at?: string | null;
  progress_percent?: number | null;
  progress_stage?: string | null;
  progress_message?: string | null;
  heartbeat_at?: string | null;
  last_log_at?: string | null;
  last_log_message?: string | null;
  current_step?: string | null;
  is_stale?: boolean | null;
};

type ContextMenuState = {
  job: JobLike;
  x: number;
  y: number;
};

function clampMenuPosition(x: number, y: number) {
  const menuWidth = 220;
  const menuHeight = 112;
  const padding = 12;

  if (typeof window === "undefined") {
    return { x, y };
  }

  return {
    x: Math.min(x, window.innerWidth - menuWidth - padding),
    y: Math.min(y, window.innerHeight - menuHeight - padding),
  };
}

function normalizeJobStatus(status: string | null | undefined): string {
  return (status || "").toLowerCase().trim();
}

function isActiveJob(job: JobLike): boolean {
  return [
    "pending",
    "queued",
    "running",
    "processing",
    "started",
    "in_progress",
  ].includes(normalizeJobStatus(job.status));
}

function minutesSince(value: string | null | undefined): number | null {
  if (!value) {
    return null;
  }

  const timestamp = new Date(value).getTime();

  if (!Number.isFinite(timestamp)) {
    return null;
  }

  return Math.max(0, Math.floor((Date.now() - timestamp) / 60000));
}

function translateJobRuntimeText(
  value: string | null | undefined,
  t: ReturnType<typeof useI18n>["t"],
): string {
  const raw = (value || "").trim();

  if (!raw) {
    return "—";
  }

  const replacements: Array<[RegExp, string]> = [
    [/^Job started$/i, t.jobs.logJobStarted],
    [/^Transcription job created$/i, t.jobs.logTranscriptionCreated],
    [/^Transcription job enqueued$/i, t.jobs.logTranscriptionEnqueued],
    [/^Подготовка транскрибации$/i, t.jobs.logPreparingTranscription],
    [/^Извлечение аудио$/i, t.jobs.logExtractingAudio],
    [/^Загрузка модели транскрибации$/i, t.jobs.logLoadingTranscriptionModel],
    [/^Сохранение транскрипта$/i, t.jobs.logSavingTranscript],
    [/^Экспорт TXT\/SRT\/VTT\/JSON$/i, t.jobs.logExportArtifacts],
    [/^Upload completed$/i, t.jobs.logUploadCompleted],
    [/^Готово$/i, t.jobs.succeeded],
    [/^Ошибка$/i, t.jobs.failed],
    [/^В процессе$/i, t.jobs.running],
    [/^Активно$/i, t.jobs.active],
    [/^Транскрипт пустой:.*$/i, t.jobs.logTranscriptEmpty],
    [/^Транскрипт слишком короткий.*$/i, t.jobs.logTranscriptTooShort],
    [/^Первый проход вернул 0 сегментов.*$/i, t.jobs.logFirstPassNoSegments],
    [/^Запускаем fallback.*$/i, t.jobs.logFallbackStarted],
    [/^Fallback transcription.*$/i, t.jobs.logFallbackStarted],
  ];

  for (const [pattern, replacement] of replacements) {
    if (pattern.test(raw)) {
      return replacement;
    }
  }

  if (/^Job failed:/i.test(raw)) {
    const reason = raw.replace(/^Job failed:\s*/i, "");
    const translatedReason = translateJobRuntimeText(reason, t);
    return `${t.jobs.logJobFailed}: ${translatedReason}`;
  }

  return raw
    .replace(/^Requested format:/i, `${t.jobs.logRequestedFormat}:`)
    .replace(/^Audio prepared:/i, `${t.jobs.logAudioPrepared}:`)
    .replace(/^Detected language:/i, `${t.jobs.logDetectedLanguage}:`)
    .replace(/^Segments created:/i, `${t.jobs.logSegmentsCreated}:`)
    .replace(/^Full text length:/i, `${t.jobs.logFullTextLength}:`)
    .replace(/^Transcript created:/i, `${t.jobs.logTranscriptCreated}:`)
    .replace(/^Job retried and enqueued$/i, t.jobs.logJobRetried)
    .replace(/^Language mode:/i, `${t.jobs.logLanguageMode}:`)
    .replace(/^Audio profile:/i, `${t.jobs.logAudioProfile}:`)
    .replace(/^Whisper params:/i, `${t.jobs.logWhisperParams}:`)
    .replace(/^Model:/i, `${t.jobs.logModel}:`)
    .replace(/^Source path:/i, `${t.jobs.logSourcePath}:`)
    .replace(/^Stored media path:/i, `${t.jobs.logStoredMediaPath}:`)
    .replace(/^Resolved media path:/i, `${t.jobs.logResolvedMediaPath}:`)
    .replace(/^Preparing transcription for media asset:/i, `${t.jobs.logPreparingMediaAsset}:`)
    .replace(/^Export artifact is empty:/i, `${t.jobs.logExportArtifactEmpty}:`);
}

function formatRelativeTime(
  value: string | null | undefined,
  t: ReturnType<typeof useI18n>["t"],
): string {
  const minutes = minutesSince(value);

  if (minutes === null) {
    return "—";
  }

  if (minutes < 1) {
    return t.jobs.justNow;
  }

  if (minutes < 60) {
    return `${minutes} ${t.jobs.minutesAgo}`;
  }

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;

  if (rest === 0) {
    return `${hours} ${t.jobs.hoursAgo}`;
  }

  return `${hours} ${t.jobs.hoursAgo} ${rest} ${t.jobs.minutesAgo}`;
}

function getActivityState(
  job: JobLike,
  t: ReturnType<typeof useI18n>["t"],
): {
  label: string;
  className: string;
  title: string;
} {
  const active = isActiveJob(job);
  const stale = Boolean(job.is_stale);

  if (!active) {
    return {
      label: "—",
      className: "text-slate-500",
      title: t.jobs.inactiveTitle,
    };
  }

  if (stale) {
    return {
      label: t.jobs.possiblyStale,
      className: "text-amber-300",
      title: t.jobs.staleTitle,
    };
  }

  return {
    label: t.jobs.active,
    className: "text-emerald-300",
    title: t.jobs.activeTitle,
  };
}

function ProgressCell({ job }: { job: JobLike }) {
  const { t } = useI18n();
  const percent = Math.max(0, Math.min(100, Number(job.progress_percent ?? 0)));
  const rawCurrentStep =
    job.current_step ||
    job.progress_message ||
    job.progress_stage ||
    job.last_log_message ||
    "—";
  const currentStep = translateJobRuntimeText(rawCurrentStep, t);
  const lastLogMessage = translateJobRuntimeText(job.last_log_message || rawCurrentStep, t);
  const lastLogAt = job.last_log_at || job.heartbeat_at || null;
  const activity = getActivityState(job, t);

  return (
    <div className="w-full min-w-0 max-w-[150px]">
      <div className="mb-1 flex min-w-0 items-center justify-between gap-1 text-[10px]">
        <span className="min-w-0 truncate text-slate-400" title={currentStep}>
          {currentStep}
        </span>
        <span className="shrink-0 font-semibold text-slate-200">{percent}%</span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-cyan-400 transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="mt-1 min-w-0 space-y-0.5 text-[10px] leading-tight">
        <div className={["truncate font-semibold", activity.className].join(" ")} title={activity.title}>
          {activity.label}
        </div>

        <div className="truncate text-slate-500" title={lastLogMessage}>
          {t.jobs.log}: {formatRelativeTime(lastLogAt, t)}
        </div>
      </div>
    </div>
  );
}

type JobTableProps = {
  jobs: JobLike[];
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
  onDownloadJob?: (job: JobLike) => void;
  onCancelJob?: (jobId: string) => void;
  onDeleteJob?: (jobId: string) => void;
};

export function JobTable({
  jobs,
  selectedJobId,
  onSelectJob,
  onDownloadJob,
  onCancelJob,
  onDeleteJob,
}: JobTableProps) {
  const { t } = useI18n();
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  const downloadLabel = (t.jobs as any).download || (t.nav as any).downloads || "Download";
  const cancelLabel = (t.jobs as any).cancel || "Cancel";
  const deleteLabel = (t.jobs as any).deleteJob || (t.common as any).delete || "Delete";
  const rightClickHint =
    (t.jobs as any).rightClickHint || "Right-click to open actions";

  useEffect(() => {
    function closeMenu() {
      setContextMenu(null);
    }

    function closeMenuOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setContextMenu(null);
      }
    }

    window.addEventListener("click", closeMenu);
    window.addEventListener("contextmenu", closeMenu);
    window.addEventListener("keydown", closeMenuOnEscape);
    window.addEventListener("scroll", closeMenu, true);
    window.addEventListener("resize", closeMenu);

    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("contextmenu", closeMenu);
      window.removeEventListener("keydown", closeMenuOnEscape);
      window.removeEventListener("scroll", closeMenu, true);
      window.removeEventListener("resize", closeMenu);
    };
  }, []);

  function handleContextMenu(event: MouseEvent<HTMLTableRowElement>, job: JobLike) {
    event.preventDefault();
    event.stopPropagation();

    onSelectJob(job.id);

    const position = clampMenuPosition(event.clientX, event.clientY);

    setContextMenu({
      job,
      x: position.x,
      y: position.y,
    });
  }

  function handleDownloadSelectedJob() {
    if (!contextMenu?.job || !onDownloadJob) {
      return;
    }

    onDownloadJob(contextMenu.job);
    setContextMenu(null);
  }

  function handleDeleteSelectedJob() {
    if (!contextMenu?.job) {
      return;
    }

    const active = isActiveJob(contextMenu.job);

    if (active) {
      if (!onCancelJob) {
        return;
      }

      onCancelJob(contextMenu.job.id);
      setContextMenu(null);
      return;
    }

    if (!onDeleteJob) {
      return;
    }

    onDeleteJob(contextMenu.job.id);
    setContextMenu(null);
  }

  const menu = contextMenu
    ? createPortal(
        <div
          className="fixed z-[9999] min-w-52 rounded-2xl border border-slate-700 bg-slate-950 p-2 shadow-2xl shadow-black/50"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(event) => event.stopPropagation()}
          onContextMenu={(event) => {
            event.preventDefault();
            event.stopPropagation();
          }}
          onMouseDown={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            disabled={!onDownloadJob}
            onClick={handleDownloadSelectedJob}
            className="w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-cyan-100 transition hover:bg-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {downloadLabel}
          </button>

          <button
            type="button"
            disabled={
              contextMenu ? (isActiveJob(contextMenu.job) ? !onCancelJob : !onDeleteJob) : true
            }
            onClick={handleDeleteSelectedJob}
            className={
              contextMenu && isActiveJob(contextMenu.job)
                ? "mt-1 w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-amber-200 transition hover:bg-amber-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                : "mt-1 w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-rose-200 transition hover:bg-rose-500/10 disabled:cursor-not-allowed disabled:opacity-50"
            }
          >
            {contextMenu && isActiveJob(contextMenu.job) ? cancelLabel : deleteLabel}
          </button>
        </div>,
        document.body,
      )
    : null;

  return (
    <div className="relative min-w-0 max-w-full overflow-hidden">
      <div className="max-w-full overflow-x-auto">
        <table className="job-table w-full min-w-[1160px] table-fixed text-sm">
          <colgroup>
            <col className="w-[28%]" />
            <col className="w-[10%]" />
            <col className="w-[10%]" />
            <col className="w-[12%]" />
            <col className="w-[18%]" />
            <col className="w-[11%]" />
            <col className="w-[11%]" />
          </colgroup>

          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              <th className="px-4 py-3">{t.jobs.job}</th>
              <th className="px-4 py-3">{t.jobs.type}</th>
              <th className="px-4 py-3">{t.jobs.status}</th>
              <th className="px-4 py-3">{t.jobs.format}</th>
              <th className="px-4 py-3">{t.jobs.progress}</th>
              <th className="px-4 py-3 whitespace-nowrap">{t.jobs.created}</th>
              <th className="px-4 py-3 pr-6 whitespace-nowrap">{t.jobs.finished}</th>
            </tr>
          </thead>

          <tbody>
            {jobs.map((job) => {
              const selected = selectedJobId === job.id;

              return (
                <tr
                  key={job.id}
                  onClick={() => onSelectJob(job.id)}
                  onContextMenu={(event) => handleContextMenu(event, job)}
                  className={[
                    "cursor-pointer select-none border-t border-slate-800 transition hover:bg-cyan-400/10",
                    selected ? "bg-cyan-400/10" : "",
                  ].join(" ")}
                  title={rightClickHint}
                >
                  <td className="min-w-0 px-4 py-3">
                    <div className="truncate font-semibold text-white">
                      {job.title || job.id}
                    </div>

                    <div className="mt-1 truncate text-xs text-slate-500">
                      {job.input_url || job.id}
                    </div>

                    <div className="mt-1 truncate text-xs text-slate-600">
                      {job.id}
                    </div>
                  </td>

                  <td className="min-w-0 px-4 py-3 text-slate-200">
                    <div className="truncate" title={mapJobType(job.type, t)}>
                      {mapJobType(job.type, t)}
                    </div>
                  </td>

                  <td className="min-w-0 px-4 py-3">
                    <span
                      className={[
                        "inline-flex max-w-full rounded-full px-3 py-1 text-xs font-semibold",
                        getJobStatusClass(job.status),
                      ].join(" ")}
                    >
                      <span className="truncate">{mapJobStatus(job.status, t)}</span>
                    </span>
                  </td>

                  <td className="min-w-0 px-4 py-3">
                    <div
                      className="truncate font-semibold text-slate-200"
                      title={job.requested_format || t.common.unavailable}
                    >
                      {job.requested_format || t.common.unavailable}
                    </div>

                    <div
                      className="mt-1 truncate text-xs text-slate-500"
                      title={job.mp4_mode || t.common.unavailable}
                    >
                      {job.mp4_mode || t.common.unavailable}
                    </div>
                  </td>

                  <td className="min-w-0 px-4 py-3">
                    <ProgressCell job={job} />
                  </td>

                  <td className="min-w-0 px-4 py-3 text-slate-300">
                    <div
                      className="whitespace-nowrap"
                      title={job.created_at ? formatDate(job.created_at) : t.common.unavailable}
                    >
                      {job.created_at ? formatDate(job.created_at) : t.common.unavailable}
                    </div>
                  </td>

                  <td className="min-w-0 px-4 py-3 pr-6 text-slate-300">
                    <div
                      className="whitespace-nowrap"
                      title={job.finished_at ? formatDate(job.finished_at) : t.common.unavailable}
                    >
                      {job.finished_at ? formatDate(job.finished_at) : t.common.unavailable}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {menu}
    </div>
  );
}
