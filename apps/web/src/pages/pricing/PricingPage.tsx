import { Link } from "react-router-dom";

import { useI18n } from "@/shared/i18n";

const plans = [
  { code: "free", price: "$0" },
  { code: "pro", price: "$15" },
  { code: "business", price: "$49" },
] as const;

export function PricingPage() {
  const { t } = useI18n();

  const titleByCode = {
    free: t.pricing.starterName,
    pro: t.pricing.proName,
    business: t.pricing.businessName,
  };

  const descByCode = {
    free: t.pricing.freeDesc,
    pro: t.pricing.proDesc,
    business: t.pricing.businessDesc,
  };

  const featuresByCode = {
    free: t.pricing.freeFeatures,
    pro: t.pricing.proFeatures,
    business: t.pricing.businessFeatures,
  };

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between">
        <Link to="/" className="font-semibold text-white">
          VATranscribe
        </Link>

        <Link to="/auth" className="premium-button">
          {t.auth.login}
        </Link>
      </header>

      <main className="mx-auto max-w-7xl py-20">
        <section className="max-w-3xl">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
            {t.pricing.billingLabel}
          </div>

          <h1 className="mt-5 text-5xl font-semibold tracking-tight">
            {t.pricing.choosePlanTitle}
          </h1>

          <p className="mt-5 text-lg leading-8 text-slate-300">
            {t.pricing.choosePlanSubtitle}
          </p>
        </section>

        <section className="mt-12 grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.code}
              className="premium-card card-border-strong flex min-h-[430px] flex-col justify-between p-8"
            >
              <div>
                <h2 className="text-2xl font-semibold">
                  {titleByCode[plan.code]}
                </h2>

                <div className="mt-6 flex items-end gap-2">
                  <span className="text-5xl font-semibold">{plan.price}</span>
                  <span className="pb-2 text-sm text-slate-400">
                    {t.pricing.perMonth}
                  </span>
                </div>

                <p className="mt-5 text-sm leading-6 text-slate-400">
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

              <Link to="/auth" className="premium-button mt-8 text-center">
                {t.common.startFree}
              </Link>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}