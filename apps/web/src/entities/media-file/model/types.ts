export type MediaFile = {
  id: string;
  kind: string;
  original_name: string;
  stored_name: string;
  mime_type: string | null;
  extension: string | null;
  size_bytes: number;
  duration_sec: number | null;
  path: string;
  checksum_sha256: string | null;
  created_at: string;
  download_url?: string | null;
};