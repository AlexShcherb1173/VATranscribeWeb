import { apiClient } from "@/shared/api/client";
import type {
  CurrentUser,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from "@/features/auth/model/types";

export async function registerUser(
  payload: RegisterRequest,
): Promise<CurrentUser> {
  const response = await apiClient.post<CurrentUser>("/auth/register", payload);
  return response.data;
}

export async function loginUser(
  payload: LoginRequest,
): Promise<TokenResponse> {
  try {
    const response = await apiClient.post<TokenResponse>("/auth/login", payload);
    return response.data;
  } catch (error: any) {
    const status = error?.response?.status;

    if (![400, 415, 422].includes(status)) {
      throw error;
    }

    const formData = new URLSearchParams();
    formData.set("username", payload.email);
    formData.set("password", payload.password);

    const response = await apiClient.post<TokenResponse>("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    return response.data;
  }
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>("/auth/me");
  return response.data;
}