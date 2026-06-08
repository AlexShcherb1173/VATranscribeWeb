export type JobStatus =
  | "pending"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled";

export type JobType =
  | "download"
  | "transcribe"
  | "combined"
  | "export"
  | "upload";

export type JobMediaAsset = {
  id: string;
  kind: string;
  original_name: string;
  stored_name: string;
  mime_type: string | null;
  extension: string | null;
  size_bytes: number;
  duration_sec: number | null;
  checksum_sha256: string | null;
  created_at: string | null;
  download_url: string | null;
};

export type Job = {
  id: string;
  type: JobType;
  status: JobStatus;
  source_type: string | null;
  title: string | null;
  input_url: string | null;
  requested_format: string | null;
  requested_file_name: string | null;
  mp4_mode: string | null;
  output_media_asset_id: string | null;
  output_media_asset: JobMediaAsset | null;
  transcription_media_asset: JobMediaAsset | null;
  selected_video_format_id: string | null;
  selected_audio_format_id: string | null;
  transcription_media_asset_id: string | null;
  download_audio: boolean;
  download_video: boolean;
  transcription_model: string | null;
  transcription_language: string | null;
  transcription_profile?: string | null;
  error_message: string | null;
  progress_percent?: number | null;
  progress_stage?: string | null;
  progress_message?: string | null;
  heartbeat_at?: string | null;
  last_log_at?: string | null;
  last_log_message?: string | null;
  current_step?: string | null;
  is_stale?: boolean | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type JobLog = {
  id: string;
  job_id: string;
  level: string;
  message: string;
  created_at: string;
};

export type JobActionResponse = {
  ok: boolean;
  job_id: string;
  status: string;
  detail: string;
};
