import { useQuery } from "@tanstack/react-query";

import { getBillingOverview } from "@/features/billing/api/billing";
import { hasAccessToken } from "@/shared/auth/token";

export function useBillingOverviewQuery() {
  return useQuery({
    queryKey: ["billing", "overview"],
    queryFn: getBillingOverview,
    enabled: hasAccessToken(),
    staleTime: 30_000,
  });
}