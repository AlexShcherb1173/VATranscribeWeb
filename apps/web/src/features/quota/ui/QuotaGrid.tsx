import { useI18n } from "@/shared/i18n";
import {
  formatBytes,
  formatHoursFromSeconds,
  percentage,
} from "@/shared/lib/format";

type QuotaGridProps = {
  quota: {
    storage_bytes_used: number;
    storage_bytes_limit: number;
    transcription_seconds_used: number;
    transcription_seconds_limit: number;
    jobs_count_used: number;
    jobs_count_limit: number;
  };
};

function QuotaCard({
  label,
  value,
  limit,
  pct,
}: {
  label: string;
  value: string;
  limit: string;
  pct: number;
}) {
  const { t } = useI18n();

  return (
    <div className="premium-card card-border-strong p-5">
      <div className="text-sm text-slate-300">{label}</div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <div className="text-2xl font-semibold text-white">{value}</div>

        <div className="text-xs text-slate-400">
          {t.profile.of} {limit}
        </div>
      </div>

      <div className="mt-5 h-2 rounded-full bg-slate-700">
        <div
          className="h-2 rounded-full bg-cyan-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-3 text-xs text-slate-400">
        {pct}% {t.profile.used}
      </div>
    </div>
  );
}

export function QuotaGrid({ quota }: QuotaGridProps) {
  const { t } = useI18n();

  return (
    <section className="grid gap-4 md:grid-cols-3">
      <QuotaCard
        label={t.profile.storage}
        value={formatBytes(quota.storage_bytes_used)}
        limit={formatBytes(quota.storage_bytes_limit)}
        pct={percentage(quota.storage_bytes_used, quota.storage_bytes_limit)}
      />

      <QuotaCard
        label={t.profile.transcriptionTime}
        value={formatHoursFromSeconds(quota.transcription_seconds_used)}
        limit={formatHoursFromSeconds(quota.transcription_seconds_limit)}
        pct={percentage(
          quota.transcription_seconds_used,
          quota.transcription_seconds_limit
        )}
      />

      <QuotaCard
        label={t.profile.jobs}
        value={`${quota.jobs_count_used}`}
        limit={`${quota.jobs_count_limit}`}
        pct={percentage(quota.jobs_count_used, quota.jobs_count_limit)}
      />
    </section>
  );
}