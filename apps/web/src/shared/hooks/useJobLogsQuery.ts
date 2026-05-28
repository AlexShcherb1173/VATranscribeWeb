import { useQuery } from "@tanstack/react-query";

import { getJobLogs } from "@/shared/api/jobs";

export function useJobLogsQuery(jobId: string | null) {
  return useQuery({
    queryKey: ["job-logs", jobId],
    queryFn: () => getJobLogs(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: 1500,
  });
}