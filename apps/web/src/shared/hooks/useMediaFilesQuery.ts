import { useQuery } from "@tanstack/react-query";

import { getMediaFiles } from "@/shared/api/files";

export function useMediaFilesQuery() {
  return useQuery({
    queryKey: ["media-files"],
    queryFn: getMediaFiles,
    refetchInterval: 5000,
  });
}