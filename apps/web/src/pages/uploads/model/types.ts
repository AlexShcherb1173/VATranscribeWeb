export type UploadQueueItemStatus =
  | "idle"
  | "uploading"
  | "succeeded"
  | "failed";

export type UploadQueueItem = {
  id: string;
  file: File;
  progress: number;
  status: UploadQueueItemStatus;
  errorMessage: string | null;
  uploadedMediaAssetId: string | null;
  uploadedStoredName: string | null;
};