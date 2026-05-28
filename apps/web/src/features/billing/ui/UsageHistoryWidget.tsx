import type { UsageHistoryPoint } from "@/entities/billing/model/types";

type UsageHistoryWidgetProps = {
  items: UsageHistoryPoint[];
};

function formatBytesCompact(value: number): string {
  if (!value) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

export function UsageHistoryWidget({ items }: UsageHistoryWidgetProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-5">
        <div className="text-lg font-semibold text-white">Usage history</div>
        <div className="mt-1 text-sm text-slate-400">
          Recent account consumption snapshots.
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
          >
            <div className="text-sm font-medium text-white">{item.label}</div>

            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  Storage
                </div>
                <div className="mt-1 text-sm text-slate-200">
                  {formatBytesCompact(item.storage_bytes_used)}
                </div>
              </div>

              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  Transcription
                </div>
                <div className="mt-1 text-sm text-slate-200">
                  {item.transcription_seconds_used.toLocaleString()} sec
                </div>
              </div>

              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  Jobs
                </div>
                <div className="mt-1 text-sm text-slate-200">
                  {item.jobs_count_used.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}