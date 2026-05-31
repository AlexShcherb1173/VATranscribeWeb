import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { Job } from "@/entities/job/model/types";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import { useUploadQueue } from "@/features/uploads/model/UploadQueueProvider";
import { useBillingOverviewQuery } from "@/shared/hooks/useBillingOverviewQuery";
import { useJobsQuery } from "@/shared/hooks/useJobsQuery";
import { useMediaFilesQuery } from "@/shared/hooks/useMediaFilesQuery";
import { useTranscriptsQuery } from "@/shared/hooks/useTranscriptsQuery";
import { useI18n } from "@/shared/i18n";
import {
  formatBytes,
  formatDate,
  formatHoursFromSeconds,
  percentage,
} from "@/shared/lib/format";
import {
  clearPendingStartUrl,
  getPendingStartUrl,
  savePendingStartUrl,
} from "@/shared/lib/pendingStartUrl";
import { MagicFlowNav } from "@/widgets/topbar/MagicFlowNav";
import { UploaderPanel } from "@/widgets/uploader/UploaderPanel";

type DashboardTaskMode = "files" | "jobs" | "succeeded" | "processing";

function UsageBar({
  label,
  used,
  limit,
  value,
}: {
  label: string;
  used: number;
  limit: number;
  value: string;
}) {
  const pct = percentage(used, limit);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.04]">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-slate-700 dark:text-slate-200">
          {label}
        </span>

        <span
          className={
            pct >= 80
              ? "font-semibold text-amber-600"
              : "text-slate-500 dark:text-slate-400"
          }
        >
          {value}
        </span>
      </div>

      <div className="mt-3 h-2 rounded-full bg-slate-100 dark:bg-white/10">
        <div
          className="h-2 rounded-full bg-slate-950 dark:bg-cyan-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function getJobTime(job: Job): number {
  return new Date(job.finished_at || job.started_at || job.created_at || 0).getTime();
}

function getNormalizedStatus(job: Job): string {
  return (job.status || "").toLowerCase().trim();
}

function isActiveJob(job: Job): boolean {
  return ["pending", "queued", "running", "processing", "started", "in_progress"].includes(
    getNormalizedStatus(job),
  );
}

function isSuccessfulJob(job: Job): boolean {
  return ["succeeded", "success", "completed", "done"].includes(getNormalizedStatus(job));
}

function isFinishedJob(job: Job): boolean {
  return [
    "succeeded",
    "success",
    "completed",
    "done",
    "failed",
    "error",
    "canceled",
    "cancelled",
  ].includes(getNormalizedStatus(job));
}

function isFileRelatedJob(job: Job): boolean {
  const dynamicJob = job as Job & {
    source_type?: string | null;
    output_media_asset_id?: string | null;
    transcription_media_asset_id?: string | null;
    media_asset_id?: string | null;
  };

  const type = (dynamicJob.type || "").toLowerCase().trim();
  const sourceType = (dynamicJob.source_type || "").toLowerCase().trim();

  return (
    type === "upload" ||
    sourceType === "file" ||
    sourceType === "local_file" ||
    sourceType === "media_asset" ||
    Boolean(dynamicJob.output_media_asset_id) ||
    Boolean(dynamicJob.transcription_media_asset_id) ||
    Boolean(dynamicJob.media_asset_id)
  );
}

function jobDetailsUrl(jobId: string): string {
  return `/app/jobs?jobId=${encodeURIComponent(jobId)}`;
}

function sortJobsNewestFirst(a: Job, b: Job): number {
  return getJobTime(b) - getJobTime(a);
}

function mapUploadStatusToJobStatus(status: UploadQueueItem["status"]): Job["status"] {
  switch (status) {
    case "succeeded":
      return "succeeded";
    case "failed":
      return "failed";
    case "idle":
    case "uploading":
    default:
      return "running";
  }
}

function mapUploadQueueItemToJob(item: UploadQueueItem): Job {
  const now = new Date().toISOString();
  const fileExtension = item.file.name.includes(".")
    ? item.file.name.split(".").pop() || null
    : null;

  return {
    id: `upload-queue:${item.id}`,
    type: "upload",
    status: mapUploadStatusToJobStatus(item.status),
    source_type: "local_file",
    title: `Upload ${item.file.name}`,
    input_url: null,
    requested_format: fileExtension,
    requested_file_name: item.file.name,
    mp4_mode: null,
    output_media_asset_id: item.uploadedMediaAssetId,
    output_media_asset: null,
    transcription_media_asset: null,
    selected_video_format_id: null,
    selected_audio_format_id: null,
    transcription_media_asset_id: null,
    download_audio: false,
    download_video: false,
    transcription_model: null,
    transcription_language: null,
    error_message: item.errorMessage,
    progress_percent: Math.max(0, Math.min(100, Number(item.progress ?? 0))),
    progress_stage: item.status === "failed" ? "failed" : item.status === "succeeded" ? "done" : "uploading",
    progress_message: item.status === "failed"
      ? item.errorMessage
      : item.status === "succeeded"
        ? "Upload completed"
        : "Uploading local file",
    created_at: now,
    started_at: now,
    finished_at: item.status === "succeeded" || item.status === "failed" ? now : null,
  };
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { t } = useI18n();

  const { data: billing } = useBillingOverviewQuery();
  const { data: apiJobs = [] } = useJobsQuery();
  const { queue: uploadQueue } = useUploadQueue();
  const { data: mediaFiles = [] } = useMediaFilesQuery();
  const { data: transcripts = [] } = useTranscriptsQuery();

  const uploadJobs = useMemo(
    () => uploadQueue.map(mapUploadQueueItemToJob),
    [uploadQueue],
  );

  const jobs = useMemo(
    () => [...uploadJobs, ...apiJobs],
    [apiJobs, uploadJobs],
  );

  const [url, setUrl] = useState("");
  const [selectedTaskMode, setSelectedTaskMode] = useState<DashboardTaskMode>("jobs");
  const [recentResultsOpen, setRecentResultsOpen] = useState(true);
  const [dashboardTasksOpen, setDashboardTasksOpen] = useState(true);

  useEffect(() => {
    const pendingUrl = getPendingStartUrl();

    if (pendingUrl) {
      setUrl(pendingUrl);
      clearPendingStartUrl();
    }
  }, []);

  const recentResults = useMemo(
    () =>
      jobs
        .filter(isFinishedJob)
        .sort(sortJobsNewestFirst)
        .slice(0, 50),
    [jobs],
  );

  const dashboardTasks = useMemo(() => {
    const sortedJobs = [...jobs].sort(sortJobsNewestFirst);

    switch (selectedTaskMode) {
      case "files":
        return sortedJobs.filter(isFileRelatedJob);
      case "succeeded":
        return sortedJobs.filter(isSuccessfulJob);
      case "processing":
        return sortedJobs.filter(isActiveJob);
      case "jobs":
      default:
        return sortedJobs;
    }
  }, [jobs, selectedTaskMode]);

  const successfulJobs = jobs.filter(isSuccessfulJob).length;
  const runningJobs = jobs.filter(isActiveJob).length;

  const quota = billing?.quota;

  const usageAlert = quota
    ? percentage(
        quota.transcription_seconds_used,
        quota.transcription_seconds_limit,
      ) >= 80
    : false;

  function handlePasteLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanUrl = url.trim();

    if (!cleanUrl) {
      return;
    }

    savePendingStartUrl(cleanUrl);
    navigate("/app/downloads");
  }

  function handleDashboardCardClick(mode: DashboardTaskMode) {
    setSelectedTaskMode(mode);
    setDashboardTasksOpen(true);
  }

  function mapJobStatus(status?: string | null): string {
    switch ((status || "").toLowerCase()) {
      case "pending":
      case "queued":
        return t.jobs.queued;
      case "running":
      case "processing":
      case "started":
      case "in_progress":
        return t.jobs.running;
      case "succeeded":
      case "success":
      case "completed":
      case "done":
        return t.jobs.succeeded;
      case "failed":
      case "error":
        return t.jobs.failed;
      case "canceled":
      case "cancelled":
        return t.jobs.canceled;
      default:
        return status || t.common.unavailable;
    }
  }

  function mapJobType(type?: string | null): string {
    switch ((type || "").toLowerCase()) {
      case "download":
        return t.jobs.download;
      case "transcribe":
      case "transcription":
        return t.jobs.transcribe;
      case "upload":
        return t.jobs.upload;
      default:
        return type || t.common.unavailable;
    }
  }

  function getStatusPillClass(status?: string | null): string {
    switch ((status || "").toLowerCase()) {
      case "succeeded":
      case "success":
      case "completed":
      case "done":
        return "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-200";
      case "failed":
      case "error":
        return "bg-rose-100 text-rose-700 dark:bg-rose-400/10 dark:text-rose-200";
      case "running":
      case "processing":
      case "started":
      case "in_progress":
        return "bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-100";
      case "pending":
      case "queued":
        return "bg-blue-100 text-blue-700 dark:bg-blue-400/10 dark:text-blue-200";
      case "canceled":
      case "cancelled":
        return "bg-slate-100 text-slate-700 dark:bg-slate-400/10 dark:text-slate-200";
      default:
        return "bg-slate-100 text-slate-700 dark:bg-white dark:text-slate-950";
    }
  }

  function getDashboardTaskTitle(mode: DashboardTaskMode): string {
    switch (mode) {
      case "files":
        return `${t.jobs.title}: ${t.files.title}`;
      case "succeeded":
        return `${t.jobs.title}: ${t.uploads.succeeded}`;
      case "processing":
        return `${t.jobs.title}: ${t.common.processing}`;
      case "jobs":
      default:
        return t.jobs.title;
    }
  }

  const storageLabel = t.profile?.storage ?? "Хранилище";
  const transcriptionTimeLabel =
    t.profile?.transcriptionTime ?? "Время транскрибации";

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-[-0.04em] text-slate-950 dark:text-white md:text-4xl">
          {t.dashboard.title}
        </h1>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          {t.dashboard.description}
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="premium-card p-4 md:p-5">
          <div className="mb-3 text-sm font-semibold text-slate-950 dark:text-white">
            {t.common.pasteLink}
          </div>

          <form
            onSubmit={handlePasteLink}
            className="flex flex-col gap-3 rounded-[1.25rem] border border-slate-200 bg-slate-50 p-2 dark:border-white/10 dark:bg-slate-950/60 md:flex-row"
          >
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder={t.common.pasteLink}
              className="min-h-11 flex-1 rounded-xl border border-transparent bg-white px-4 text-sm outline-none transition focus:border-cyan-300 dark:bg-white/5 dark:text-white"
            />

            <button type="submit" className="premium-button min-h-11">
              {t.common.pasteLink}
            </button>
          </form>
        </div>

        <div className="premium-card p-4 md:p-5">
          <div className="mb-3">
            <div className="text-sm font-semibold text-slate-950 dark:text-white">
              {t.common.uploadFile}
            </div>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              MP3, WAV, MP4, MOV, M4A
            </p>
          </div>

          <UploaderPanel compact redirectToFilesOnSelect />
        </div>
      </section>

      {usageAlert ? (
        <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5 text-amber-950 dark:border-amber-300/20 dark:bg-amber-300/10 dark:text-amber-100">
          <div className="font-semibold">{t.dashboard.almostOut}</div>
          <div className="mt-1">
            <MagicFlowNav />
          </div>
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-4">
        <DashboardMetricCard
          label={t.files.title}
          value={mediaFiles.length.toString()}
          active={selectedTaskMode === "files"}
          onClick={() => handleDashboardCardClick("files")}
        />
        <DashboardMetricCard
          label={t.jobs.title}
          value={jobs.length.toString()}
          active={selectedTaskMode === "jobs"}
          onClick={() => handleDashboardCardClick("jobs")}
        />
        <DashboardMetricCard
          label={t.uploads.succeeded}
          value={successfulJobs.toString()}
          active={selectedTaskMode === "succeeded"}
          onClick={() => handleDashboardCardClick("succeeded")}
        />
        <DashboardMetricCard
          label={t.common.processing}
          value={runningJobs.toString()}
          active={selectedTaskMode === "processing"}
          onClick={() => handleDashboardCardClick("processing")}
        />
      </section>

      {quota ? (
        <section className="grid gap-4 lg:grid-cols-3">
          <UsageBar
            label={storageLabel}
            used={quota.storage_bytes_used}
            limit={quota.storage_bytes_limit}
            value={`${formatBytes(quota.storage_bytes_used)} / ${formatBytes(
              quota.storage_bytes_limit,
            )}`}
          />

          <UsageBar
            label={transcriptionTimeLabel}
            used={quota.transcription_seconds_used}
            limit={quota.transcription_seconds_limit}
            value={`${formatHoursFromSeconds(
              quota.transcription_seconds_used,
            )} / ${formatHoursFromSeconds(quota.transcription_seconds_limit)}`}
          />

          <UsageBar
            label={t.jobs.title}
            used={quota.jobs_count_used}
            limit={quota.jobs_count_limit}
            value={`${quota.jobs_count_used} / ${quota.jobs_count_limit}`}
          />
        </section>
      ) : null}

      <section className="grid items-start gap-6 xl:grid-cols-2">
        <CollapsibleDashboardPanel
          title={t.dashboard.recentResults}
          open={recentResultsOpen}
          onToggle={() => setRecentResultsOpen((value) => !value)}
        >
          {recentResults.length ? (
            <div className="max-h-[590px] space-y-3 overflow-y-auto pr-2">
              {recentResults.map((job) => (
                <JobResultLink
                  key={job.id}
                  job={job}
                  mapJobStatus={mapJobStatus}
                  mapJobType={mapJobType}
                  getStatusPillClass={getStatusPillClass}
                />
              ))}
            </div>
          ) : (
            <EmptyBox>{t.dashboard.empty}</EmptyBox>
          )}
        </CollapsibleDashboardPanel>

        <CollapsibleDashboardPanel
          title={getDashboardTaskTitle(selectedTaskMode)}
          badge={`${dashboardTasks.length}`}
          open={dashboardTasksOpen}
          onToggle={() => setDashboardTasksOpen((value) => !value)}
        >
          {dashboardTasks.length ? (
            <div className="max-h-[590px] space-y-3 overflow-y-auto pr-2">
              {dashboardTasks.map((job) => (
                <DashboardTaskItem
                  key={job.id}
                  job={job}
                  mapJobStatus={mapJobStatus}
                  mapJobType={mapJobType}
                  getStatusPillClass={getStatusPillClass}
                />
              ))}
            </div>
          ) : (
            <EmptyBox>
              {selectedTaskMode === "jobs"
                ? t.jobs.noSelectedJob
                : "Нет задач для выбранного фильтра."}
            </EmptyBox>
          )}
        </CollapsibleDashboardPanel>
      </section>
    </div>
  );
}

function DashboardMetricCard({
  label,
  value,
  active,
  onClick,
}: {
  label: string;
  value: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        "min-h-[7rem] rounded-2xl border p-5 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-300/70",
        "bg-white text-slate-950 shadow-sm dark:bg-white/[0.04] dark:text-white",
        active
          ? "border-cyan-300 bg-cyan-50 shadow-[0_0_0_1px_rgba(103,232,249,0.22)] dark:bg-cyan-400/10"
          : "border-slate-200 hover:border-cyan-300/70 hover:bg-cyan-50/60 dark:border-white/10 dark:hover:border-cyan-300/60 dark:hover:bg-cyan-400/5",
      ].join(" ")}
    >
      <div
        className={[
          "text-sm font-medium transition",
          active ? "text-cyan-700 dark:text-cyan-200" : "text-slate-600 dark:text-slate-300",
        ].join(" ")}
      >
        {label}
      </div>

      <div className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
        {value}
      </div>
    </button>
  );
}

function CollapsibleDashboardPanel({
  title,
  badge,
  open,
  onToggle,
  children,
}: {
  title: string;
  badge?: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="premium-card flex min-h-[140px] flex-col p-5 md:p-6">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="mb-4 flex w-full items-center justify-between gap-4 text-left"
      >
        <div className="flex min-w-0 items-center gap-3">
          <h2 className="truncate text-lg font-semibold text-slate-950 dark:text-white">
            {title}
          </h2>

          {badge ? (
            <span className="shrink-0 rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 dark:border-white/10 dark:text-slate-300">
              {badge}
            </span>
          ) : null}
        </div>

        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-slate-600 dark:border-white/10 dark:text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? <div className="min-h-0 flex-1">{children}</div> : null}
    </div>
  );
}

function JobResultLink({
  job,
  mapJobStatus,
  mapJobType,
  getStatusPillClass,
}: {
  job: Job;
  mapJobStatus: (status?: string | null) => string;
  mapJobType: (type?: string | null) => string;
  getStatusPillClass: (status?: string | null) => string;
}) {
  return (
    <Link
      to={jobDetailsUrl(job.id)}
      className="block rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:bg-white hover:shadow-md dark:border-white/10 dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"
    >
      <JobItemContent
        job={job}
        mapJobStatus={mapJobStatus}
        mapJobType={mapJobType}
        getStatusPillClass={getStatusPillClass}
        date={job.finished_at || job.created_at}
      />
    </Link>
  );
}

function DashboardTaskItem({
  job,
  mapJobStatus,
  mapJobType,
  getStatusPillClass,
}: {
  job: Job;
  mapJobStatus: (status?: string | null) => string;
  mapJobType: (type?: string | null) => string;
  getStatusPillClass: (status?: string | null) => string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/[0.03]">
      <JobItemContent
        job={job}
        mapJobStatus={mapJobStatus}
        mapJobType={mapJobType}
        getStatusPillClass={getStatusPillClass}
        date={job.started_at || job.finished_at || job.created_at}
      />
    </div>
  );
}

function JobItemContent({
  job,
  mapJobStatus,
  mapJobType,
  getStatusPillClass,
  date,
}: {
  job: Job;
  mapJobStatus: (status?: string | null) => string;
  mapJobType: (type?: string | null) => string;
  getStatusPillClass: (status?: string | null) => string;
  date?: string | null;
}) {
  return (
    <>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div
            className="truncate font-medium text-slate-950 dark:text-white"
            title={job.title || job.requested_file_name || job.id}
          >
            {job.title || job.requested_file_name || job.id}
          </div>

          <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">
            {mapJobType(job.type)}
          </div>
        </div>

        <span
          className={[
            "shrink-0 rounded-full px-3 py-1 text-xs font-medium",
            getStatusPillClass(job.status),
          ].join(" ")}
        >
          {mapJobStatus(job.status)}
        </span>
      </div>

      <div className="mt-3 text-xs text-slate-400">
        {formatDate(date)}
      </div>
    </>
  );
}

function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
      {children}
    </div>
  );
}

