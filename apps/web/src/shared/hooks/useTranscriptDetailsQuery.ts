import { useQuery } from "@tanstack/react-query";

import { getTranscript } from "@/shared/api/transcriptions";

export function useTranscriptDetailsQuery(transcriptId: string | null) {
  return useQuery({
    queryKey: ["transcript", transcriptId],
    queryFn: () => getTranscript(transcriptId as string),
    enabled: Boolean(transcriptId),
    refetchInterval: 5000,
  });
}