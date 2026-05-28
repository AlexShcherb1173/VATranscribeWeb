import { useQuery } from "@tanstack/react-query";

import { getJobs } from "@/shared/api/jobs";

export function useJobsQuery() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: () => getJobs(),
    refetchInterval: 2000,
  });
}