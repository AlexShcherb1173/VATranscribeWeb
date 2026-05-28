import type { UploadQueueItem } from "@/features/uploads/model/types";
import { useI18n } from "@/shared/i18n";
import { Card } from "@/shared/ui/Card";

export type UploadQueueFilter = "all" | "succeeded" | "uploading" | "failed";

type UploadResultCardProps = {
  items: UploadQueueItem[];
  activeFilter?: UploadQueueFilter;
  onFilterChange?: (filter: UploadQueueFilter) => void;
};

type SummaryItemProps = {
  label: string;
  value: string;
  color: string;
  active?: boolean;
  onClick?: () => void;
};

function SummaryItem({ label, value, color, active = false, onClick }: SummaryItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-xl border bg-slate-950/70 p-4 text-left transition",
        active
          ? "border-cyan-400/70 shadow-[0_0_0_1px_rgba(34,211,238,0.25)]"
          : "border-slate-800 hover:border-slate-600 hover:bg-slate-900/80",
      ].join(" ")}
    >
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div className={`mt-2 text-2xl font-semibold ${color}`}>{value}</div>
    </button>
  );
}

export function UploadResultCard({
  items,
  activeFilter = "all",
  onFilterChange,
}: UploadResultCardProps) {
  const { t } = useI18n();

  const succeeded = items.filter((item) => item.status === "succeeded").length;
  const failed = items.filter((item) => item.status === "failed").length;
  const uploading = items.filter((item) => item.status === "uploading").length;

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="text-lg font-medium text-white">
          {t.uploads.summary}
        </div>

        <button
          type="button"
          onClick={() => onFilterChange?.("all")}
          className={[
            "rounded-xl border px-3 py-1 text-xs font-semibold transition",
            activeFilter === "all"
              ? "border-cyan-400 bg-cyan-500/10 text-cyan-200"
              : "border-slate-800 text-slate-400 hover:border-slate-600",
          ].join(" ")}
        >
          {t.jobs.all}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryItem
          label={t.uploads.succeeded}
          value={String(succeeded)}
          color="text-emerald-300"
          active={activeFilter === "succeeded"}
          onClick={() => onFilterChange?.("succeeded")}
        />

        <SummaryItem
          label={t.uploads.uploadingLabel}
          value={String(uploading)}
          color="text-blue-300"
          active={activeFilter === "uploading"}
          onClick={() => onFilterChange?.("uploading")}
        />

        <SummaryItem
          label={t.uploads.failed}
          value={String(failed)}
          color="text-rose-300"
          active={activeFilter === "failed"}
          onClick={() => onFilterChange?.("failed")}
        />
      </div>
    </Card>
  );
}
