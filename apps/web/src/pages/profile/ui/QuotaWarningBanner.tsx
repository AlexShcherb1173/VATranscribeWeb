import { Link } from "react-router-dom";

import type { UserQuota } from "@/entities/quota/model/types";

type QuotaWarningBannerProps = {
  quota: UserQuota;
};

function getUsagePercent(used: number, limit: number): number {
  if (!limit) return 0;
  return Math.round((used / limit) * 100);
}

export function QuotaWarningBanner({ quota }: QuotaWarningBannerProps) {
  const storagePercent = getUsagePercent(
    quota.storage_bytes_used,
    quota.storage_bytes_limit,
  );
  const transcriptionPercent = getUsagePercent(
    quota.transcription_seconds_used,
    quota.transcription_seconds_limit,
  );
  const jobsPercent = getUsagePercent(
    quota.jobs_count_used,
    quota.jobs_count_limit,
  );

  const highest = Math.max(storagePercent, transcriptionPercent, jobsPercent);

  if (highest < 70) {
    return null;
  }

  const tone =
    highest >= 90
      ? "border-rose-800 bg-rose-950/40 text-rose-100"
      : "border-amber-700 bg-amber-950/30 text-amber-100";

  const message =
    highest >= 90
      ? "You are close to your current limits. Upgrade your plan or reduce usage to avoid blocked operations."
      : "Quota usage is increasing. Consider upgrading before limits affect uploads and transcription jobs.";

  return (
    <div className={`rounded-2xl border px-4 py-4 ${tone}`}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-sm font-semibold">Quota warning</div>
          <div className="mt-1 text-sm opacity-90">{message}</div>
        </div>

        <div className="flex shrink-0 gap-3">
          <Link
            to="/upgrade"
            className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-cyan-400"
          >
            Upgrade plan
          </Link>

          <Link
            to="/billing"
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
          >
            Billing
          </Link>
        </div>
      </div>
    </div>
  );
}