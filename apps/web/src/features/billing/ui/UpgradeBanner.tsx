import { Link } from "react-router-dom";

type UpgradeBannerProps = {
  title?: string;
  description?: string;
};

export function UpgradeBanner({
  title = "Need more capacity?",
  description = "Upgrade your plan to unlock higher storage, transcription time and monthly job limits.",
}: UpgradeBannerProps) {
  return (
    <div className="rounded-2xl border border-cyan-800/60 bg-cyan-500/10 p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-lg font-semibold text-white">{title}</div>
          <div className="mt-1 text-sm text-slate-300">{description}</div>
        </div>

        <div className="flex shrink-0 gap-3">
          <Link
            to="/upgrade"
            className="rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-400"
          >
            Upgrade plan
          </Link>

          <Link
            to="/billing"
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
          >
            Open billing
          </Link>
        </div>
      </div>
    </div>
  );
}