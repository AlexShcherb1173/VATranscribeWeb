import { useMutation, useQueryClient } from "@tanstack/react-query";

import { upgradePlan } from "@/features/billing/api/billing";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { toastError, toastSuccess } from "@/shared/ui/toast";

export function useUpgradePlanMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: upgradePlan,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["billing", "overview"] });
      toastSuccess("Plan updated", "Your billing plan has been changed.");
    },
    onError: (error: any) => {
      toastError("Upgrade failed", extractErrorMessage(error));
    },
  });
}