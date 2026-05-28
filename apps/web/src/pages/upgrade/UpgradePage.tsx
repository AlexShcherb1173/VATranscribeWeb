import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useI18n } from "@/shared/i18n";

export function UpgradePage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [open, setOpen] = useState(true);

  return (
    <div className="premium-card p-8">
      <div className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">
          VATranscribe Pro
        </div>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {t.pricing.title}
        </h1>
        <p className="mt-3 text-slate-600 dark:text-slate-300">{t.pricing.subtitle}</p>
        <button type="button" onClick={() => setOpen(true)} className="mt-6 premium-button">
          {t.common.upgradeToPro}
        </button>
      </div>
      {/*<PricingModal*/}
      {/*  open={open}*/}
      {/*  onClose={() => {*/}
      {/*    setOpen(false);*/}
      {/*    navigate("/app/billing");*/}
      {/*  }}*/}
      {/*/>*/}
    </div>
  );
}
