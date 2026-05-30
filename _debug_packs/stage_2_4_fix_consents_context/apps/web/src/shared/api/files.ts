import { apiClient } from "@/shared/api/client";
import type { MediaFile } from "@/entities/media-file/model/types";

export async function getMediaFiles(): Promise<MediaFile[]> {
  const response = await apiClient.get<MediaFile[]>("/media-assets");
  return response.data;
}

export async function deleteMediaFile(mediaAssetId: string): Promise<void> {
  await apiClient.delete(`/media-assets/${mediaAssetId}`);
}

export async function downloadMediaFile(mediaAssetId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/media-assets/${mediaAssetId}/download`, {
    responseType: "blob",
  });

  return response.data;
}

export function saveBlob(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
}
