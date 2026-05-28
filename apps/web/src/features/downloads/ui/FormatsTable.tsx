import type { DownloadFormatInfo } from "@/features/downloads/model/types";
import { Card } from "@/shared/ui/Card";
import { EmptyState } from "@/shared/ui/EmptyState";

type FormatsTableProps = {
  formats: DownloadFormatInfo[];
  selectedFormatId: string;
  selectedVideoFormatId: string;
  selectedAudioFormatId: string;
  onSelectFormat: (value: string) => void;
  onSelectVideoFormat: (value: string) => void;
  onSelectAudioFormat: (value: string) => void;
};

function formatFilesize(bytes: number | null): string {
  if (!bytes || bytes <= 0) {
    return "—";
  }

  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function formatLabel(format: DownloadFormatInfo): string {
  return [
    format.format_id || "—",
    format.ext || "—",
    format.resolution || format.format_note || "—",
    format.vcodec && format.vcodec !== "none" ? `V: ${format.vcodec}` : null,
    format.acodec && format.acodec !== "none" ? `A: ${format.acodec}` : null,
    format.tbr ? `${format.tbr} kbps` : null,
    formatFilesize(format.filesize),
  ]
    .filter(Boolean)
    .join(" · ");
}

export function FormatsTable({
  formats,
  selectedFormatId,
  selectedVideoFormatId,
  selectedAudioFormatId,
  onSelectFormat,
  onSelectVideoFormat,
  onSelectAudioFormat,
}: FormatsTableProps) {
  if (!formats.length) {
    return (
      <EmptyState
        title="Форматы не найдены"
        description="Сначала проанализируй ссылку."
      />
    );
  }

  const videoFormats = formats.filter(
    (item) => !item.audio_only && item.vcodec !== "none",
  );

  const audioFormats = formats.filter(
    (item) => item.audio_only || item.vcodec === "none" || item.acodec !== "none",
  );

  return (
    <div className="grid gap-4">
      <Card className="overflow-hidden">
        <div className="border-b border-slate-800 px-4 py-3">
          <h3 className="text-sm font-medium text-white">
            Все доступные форматы
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Выбери один формат для режима “Selected original”.
          </p>
        </div>

        <div className="max-h-[320px] overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900/90 text-left text-slate-400">
              <tr>
                <th className="px-4 py-3">Выбор</th>
                <th className="px-4 py-3">Формат</th>
              </tr>
            </thead>

            <tbody>
              {formats.map((format) => {
                const id = format.format_id || "";

                return (
                  <tr
                    key={`all-${id}-${format.ext}-${format.resolution}`}
                    onClick={() => id && onSelectFormat(id)}
                    className={[
                      "cursor-pointer border-t border-slate-800/70 text-slate-200 transition hover:bg-cyan-400/10",
                      selectedFormatId === id ? "bg-cyan-400/10" : "",
                    ].join(" ")}
                  >
                    <td className="px-4 py-3">
                      <input
                        type="radio"
                        name="selected-format"
                        checked={selectedFormatId === id}
                        onChange={() => id && onSelectFormat(id)}
                      />
                    </td>

                    <td className="px-4 py-3">{formatLabel(format)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="overflow-hidden">
          <div className="border-b border-slate-800 px-4 py-3">
            <h3 className="text-sm font-medium text-white">Video formats</h3>
          </div>

          <div className="max-h-[360px] overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-900/90 text-left text-slate-400">
                <tr>
                  <th className="px-4 py-3">Pick</th>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Resolution</th>
                  <th className="px-4 py-3">Ext</th>
                  <th className="px-4 py-3">VCodec</th>
                  <th className="px-4 py-3">Size</th>
                </tr>
              </thead>

              <tbody>
                {videoFormats.map((format) => {
                  const id = format.format_id || "";

                  return (
                    <tr
                      key={`video-${id}-${format.ext}-${format.resolution}`}
                      onClick={() => id && onSelectVideoFormat(id)}
                      className={[
                        "cursor-pointer border-t border-slate-800/70 text-slate-200 transition hover:bg-cyan-400/10",
                        selectedVideoFormatId === id ? "bg-cyan-400/10" : "",
                      ].join(" ")}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="radio"
                          name="video-format"
                          checked={selectedVideoFormatId === id}
                          onChange={() => id && onSelectVideoFormat(id)}
                        />
                      </td>

                      <td className="px-4 py-3">{id || "—"}</td>
                      <td className="px-4 py-3">{format.resolution || "—"}</td>
                      <td className="px-4 py-3">{format.ext || "—"}</td>
                      <td className="px-4 py-3">{format.vcodec || "—"}</td>
                      <td className="px-4 py-3">{formatFilesize(format.filesize)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="overflow-hidden">
          <div className="border-b border-slate-800 px-4 py-3">
            <h3 className="text-sm font-medium text-white">Audio formats</h3>
          </div>

          <div className="max-h-[360px] overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-900/90 text-left text-slate-400">
                <tr>
                  <th className="px-4 py-3">Pick</th>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Ext</th>
                  <th className="px-4 py-3">ACodec</th>
                  <th className="px-4 py-3">Bitrate</th>
                  <th className="px-4 py-3">Size</th>
                </tr>
              </thead>

              <tbody>
                {audioFormats.map((format) => {
                  const id = format.format_id || "";

                  return (
                    <tr
                      key={`audio-${id}-${format.ext}-${format.acodec}`}
                      onClick={() => id && onSelectAudioFormat(id)}
                      className={[
                        "cursor-pointer border-t border-slate-800/70 text-slate-200 transition hover:bg-cyan-400/10",
                        selectedAudioFormatId === id ? "bg-cyan-400/10" : "",
                      ].join(" ")}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="radio"
                          name="audio-format"
                          checked={selectedAudioFormatId === id}
                          onChange={() => id && onSelectAudioFormat(id)}
                        />
                      </td>

                      <td className="px-4 py-3">{id || "—"}</td>
                      <td className="px-4 py-3">{format.ext || "—"}</td>
                      <td className="px-4 py-3">{format.acodec || "—"}</td>
                      <td className="px-4 py-3">{format.tbr ? `${format.tbr}` : "—"}</td>
                      <td className="px-4 py-3">{formatFilesize(format.filesize)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}