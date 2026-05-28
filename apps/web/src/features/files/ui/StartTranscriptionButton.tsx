import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { createTranscriptionJob } from "@/shared/api/transcriptions";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { toastError, toastSuccess } from "@/shared/ui/toast";

type StartTranscriptionButtonProps = {
  mediaAssetId: string;
  className?: string;
  label?: string;
  navigateToJobsOnSuccess?: boolean;
  onSuccess?: (job: any) => void;
  modelName?: string;
  language?: string | null;
};

export function StartTranscriptionButton({
  mediaAssetId,
  className,
  label,
  navigateToJobsOnSuccess = true,
  onSuccess,
  modelName = "medium",
  language = "ru",
}: StartTranscriptionButtonProps) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      createTranscriptionJob({
        media_asset_id: mediaAssetId,
        model_name: modelName,
        language,
        export_formats: ["txt", "srt", "vtt", "json"],
      }),
    onSuccess: async (data: any) => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["quota", "me"] });

      toastSuccess(
        t.common.success,
        data?.id
          ? `${t.jobs.created}: ${data.id}`
          : t.jobs.created,
      );

      onSuccess?.(data);

      if (navigateToJobsOnSuccess) {
        navigate("/app/jobs");
      }
    },
    onError: (error: any) => {
      toastError(t.common.failed, extractErrorMessage(error, t));
    },
  });

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        mutation.mutate();
      }}
      disabled={mutation.isPending || !mediaAssetId}
      className={
        className ??
        "rounded-xl bg-cyan-500 px-3 py-2 text-xs font-medium text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
      }
    >
      {mutation.isPending ? t.common.processing : label ?? t.files.transcribe}
    </button>
  );
}
