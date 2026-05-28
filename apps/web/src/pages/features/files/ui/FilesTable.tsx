import { useEffect, useState, type MouseEvent } from "react";
import { createPortal } from "react-dom";

import type { MediaFile } from "@/entities/media-file/model/types";
import { useI18n } from "@/shared/i18n";
import { formatBytes, formatDate } from "@/shared/lib/format";

export type UploadPreviewItem = {
  id: string;
  file: File;
  progress: number;
  status: "idle" | "uploading" | "succeeded" | "failed";
  errorMessage?: string | null;
  uploadedMediaAssetId?: string | null;
  uploadedStoredName?: string | null;
};

type FilesTableProps = {
  files: MediaFile[];
  uploadItems?: UploadPreviewItem[];
  selectedFileId: string | null;
  deletingFileId?: string | null;
  transcribingFileId?: string | null;
  onSelectFile: (fileId: string) => void;
  onDeleteFile?: (file: MediaFile) => void;
  onTranscribeFile?: (file: MediaFile) => void;
  transcribeFileLabel?: string;
  transcribingFileLabel?: string;
  deleteFileLabel?: string;
  deletingFileLabel?: string;
};

type ContextMenuState = {
  file: MediaFile;
  x: number;
  y: number;
};

function clampMenuPosition(x: number, y: number) {
  const menuWidth = 236;
  const menuHeight = 112;
  const padding = 12;

  if (typeof window === "undefined") {
    return { x, y };
  }

  return {
    x: Math.min(x, window.innerWidth - menuWidth - padding),
    y: Math.min(y, window.innerHeight - menuHeight - padding),
  };
}

function getUploadStatusLabel(item: UploadPreviewItem, t: ReturnType<typeof useI18n>["t"]) {
  if (item.status === "failed") {
    return t.uploads.failed;
  }

  if (item.status === "succeeded") {
    return t.uploads.succeeded;
  }

  return t.uploads.uploadingLabel;
}

export function FilesTable({
  files,
  uploadItems = [],
  selectedFileId,
  deletingFileId = null,
  transcribingFileId = null,
  onSelectFile,
  onDeleteFile,
  onTranscribeFile,
  transcribeFileLabel,
  transcribingFileLabel,
  deleteFileLabel,
  deletingFileLabel,
}: FilesTableProps) {
  const { t } = useI18n();
  const resolvedDeleteFileLabel =
    deleteFileLabel || (t.files as any).deleteFile || (t.files as any).remove || (t.common as any).delete || "Удалить";
  const resolvedTranscribeFileLabel =
    transcribeFileLabel || (t.files as any).transcribe || "Транскрибировать";
  const resolvedDeletingFileLabel =
    deletingFileLabel || (t.files as any).deleting || t.common.processing || "Удаление...";
  const resolvedTranscribingFileLabel =
    transcribingFileLabel || t.common.processing || "Запуск...";
  const rightClickHint =
    (t.files as any).rightClickHint || "ПКМ: открыть меню действий";

  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  useEffect(() => {
    function closeMenu() {
      setContextMenu(null);
    }

    function closeMenuOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setContextMenu(null);
      }
    }

    window.addEventListener("click", closeMenu);
    window.addEventListener("contextmenu", closeMenu);
    window.addEventListener("keydown", closeMenuOnEscape);
    window.addEventListener("scroll", closeMenu, true);
    window.addEventListener("resize", closeMenu);

    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("contextmenu", closeMenu);
      window.removeEventListener("keydown", closeMenuOnEscape);
      window.removeEventListener("scroll", closeMenu, true);
      window.removeEventListener("resize", closeMenu);
    };
  }, []);

  function handleContextMenu(event: MouseEvent<HTMLTableRowElement>, file: MediaFile) {
    event.preventDefault();
    event.stopPropagation();

    onSelectFile(file.id);

    const position = clampMenuPosition(event.clientX, event.clientY);

    setContextMenu({
      file,
      x: position.x,
      y: position.y,
    });
  }

  function handleDeleteFromContextMenu() {
    if (!contextMenu?.file || !onDeleteFile) {
      return;
    }

    onDeleteFile(contextMenu.file);
    setContextMenu(null);
  }

  function handleTranscribeFromContextMenu() {
    if (!contextMenu?.file || !onTranscribeFile) {
      return;
    }

    onTranscribeFile(contextMenu.file);
    setContextMenu(null);
  }

  const menu = contextMenu
    ? createPortal(
        <div
          className="fixed z-[9999] min-w-56 rounded-2xl border border-slate-700 bg-slate-950 p-2 shadow-2xl shadow-black/50"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(event) => event.stopPropagation()}
          onContextMenu={(event) => {
            event.preventDefault();
            event.stopPropagation();
          }}
          onMouseDown={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            disabled={
              !onTranscribeFile ||
              deletingFileId === contextMenu.file.id ||
              transcribingFileId === contextMenu.file.id
            }
            onClick={handleTranscribeFromContextMenu}
            className="w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-cyan-100 transition hover:bg-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label={resolvedTranscribeFileLabel}
            title={resolvedTranscribeFileLabel}
          >
            {transcribingFileId === contextMenu.file.id
              ? resolvedTranscribingFileLabel
              : resolvedTranscribeFileLabel}
          </button>

          <button
            type="button"
            disabled={
              !onDeleteFile ||
              deletingFileId === contextMenu.file.id ||
              transcribingFileId === contextMenu.file.id
            }
            onClick={handleDeleteFromContextMenu}
            className="mt-1 w-full rounded-xl px-3 py-2 text-left text-sm font-semibold text-rose-200 transition hover:bg-rose-500/10 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label={resolvedDeleteFileLabel}
            title={resolvedDeleteFileLabel}
          >
            {deletingFileId === contextMenu.file.id
              ? resolvedDeletingFileLabel
              : resolvedDeleteFileLabel}
          </button>
        </div>,
        document.body,
      )
    : null;

  return (
    <div className="relative min-w-0 max-w-full overflow-hidden">
      <div className="max-w-full overflow-hidden">
        <table className="w-full table-fixed text-sm">
          <colgroup>
            <col className="w-[38%]" />
            <col className="w-[10%]" />
            <col className="w-[10%]" />
            <col className="w-[12%]" />
            <col className="w-[14%]" />
            <col className="w-[16%]" />
          </colgroup>

          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              <th className="px-4 py-3">{t.files.file}</th>
              <th className="px-4 py-3">{t.files.kind}</th>
              <th className="px-4 py-3">{t.files.size}</th>
              <th className="px-4 py-3">{t.files.duration}</th>
              <th className="px-4 py-3">{t.files.created}</th>
              <th className="px-4 py-3">{t.files.action}</th>
            </tr>
          </thead>

          <tbody>
            {uploadItems.map((item) => {
              const progress = Math.max(0, Math.min(100, Number(item.progress ?? 0)));
              const failed = item.status === "failed";

              return (
                <tr
                  key={item.id}
                  className={[
                    "border-t border-slate-800",
                    failed ? "bg-rose-500/5" : "bg-cyan-400/5",
                  ].join(" ")}
                >
                  <td className="min-w-0 px-4 py-3">
                    <div className="truncate font-medium text-white" title={item.file.name}>
                      {item.file.name}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      {getUploadStatusLabel(item, t)}
                    </div>

                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className={[
                          "h-full rounded-full transition-all",
                          failed ? "bg-rose-400" : "bg-cyan-400",
                        ].join(" ")}
                        style={{ width: `${progress}%` }}
                      />
                    </div>

                    {item.errorMessage ? (
                      <div className="mt-2 break-words text-xs text-rose-200">
                        {item.errorMessage}
                      </div>
                    ) : null}
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">
                      {item.file.type?.startsWith("video/")
                        ? "video"
                        : item.file.type?.startsWith("audio/")
                          ? "audio"
                          : "file"}
                    </div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">{formatBytes(item.file.size)}</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">—</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">{progress}%</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-400">
                    <div className="truncate">
                      {item.status === "failed" ? t.common.failed : t.common.processing}
                    </div>
                  </td>
                </tr>
              );
            })}

            {files.map((file) => {
              const selected = selectedFileId === file.id;
              const isDeleting = deletingFileId === file.id;
              const isTranscribing = transcribingFileId === file.id;
              const displayName = file.stored_name || file.original_name || file.id;

              return (
                <tr
                  key={file.id}
                  onClick={() => onSelectFile(file.id)}
                  onContextMenu={(event) => handleContextMenu(event, file)}
                  className={[
                    "cursor-pointer select-none border-t border-slate-800 transition hover:bg-cyan-400/10",
                    selected ? "bg-cyan-400/10" : "",
                    isDeleting || isTranscribing ? "opacity-50" : "",
                  ].join(" ")}
                  title={rightClickHint}
                >
                  <td className="min-w-0 px-4 py-3">
                    <div className="truncate font-medium text-white" title={displayName}>
                      {displayName}
                    </div>

                    <div className="mt-1 truncate text-xs text-slate-500">
                      {file.id}
                    </div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">{file.kind}</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">{formatBytes(file.size_bytes)}</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate">{file.duration_sec ? `${file.duration_sec} sec` : "—"}</div>
                  </td>

                  <td className="min-w-0 px-3 py-3 text-slate-300">
                    <div className="truncate" title={formatDate(file.created_at)}>
                      {formatDate(file.created_at)}
                    </div>
                  </td>

                  <td className="min-w-0 px-3 py-3">
                    <div
                      className="flex flex-wrap items-center gap-2"
                      onClick={(event) => {
                        event.stopPropagation();
                      }}
                    >
                      <button
                        type="button"
                        disabled={isDeleting || isTranscribing || !onTranscribeFile}
                        onClick={() => onTranscribeFile?.(file)}
                        className="rounded-xl bg-cyan-500 px-3 py-2 text-[11px] font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isTranscribing ? resolvedTranscribingFileLabel : resolvedTranscribeFileLabel}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}

            {!uploadItems.length && !files.length ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-sm text-slate-400">
                  {t.files.helper}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {menu}
    </div>
  );
}
