import type { BillingOverview } from "@/entities/billing/model/types";
import { UpgradePlanCard } from "@/features/billing/ui/UpgradePlanCard";

type PlanSelectorCardProps = {
  overview: BillingOverview;
  isPending?: boolean;
  onSelectPlan: (planCode: string) => void;
};

export function PlanSelectorCard({
  overview,
  isPending = false,
  onSelectPlan,
}: PlanSelectorCardProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-5">
        <div className="text-lg font-semibold text-white">Available plans</div>
        <div className="mt-1 text-sm text-slate-400">
          Choose a plan that matches your current workload.
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {overview.available_plans.map((plan) => (
          <UpgradePlanCard
            key={plan.id}
            plan={plan}
            currentPlanCode={overview.current_plan.code}
            onSelect={onSelectPlan}
            isPending={isPending}
          />
        ))}
      </div>
    </div>
  );
}