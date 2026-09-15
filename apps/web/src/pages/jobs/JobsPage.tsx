import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import type { Job } from "@/entities/job/model/types";
import { deleteJob, stopJob } from "@/features/jobs/api/jobs";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import { useUploadQueue } from "@/features/uploads/model/UploadQueueProvider";
import { downloadMediaFile, saveBlob } from "@/shared/api/files";
import { getJob } from "@/shared/api/jobs";
import { JobActions } from "@/features/jobs/ui/JobActions";
import { JobDetailsCard } from "@/features/jobs/ui/JobDetailsCard";
import { useJobDetailsQuery } from "@/shared/hooks/useJobDetailsQuery";
import { useJobLogsQuery } from "@/shared/hooks/useJobLogsQuery";
import { useJobsQuery } from "@/shared/hooks/useJobsQuery";
import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Spinner } from "@/shared/ui/Spinner";
import { toastError, toastSuccess } from "@/shared/ui/toast";
import { JobFilters } from "@/widgets/job-table/JobFilters";
import { JobTable } from "@/widgets/job-table/JobTable";

type JobStatusFilter = "" | "queued" | "running" | "succeeded" | "failed" | "canceled";

type JobLogLike = {
  id?: string | null;
  level?: string | null;
  message?: string | null;
  created_at?: string | null;
};

const STATUS_GROUPS: Record<Exclude<JobStatusFilter, "">, string[]> = {
  queued: ["pending", "queued"],
  running: ["running", "processing", "started", "in_progress"],
  succeeded: ["succeeded", "success", "completed", "done"],
  failed: ["failed", "error"],
  canceled: ["canceled", "cancelled"],
};

function normalizeJobStatus(status: string | null | undefined): string {
  return (status || "").toLowerCase().trim();
}

function matchesStatusFilter(
  jobStatus: string | null | undefined,
  filter: JobStatusFilter,
): boolean {
  if (!filter) {
    return true;
  }

  const normalized = normalizeJobStatus(jobStatus);
  const group = STATUS_GROUPS[filter];

  if (!group) {
    return normalized === filter;
  }

  return group.includes(normalized);
}

function countByStatusFilter(
  jobs: Array<{ status?: string | null }>,
  filter: JobStatusFilter,
): number {
  if (!filter) {
    return jobs.length;
  }

  return jobs.filter((job) => matchesStatusFilter(job.status, filter)).length;
}

function isActiveJobStatus(status: string | null | undefined): boolean {
  return matchesStatusFilter(status, "queued") || matchesStatusFilter(status, "running");
}

function isUploadQueueJobId(jobId: string | null | undefined): boolean {
  return Boolean(jobId && jobId.startsWith("upload-queue:"));
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
    heartbeat_at: now,
    last_log_at: now,
    last_log_message: item.status === "failed"
      ? item.errorMessage
      : item.status === "succeeded"
        ? "Upload completed"
        : "Uploading local file",
    current_step: item.status === "failed"
      ? item.errorMessage
      : item.status === "succeeded"
        ? "Upload completed"
        : "Uploading local file",
    is_stale: false,
    created_at: now,
    started_at: now,
    finished_at: item.status === "succeeded" || item.status === "failed" ? now : null,
  };
}

function getApiErrorMessage(error: unknown): string | null {
  if (!error || typeof error !== "object") {
    return null;
  }

  const response = (error as { response?: { data?: unknown } }).response;
  const data = response?.data;

  if (!data) {
    return null;
  }

  if (typeof data === "string") {
    return data;
  }

  if (typeof data === "object" && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }

          if (item && typeof item === "object" && "msg" in item) {
            const message = (item as { msg?: unknown }).msg;
            return typeof message === "string" ? message : null;
          }

          return null;
        })
        .filter(Boolean)
        .join("\n");
    }
  }

  return null;
}

function translateLogMessage(
  message: string | null | undefined,
  t: ReturnType<typeof useI18n>["t"],
): string {
  const raw = message || "—";

  const exact: Array<[RegExp, string]> = [
    [/^Download job created$/i, t.jobs.logDownloadCreated],
    [/^Download job enqueued$/i, t.jobs.logDownloadEnqueued],
    [/^Transcription job created$/i, t.jobs.logTranscriptionCreated],
    [/^Transcription job enqueued$/i, t.jobs.logTranscriptionEnqueued],
    [/^Job started$/i, t.jobs.logJobStarted],
    [/^Job retried and enqueued$/i, t.jobs.logJobRetried],
    [/^Подготовка транскрибации$/i, t.jobs.logPreparingTranscription],
    [/^Извлечение аудио$/i, t.jobs.logExtractingAudio],
    [/^Загрузка модели транскрибации$/i, t.jobs.logLoadingTranscriptionModel],
    [/^Отделение вокала от музыки$/i, t.jobs.logVocalIsolation],
    [/^Сохранение транскрипта$/i, t.jobs.logSavingTranscript],
    [/^Экспорт TXT\/SRT\/VTT\/JSON$/i, t.jobs.logExportArtifacts],
    [/^Upload completed$/i, t.jobs.logUploadCompleted],
    [/^Транскрипт пустой:.*$/i, t.jobs.logTranscriptEmpty],
    [/^Транскрипт слишком короткий.*$/i, t.jobs.logTranscriptTooShort],
    [/^Первый проход вернул 0 сегментов.*$/i, t.jobs.logFirstPassNoSegments],
    [/^Запускаем fallback.*$/i, t.jobs.logFallbackStarted],
    [/^Fallback transcription.*$/i, t.jobs.logFallbackStarted],
    [/^Lyrics \/ Music clip requires.*$/i, "Lyrics / Music clip requires a stronger model. Upgrading model to medium."],
  ];

  for (const [pattern, replacement] of exact) {
    if (pattern.test(raw)) {
      return replacement;
    }
  }

  if (/^Job failed:/i.test(raw)) {
    const reason = raw.replace(/^Job failed:\s*/i, "");
    const translatedReason = translateLogMessage(reason, t);
    return `${t.jobs.logJobFailed}: ${translatedReason}`;
  }

  return raw
    .replace(/^Requested format:/i, `${t.jobs.logRequestedFormat}:`)
    .replace(/^Audio prepared:/i, `${t.jobs.logAudioPrepared}:`)
    .replace(/^Detected language:/i, `${t.jobs.logDetectedLanguage}:`)
    .replace(/^Segments created:/i, `${t.jobs.logSegmentsCreated}:`)
    .replace(/^Full text length:/i, `${t.jobs.logFullTextLength}:`)
    .replace(/^Coverage ratio:/i, `${t.jobs.logCoverageRatio}:`)
    .replace(/^Quality status:/i, `${t.jobs.logQualityStatus}:`)
    .replace(/^Demucs vocals extracted:/i, `${t.jobs.logDemucsVocalsExtracted}:`)
    .replace(/^Using isolated vocals for transcription:/i, `${t.jobs.logUsingIsolatedVocals}:`)
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

export function JobsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [status, setStatus] = useState<JobStatusFilter>("");
  const [type, setType] = useState("");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(
    searchParams.get("jobId"),
  );
  const [tableOpen, setTableOpen] = useState(true);
  const [detailsOpen, setDetailsOpen] = useState(true);
  const [logsOpen, setLogsOpen] = useState(false);

  const jobsQuery = useJobsQuery();
  const { queue: uploadQueue } = useUploadQueue();

  const uploadJobs = useMemo(
    () => uploadQueue.map(mapUploadQueueItemToJob),
    [uploadQueue],
  );

  const data = useMemo(
    () => [...uploadJobs, ...(jobsQuery.data ?? [])],
    [jobsQuery.data, uploadJobs],
  );

  const jobs = useMemo(() => {
    return data.filter((job) => {
      const statusMatch = matchesStatusFilter(job.status, status);
      const typeMatch = type ? job.type === type : true;

      return statusMatch && typeMatch;
    });
  }, [data, status, type]);

  const totalJobs = data.length;
  const queuedJobs = countByStatusFilter(data, "queued");
  const runningJobs = countByStatusFilter(data, "running");
  const succeededJobs = countByStatusFilter(data, "succeeded");
  const failedJobs = countByStatusFilter(data, "failed");

  const syncSelectedJob = useCallback(
    (jobId: string | null, replace = false) => {
      setSelectedJobId(jobId);

      const nextParams = new URLSearchParams(searchParams);

      if (jobId) {
        nextParams.set("jobId", jobId);
      } else {
        nextParams.delete("jobId");
      }

      setSearchParams(nextParams, { replace });
    },
    [searchParams, setSearchParams],
  );

  useEffect(() => {
    const jobIdFromUrl = searchParams.get("jobId");
    const selectedExists = selectedJobId
      ? jobs.some((job) => job.id === selectedJobId)
      : false;
    const urlJobExists = jobIdFromUrl
      ? jobs.some((job) => job.id === jobIdFromUrl)
      : false;

    if (!jobs.length) {
      if (selectedJobId || jobIdFromUrl) {
        syncSelectedJob(null, true);
      }

      return;
    }

    if (jobIdFromUrl && urlJobExists) {
      if (selectedJobId !== jobIdFromUrl) {
        setSelectedJobId(jobIdFromUrl);
      }

      return;
    }

    if (selectedExists) {
      if (jobIdFromUrl !== selectedJobId) {
        syncSelectedJob(selectedJobId, true);
      }

      return;
    }

    syncSelectedJob(jobs[0].id, true);
  }, [jobs, searchParams, selectedJobId, syncSelectedJob]);

  useEffect(() => {
    setLogsOpen(false);
  }, [selectedJobId]);

  const selectedUploadJob = useMemo(
    () => uploadJobs.find((job) => job.id === selectedJobId) ?? null,
    [selectedJobId, uploadJobs],
  );
  const realSelectedJobId = selectedUploadJob ? null : selectedJobId;

  const jobDetailsQuery = useJobDetailsQuery(realSelectedJobId);
  const jobLogsQuery = useJobLogsQuery(realSelectedJobId);
  const selectedJobDetails = selectedUploadJob ?? jobDetailsQuery.data ?? null;
  const selectedJobLogs = selectedUploadJob
    ? [
        {
          id: `${selectedUploadJob.id}:progress`,
          job_id: selectedUploadJob.id,
          level: selectedUploadJob.status === "failed" ? "ERROR" : "INFO",
          message: selectedUploadJob.progress_message || "Uploading local file",
          created_at: selectedUploadJob.created_at,
        },
      ]
    : jobLogsQuery.data ?? [];

  const deleteJobMutation = useMutation({
    mutationFn: (jobId: string) => deleteJob(jobId, false),
    onMutate: async (deletedJobId) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: ["jobs"] }),
        queryClient.cancelQueries({ queryKey: ["job", deletedJobId] }),
        queryClient.cancelQueries({ queryKey: ["job-logs", deletedJobId] }),
      ]);

      const previousJobs = queryClient.getQueryData<typeof data>(["jobs"]);

      queryClient.setQueryData<typeof data>(["jobs"], (currentJobs) => {
        if (!currentJobs) {
          return currentJobs;
        }

        return currentJobs.filter((job) => job.id !== deletedJobId);
      });

      queryClient.removeQueries({ queryKey: ["job", deletedJobId] });
      queryClient.removeQueries({ queryKey: ["job-logs", deletedJobId] });

      if (selectedJobId === deletedJobId) {
        syncSelectedJob(null, true);
      }

      return { previousJobs };
    },
    onSuccess: async (_data, deletedJobId) => {
      queryClient.removeQueries({ queryKey: ["job", deletedJobId] });
      queryClient.removeQueries({ queryKey: ["job-logs", deletedJobId] });

      await queryClient.invalidateQueries({ queryKey: ["jobs"] });

      toastSuccess(t.common.success, t.jobs.jobDeleted);
    },
    onError: (error, _deletedJobId, context) => {
      if (context?.previousJobs) {
        queryClient.setQueryData(["jobs"], context.previousJobs);
      }

      toastError(
        t.common.error,
        getApiErrorMessage(error) ||
          t.jobs.activeJobCannotBeDeleted,
      );
    },
  });


  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => stopJob(jobId),
    onSuccess: async (_data, jobId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
        queryClient.invalidateQueries({ queryKey: ["job-logs", jobId] }),
      ]);

      toastSuccess(
        t.common.success,
        (t.jobs as any).cancelled || (t.jobs as any).cancel || t.jobs.jobCancelled,
      );
    },
    onError: (error) => {
      toastError(
        t.common.error,
        getApiErrorMessage(error) ||
          t.jobs.cancelFailed,
      );
    },
  });

  function handleStatusCardClick(nextStatus: JobStatusFilter) {
    setStatus(nextStatus);
    setTableOpen(true);
  }

  function handleFilterStatusChange(nextStatus: string) {
    setStatus(nextStatus as JobStatusFilter);
    setTableOpen(true);
  }

  function handleTypeFilterChange(nextType: string) {
    setType(nextType);
    setTableOpen(true);
  }

  function handleSelectJob(jobId: string) {
    syncSelectedJob(jobId);
    setDetailsOpen(true);
  }


  async function handleDownloadJob(job: { id: string }) {
    syncSelectedJob(job.id);
    setDetailsOpen(true);

    if (isUploadQueueJobId(job.id)) {
      toastError(
        t.common.error,
        t.jobs.uploadHasNoOutput,
      );
      return;
    }

    try {
      const jobDetails = await getJob(job.id);
      const outputAsset = jobDetails.output_media_asset;
      const outputAssetId = outputAsset?.id || jobDetails.output_media_asset_id;

      if (!outputAssetId) {
        toastError(
          t.common.error,
          t.jobs.jobHasNoOutput,
        );
        return;
      }

      const fileName =
        outputAsset?.stored_name ||
        outputAsset?.original_name ||
        jobDetails.requested_file_name ||
        `media-${outputAssetId}`;

      const blob = await downloadMediaFile(outputAssetId);
      saveBlob(blob, fileName);
    } catch {
      toastError(
        t.common.error,
        t.jobs.downloadOutputFailed,
      );
    }
  }

  function handleCancelJob(jobId: string) {
    if (isUploadQueueJobId(jobId)) {
      toastError(
        t.common.error,
        t.jobs.browserUploadCancelUnavailable,
      );
      return;
    }

    const confirmed = window.confirm(
      (t.jobs as any).confirmCancelJob ||
        t.jobs.confirmCancelActiveJob,
    );

    if (!confirmed) {
      return;
    }

    cancelJobMutation.mutate(jobId);
  }

  function handleDeleteJob(jobId: string) {
    if (isUploadQueueJobId(jobId)) {
      toastError(t.common.error, t.jobs.uploadCleanupHint);
      return;
    }

    const job = data.find((item) => item.id === jobId);

    if (isActiveJobStatus(job?.status)) {
      handleCancelJob(jobId);
      return;
    }

    const confirmed = window.confirm(t.jobs.confirmDeleteJob);

    if (!confirmed) {
      return;
    }

    deleteJobMutation.mutate(jobId);
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.jobs.title} description={t.jobs.description} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label={t.jobs.all}
          value={totalJobs}
          active={status === ""}
          onClick={() => handleStatusCardClick("")}
        />
        <StatCard
          label={t.jobs.queued}
          value={queuedJobs}
          active={status === "queued"}
          onClick={() => handleStatusCardClick("queued")}
        />
        <StatCard
          label={t.jobs.running}
          value={runningJobs}
          active={status === "running"}
          onClick={() => handleStatusCardClick("running")}
        />
        <StatCard
          label={t.jobs.succeeded}
          value={succeededJobs}
          active={status === "succeeded"}
          onClick={() => handleStatusCardClick("succeeded")}
        />
        <StatCard
          label={t.jobs.failed}
          value={failedJobs}
          active={status === "failed"}
          onClick={() => handleStatusCardClick("failed")}
          danger
        />
      </section>

      <div className="grid min-w-0 max-w-full gap-6 overflow-hidden xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.55fr)]">
        <Card className="min-w-0 max-w-full p-5">
          <JobFilters
            status={status}
            type={type}
            onStatusChange={handleFilterStatusChange}
            onTypeChange={handleTypeFilterChange}
          />
        </Card>

        <Card className="min-w-0 max-w-full p-5">
          <div className="mb-4 text-sm font-semibold text-white">
            {t.jobs.actions}
          </div>

          {jobDetailsQuery.isLoading && !selectedUploadJob ? (
            <div className="flex items-center gap-3 text-slate-300">
              <Spinner />
              <span>{t.jobs.loadingDetails}</span>
            </div>
          ) : selectedUploadJob ? (
            <div className="text-sm text-slate-400">
              {t.jobs.uploadQueueJobHint || "Local upload is shown as a job. Manage it on the Files page."}
            </div>
          ) : jobDetailsQuery.data ? (
            <JobActions job={jobDetailsQuery.data} />
          ) : (
            <div className="text-sm text-slate-400">
              {t.jobs.noSelectedJob}
            </div>
          )}
        </Card>
      </div>

      {jobsQuery.isLoading ? (
        <Card className="p-5">
          <div className="flex items-center gap-3 text-slate-300">
            <Spinner />
            <span>{t.jobs.loading}</span>
          </div>
        </Card>
      ) : (
        <div className="grid min-w-0 max-w-full gap-6 overflow-hidden xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.55fr)]">
          <div className="min-w-0 overflow-hidden">
            <CollapsibleJobsTable
              title={t.jobs.title}
              count={jobs.length}
              open={tableOpen}
              onToggle={() => setTableOpen((value) => !value)}
            >
              {jobs.length ? (
                <JobTable
                  jobs={jobs}
                  selectedJobId={selectedJobId}
                  onSelectJob={handleSelectJob}
                  onDownloadJob={handleDownloadJob}
                  onCancelJob={handleCancelJob}
                  onDeleteJob={handleDeleteJob}
                />
              ) : (
                <div className="p-8 text-center">
                  <div className="text-lg font-semibold text-white">
                    {t.common.noJobsFound}
                  </div>

                  <p className="mt-3 text-sm text-slate-400">
                    {t.common.noJobsHint}
                  </p>
                </div>
              )}
            </CollapsibleJobsTable>
          </div>

          <aside className="grid min-w-0 max-w-full content-start gap-6 overflow-hidden">
            {jobDetailsQuery.isLoading && !selectedUploadJob ? (
              <Card className="p-5">
                <div className="flex items-center gap-3 text-slate-300">
                  <Spinner />
                  <span>{t.jobs.loadingDetails}</span>
                </div>
              </Card>
            ) : selectedJobDetails ? (
              <CollapsibleJobDetails
                title={t.jobs.job}
                open={detailsOpen}
                onToggle={() => setDetailsOpen((value) => !value)}
              >
                <JobDetailsCard job={selectedJobDetails} />
              </CollapsibleJobDetails>
            ) : (
              <Card className="p-5 text-sm text-slate-400">
                {t.jobs.noSelectedJob}
              </Card>
            )}

            <CollapsibleLogs
              logs={selectedJobLogs}
              loading={!selectedUploadJob && jobLogsQuery.isLoading}
              open={logsOpen}
              onToggle={() => setLogsOpen((value) => !value)}
              emptyTitle={t.common.noLogsYet}
              emptyDescription={t.common.logsHint}
              loadingLabel={t.jobs.loadingLogs}
              t={t}
            />
          </aside>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  danger = false,
  active = false,
  onClick,
}: {
  label: string;
  value: number;
  danger?: boolean;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        "group rounded-2xl border p-5 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-300/70",
        active
          ? "border-cyan-300/70 bg-cyan-400/10 shadow-[0_0_0_1px_rgba(103,232,249,0.25)]"
          : "border-slate-800 bg-slate-900/70 hover:border-cyan-400/50 hover:bg-cyan-400/5",
      ].join(" ")}
    >
      <div
        className={[
          "text-sm transition",
          active ? "text-cyan-200" : "text-slate-400 group-hover:text-slate-200",
        ].join(" ")}
      >
        {label}
      </div>

      <div
        className={[
          "mt-3 text-3xl font-semibold tracking-tight transition",
          danger ? "text-rose-300" : "text-white",
        ].join(" ")}
      >
        {value}
      </div>
    </button>
  );
}


function CollapsibleJobsTable({
  title,
  count,
  open,
  onToggle,
  children,
}: {
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <Card className="min-w-0 max-w-full overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-5 py-4 text-left transition hover:bg-white/[0.03]"
        aria-expanded={open}
      >
        <div className="flex min-w-0 items-center gap-3">
          <span className="text-sm font-semibold text-white">
            {title}
          </span>

          <span className="shrink-0 rounded-full border border-slate-700 px-2.5 py-1 text-xs font-semibold text-slate-300">
            {count}
          </span>
        </div>

        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-700 text-sm font-semibold text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="max-h-[620px] min-w-0 max-w-full overflow-y-auto">
          {children}
        </div>
      ) : null}
    </Card>
  );
}

function CollapsibleJobDetails({
  title,
  open,
  onToggle,
  children,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-5 py-4 text-left transition hover:bg-white/[0.03]"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-white">
          {title}
        </span>

        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-700 text-sm font-semibold text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="max-h-[620px] overflow-y-auto p-5 pr-3">
          {children}
        </div>
      ) : null}
    </Card>
  );
}

function CollapsibleLogs({
  logs,
  loading,
  open,
  onToggle,
  emptyTitle,
  emptyDescription,
  loadingLabel,
  t,
}: {
  logs: JobLogLike[];
  loading: boolean;
  open: boolean;
  onToggle: () => void;
  emptyTitle: string;
  emptyDescription: string;
  loadingLabel: string;
  t: ReturnType<typeof useI18n>["t"];
}) {
  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-5 py-4 text-left transition hover:bg-white/[0.03]"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-white">
          {t.jobs.logs}
        </span>

        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-700 text-sm font-semibold text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="p-5">
          {loading ? (
            <div className="flex items-center gap-3 text-slate-300">
              <Spinner />
              <span>{loadingLabel}</span>
            </div>
          ) : logs.length ? (
            <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
              {logs.map((log, index) => (
                <div
                  key={log.id || `${log.created_at || "log"}-${index}`}
                  className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-3 text-xs">
                    <span className="font-semibold uppercase text-cyan-300">
                      {log.level || "INFO"}
                    </span>

                    <span className="text-slate-500">
                      {log.created_at ? formatDate(log.created_at) : "—"}
                    </span>
                  </div>

                  <div className="whitespace-pre-wrap break-words text-sm text-slate-200">
                    {translateLogMessage(log.message, t)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 text-center">
              <div className="text-lg font-semibold text-white">
                {emptyTitle}
              </div>

              <p className="mt-3 text-sm text-slate-400">
                {emptyDescription}
              </p>
            </div>
          )}
        </div>
      ) : null}
    </Card>
  );
}
