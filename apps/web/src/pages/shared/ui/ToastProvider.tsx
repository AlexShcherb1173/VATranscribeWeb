import { PropsWithChildren, useEffect, useMemo, useState } from "react";

import { bindToastEmitter, type ToastItem } from "@/shared/ui/toast";

function variantClasses(variant: ToastItem["variant"]): string {
  if (variant === "success") {
    return "border-emerald-800 bg-emerald-950/80 text-emerald-100";
  }

  if (variant === "error") {
    return "border-rose-800 bg-rose-950/80 text-rose-100";
  }

  return "border-cyan-800 bg-slate-900 text-slate-100";
}

export function ToastProvider({ children }: PropsWithChildren) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const api = useMemo(
    () => ({
      push(toast: Omit<ToastItem, "id">) {
        const id = crypto.randomUUID();

        setItems((prev) => [...prev, { id, ...toast }]);

        window.setTimeout(() => {
          setItems((prev) => prev.filter((item) => item.id !== id));
        }, 4000);
      },
    }),
    [],
  );

  useEffect(() => {
    bindToastEmitter(api.push);
    return () => bindToastEmitter(null);
  }, [api]);

  function removeToast(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <>
      {children}

      <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-full max-w-sm flex-col gap-3">
        {items.map((item) => (
          <div
            key={item.id}
            className={[
              "pointer-events-auto rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur",
              variantClasses(item.variant),
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">{item.title}</div>
                {item.description ? (
                  <div className="mt-1 text-xs opacity-90">{item.description}</div>
                ) : null}
              </div>

              <button
                type="button"
                onClick={() => removeToast(item.id)}
                className="text-xs opacity-70 transition hover:opacity-100"
              >
                Close
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}