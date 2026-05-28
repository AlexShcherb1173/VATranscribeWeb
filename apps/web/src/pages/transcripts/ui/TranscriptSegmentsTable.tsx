import type { TranscriptSegment } from "@/entities/transcript/model/types";

function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds || 0));
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

export function TranscriptSegmentsTable({
  segments = [],
}: {
  segments?: TranscriptSegment[];
}) {
  if (!segments.length) {
    return null;
  }

  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Сегменты</h2>

      <div className="max-h-[360px] overflow-auto">
        <table className="w-full text-sm">
          <tbody>
            {segments.map((segment) => (
              <tr key={segment.id} className="border-t border-slate-800">
                <td className="w-28 px-3 py-3 text-xs text-slate-500">
                  {formatTime(segment.start_sec)} — {formatTime(segment.end_sec)}
                </td>

                <td className="px-3 py-3 text-slate-100">
                  {segment.text}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
