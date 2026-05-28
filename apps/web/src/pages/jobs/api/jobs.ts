import { apiClient } from "@/shared/api/client";

export type JobActionResponse = {
  ok: boolean;
  job_id: string;
  status: string;
  detail: string;
};

export type DeleteJobResponse = {
  ok: boolean;
  job_id: string;
  deleted_media: boolean;
  deleted_media_asset_id: string;
};

export async function restartJob(jobId: string): Promise<JobActionResponse> {
  const response = await apiClient.post<JobActionResponse>(
    `/jobs/${jobId}/restart`,
  );

  return response.data;
}

export async function stopJob(jobId: string): Promise<JobActionResponse> {
  const response = await apiClient.post<JobActionResponse>(
    `/jobs/${jobId}/stop`,
  );

  return response.data;
}

export async function deleteJob(
  jobId: string,
  deleteMedia = false,
): Promise<DeleteJobResponse> {
  const response = await apiClient.delete<DeleteJobResponse>(`/jobs/${jobId}`, {
    params: {
      delete_media: deleteMedia,
    },
  });

  return response.data;
}
