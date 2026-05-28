import type { ExportArtifact, Transcript } from "@/entities/transcript/model/types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

function getAuthToken(): string | null {
  return (
    localStorage.getItem("vatranscribe_access_token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token")
  );
}

function authHeaders(): HeadersInit {
  const token = getAuthToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    return payload.detail || payload.message || response.statusText;
  } catch {
    return response.statusText;
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function getTranscripts(): Promise<Transcript[]> {
  return requestJson<Transcript[]>("/transcripts");
}

export async function getTranscript(transcriptId: string): Promise<Transcript> {
  return requestJson<Transcript>(`/transcripts/${transcriptId}`);
}

export async function deleteTranscript(transcriptId: string): Promise<void> {
  await requestJson(`/transcripts/${transcriptId}`, {
    method: "DELETE",
  });
}

export async function downloadExportArtifact(artifact: ExportArtifact): Promise<Blob> {
  const response = await fetch(
    buildUrl(artifact.download_url || `/transcripts/export-artifacts/${artifact.id}/download`),
    {
      headers: authHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.blob();
}

export async function deleteExportArtifact(artifactId: string): Promise<void> {
  await requestJson(`/transcripts/export-artifacts/${artifactId}`, {
    method: "DELETE",
  });
}

export function saveBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}

export function getExportArtifactFileName(
  artifact: ExportArtifact,
  sourceName?: string | null,
): string {
  const ext = artifact.format?.toLowerCase() || "txt";
  const baseName = (sourceName || "transcript")
    .replace(/\.[a-z0-9]{1,8}$/i, "")
    .replace(/[^\p{L}\p{N}_\- .]+/gu, "")
    .trim();

  return `${baseName || artifact.transcript_id}.${ext}`;
}

export type CreateTranscriptionJobPayload = {
  media_asset_id: string;
  model_name?: string | null;
  language?: string | null;
  export_formats?: Array<"txt" | "srt" | "vtt" | "json">;
  transcription_scheme?: string | null;
  content_profile?: string | null;
  generate_summary?: boolean;
  generate_content_pack?: boolean;
};

export async function createTranscriptionJob(
  payload: CreateTranscriptionJobPayload,
) {
  return requestJson("/transcriptions/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
