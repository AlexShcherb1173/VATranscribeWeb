export type ToastVariant = "success" | "error" | "info";

export type ToastItem = {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
};

let emitter: ((toast: Omit<ToastItem, "id">) => void) | null = null;

export function bindToastEmitter(
  nextEmitter: ((toast: Omit<ToastItem, "id">) => void) | null,
) {
  emitter = nextEmitter;
}

export function showToast(toast: Omit<ToastItem, "id">) {
  emitter?.(toast);
}

export function toastSuccess(title: string, description?: string) {
  showToast({ title, description, variant: "success" });
}

export function toastError(title: string, description?: string) {
  showToast({ title, description, variant: "error" });
}

export function toastInfo(title: string, description?: string) {
  showToast({ title, description, variant: "info" });
}