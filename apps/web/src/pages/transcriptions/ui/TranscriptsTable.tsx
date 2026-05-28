import { useEffect, useState, type MouseEvent } from "react";

import type { Transcript } from "@/entities/transcript/model/types";
import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";

type ContextMenuState = {
  transcript: Transcript;
  x: number;
  y: number;
};

type TranscriptsTableProps = {
  transcripts: Transcript[];
  selectedTranscriptId: string | null;
  onSelectTranscript: (transcriptId: string) => void;
  onDownloadExport: (transcript: Transcript, format: string) => void;
  onDeleteTranscript: (transcript: Transcript) => void;
};

function getTranscriptName(transcript: Transcript): string {
  return (
    transcript.display_name ||
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.id
  );
}

function getSourceMediaName(transcript: Transcript): string {
  return (
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.media_asset_id
  );
}

export function TranscriptsTable({
  transcripts,
  selectedTranscriptId,
  onSelectTranscript,
  onDownloadExport,
  onDeleteTranscript,
}: TranscriptsTableProps) {
  const { t } = useI18n();
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

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

  function handleContextMenu(event: MouseEvent, transcript: Transcript) {
    event.preventDefault();
    onSelectTranscript(transcript.id);
    setContextMenu({
      transcript,
      x: event.clientX,
      y: event.clientY,
    });
  }

  function handleDownload(format: string) {
    if (!contextMenu) {
      return;
    }

    onDownloadExport(contextMenu.transcript, format);
    setContextMenu(null);
  }

  function handleDelete() {
    if (!contextMenu) {
      return;
    }

    onDeleteTranscript(contextMenu.transcript);
    setContextMenu(null);
  }

  return (
    <div className="relative min-w-0 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-base font-semibold text-white">{t.transcriptions.resultsTitle}</h2>
      </div>

      <div className="max-w-full overflow-x-auto">
        <table className="w-full min-w-[760px] table-fixed text-sm">
          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              <th className="w-[44%] px-4 py-3">{t.transcriptions.resultColumn}</th>
              <th className="w-[10%] px-4 py-3">{t.transcriptions.language}</th>
              <th className="w-[14%] px-4 py-3">{t.transcriptions.model}</th>
              <th className="w-[16%] px-4 py-3">{t.transcriptions.engine}</th>
              <th className="w-[16%] px-4 py-3">{t.transcriptions.created}</th>
            </tr>
          </thead>

          <tbody>
            {transcripts.map((transcript) => {
              const selected = transcript.id === selectedTranscriptId;
              const name = getTranscriptName(transcript);

              return (
                <tr
                  key={transcript.id}
                  onClick={() => onSelectTranscript(transcript.id)}
                  onContextMenu={(event) => handleContextMenu(event, transcript)}
                  className={[
                    "cursor-pointer border-t border-slate-800 transition hover:bg-cyan-400/10",
                    selected ? "bg-cyan-400/10" : "",
                  ].join(" ")}
                  title={t.transcriptions.contextMenuHint}
                >
                  <td className="min-w-0 px-4 py-3">
                    <div className="truncate font-semibold text-white" title={name}>
                      {name}
                    </div>

                    <div className="mt-1 truncate text-xs text-slate-500">
                      {t.transcriptions.id}: {transcript.id}
                    </div>

                    <div className="mt-1 truncate text-xs text-slate-600">
                      {t.transcriptions.sourceMedia}: {getSourceMediaName(transcript)}
                    </div>
                  </td>

                  <td className="px-4 py-3 font-semibold text-slate-200">
                    {transcript.language || "—"}
                  </td>

                  <td className="px-4 py-3 text-slate-200">
                    {transcript.model_name || "—"}
                  </td>

                  <td className="px-4 py-3 text-slate-200">
                    {transcript.engine || "—"}
                  </td>

                  <td className="px-4 py-3 text-slate-300">
                    {transcript.created_at ? formatDate(transcript.created_at) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {contextMenu ? (
        <div
          className="fixed z-50 min-w-56 rounded-2xl border border-slate-700 bg-slate-950 p-2 shadow-2xl"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(event) => event.stopPropagation()}
        >
          {["txt", "srt", "vtt", "json"].map((format) => (
            <button
              key={format}
              type="button"
              onClick={() => handleDownload(format)}
              className="w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-cyan-200 transition hover:bg-cyan-400/10"
            >
              {t.transcriptions.download} {format.toUpperCase()}
            </button>
          ))}

          <button
            type="button"
            onClick={handleDelete}
            className="mt-1 w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-rose-200 transition hover:bg-rose-500/10"
          >
            {t.common.delete}
          </button>
        </div>
      ) : null}
    </div>
  );
}
