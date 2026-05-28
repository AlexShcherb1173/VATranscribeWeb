import { apiClient } from "@/shared/api/client";
import type { MediaFile } from "@/entities/media-file/model/types";

export async function uploadMediaFile(
  file: File,
  onProgress?: (progress: number) => void,
): Promise<MediaFile> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<MediaFile>("/uploads", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) {
        return;
      }

      const progress = Math.round((event.loaded * 100) / event.total);
      onProgress(progress);
    },
  });

  return response.data;
}