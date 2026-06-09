import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useBillingOverviewQuery } from "@/shared/hooks/useBillingOverviewQuery";
import { useUpgradePlanMutation } from "@/shared/hooks/useUpgradePlanMutation";
import { useI18n } from "@/shared/i18n";
import { formatBytes, formatHoursFromSeconds, percentage } from "@/shared/lib/format";
import { toastSuccess } from "@/shared/ui/toast";

const plans = [
  { code: "free", price: "$0" },
  { code: "pro", price: "$12" },
  { code: "business", price: "$49" },
] as const;

type PlanCode = (typeof plans)[number]["code"];

function normalizePlanCode(planCode?: string | null): PlanCode {
  if (planCode === "pro" || planCode === "business" || planCode === "free") {
    return planCode;
  }

  if (planCode === "starter") {
    return "free";
  }

  return "free";
}

function BillingUsageCard({
  label,
  value,
  pct,
}: {
  label: string;
  value: string;
  pct: number;
}) {
  const { t } = useI18n();
  const [searchParams] = useSearchParams();

  return (
    <div className="premium-card card-border-strong p-6">
      <div className="text-sm text-slate-300">{label}</div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <div className="text-2xl font-semibold text-white">{value}</div>

        <div className="text-xs text-slate-400">
          {pct}% {t.profile.used}
        </div>
      </div>

      <div className="mt-5 h-2 rounded-full bg-slate-700">
        <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function BillingPage() {
  const { t } = useI18n();
  const [searchParams] = useSearchParams();
  const { data } = useBillingOverviewQuery();
  const upgradeMutation = useUpgradePlanMutation();

  const quota = data?.quota;
  const currentPlan = normalizePlanCode(data?.current_plan?.code);

    const requestedPlan = normalizePlanCode(searchParams.get("plan"));
  const [selectedPlan, setSelectedPlan] = useState<PlanCode>(requestedPlan);

  useEffect(() => {
    const planFromQuery = searchParams.get("plan");

    if (planFromQuery) {
      setSelectedPlan(normalizePlanCode(planFromQuery));
      return;
    }

    setSelectedPlan(currentPlan);
  }, [currentPlan, searchParams]);
  const [fakePaymentOpen, setFakePaymentOpen] = useState(false);

  const featuresByCode = useMemo(
    () => ({
      free: t.pricing.freeFeatures,
      pro: t.pricing.proFeatures,
      business: t.pricing.businessFeatures,
    }),
    [t],
  );

  const descByCode = useMemo(
    () => ({
      free: t.pricing.freeDesc,
      pro: t.pricing.proDesc,
      business: t.pricing.businessDesc,
    }),
    [t],
  );

  const titleByCode = useMemo(
    () => ({
      free: t.pricing.starterName,
      pro: t.pricing.proName,
      business: t.pricing.businessName,
    }),
    [t],
  );

  async function handleFakePayment() {
    await upgradeMutation.mutateAsync(selectedPlan);

    toastSuccess(
      t.common.success,
      `${titleByCode[selectedPlan]}: ${t.billing.fakePaymentCompleted}`,
    );

    setFakePaymentOpen(false);
  }

  return (
    <div className="space-y-8">
      <section className="premium-card card-border-strong p-8 md:p-10">
        <div className="max-w-3xl">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
            {t.pricing.billingLabel}
          </div>

          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white md:text-5xl">
            {t.pricing.choosePlanTitle}
          </h1>

          <p className="mt-4 text-base leading-7 text-slate-300">
            {t.pricing.choosePlanSubtitle}
          </p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan) => {
          const selected = selectedPlan === plan.code;
          const realCurrent = currentPlan === plan.code;

          return (
            <button
              key={plan.code}
              type="button"
              onClick={() => setSelectedPlan(plan.code)}
              className={[
                "premium-card card-border-strong flex min-h-[430px] cursor-pointer flex-col justify-between p-8 text-left transition",
                "hover:border-cyan-300/80 hover:bg-cyan-300/[0.04]",
                selected ? "border-cyan-300 shadow-[0_0_0_1px_rgba(103,232,249,0.55)]" : "",
              ].join(" ")}
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-2xl font-semibold text-white">
                    {titleByCode[plan.code]}
                  </h3>

                  {realCurrent ? (
                    <span className="rounded-full border border-cyan-300/50 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-200">
                      {t.profile.active}
                    </span>
                  ) : null}
                </div>

                <div className="mt-6 flex items-end gap-2">
                  <span className="text-5xl font-semibold tracking-tight text-white">
                    {plan.price}
                  </span>

                  <span className="pb-2 text-sm text-slate-400">
                    {t.pricing.perMonth}
                  </span>
                </div>

                <p className="mt-4 min-h-12 text-sm leading-6 text-slate-400">
                  {descByCode[plan.code]}
                </p>

                <ul className="mt-8 space-y-4">
                  {featuresByCode[plan.code].map((feature) => (
                    <li key={feature} className="flex gap-3 text-sm text-slate-200">
                      <span className="text-cyan-300">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div
                className={[
                  "mt-8 rounded-2xl px-5 py-3 text-center text-sm font-semibold transition",
                  selected ? "bg-cyan-300 text-slate-950" : "border border-slate-500 text-white",
                ].join(" ")}
              >
                {selected ? t.common.ready : t.common.select}
              </div>
            </button>
          );
        })}
      </section>

      <section className="premium-card card-border-strong p-6 md:flex md:items-center md:justify-between">
        <div>
          <div className="text-sm text-slate-400">{t.pricing.currentPlan}</div>

          <div className="mt-2 text-2xl font-semibold text-white">
            {titleByCode[currentPlan]}
          </div>

          {selectedPlan !== currentPlan ? (
            <div className="mt-2 text-sm text-cyan-200">
              {t.billing.selectedPlan}: {titleByCode[selectedPlan]}
            </div>
          ) : null}
        </div>

        <button
          type="button"
          onClick={() => setFakePaymentOpen(true)}
          className="premium-button mt-5 md:mt-0"
        >
          {t.common.select}
        </button>
      </section>

      {quota ? (
        <section className="grid gap-6 lg:grid-cols-3">
          <BillingUsageCard
            label={t.profile.storage}
            value={`${formatBytes(quota.storage_bytes_used)} / ${formatBytes(
              quota.storage_bytes_limit,
            )}`}
            pct={percentage(quota.storage_bytes_used, quota.storage_bytes_limit)}
          />

          <BillingUsageCard
            label={t.profile.transcriptionTime}
            value={`${formatHoursFromSeconds(
              quota.transcription_seconds_used,
            )} / ${formatHoursFromSeconds(quota.transcription_seconds_limit)}`}
            pct={percentage(
              quota.transcription_seconds_used,
              quota.transcription_seconds_limit,
            )}
          />

          <BillingUsageCard
            label={t.profile.jobs}
            value={`${quota.jobs_count_used} / ${quota.jobs_count_limit}`}
            pct={percentage(quota.jobs_count_used, quota.jobs_count_limit)}
          />
        </section>
      ) : null}

      {fakePaymentOpen ? (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 px-4 py-10 backdrop-blur-xl">
          <div className="mx-auto max-w-xl rounded-[2rem] border border-slate-500 bg-slate-950 p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-slate-700 pb-5">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
                  {t.billing.fakePayment}
                </div>

                <h2 className="mt-3 text-2xl font-semibold text-white">
                  {t.common.select}
                </h2>

                <p className="mt-2 text-sm text-slate-400">
                  {t.billing.fakePaymentDescription}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setFakePaymentOpen(false)}
                className="rounded-full border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:border-cyan-300"
              >
                {t.common.close}
              </button>
            </div>

            <div className="mt-6 space-y-4">
              <div className="rounded-2xl border border-slate-600 bg-white/[0.03] p-4">
                <div className="text-sm text-slate-400">
                  {t.billing.selectedPlan}
                </div>

                <div className="mt-1 text-xl font-semibold text-white">
                  {titleByCode[selectedPlan]}
                </div>
              </div>

              <input
                disabled
                value="4242 4242 4242 4242"
                className="w-full rounded-2xl border border-slate-600 bg-slate-950 px-4 py-3 text-slate-300"
              />

              <div className="grid grid-cols-2 gap-3">
                <input
                  disabled
                  value="12/30"
                  className="rounded-2xl border border-slate-600 bg-slate-950 px-4 py-3 text-slate-300"
                />

                <input
                  disabled
                  value="123"
                  className="rounded-2xl border border-slate-600 bg-slate-950 px-4 py-3 text-slate-300"
                />
              </div>

              <button
                type="button"
                onClick={handleFakePayment}
                disabled={upgradeMutation.isPending}
                className="premium-button w-full disabled:opacity-60"
              >
                {upgradeMutation.isPending ? t.common.processing : t.common.select}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}