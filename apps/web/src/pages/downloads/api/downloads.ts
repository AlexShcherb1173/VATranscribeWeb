import { apiClient } from "@/shared/api/client";
import type {
  CreateDownloadJobRequest,
  CreatedJobResponse,
  DownloadAnalyzeRequest,
  DownloadAnalyzeResponse,
} from "@/features/downloads/model/types";

type BackendAnalyzeResponse = {
  url: string;
  platform?: string | null;
  title?: string | null;
  duration_seconds?: number | null;
  thumbnail_url?: string | null;
  available_formats?: any[];
  extract_audio?: boolean;
};

function normalizeAnalyzeResponse(data: BackendAnalyzeResponse): DownloadAnalyzeResponse {
  return {
    title: data.title ?? null,
    duration: data.duration_seconds ?? null,
    webpage_url: data.url,
    extractor: data.platform ?? null,
    formats: (data.available_formats ?? []).map((item) => ({
      format_id: item.format_id ?? item.id ?? null,
      ext: item.ext ?? null,
      format_note: item.format_note ?? item.note ?? null,
      resolution: item.resolution ?? null,
      height: item.height ?? null,
      width: item.width ?? null,
      fps: item.fps ?? null,
      vcodec: item.vcodec ?? null,
      acodec: item.acodec ?? null,
      filesize: item.filesize ?? item.filesize_approx ?? null,
      tbr: item.tbr ?? null,
      audio_only: Boolean(item.audio_only ?? (item.vcodec === "none" && item.acodec !== "none")),
      video_only: Boolean(item.video_only ?? (item.acodec === "none" && item.vcodec !== "none")),
    })),
  };
}

export async function analyzeDownloadUrl(
  payload: DownloadAnalyzeRequest,
): Promise<DownloadAnalyzeResponse> {
  const response = await apiClient.post<BackendAnalyzeResponse>(
    "/downloads/analyze",
    payload,
  );
  return normalizeAnalyzeResponse(response.data);
}

export async function createDownloadJob(
  payload: CreateDownloadJobRequest,
): Promise<CreatedJobResponse> {
  const response = await apiClient.post<CreatedJobResponse>(
    "/downloads/jobs",
    payload,
  );
  return response.data;
}
