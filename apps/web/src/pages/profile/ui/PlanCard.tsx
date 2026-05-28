import { useI18n } from "@/shared/i18n";
import { formatBytes, formatHoursFromSeconds } from "@/shared/lib/format";

type PlanCardProps = {
  quota: {
    plan_code: string;
    subscription_status?: string;
    storage_bytes_limit: number;
    transcription_seconds_limit: number;
    jobs_count_limit: number;
  };
};

export function PlanCard({ quota }: PlanCardProps) {
  const { t } = useI18n();

  return (
    <section className="premium-card border-slate-600/60 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm text-slate-300">{t.profile.currentPlan}</div>

          <div className="mt-3 text-2xl font-semibold text-white capitalize">
            {quota.plan_code}
          </div>
        </div>

        <span className="rounded-full border border-cyan-300/50 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-200">
          {t.profile.active}
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-600/60 bg-slate-950/40 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {t.profile.storageLimit}
          </div>
          <div className="mt-3 font-semibold text-white">
            {formatBytes(quota.storage_bytes_limit)}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-600/60 bg-slate-950/40 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {t.profile.transcriptionTime}
          </div>
          <div className="mt-3 font-semibold text-white">
            {formatHoursFromSeconds(quota.transcription_seconds_limit)}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-600/60 bg-slate-950/40 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {t.profile.jobLimit}
          </div>
          <div className="mt-3 font-semibold text-white">
            {quota.jobs_count_limit} {t.profile.jobs.toLowerCase()}
          </div>
        </div>
      </div>
    </section>
  );
}