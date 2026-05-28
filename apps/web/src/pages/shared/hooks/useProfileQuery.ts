import { useQuery } from "@tanstack/react-query";

import { getMyProfile } from "@/features/profile/api/profile";
import { hasAccessToken } from "@/shared/auth/token";

export function useProfileQuery() {
  return useQuery({
    queryKey: ["profile", "me"],
    queryFn: getMyProfile,
    enabled: hasAccessToken(),
    staleTime: 30_000,
  });
}
