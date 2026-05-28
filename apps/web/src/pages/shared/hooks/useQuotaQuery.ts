import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type { UserQuota } from "@/entities/quota/model/types";
import { hasAccessToken } from "@/shared/auth/token";

async function getMyQuota(): Promise<UserQuota> {
  const response = await apiClient.get<UserQuota>("/quota/me");
  return response.data;
}

export function useQuotaQuery() {
  return useQuery({
    queryKey: ["quota", "me"],
    queryFn: getMyQuota,
    enabled: hasAccessToken(),
    staleTime: 15_000,
  });
}