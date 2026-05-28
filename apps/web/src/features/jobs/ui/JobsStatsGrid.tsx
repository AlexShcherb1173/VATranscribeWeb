import type { Job } from "@/entities/job/model/types";
import { Card } from "@/shared/ui/Card";

type JobsStatsGridProps = {
  jobs: Job[];
};

export function JobsStatsGrid({ jobs }: JobsStatsGridProps) {
  const total = jobs.length;
  const queued = jobs.filter((job) => job.status === "queued").length;
  const running = jobs.filter((job) => job.status === "running").length;
  const succeeded = jobs.filter((job) => job.status === "succeeded").length;
  const failed = jobs.filter((job) => job.status === "failed").length;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <MetricCard title="Total" value={String(total)} />
      <MetricCard title="Queued" value={String(queued)} />
      <MetricCard title="Running" value={String(running)} />
      <MetricCard title="Succeeded" value={String(succeeded)} />
      <MetricCard title="Failed" value={String(failed)} />
    </div>
  );
}

type MetricCardProps = {
  title: string;
  value: string;
};

function MetricCard({ title, value }: MetricCardProps) {
  return (
    <Card className="p-5">
      <div className="text-sm text-slate-400">{title}</div>
      <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
    </Card>
  );
}