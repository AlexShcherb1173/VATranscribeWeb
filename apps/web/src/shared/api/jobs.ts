import { apiClient } from "@/shared/api/client";
import type { Job, JobActionResponse, JobLog } from "@/entities/job/model/types";

export type GetJobsParams = {
  status?: string;
  type?: string;
};

export async function getJobs(_params?: GetJobsParams): Promise<Job[]> {
  const response = await apiClient.get<Job[]>("/jobs");
  return response.data;
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await apiClient.get<Job>(`/jobs/${jobId}`);
  return response.data;
}

export async function getJobLogs(jobId: string): Promise<JobLog[]> {
  const response = await apiClient.get<JobLog[]>(`/jobs/${jobId}/logs`);
  return response.data;
}

export async function retryJob(jobId: string): Promise<JobActionResponse> {
  const response = await apiClient.post<JobActionResponse>(`/jobs/${jobId}/retry`);
  return response.data;
}

export async function cancelJob(jobId: string): Promise<JobActionResponse> {
  const response = await apiClient.post<JobActionResponse>(`/jobs/${jobId}/cancel`);
  return response.data;
}