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

export type CreateDownloadJobRequest = {
  url: string;
  requested_format: "mp3" | "mp4";
  requested_file_name: string;
  mp4_mode: "fast" | "compatible";
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