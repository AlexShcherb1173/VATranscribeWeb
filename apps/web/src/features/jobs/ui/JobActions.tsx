import { useMutation, useQueryClient } from "@tanstack/react-query";

import { restartJob, stopJob } from "@/features/jobs/api/jobs";
import { useI18n } from "@/shared/i18n";
import { toastError, toastSuccess } from "@/shared/ui/toast";

type JobActionsProps = {
  job: {
    id: string;
    status?: string | null;
  };
};

export function JobActions({ job }: JobActionsProps) {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  const restartMutation = useMutation({
    mutationFn: (jobId: string) => restartJob(jobId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["job-logs", job.id] });

      toastSuccess(t.common.success, t.jobs.restart);
    },
    onError: () => {
      toastError(t.common.error, t.common.requestFailed);
    },
  });

  const stopMutation = useMutation({
    mutationFn: (jobId: string) => stopJob(jobId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["job-logs", job.id] });

      toastSuccess(t.common.success, t.jobs.cancel);
    },
    onError: () => {
      toastError(t.common.error, t.common.requestFailed);
    },
  });

  const canRetry =
    job.status === "failed" ||
    job.status === "canceled" ||
    job.status === "succeeded";

  const canCancel =
    job.status === "pending" ||
    job.status === "queued" ||
    job.status === "running";

  return (
    <div className="grid min-w-0 grid-cols-2 gap-3">
      <button
        type="button"
        disabled={!canRetry || restartMutation.isPending}
        onClick={() => restartMutation.mutate(job.id)}
        className="inline-flex min-h-11 min-w-0 items-center justify-center rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {restartMutation.isPending ? t.common.processing : t.jobs.retry}
      </button>

      <button
        type="button"
        disabled={!canCancel || stopMutation.isPending}
        onClick={() => stopMutation.mutate(job.id)}
        className="inline-flex min-h-11 min-w-0 items-center justify-center rounded-xl border border-rose-500 px-4 py-3 text-sm font-semibold text-rose-200 transition hover:bg-rose-500/10 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {stopMutation.isPending ? t.common.processing : t.jobs.cancel}
      </button>
    </div>
  );
}
