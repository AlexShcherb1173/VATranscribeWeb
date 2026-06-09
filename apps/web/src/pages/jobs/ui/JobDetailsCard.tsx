import { useState } from "react";

import { downloadMediaFile, saveBlob } from "@/shared/api/files";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { formatBytes, formatDate } from "@/shared/lib/format";
import {
  getJobStatusClass,
  mapJobStatus,
  mapJobType,
  mapSourceType,
} from "@/shared/lib/job-mappers";
import { Card } from "@/shared/ui/Card";
import { toastError } from "@/shared/ui/toast";

type JobMediaAsset = {
  id: string;
  stored_name?: string | null;
  original_name?: string | null;
  path?: string | null;
  size_bytes?: number | null;
  download_url?: string | null;
};

type JobDetailsCardProps = {
  job: {
    id: string;
    title?: string | null;
    type?: string | null;
    status?: string | null;
    source_type?: string | null;
    requested_format?: string | null;
    requested_file_name?: string | null;
    mp4_mode?: string | null;
    transcription_model?: string | null;
    transcription_language?: string | null;
    created_at?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    input_url?: string | null;
    output_media_asset_id?: string | null;
    output_media_asset?: JobMediaAsset | null;
    transcription_media_asset_id?: string | null;
    transcription_media_asset?: JobMediaAsset | null;
    error_message?: string | null;
  };
};

function asDisplayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value);
}

function translateJobRuntimeText(
  value: string | number | null | undefined,
  t: ReturnType<typeof useI18n>["t"],
): string {
  const raw = asDisplayValue(value);

  if (raw === "—") {
    return raw;
  }

  const replacements: Array<[RegExp, string]> = [
    [/^Job started$/i, t.jobs.logJobStarted],
    [/^Transcription job created$/i, t.jobs.logTranscriptionCreated],
    [/^Transcription job enqueued$/i, t.jobs.logTranscriptionEnqueued],
    [/^Подготовка транскрибации$/i, t.jobs.logPreparingTranscription],
    [/^Извлечение аудио$/i, t.jobs.logExtractingAudio],
    [/^Загрузка модели транскрибации$/i, t.jobs.logLoadingTranscriptionModel],
    [/^Отделение вокала от музыки$/i, t.jobs.logVocalIsolation],
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
    [/^Lyrics \/ Music clip requires.*$/i, "Lyrics / Music clip requires a stronger model. Upgrading model to medium."],
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

function DetailItem({
  label,
  value,
  wide = false,
}: {
  label: string;
  value: string | number | null | undefined;
  wide?: boolean;
}) {
  const displayValue = asDisplayValue(value);

  return (
    <div className={["min-w-0 max-w-full overflow-hidden", wide ? "sm:col-span-2" : ""].join(" ")}>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div
        className="job-detail-value mt-1 max-w-full text-sm font-medium text-slate-100"
        title={displayValue === "—" ? undefined : displayValue}
      >
        {displayValue}
      </div>
    </div>
  );
}

function getMediaAssetFileName(asset: JobMediaAsset): string {
  return asset.stored_name || asset.original_name || `media-${asset.id}`;
}

type MediaAssetBoxProps = {
  asset: JobMediaAsset;
  title?: string;
};

function MediaAssetBox({ asset, title }: MediaAssetBoxProps) {
  const { t } = useI18n();
  const [isDownloading, setIsDownloading] = useState(false);
  const fileName = getMediaAssetFileName(asset);

  async function handleDownload() {
    if (isDownloading) {
      return;
    }

    setIsDownloading(true);

    try {
      const blob = await downloadMediaFile(asset.id);
      saveBlob(blob, fileName);
    } catch (error: any) {
      toastError(t.common.failed, extractErrorMessage(error));
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="min-w-0 max-w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60 p-4 sm:col-span-2">
      {title ? (
        <div className="mb-4 min-w-0 max-w-full overflow-hidden text-sm font-semibold text-white">
          <span className="job-detail-value block max-w-full" title={title}>
            {title}
          </span>
        </div>
      ) : null}

      <div className="grid min-w-0 max-w-full gap-3 sm:grid-cols-2">
        <DetailItem label={t.jobs.fileName} value={fileName} />

        <DetailItem
          label={t.files.size}
          value={asset.size_bytes ? formatBytes(asset.size_bytes) : null}
        />
      </div>

      <button
        type="button"
        disabled={isDownloading}
        onClick={handleDownload}
        className="mt-4 inline-flex max-w-full rounded-xl bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className="truncate">
          {isDownloading ? t.files.downloading : t.files.download}
        </span>
      </button>
    </div>
  );
}

export function JobDetailsCard({ job }: JobDetailsCardProps) {
  const { t } = useI18n();
  const title = job.title || job.requested_file_name || job.id;

  return (
    <Card className="min-w-0 max-w-full overflow-hidden p-5">
      <div className="mb-5 flex min-w-0 max-w-full items-start justify-between gap-4 overflow-hidden">
        <div className="min-w-0 flex-1 overflow-hidden">
          <div className="text-lg font-semibold text-white">
            {mapJobType(job.type, t)}
          </div>

          <h2
            className="job-detail-title mt-2 max-w-full text-xl font-semibold text-white"
            title={title}
          >
            {title}
          </h2>

          <div
            className="job-detail-value mt-2 max-w-full text-xs text-slate-500"
            title={job.id}
          >
            {job.id}
          </div>
        </div>

        <span
          className={[
            "shrink-0 rounded-full px-3 py-1 text-xs font-semibold",
            getJobStatusClass(job.status),
          ].join(" ")}
        >
          {mapJobStatus(job.status, t)}
        </span>
      </div>

      <div className="grid min-w-0 max-w-full gap-x-5 gap-y-5 sm:grid-cols-2">
        <DetailItem label={t.jobs.type} value={mapJobType(job.type, t)} />
        <DetailItem label={t.jobs.sourceType} value={mapSourceType(job.source_type, t)} />
        <DetailItem label={t.jobs.requestedFormat} value={job.requested_format} />
        <DetailItem label={t.jobs.fileName} value={job.requested_file_name} />
        <DetailItem label={t.jobs.mp4Mode} value={job.mp4_mode} />
        <DetailItem label={t.jobs.transcriptionModel} value={job.transcription_model} />
        <DetailItem label={t.jobs.language} value={job.transcription_language} />

        <DetailItem
          label={t.jobs.created}
          value={job.created_at ? formatDate(job.created_at) : null}
        />

        <DetailItem
          label={t.jobs.started}
          value={job.started_at ? formatDate(job.started_at) : null}
        />

        <DetailItem
          label={t.jobs.finished}
          value={job.finished_at ? formatDate(job.finished_at) : null}
        />

        <DetailItem label={t.jobs.inputUrl} value={job.input_url} wide />

        <DetailItem
          label={t.jobs.outputMediaAsset}
          value={
            job.output_media_asset?.stored_name ||
            job.output_media_asset?.original_name ||
            job.output_media_asset_id
          }
          wide
        />

        {job.output_media_asset ? (
          <MediaAssetBox
            asset={job.output_media_asset}
            title={t.jobs.outputMediaAsset}
          />
        ) : null}

        <DetailItem
          label={t.jobs.transcriptionMediaAsset}
          value={
            job.transcription_media_asset?.stored_name ||
            job.transcription_media_asset?.original_name ||
            job.transcription_media_asset_id
          }
          wide
        />

        {job.transcription_media_asset ? (
          <MediaAssetBox
            asset={job.transcription_media_asset}
            title={t.jobs.transcriptionMediaAsset}
          />
        ) : null}

        <DetailItem label={t.jobs.error} value={translateJobRuntimeText(job.error_message, t)} wide />
      </div>
    </Card>
  );
}
