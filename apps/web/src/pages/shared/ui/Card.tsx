import type { PropsWithChildren } from "react";

import { cn } from "@/shared/lib/utils";

type CardProps = PropsWithChildren<{
  className?: string;
}>;

export function Card({ className, children }: CardProps) {
  return (
    <div
      className={cn(
        "min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 shadow-[0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur",
        className,
      )}
    >
      {children}
    </div>
  );
}