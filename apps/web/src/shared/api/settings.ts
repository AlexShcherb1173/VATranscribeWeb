import { apiClient } from "@/shared/api/client";

export type YoutubeCookiesStatus = {
  configured: boolean;
  source_filename: string | null;
  cookie_format: string | null;
  size_bytes: number | null;
  updated_at: string | null;
};

export async function getYoutubeCookiesStatus(): Promise<YoutubeCookiesStatus> {
  const response = await apiClient.get<YoutubeCookiesStatus>("/youtube-cookies/status");
  return response.data;
}

export async function uploadYoutubeCookies(file: File): Promise<YoutubeCookiesStatus> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<YoutubeCookiesStatus>(
    "/youtube-cookies",
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
  const response = await apiClient.delete<YoutubeCookiesStatus>("/youtube-cookies");
  return response.data;
}
