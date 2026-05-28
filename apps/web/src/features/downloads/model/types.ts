export type DownloadFormatInfo = {
  format_id: string | null;
  ext: string | null;
  format_note: string | null;
  resolution: string | null;
  height: number | null;
  width: number | null;
  fps: number | null;
  vcodec: string | null;
  acodec: string | null;
  filesize: number | null;
  tbr: number | null;
  audio_only: boolean;
  video_only: boolean;
};

export type DownloadAnalyzeResponse = {
  title: string | null;
  duration: number | null;
  webpage_url: string;
  extractor: string | null;
  formats: DownloadFormatInfo[];
};

export type DownloadAnalyzeRequest = {
  url: string;
};

export type DownloadMode =
  | "audio_mp3"
  | "video_mp4_compatible"
  | "video_mp4_fast"
  | "selected_original"
  | "best_available";

export type CreateDownloadJobRequest = {
  url: string;
  download_mode: DownloadMode;
  requested_format: string;
  requested_file_name: string;
  mp4_mode: "fast" | "compatible";
  selected_format_id?: string | null;
  selected_video_format_id?: string | null;
  selected_audio_format_id?: string | null;
};

export type CreatedJobResponse = {
  id: string;
  type: string;
  status: string;
  title: string | null;
  requested_format: string | null;
  requested_file_name: string | null;
  mp4_mode: string | null;
};