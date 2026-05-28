export type UserProfile = {
  id: string;
  user_id: string;
  full_name: string | null;
  company_name: string | null;
  timezone: string | null;
  locale: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
};

export type UpdateUserProfileRequest = {
  full_name?: string | null;
  company_name?: string | null;
  timezone?: string | null;
  locale?: string | null;
  avatar_url?: string | null;
};