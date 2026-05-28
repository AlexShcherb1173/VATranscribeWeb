import { useUpgradePlanMutation } from "@/shared/hooks/useUpgradePlanMutation";
import { useI18n } from "@/shared/i18n";

type PricingModalProps = {
  open: boolean;
  onClose: () => void;
};

const plans = [
  { code: "free", price: "$0", highlighted: false },
  { code: "pro", price: "$15", highlighted: true },
  { code: "business", price: "$49", highlighted: false },
] as const;

export function PricingModal({ open, onClose }: PricingModalProps) {
  const { t } = useI18n();
  const upgradeMutation = useUpgradePlanMutation();

  if (!open) {
    return null;
  }

  const featuresByCode = {
    free: t.pricing.freeFeatures,
    pro: t.pricing.proFeatures,
    business: t.pricing.businessFeatures,
  };

  const descByCode = {
    free: t.pricing.freeDesc,
    pro: t.pricing.proDesc,
    business: t.pricing.businessDesc,
  };

  const titleByCode = {
    free: t.pricing.starterName,
    pro: t.pricing.proName,
    business: t.pricing.businessName,
  };

  async function handleSelect(planCode: string) {
    await upgradeMutation.mutateAsync(planCode);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 px-4 py-10 backdrop-blur-xl">
      <div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-slate-600/70 bg-slate-950 p-5 shadow-2xl shadow-slate-950/40">
        <div className="flex items-start justify-between gap-4 border-b border-slate-700 pb-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-300">
              VATranscribe
            </p>

            <h2 className="mt-2 text-2xl font-semibold text-white">
              {t.pricing.title}
            </h2>

            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              {t.pricing.subtitle}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-600 px-4 py-2 text-sm text-slate-300 transition hover:border-cyan-300 hover:bg-cyan-300/10 hover:text-white"
          >
            {t.common.close}
          </button>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.code}
              className={[
                "relative rounded-[1.5rem] border p-5 transition",
                plan.highlighted
                  ? "border-cyan-300 bg-cyan-300/10 shadow-xl shadow-cyan-500/10"
                  : "border-slate-700 bg-white/[0.03]",
              ].join(" ")}
            >
              {plan.highlighted ? (
                <div className="absolute right-4 top-4 rounded-full bg-cyan-300 px-3 py-1 text-xs font-medium text-slate-950">
                  Best value
                </div>
              ) : null}

              <h3 className="text-lg font-semibold text-white">
                {titleByCode[plan.code]}
              </h3>

              <p className="mt-2 min-h-10 text-sm text-slate-400">
                {descByCode[plan.code]}
              </p>

              <div className="mt-5 flex items-end gap-1">
                <span className="text-4xl font-semibold text-white">
                  {plan.price}
                </span>

                <span className="pb-1 text-sm text-slate-500">
                  {t.pricing.perMonth}
                </span>
              </div>

              <ul className="mt-5 space-y-3 text-sm text-slate-300">
                {featuresByCode[plan.code].map((feature) => (
                  <li key={feature} className="flex gap-2">
                    <span className="mt-0.5 text-cyan-300">✓</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                onClick={() => handleSelect(plan.code)}
                disabled={upgradeMutation.isPending}
                className={[
                  "mt-6 w-full rounded-2xl px-4 py-3 text-sm font-semibold transition disabled:opacity-60",
                  plan.highlighted
                    ? "bg-cyan-300 text-slate-950 hover:bg-cyan-200"
                    : "border border-slate-600 bg-white/5 text-white hover:border-cyan-300 hover:bg-cyan-300/10",
                ].join(" ")}
              >
                {plan.code === "free" ? t.common.startFree : t.pricing.upgrade}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}