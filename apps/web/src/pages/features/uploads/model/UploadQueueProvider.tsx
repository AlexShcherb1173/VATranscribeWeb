import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { uploadMediaFile } from "@/features/uploads/api/uploads";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { toastError, toastInfo, toastSuccess } from "@/shared/ui/toast";

type UploadQueueContextValue = {
  queue: UploadQueueItem[];
  isUploading: boolean;
  uploadFiles: (files: File[], options?: UploadFilesOptions) => Promise<string | null>;
  clearSucceeded: () => void;
  clearFailed: () => void;
  clearCompleted: () => void;
};

type UploadFilesOptions = {
  suppressToasts?: boolean;
};

const UploadQueueContext = createContext<UploadQueueContextValue | null>(null);

function createQueueItem(file: File): UploadQueueItem {
  return {
    id: `${file.name}-${file.size}-${crypto.randomUUID()}`,
    file,
    progress: 0,
    status: "idle",
    errorMessage: null,
    uploadedMediaAssetId: null,
    uploadedStoredName: null,
  };
}

export function UploadQueueProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const uploadRunRef = useRef(Promise.resolve());

  const uploadFiles = useCallback(
    async (files: File[], options: UploadFilesOptions = {}) => {
      if (!files.length) {
        return null;
      }

      const suppressToasts = Boolean(options.suppressToasts);
      const initialItems = files.map(createQueueItem);

      setQueue((prev) => [...initialItems, ...prev]);

      if (!suppressToasts) {
        toastInfo(
          t.uploads.uploadStartedTitle,
          `${files.length} ${t.uploads.uploadStartedDescription}`,
        );
      }

      let firstUploadedMediaAssetId: string | null = null;

      const run = async () => {
        for (const item of initialItems) {
          setQueue((prev) =>
            prev.map((queueItem) =>
              queueItem.id === item.id
                ? {
                    ...queueItem,
                    status: "uploading",
                    progress: 0,
                    errorMessage: null,
                  }
                : queueItem,
            ),
          );

          try {
            const uploaded = await uploadMediaFile(item.file, (progress) => {
              setQueue((prev) =>
                prev.map((queueItem) =>
                  queueItem.id === item.id ? { ...queueItem, progress } : queueItem,
                ),
              );
            });

            if (!firstUploadedMediaAssetId) {
              firstUploadedMediaAssetId = uploaded.id;
            }

            setQueue((prev) =>
              prev.map((queueItem) =>
                queueItem.id === item.id
                  ? {
                      ...queueItem,
                      progress: 100,
                      status: "succeeded",
                      uploadedMediaAssetId: uploaded.id,
                      uploadedStoredName: uploaded.stored_name,
                    }
                  : queueItem,
              ),
            );

            if (!suppressToasts) {
              toastSuccess(
                t.uploads.uploadCompletedTitle,
                `${uploaded.stored_name} ${t.uploads.uploadCompletedDescription}`,
              );
            }
          } catch (error: any) {
            const message = extractErrorMessage(error);

            setQueue((prev) =>
              prev.map((queueItem) =>
                queueItem.id === item.id
                  ? {
                      ...queueItem,
                      status: "failed",
                      progress: Math.max(0, Math.min(100, Number(queueItem.progress ?? 0))),
                      errorMessage: message,
                    }
                  : queueItem,
              ),
            );

            if (!suppressToasts) {
              toastError(t.uploads.uploadFailedTitle, message);
            }
          }
        }

        await queryClient.invalidateQueries({ queryKey: ["media-files"] });
        await queryClient.invalidateQueries({ queryKey: ["quota", "me"] });

        return firstUploadedMediaAssetId;
      };

      const chainedRun = uploadRunRef.current.then(run, run);
      uploadRunRef.current = chainedRun.then(
        () => undefined,
        () => undefined,
      );

      return chainedRun;
    },
    [queryClient, t],
  );

  const clearSucceeded = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status !== "succeeded"));
  }, []);

  const clearFailed = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status !== "failed"));
  }, []);

  const clearCompleted = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status === "idle" || item.status === "uploading"));
  }, []);

  const value = useMemo<UploadQueueContextValue>(
    () => ({
      queue,
      isUploading: queue.some((item) => item.status === "idle" || item.status === "uploading"),
      uploadFiles,
      clearSucceeded,
      clearFailed,
      clearCompleted,
    }),
    [clearCompleted, clearFailed, clearSucceeded, queue, uploadFiles],
  );

  return <UploadQueueContext.Provider value={value}>{children}</UploadQueueContext.Provider>;
}

export function useUploadQueue() {
  const context = useContext(UploadQueueContext);

  if (!context) {
    throw new Error("useUploadQueue must be used inside UploadQueueProvider");
  }

  return context;
}
