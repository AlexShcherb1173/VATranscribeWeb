import type { JobStatus } from "@/entities/job/model/types";
import { cn } from "@/shared/lib/utils";

type BadgeProps = {
  status: JobStatus;
};

const statusStyles: Record<JobStatus, string> = {
  pending: "bg-slate-700/70 text-slate-100",
  queued: "bg-blue-500/20 text-blue-300",
  running: "bg-amber-500/20 text-amber-300",
  succeeded: "bg-emerald-500/20 text-emerald-300",
  failed: "bg-rose-500/20 text-rose-300",
  canceled: "bg-slate-600/40 text-slate-300",
};

export function Badge({ status }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize",
        statusStyles[status],
      )}
    >
      {status}
    </span>
  );
}