type QuotaCardProps = {
  title: string;
  used: number;
  limit: number;
  unitLabel: string;
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatBytes(value: number): string {
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

function formatValue(value: number, unitLabel: string): string {
  if (unitLabel === "bytes") {
    return formatBytes(value);
  }

  return `${formatNumber(value)} ${unitLabel}`;
}

export function QuotaCard({
  title,
  used,
  limit,
  unitLabel,
}: QuotaCardProps) {
  const safeLimit = Math.max(limit, 1);
  const percent = Math.min(Math.round((used / safeLimit) * 100), 100);

  const barClass =
    percent >= 90
      ? "bg-rose-500"
      : percent >= 70
        ? "bg-amber-400"
        : "bg-cyan-500";

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="text-sm text-slate-400">{title}</div>

      <div className="mt-3 flex items-end justify-between gap-4">
        <div className="text-lg font-semibold text-white">
          {formatValue(used, unitLabel)}
        </div>
        <div className="text-xs text-slate-500">
          of {formatValue(limit, unitLabel)}
        </div>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full transition-all ${barClass}`}
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="mt-2 text-xs text-slate-400">{percent}% used</div>
    </div>
  );
}