import { apiClient } from "@/shared/api/client";

export type YoutubeCookiesStatus = {
  configured: boolean;
  exists: boolean;
  path: string | null;
  size_bytes: number | null;
};

export async function getYoutubeCookiesStatus(): Promise<YoutubeCookiesStatus> {
  const response = await apiClient.get<YoutubeCookiesStatus>("/settings/youtube-cookies");
  return response.data;
}

export async function uploadYoutubeCookies(file: File): Promise<YoutubeCookiesStatus> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<YoutubeCookiesStatus>(
    "/settings/youtube-cookies",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

export async function deleteYoutubeCookies(): Promise<YoutubeCookiesStatus> {
  const response = await apiClient.delete<YoutubeCookiesStatus>("/settings/youtube-cookies");
  return response.data;
}