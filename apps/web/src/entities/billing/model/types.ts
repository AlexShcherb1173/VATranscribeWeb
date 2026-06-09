export type BillingPeriod = "monthly" | "yearly" | string;

export type PlanCode =
  | "free"
  | "starter"
  | "pro"
  | "business"
  | "enterprise"
  | string;

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "cancelled"
  | "expired"
  | "inactive"
  | string;

export type BillingPlan = {
  id: string;
  code: PlanCode;
  name: string;
  description?: string | null;

  price_monthly: number;
  price_yearly?: number | null;
  currency: string;

  storage_bytes_limit: number;
  transcription_seconds_limit: number;
  jobs_count_limit: number;

  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type Plan = BillingPlan;
export type CurrentPlan = BillingPlan;

export type Subscription = {
  id: string;
  user_id?: string;
  plan_id?: string;
  plan_code?: PlanCode;

  status: SubscriptionStatus;
  billing_period?: BillingPeriod | null;

  current_period_start: string;
  current_period_end: string;

  started_at?: string | null;
  cancelled_at?: string | null;
  expires_at?: string | null;

  cancel_at_period_end: boolean;

  created_at?: string | null;
  updated_at?: string | null;
};

export type UserQuota = {
  id?: string;
  user_id?: string;

  plan_code?: string;
  subscription_status?: string;

  storage_bytes_used: number;
  storage_bytes_limit: number;

  transcription_seconds_used: number;
  transcription_seconds_limit: number;

  jobs_count_used: number;
  jobs_count_limit: number;

  created_at?: string | null;
  updated_at?: string | null;
};

export type Quota = UserQuota;

export type BillingUsageHistoryItem = {
  id?: string;
  user_id?: string;

  label: string;
  date: string;
  created_at?: string | null;

  storage_bytes_used: number;
  transcription_seconds_used: number;
  jobs_count_used: number;

  storage_used?: number;
  transcription_used?: number;
  jobs_used?: number;
};

export type UsageHistoryItem = BillingUsageHistoryItem;
export type UsageHistoryPoint = BillingUsageHistoryItem;

export type BillingOverviewResponse = {
  current_plan: BillingPlan;
  subscription: Subscription;
  quota: UserQuota;
  usage_history: BillingUsageHistoryItem[];
  available_plans: BillingPlan[];
};

export type BillingOverview = BillingOverviewResponse;

export type BillingUpgradeRequest = {
  plan_code: PlanCode;
  billing_period: BillingPeriod;
};

export type BillingUpgradeResponse = {
  current_plan: BillingPlan;
  subscription: Subscription;
  quota: UserQuota;
};

export type BillingState = {
  overview: BillingOverviewResponse | null;
  isLoading: boolean;
  error: string | null;
};
