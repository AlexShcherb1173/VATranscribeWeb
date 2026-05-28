import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { destroySession } from "@/shared/auth/session";
import { useBillingOverviewQuery } from "@/shared/hooks/useBillingOverviewQuery";
import { useCurrentUserQuery } from "@/shared/hooks/useCurrentUserQuery";
import { useI18n } from "@/shared/i18n";
import { formatHoursFromSeconds, percentage } from "@/shared/lib/format";
import { toastInfo } from "@/shared/ui/toast";
import { MagicFlowNav } from "@/widgets/topbar/MagicFlowNav";

function LanguageToggle() {
  const { language, setLanguage } = useI18n();
  return (
    <div className="hidden rounded-full border border-slate-200 bg-white p-1 text-xs font-semibold dark:border-white/10 dark:bg-white/5 sm:flex">
      {(["en", "ru"] as const).map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => setLanguage(item)}
          className={[
            "rounded-full px-2.5 py-1 transition",
            language === item
              ? "bg-slate-950 text-white dark:bg-cyan-300 dark:text-slate-950"
              : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white",
          ].join(" ")}
        >
          {item.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

export function Topbar() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const { data: user } = useCurrentUserQuery();
  const { data: billing } = useBillingOverviewQuery();
  const [pricingOpen, setPricingOpen] = useState(false);

  const quota = billing?.quota;
  const minutesPct = quota
    ? percentage(quota.transcription_seconds_used, quota.transcription_seconds_limit)
    : 0;

  async function handleLogout() {
    destroySession();
    queryClient.clear();
    toastInfo(t.common.sessionClosed, t.common.signedOut);
    navigate("/", { replace: true });
  }

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-slate-50/80 px-4 py-4 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/80 md:px-6 xl:px-8">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <MagicFlowNav />
          <div className="mt-1 hidden text-xs text-slate-500 dark:text-slate-400 sm:block">
            {user?.email || t.common.authenticatedWorkspace}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3">
          {billing ? (
            <div className="hidden min-w-[220px] rounded-2xl border border-slate-200 bg-white px-3 py-2 dark:border-white/10 dark:bg-white/5 md:block">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  {billing.current_plan.name}
                </span>
                <span className={minutesPct > 80 ? "text-amber-600" : "text-slate-500 dark:text-slate-400"}>
                  {formatHoursFromSeconds(quota?.transcription_seconds_used)} / {formatHoursFromSeconds(quota?.transcription_seconds_limit)}
                </span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-slate-100 dark:bg-white/10">
                <div className="h-1.5 rounded-full bg-cyan-500" style={{ width: `${minutesPct}%` }} />
              </div>
            </div>
          ) : null}

          <LanguageToggle />

          <button type="button" onClick={() => setPricingOpen(true)} className="premium-button hidden sm:inline-flex">
            <Link to="/app/billing" className="premium-button">
                 {t.common.goToSubscriptions}
            </Link>
          </button>

          <Link to="/app" className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 lg:hidden">
            VA
          </Link>

          <button type="button" onClick={handleLogout} className="secondary-button px-4 py-2 text-xs">
            {t.common.logout}
          </button>
        </div>
      </div>


    </header>
  );
}
