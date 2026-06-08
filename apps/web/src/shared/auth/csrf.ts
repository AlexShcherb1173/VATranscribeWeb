const CSRF_COOKIE_NAME = "vatranscribe_csrf_token";
export const CSRF_HEADER_NAME = "X-CSRF-Token";

export function getCsrfToken(): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [rawName, ...rawValue] = cookie.trim().split("=");
    if (rawName === CSRF_COOKIE_NAME) {
      return decodeURIComponent(rawValue.join("="));
    }
  }

  return null;
}
