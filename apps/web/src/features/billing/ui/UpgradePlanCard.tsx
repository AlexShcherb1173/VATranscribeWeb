import type { BillingPlan } from "@/entities/billing/model/types";

type UpgradePlanCardProps = {
  plan: BillingPlan;
  currentPlanCode: string;
  onSelect: (planCode: string) => void;
  isPending?: boolean;
};

function formatBytesCompact(value: number): string {
  if (!value) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function formatPrice(value: number, currency: string): string {
  if (value === 0) {
    return "Free";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

export function UpgradePlanCard({
  plan,
  currentPlanCode,
  onSelect,
  isPending = false,
}: UpgradePlanCardProps) {
  const isCurrent = currentPlanCode === plan.code;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-white">{plan.name}</div>
          <div className="mt-1 text-sm text-slate-400">
            {formatPrice(plan.price_monthly, plan.currency)} / month
          </div>
        </div>

        {isCurrent ? (
          <div className="rounded-full border border-cyan-800 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-300">
            Current
          </div>
        ) : null}
      </div>

      <div className="mt-5 space-y-3 text-sm text-slate-300">
        <div>Storage: {formatBytesCompact(plan.storage_bytes_limit)}</div>
        <div>Transcription: {plan.transcription_seconds_limit.toLocaleString()} sec</div>
        <div>Jobs: {plan.jobs_count_limit.toLocaleString()}</div>
      </div>

      <button
        type="button"
        disabled={isCurrent || isPending}
        onClick={() => onSelect(plan.code)}
        className="mt-5 w-full rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isCurrent ? "Current plan" : isPending ? "Updating..." : "Choose plan"}
      </button>
    </div>
  );
}