import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "@/shared/auth/token";

export function saveSession(accessToken: string): void {
  setAccessToken(accessToken);
}

export function destroySession(): void {
  clearAccessToken();
}

export function getSessionToken(): string | null {
  return getAccessToken();
}