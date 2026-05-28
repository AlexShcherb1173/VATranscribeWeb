import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth/api/auth";
import { hasAccessToken } from "@/shared/auth/token";

export function useCurrentUserQuery() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: hasAccessToken(),
    retry: false,
    staleTime: 30_000,
  });
}