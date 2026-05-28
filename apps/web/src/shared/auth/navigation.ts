const REDIRECT_AFTER_LOGIN_KEY = "vatranscribe_redirect_after_login";

export function saveRedirectAfterLogin(path: string): void {
  sessionStorage.setItem(REDIRECT_AFTER_LOGIN_KEY, path);
}

export function consumeRedirectAfterLogin(): string | null {
  const value = sessionStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
  sessionStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
  return value;
}