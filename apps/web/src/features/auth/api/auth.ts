import { apiClient } from "@/shared/api/client";
import type {
  CurrentUser,
  LegalDocumentAcceptance,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from "@/features/auth/model/types";

const REQUIRED_LEGAL_ACCEPTANCES: LegalDocumentAcceptance[] = [
  { document_type: "terms", document_version: "1.0", accepted: true },
  { document_type: "privacy", document_version: "1.0", accepted: true },
  { document_type: "personal_data", document_version: "1.0", accepted: true },
];

function normalizeRegisterPayload(payload: RegisterRequest): RegisterRequest {
  const acceptedLegalDocuments =
    payload.accepted_legal_documents?.length > 0
      ? payload.accepted_legal_documents
      : REQUIRED_LEGAL_ACCEPTANCES;

  return {
    ...payload,
    email: payload.email.trim(),
    accepted_legal_documents: acceptedLegalDocuments,
  };
}

export async function registerUser(
  payload: RegisterRequest,
): Promise<CurrentUser> {
  const response = await apiClient.post<CurrentUser>(
    "/auth/register",
    normalizeRegisterPayload(payload),
  );

  return response.data;
}

export async function loginUser(
  payload: LoginRequest,
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

export async function refreshSession(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh");
  return response.data;
}

export async function logoutUser(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>("/auth/me");
  return response.data;
}
