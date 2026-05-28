import type { BillingOverview } from "@/entities/billing/model/types";

type BillingSummaryCardProps = {
  overview: BillingOverview;
};

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

export function BillingSummaryCard({ overview }: BillingSummaryCardProps) {
  const { current_plan, subscription } = overview;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-sm text-slate-400">Current subscription</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {current_plan.name}
          </div>
          <div className="mt-1 text-sm text-slate-400">
            {formatPrice(current_plan.price_monthly, current_plan.currency)} / month
          </div>
        </div>

        <div className="rounded-full border border-emerald-800 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
          {subscription.status}
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Period start
          </div>
          <div className="mt-1 text-sm text-white">
            {new Date(subscription.current_period_start).toLocaleDateString()}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Period end
          </div>
          <div className="mt-1 text-sm text-white">
            {new Date(subscription.current_period_end).toLocaleDateString()}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Cancellation
          </div>
          <div className="mt-1 text-sm text-white">
            {subscription.cancel_at_period_end ? "Scheduled" : "Not scheduled"}
          </div>
        </div>
      </div>
    </div>
  );
}