import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type SetStateAction,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { uploadMediaFile } from "@/features/uploads/api/uploads";
import type { UploadQueueItem } from "@/features/uploads/model/types";
import type { UserQuota } from "@/entities/quota/model/types";
import { apiClient } from "@/shared/api/client";
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

const BYTE_UNITS = ["B", "KB", "MB", "GB", "TB"] as const;

function formatBytes(bytes: number, language: "en" | "ru"): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return `0 ${BYTE_UNITS[0]}`;
  }

  const unitIndex = Math.min(
    BYTE_UNITS.length - 1,
    Math.floor(Math.log(bytes) / Math.log(1024)),
  );
  const value = bytes / 1024 ** unitIndex;
  const fractionDigits = unitIndex >= 3 ? 1 : 0;

  return `${value.toLocaleString(language === "ru" ? "ru-RU" : "en-US", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  })} ${BYTE_UNITS[unitIndex]}`;
}

async function getMyQuota(): Promise<UserQuota> {
  const response = await apiClient.get<UserQuota>("/quota/me");
  return response.data;
}

function buildStorageQuotaMessage(params: {
  language: "en" | "ru";
  limitBytes: number;
  usedBytes: number;
  fileBytes: number;
  reservedBytes: number;
}): string {
  const { language, limitBytes, usedBytes, fileBytes, reservedBytes } = params;
  const effectiveUsedBytes = usedBytes + reservedBytes;
  const availableBytes = Math.max(0, limitBytes - effectiveUsedBytes);

  const limit = formatBytes(limitBytes, language);
  const used = formatBytes(effectiveUsedBytes, language);
  const file = formatBytes(fileBytes, language);
  const available = formatBytes(availableBytes, language);

  if (language === "ru") {
    return `Недостаточно места. Ваш лимит: ${limit}, занято: ${used}, файл: ${file}. Доступно: ${available}.`;
  }

  return `Not enough storage. Your limit: ${limit}, used: ${used}, file: ${file}. Available: ${available}.`;
}

function isActiveUploadItem(item: UploadQueueItem): boolean {
  return item.status === "idle" || item.status === "uploading";
}


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
  const { language, t } = useI18n();
  const queryClient = useQueryClient();

  const [queue, setQueueState] = useState<UploadQueueItem[]>([]);
  const queueRef = useRef<UploadQueueItem[]>([]);
  const uploadRunRef = useRef(Promise.resolve());

  const setQueue = useCallback((updater: SetStateAction<UploadQueueItem[]>) => {
    setQueueState((prev) => {
      const next = typeof updater === "function"
        ? (updater as (current: UploadQueueItem[]) => UploadQueueItem[])(prev)
        : updater;

      queueRef.current = next;
      return next;
    });
  }, []);

  const uploadFiles = useCallback(
    async (files: File[], options: UploadFilesOptions = {}) => {
      if (!files.length) {
        return null;
      }

      const suppressToasts = Boolean(options.suppressToasts);
      const selectedItems = files.map(createQueueItem);

      let uploadableItems = selectedItems;
      let rejectedItems: UploadQueueItem[] = [];

      try {
        const quota = await queryClient.fetchQuery({
          queryKey: ["quota", "me"],
          queryFn: getMyQuota,
          staleTime: 0,
        });

        let reservedBytes = queueRef.current
          .filter(isActiveUploadItem)
          .reduce((sum, item) => sum + item.file.size, 0);

        uploadableItems = [];
        rejectedItems = [];

        for (const item of selectedItems) {
          const effectiveUsedBytes = quota.storage_bytes_used + reservedBytes;
          const availableBytes = Math.max(0, quota.storage_bytes_limit - effectiveUsedBytes);

          if (item.file.size > availableBytes) {
            rejectedItems.push({
              ...item,
              status: "failed",
              progress: 0,
              errorMessage: buildStorageQuotaMessage({
                language,
                limitBytes: quota.storage_bytes_limit,
                usedBytes: quota.storage_bytes_used,
                fileBytes: item.file.size,
                reservedBytes,
              }),
            });
            continue;
          }

          uploadableItems.push(item);
          reservedBytes += item.file.size;
        }
      } catch {
        // If quota cannot be fetched, do not block upload here.
        // The backend will still enforce quota and return a precise error.
        uploadableItems = selectedItems;
        rejectedItems = [];
      }

      if (rejectedItems.length) {
        setQueue((prev) => [...rejectedItems, ...prev]);

        if (!suppressToasts) {
          const firstMessage = rejectedItems[0]?.errorMessage ?? t.uploads.uploadFailedTitle;
          toastError(t.uploads.uploadFailedTitle, firstMessage);
        }
      }

      if (!uploadableItems.length) {
        return null;
      }

      setQueue((prev) => [...uploadableItems, ...prev]);
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });

      if (!suppressToasts) {
        toastInfo(
          t.uploads.uploadStartedTitle,
          `${uploadableItems.length} ${t.uploads.uploadStartedDescription}`,
        );
      }

      let firstUploadedMediaAssetId: string | null = null;

      const run = async () => {
        for (const item of uploadableItems) {
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
        await queryClient.invalidateQueries({ queryKey: ["jobs"] });

        return firstUploadedMediaAssetId;
      };

      const chainedRun = uploadRunRef.current.then(run, run);
      uploadRunRef.current = chainedRun.then(
        () => undefined,
        () => undefined,
      );

      return chainedRun;
    },
    [language, queryClient, setQueue, t],
  );

  const clearSucceeded = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status !== "succeeded"));
  }, [setQueue]);

  const clearFailed = useCallback(() => {
    setQueue((prev) => prev.filter((item) => item.status !== "failed"));
  }, [setQueue]);

  const clearCompleted = useCallback(() => {
    setQueue((prev) =>
      prev.filter((item) => item.status === "idle" || item.status === "uploading"),
    );
  }, [setQueue]);

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
