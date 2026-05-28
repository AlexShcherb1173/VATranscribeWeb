import { apiClient } from "@/shared/api/client";
import type { BillingOverview, BillingUpgradeResponse } from "@/entities/billing/model/types";

export async function getBillingOverview(): Promise<BillingOverview> {
  const response = await apiClient.get<BillingOverview>("/billing/overview");
  return response.data;
}

export async function upgradePlan(planCode: string): Promise<BillingUpgradeResponse> {
  const response = await apiClient.post<BillingUpgradeResponse>("/billing/upgrade", {
    plan_code: planCode,
    billing_period: "monthly",
  });
  return response.data;
}
