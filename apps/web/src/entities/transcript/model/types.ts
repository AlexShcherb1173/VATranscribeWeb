import type { MediaFile } from "@/entities/media-file/model/types";

export type TranscriptSegment = {
  id: string;
  transcript_id: string;
  start_sec: number;
  end_sec: number;
  text: string;
  speaker_label?: string | null;
  confidence?: string | null;
  order_index?: number | null;
};

export type ExportArtifact = {
  id: string;
  transcript_id: string;
  format: string;
  size_bytes: number;
  created_at: string;
  download_url?: string | null;
};

export type Transcript = {
  id: string;
  job_id: string;
  media_asset_id: string;
  media_asset?: MediaFile | null;
  source_file_name?: string | null;
  display_name?: string | null;
  language: string;
  model_name: string;
  engine: string;
  full_text: string;
  duration_sec?: number | null;
  segments_count?: number | null;
  coverage_sec?: number | null;
  coverage_ratio?: string | number | null;
  quality_status?: "good" | "partial" | "low_quality" | "hallucinated" | "empty" | string | null;
  quality_warning?: string | null;
  created_at: string;
  segments?: TranscriptSegment[];
  exports?: ExportArtifact[];
};
