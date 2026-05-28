import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateMyProfile } from "@/features/profile/api/profile";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { toastError, toastSuccess } from "@/shared/ui/toast";

export function useUpdateProfileMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateMyProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
      toastSuccess("Profile updated", "Your account settings were saved.");
    },
    onError: (error: any) => {
      toastError("Profile update failed", extractErrorMessage(error));
    },
  });
}