const PENDING_START_URL_KEY = "vatranscribe_pending_start_url";

export function savePendingStartUrl(url: string): void {
  const normalized = url.trim();

  if (!normalized) {
    return;
  }

  sessionStorage.setItem(PENDING_START_URL_KEY, normalized);
}

export function getPendingStartUrl(): string {
  return sessionStorage.getItem(PENDING_START_URL_KEY) || "";
}

export function clearPendingStartUrl(): void {
  sessionStorage.removeItem(PENDING_START_URL_KEY);
}