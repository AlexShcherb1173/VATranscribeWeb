import { Link } from "react-router-dom";

import { StartTranscriptionButton } from "@/features/files/ui/StartTranscriptionButton";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import { useI18n } from "@/shared/i18n";
import { Card } from "@/shared/ui/Card";
import { EmptyState } from "@/shared/ui/EmptyState";

type UploadQueueProps = {
  items: UploadQueueItem[];
  title?: string;
};

function statusColor(status: UploadQueueItem["status"]): string {
  switch (status) {
    case "uploading":
      return "bg-blue-500";
    case "succeeded":
      return "bg-emerald-500";
    case "failed":
      return "bg-rose-500";
    default:
      return "bg-slate-600";
  }
}

function formatStatus(status: UploadQueueItem["status"], t: ReturnType<typeof useI18n>["t"]): string {
  switch (status) {
    case "idle":
      return t.common.ready;
    case "uploading":
      return t.uploads.uploadingLabel;
    case "succeeded":
      return t.uploads.succeeded;
    case "failed":
      return t.uploads.failed;
    default:
      return String(status);
  }
}

export function UploadQueue({ items, title }: UploadQueueProps) {
  const { t } = useI18n();

  if (!items.length) {
    return (
      <EmptyState
        title={t.uploads.queueEmptyTitle}
        description={t.uploads.queueEmptyDescription}
      />
    );
  }

  return (
    <Card className="p-5">
      <div className="mb-4 text-lg font-medium text-white">
        {title || t.uploads.queueTitle}
      </div>

      <div className="space-y-4">
        {items.map((item) => {
          const isReady = item.status === "succeeded" && item.uploadedMediaAssetId;

          return (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-white">
                    {item.file.name}
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    {(item.file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>

                <div className="text-xs text-slate-300">
                  {formatStatus(item.status, t)}
                </div>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full transition-all ${statusColor(item.status)}`}
                  style={{ width: `${item.progress}%` }}
                />
              </div>

              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs">
                <span className="text-slate-400">{item.progress}%</span>

                {item.uploadedMediaAssetId ? (
                  <span className="text-emerald-300">
                    {t.uploads.mediaAssetId}: {item.uploadedMediaAssetId}
                  </span>
                ) : null}

                {item.errorMessage ? (
                  <span className="text-rose-300">{item.errorMessage}</span>
                ) : null}
              </div>

              {isReady ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link
                    to={`/app/files?fileId=${item.uploadedMediaAssetId}`}
                    className="rounded-xl bg-cyan-500 px-3 py-2 text-xs font-medium text-slate-950 transition hover:bg-cyan-400"
                  >
                    {t.uploads.workWithFile}
                  </Link>

                  <StartTranscriptionButton mediaAssetId={item.uploadedMediaAssetId!} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </Card>
  );
}