import { apiClient } from "@/shared/api/client";
import type {
  UpdateUserProfileRequest,
  UserProfile,
} from "@/entities/profile/model/types";

export async function getMyProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/profile");
  return response.data;
}

export async function updateMyProfile(
  payload: UpdateUserProfileRequest,
): Promise<UserProfile> {
  const response = await apiClient.patch<UserProfile>("/profile", payload);
  return response.data;
}