import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth/api/auth";

export function useCurrentUserQuery() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 30_000,
  });
}
