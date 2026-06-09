import { useEffect, useState, type MouseEvent } from "react";

import type { ExportArtifact, Transcript } from "@/entities/transcript/model/types";
import { formatBytes } from "@/shared/lib/format";

type ContextMenuState = {
  artifact: ExportArtifact;
  x: number;
  y: number;
};

type TranscriptExportsProps = {
  transcript: Transcript;
  exportsList?: ExportArtifact[];
  onDownloadExport: (transcript: Transcript, artifact: ExportArtifact) => void;
  onDeleteExport: (artifact: ExportArtifact) => void;
};

export function TranscriptExports({
  transcript,
  exportsList,
  onDownloadExport,
  onDeleteExport,
}: TranscriptExportsProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const exports = exportsList || transcript.exports || [];

  useEffect(() => {
    function closeMenu() {
      setContextMenu(null);
    }

    window.addEventListener("click", closeMenu);
    window.addEventListener("keydown", closeMenu);

    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("keydown", closeMenu);
    };
  }, []);

  function handleContextMenu(event: MouseEvent, artifact: ExportArtifact) {
    event.preventDefault();
    setContextMenu({
      artifact,
      x: event.clientX,
      y: event.clientY,
    });
  }

  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-white">Файлы</h2>
          <p className="mt-1 text-xs text-slate-500">
            Скачать созданные файлы результата
          </p>
        </div>

        <span className="shrink-0 rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
          {exports.length} элемент(ов)
        </span>
      </div>

      <div className="space-y-3">
        {exports.map((artifact) => (
          <div
            key={artifact.id}
            onContextMenu={(event) => handleContextMenu(event, artifact)}
            className="min-w-0 rounded-2xl border border-slate-800 bg-slate-950/50 p-4"
            title="ПКМ — открыть действия"
          >
            <div className="flex min-w-0 items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="rounded-lg bg-cyan-400/10 px-2 py-1 text-xs font-semibold uppercase text-cyan-200">
                    {artifact.format}
                  </span>

                  <span className="text-xs text-slate-400">
                    {formatBytes(artifact.size_bytes)}
                  </span>
                </div>

                <div className="mt-2 min-w-0 break-words text-sm font-semibold text-white [overflow-wrap:anywhere]">
                  {(artifact.format || "file").toUpperCase()}
                </div>

                <div className="mt-1 truncate text-xs text-slate-600">
                  ID: {artifact.id}
                </div>
              </div>

              <button
                type="button"
                onClick={() => onDownloadExport(transcript, artifact)}
                className="shrink-0 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-semibold uppercase text-slate-950 transition hover:bg-cyan-400"
              >
                Скачать
              </button>
            </div>
          </div>
        ))}

        {!exports.length ? (
          <div className="rounded-2xl border border-dashed border-slate-800 p-6 text-sm text-slate-400">
            Файлы результата пока не созданы.
          </div>
        ) : null}
      </div>

      {contextMenu ? (
        <div
          className="fixed z-50 min-w-48 rounded-2xl border border-slate-700 bg-slate-950 p-2 shadow-2xl"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            onClick={() => {
              onDownloadExport(transcript, contextMenu.artifact);
              setContextMenu(null);
            }}
            className="w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-cyan-200 transition hover:bg-cyan-400/10"
          >
            Скачать
          </button>

          <button
            type="button"
            onClick={() => {
              onDeleteExport(contextMenu.artifact);
              setContextMenu(null);
            }}
            className="w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-rose-200 transition hover:bg-rose-500/10"
          >
            Удалить файл
          </button>
        </div>
      ) : null}
    </section>
  );
}
