import { useMemo, useState } from "react";

import type { Transcript } from "@/entities/transcript/model/types";
import { useI18n } from "@/shared/i18n";

type SubtitleFormat = "srt" | "vtt" | "txt";

type SubtitleGeneratorProps = {
  transcript: Transcript;
  isGenerating?: boolean;
  onGenerate: (formats: SubtitleFormat[]) => void;
};

function hasSubtitleFormat(transcript: Transcript, format: SubtitleFormat): boolean {
  const targetFormat = format === "txt" ? "subtitle_txt" : format;

  return Boolean(
    transcript.exports?.some(
      (artifact) => artifact.format?.toLowerCase() === targetFormat,
    ),
  );
}

export function SubtitleGenerator({
  transcript,
  isGenerating = false,
  onGenerate,
}: SubtitleGeneratorProps) {
  const { t } = useI18n();
  const [selectedFormats, setSelectedFormats] = useState<SubtitleFormat[]>(["srt", "vtt"]);

  const formatOptions = useMemo(
    () => [
      {
        value: "srt" as const,
        title: "SRT",
        description: t.transcriptions.classicSubtitleDesc,
      },
      {
        value: "vtt" as const,
        title: "VTT",
        description: t.transcriptions.webvttDesc,
      },
      {
        value: "txt" as const,
        title: "TXT",
        description: t.transcriptions.timedTextDesc,
      },
    ],
    [t],
  );

  const hasSegments = Boolean(transcript.segments?.length);
  const existingFormats = useMemo(
    () => formatOptions.filter((item) => hasSubtitleFormat(transcript, item.value)),
    [formatOptions, transcript],
  );

  function toggleFormat(format: SubtitleFormat) {
    setSelectedFormats((current) => {
      if (current.includes(format)) {
        return current.filter((item) => item !== format);
      }

      return [...current, format];
    });
  }

  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex min-w-0 items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-white">{t.transcriptions.subtitleFromText}</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {t.transcriptions.subtitleDescription}
          </p>
        </div>

        <span className="shrink-0 rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
          {hasSegments
            ? `${transcript.segments?.length ?? 0} ${t.transcriptions.segmentCountShort}`
            : t.transcriptions.textFallback}
        </span>
      </div>

      {existingFormats.length ? (
        <div className="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-3 text-xs text-cyan-100">
          {t.transcriptions.alreadyCreated}: {existingFormats.map((item) => item.title).join(", ")}.{" "}
          {t.transcriptions.regenerateWillUpdate}
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {formatOptions.map((option) => {
          const checked = selectedFormats.includes(option.value);

          return (
            <button
              key={option.value}
              type="button"
              onClick={() => toggleFormat(option.value)}
              className={[
                "rounded-2xl border p-4 text-left transition",
                checked
                  ? "border-cyan-400 bg-cyan-400/10 text-white"
                  : "border-slate-800 bg-slate-950/50 text-slate-300 hover:border-slate-700",
              ].join(" ")}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-bold uppercase">{option.title}</span>
                <span
                  className={[
                    "h-3 w-3 rounded-full border",
                    checked ? "border-cyan-300 bg-cyan-300" : "border-slate-600",
                  ].join(" ")}
                />
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                {option.description}
              </p>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        disabled={isGenerating || !selectedFormats.length}
        onClick={() => onGenerate(selectedFormats)}
        className="mt-4 w-full rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isGenerating ? t.transcriptions.creatingSubtitles : t.transcriptions.createSubtitles}
      </button>
    </section>
  );
}
