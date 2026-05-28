import { FormEvent, useEffect, useMemo, useState } from "react";

import type {
  DownloadFormatInfo,
  DownloadMode,
} from "@/features/downloads/model/types";
import { useI18n } from "@/shared/i18n";

type DownloadJobFormProps = {
  url: string;
  title: string | null;
  isSubmitting: boolean;
  selectedFormat: DownloadFormatInfo | null;
  selectedVideoFormatId: string;
  selectedAudioFormatId: string;
  onSubmit: (payload: {
    downloadMode: DownloadMode;
    requestedFormat: string;
    requestedFileName: string;
    mp4Mode: "fast" | "compatible";
    selectedFormatId: string | null;
    selectedVideoFormatId: string | null;
    selectedAudioFormatId: string | null;
  }) => void;
};

function slugifyFileName(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9а-яё_\-\s.]/gi, "")
    .replace(/\s+/g, "_")
    .replace(/_+/g, "_")
    .replace(/\.+/g, ".")
    .slice(0, 140);
}

function stripExtension(value: string): string {
  return value.replace(/\.[a-z0-9]{2,5}$/i, "");
}

function extensionForMode(
  mode: DownloadMode,
  selectedFormat: DownloadFormatInfo | null,
): string {
  if (mode === "audio_mp3") return "mp3";
  if (mode === "video_mp4_compatible") return "mp4";
  if (mode === "video_mp4_fast") return "mp4";
  if (mode === "selected_original") return selectedFormat?.ext || "media";
  return selectedFormat?.ext || "mp4";
}

export function DownloadJobForm({
  url,
  title,
  isSubmitting,
  selectedFormat,
  selectedVideoFormatId,
  selectedAudioFormatId,
  onSubmit,
}: DownloadJobFormProps) {
  const { t } = useI18n();

  const [downloadMode, setDownloadMode] =
    useState<DownloadMode>("video_mp4_compatible");

  const [requestedFileName, setRequestedFileName] = useState("");

  const outputExtension = useMemo(
    () => extensionForMode(downloadMode, selectedFormat),
    [downloadMode, selectedFormat],
  );

  const normalizedFileName = useMemo(() => {
    const base = stripExtension(slugifyFileName(requestedFileName) || "media_file");
    return `${base}.${outputExtension}`;
  }, [requestedFileName, outputExtension]);

  useEffect(() => {
    if (!title) return;

    setRequestedFileName((prev) => {
      if (prev.trim()) return prev;
      return slugifyFileName(title) || "media_file";
    });
  }, [title]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const selectedFormatId = selectedFormat?.format_id || null;

    const requestedFormat =
      downloadMode === "audio_mp3"
        ? "mp3"
        : downloadMode === "video_mp4_compatible" || downloadMode === "video_mp4_fast"
          ? "mp4"
          : outputExtension;

    const mp4Mode = downloadMode === "video_mp4_fast" ? "fast" : "compatible";

    onSubmit({
      downloadMode,
      requestedFormat,
      requestedFileName: normalizedFileName,
      mp4Mode,
      selectedFormatId,
      selectedVideoFormatId: selectedVideoFormatId || null,
      selectedAudioFormatId: selectedAudioFormatId || null,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
    >
      <div className="mb-4">
        <h2 className="text-lg font-medium text-white">
          {t.downloads.createTitle}
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Выбери режим скачивания, имя файла и создай задачу.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <label className="block">
          <span className="mb-1.5 block text-sm text-slate-300">
            {t.downloads.sourceUrl}
          </span>

          <input
            type="text"
            value={url}
            disabled
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-400"
          />
        </label>

        <label className="block">
          <span className="mb-1.5 block text-sm text-slate-300">
            {t.downloads.outputFilename}
          </span>

          <input
            type="text"
            value={requestedFileName}
            onChange={(event) => setRequestedFileName(event.target.value)}
            placeholder="lesson_01"
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-500"
          />

          <div className="mt-1 text-xs text-slate-500">
            Итоговое имя:{" "}
            <span className="text-cyan-300">{normalizedFileName}</span>
          </div>
        </label>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <label className="block">
          <span className="mb-1.5 block text-sm text-slate-300">
            Режим скачивания
          </span>

          <select
            value={downloadMode}
            onChange={(event) => setDownloadMode(event.target.value as DownloadMode)}
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-500"
          >
            <option value="video_mp4_compatible">
              MP4 compatible — видео + аудио
            </option>
            <option value="video_mp4_fast">
              MP4 fast — быстрый MP4
            </option>
            <option value="audio_mp3">
              MP3 audio — только аудио
            </option>
            <option value="selected_original">
              Selected original — выбранный формат как есть
            </option>
            <option value="best_available">
              Best available — лучший доступный формат
            </option>
          </select>
        </label>

        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-sm text-slate-400">
          <div>
            <span className="text-slate-300">Выбранный формат:</span>{" "}
            {selectedFormat?.format_id || t.downloads.auto}
          </div>

          <div className="mt-1">
            <span className="text-slate-300">{t.downloads.selectedVideo}:</span>{" "}
            {selectedVideoFormatId || t.downloads.auto}
          </div>

          <div className="mt-1">
            <span className="text-slate-300">{t.downloads.selectedAudio}:</span>{" "}
            {selectedAudioFormatId || t.downloads.auto}
          </div>
        </div>
      </div>

      <div className="mt-5">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? t.downloads.creating : t.downloads.createJob}
        </button>
      </div>
    </form>
  );
}