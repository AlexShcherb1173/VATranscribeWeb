export type UserQuota = {
  id: string;
  user_id: string;

  storage_bytes_used: number;
  transcription_seconds_used: number;
  jobs_count_used: number;

  storage_bytes_limit: number;
  transcription_seconds_limit: number;
  jobs_count_limit: number;

  created_at: string;
  updated_at: string;
};