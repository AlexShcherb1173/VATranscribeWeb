import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useUploadQueue } from "@/features/uploads/model/UploadQueueProvider";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import { UploadDropzone } from "@/features/uploads/ui/UploadDropzone";
import { UploadQueue } from "@/features/uploads/ui/UploadQueue";
import {
  UploadResultCard,
  type UploadQueueFilter,
} from "@/features/uploads/ui/UploadResultCard";
import { useI18n } from "@/shared/i18n";

type UploaderPanelProps = {
  redirectToFilesOnUpload?: boolean;
  redirectToFilesOnSelect?: boolean;
  compact?: boolean;
  showQueue?: boolean;
  showSummary?: boolean;
  suppressToasts?: boolean;
  onQueueChange?: (items: UploadQueueItem[]) => void;
};

type UploadLocationState = {
  pendingFiles?: File[];
};

function UploadInlineProgress({ items }: { items: UploadQueueItem[] }) {
  const { t } = useI18n();

  const activeItems = useMemo(
    () =>
      items
        .filter((item) => item.status === "idle" || item.status === "uploading" || item.status === "failed")
        .slice(0, 4),
    [items],
  );

  if (!activeItems.length) {
    return null;
  }

  return (
    <div className="mt-4 grid gap-3">
      {activeItems.map((item) => {
        const progress = Math.max(0, Math.min(100, Number(item.progress ?? 0)));
        const failed = item.status === "failed";

        return (
          <div
            key={item.id}
            className={[
              "rounded-2xl border p-3 text-left",
              failed
                ? "border-rose-500/40 bg-rose-500/10"
                : "border-cyan-300/25 bg-cyan-400/5",
            ].join(" ")}
          >
            <div className="flex min-w-0 items-center justify-between gap-3 text-xs">
              <div className="min-w-0 truncate font-semibold text-white" title={item.file.name}>
                {item.file.name}
              </div>

              <div className={failed ? "shrink-0 text-rose-200" : "shrink-0 text-cyan-100"}>
                {failed ? t.uploads.failed : `${progress}%`}
              </div>
            </div>

            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
              <div
                className={[
                  "h-full rounded-full transition-all",
                  failed ? "bg-rose-400" : "bg-cyan-400",
                ].join(" ")}
                style={{ width: `${progress}%` }}
              />
            </div>

            {item.errorMessage ? (
              <div className="mt-2 break-words text-xs text-rose-200">
                {item.errorMessage}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export function UploaderPanel({
  redirectToFilesOnUpload = false,
  redirectToFilesOnSelect = false,
  compact = false,
  showQueue = true,
  showSummary = true,
  suppressToasts = false,
  onQueueChange,
}: UploaderPanelProps) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const { queue, isUploading, uploadFiles } = useUploadQueue();
  const [queueFilter, setQueueFilter] = useState<UploadQueueFilter>("all");

  useEffect(() => {
    onQueueChange?.(queue);
  }, [onQueueChange, queue]);

  useEffect(() => {
    const state = location.state as UploadLocationState | null;
    const pendingFiles = state?.pendingFiles;

    if (pendingFiles?.length) {
      void uploadFiles(pendingFiles, { suppressToasts });

      navigate(location.pathname + location.search, {
        replace: true,
        state: null,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFilesSelected(files: File[]) {
    if (!files.length) {
      return;
    }

    if (redirectToFilesOnSelect) {
      navigate("/app/files", {
        state: {
          pendingFiles: files,
        },
      });

      return;
    }

    void uploadFiles(files, { suppressToasts }).then((firstUploadedMediaAssetId) => {
      if (redirectToFilesOnUpload && firstUploadedMediaAssetId) {
        navigate(`/app/files?fileId=${firstUploadedMediaAssetId}`, {
          replace: true,
        });
      }
    });
  }

  const filteredQueue =
    queueFilter === "all"
      ? queue
      : queue.filter((item) => item.status === queueFilter);

  return (
    <div className={compact ? "grid gap-3" : "grid gap-6"}>
      <div>
        <UploadDropzone
          compact={compact}
          isBusy={isUploading}
          onFilesSelected={handleFilesSelected}
        />

        {!compact ? <UploadInlineProgress items={queue} /> : null}
      </div>

      {!compact ? (
        <>
          {showSummary ? (
            <UploadResultCard
              items={queue}
              activeFilter={queueFilter}
              onFilterChange={setQueueFilter}
            />
          ) : null}

          {showQueue ? (
            <UploadQueue
              items={filteredQueue}
              title={
                queueFilter === "all"
                  ? t.uploads.queueTitle
                  : `${t.uploads.queueTitle}: ${
                      queueFilter === "succeeded"
                        ? t.uploads.succeeded
                        : queueFilter === "uploading"
                          ? t.uploads.uploadingLabel
                          : t.uploads.failed
                    }`
              }
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
