import { useQuery } from "@tanstack/react-query";

import { getTranscripts } from "@/shared/api/transcriptions";

export function useTranscriptsQuery() {
  return useQuery({
    queryKey: ["transcripts"],
    queryFn: getTranscripts,
    refetchInterval: 5000,
  });
}