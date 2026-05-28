import type { Transcript } from "@/entities/transcript/model/types";
import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";

function getTranscriptName(transcript: Transcript): string {
  return (
    transcript.display_name ||
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.id
  );
}

function getSourceMediaName(transcript: Transcript): string {
  return (
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.media_asset_id
  );
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div className="mt-1 min-w-0 break-words text-sm font-semibold text-slate-100 [overflow-wrap:anywhere]">
        {value || "—"}
      </div>
    </div>
  );
}

function getQualityLabel(status: string | null | undefined, t: any): string {
  const normalized = (status || "").toLowerCase();

  if (normalized === "good") return t.transcriptions.qualityGood;
  if (normalized === "partial") return t.transcriptions.qualityPartial;
  if (normalized === "low_quality") return t.transcriptions.qualityLow;
  if (normalized === "hallucinated") return t.transcriptions.qualityHallucinated || "Hallucinated";
  if (normalized === "empty") return t.transcriptions.qualityEmpty;

  return status || "—";
}

function getCoverageValue(transcript: Transcript): string {
  const raw = transcript.coverage_ratio;
  const numeric = typeof raw === "number" ? raw : Number(raw || 0);

  if (!Number.isFinite(numeric) || numeric <= 0) {
    return "—";
  }

  return `${Math.round(numeric * 100)}%`;
}

function getQualityWarningMessage(value: string | null | undefined, t: any): string | null {
  if (!value) {
    return null;
  }

  const normalized = value.trim();
  const lower = normalized.toLowerCase();
  const warnings = t.transcriptions.qualityWarnings || {};

  if (warnings[normalized]) {
    return warnings[normalized];
  }

  if (lower.includes("hallucinated") || lower.includes("repeated") || lower.includes("lyrics_repeated_or_hallucinated")) {
    return warnings.lyrics_repeated_or_hallucinated || normalized;
  }

  if (lower.includes("lyrics_low_repetition")) {
    return warnings.lyrics_low_repetition || normalized;
  }

  if (lower.includes("lyrics_empty_after_cleanup") || lower.includes("became empty after removing")) {
    return warnings.lyrics_empty_after_cleanup || normalized;
  }

  if (lower.includes("lyrics_cleaned_low_quality") || lower.includes("obvious repeated fragments were removed")) {
    return warnings.lyrics_cleaned_low_quality || normalized;
  }

  if (lower.includes("lyrics_cleaned_partial") || lower.includes("transcript was cleaned")) {
    return warnings.lyrics_cleaned_partial || normalized;
  }

  if (lower.includes("lyrics_loops_trimmed") || lower.includes("asr loop fragments") || lower.includes("chorus sections were preserved")) {
    return warnings.lyrics_loops_trimmed || normalized;
  }

  if (lower.includes("lyrics_noise_removed_partial") || lower.includes("foreign-script") || lower.includes("noise-caption")) {
    return warnings.lyrics_noise_removed_partial || normalized;
  }

  if (lower.includes("transcript_empty") || lower.includes("transcript is empty")) {
    return warnings.transcript_empty || normalized;
  }

  if (lower.includes("duration_low_quality") || lower.includes("quality is low for the media duration")) {
    return warnings.duration_low_quality || normalized;
  }

  if (lower.includes("duration_partial") || lower.includes("looks partial")) {
    return warnings.duration_partial || normalized;
  }

  return normalized;
}

export function TranscriptCard({ transcript }: { transcript: Transcript }) {
  const { t } = useI18n();

  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-5 min-w-0">
        <h2 className="text-lg font-semibold text-white">{t.transcriptions.transcript}</h2>

        <div className="mt-2 min-w-0 break-words text-xl font-semibold text-white [overflow-wrap:anywhere]">
          {getTranscriptName(transcript)}
        </div>

        <div className="mt-2 break-all text-xs text-slate-500">
          {t.transcriptions.id}: {transcript.id}
        </div>
      </div>

      <div className="grid min-w-0 gap-5 sm:grid-cols-3">
        <DetailItem label={t.transcriptions.language} value={transcript.language} />
        <DetailItem label={t.transcriptions.model} value={transcript.model_name} />
        <DetailItem label={t.transcriptions.engine} value={transcript.engine} />
        <DetailItem label={t.transcriptions.jobId} value={transcript.job_id} />
        <DetailItem label={t.transcriptions.sourceFile} value={getSourceMediaName(transcript)} />
        <DetailItem label={t.transcriptions.mediaAssetId} value={transcript.media_asset_id} />
        <DetailItem
          label={t.transcriptions.created}
          value={transcript.created_at ? formatDate(transcript.created_at) : null}
        />
        <DetailItem label={t.transcriptions.quality} value={getQualityLabel(transcript.quality_status, t)} />
        <DetailItem label={t.transcriptions.coverage} value={getCoverageValue(transcript)} />
        <DetailItem label={t.transcriptions.segmentsCount} value={transcript.segments_count ?? transcript.segments?.length ?? null} />
      </div>

      {transcript.quality_warning ? (
        <div className="mt-5 rounded-2xl border border-amber-300/30 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-200/80">
            {t.transcriptions.qualityWarning}
          </div>
          {getQualityWarningMessage(transcript.quality_warning, t)}
        </div>
      ) : null}

      <div className="mt-6">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          {t.transcriptions.fullText}
        </div>

        <div className="max-h-[360px] min-w-0 overflow-auto whitespace-pre-wrap rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-sm leading-6 text-slate-100">
          {transcript.full_text || "—"}
        </div>
      </div>
    </section>
  );
}
