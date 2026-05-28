import { useI18n } from "@/shared/i18n";
import { formatDate } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";

type JobLog = {
  id: string;
  level?: string | null;
  message?: string | null;
  created_at?: string | null;
};

type JobLogsPanelProps = {
  logs: JobLog[];
};

function translateLogMessage(message: string | null | undefined, t: ReturnType<typeof useI18n>["t"]) {
  const raw = message || "—";

  const exact: Array<[RegExp, string]> = [
    [/^Download job created$/i, t.jobs.logDownloadCreated],
    [/^Download job enqueued$/i, t.jobs.logDownloadEnqueued],
    [/^Transcription job created$/i, t.jobs.logTranscriptionCreated],
    [/^Transcription job enqueued$/i, t.jobs.logTranscriptionEnqueued],
    [/^Job started$/i, t.jobs.logJobStarted],
    [/^Job retried and enqueued$/i, t.jobs.logJobRetried],
    [/^Подготовка транскрибации$/i, t.jobs.logPreparingTranscription],
    [/^Извлечение аудио$/i, t.jobs.logExtractingAudio],
    [/^Загрузка модели транскрибации$/i, t.jobs.logLoadingTranscriptionModel],
    [/^Сохранение транскрипта$/i, t.jobs.logSavingTranscript],
    [/^Экспорт TXT\/SRT\/VTT\/JSON$/i, t.jobs.logExportArtifacts],
    [/^Upload completed$/i, t.jobs.logUploadCompleted],
    [/^Транскрипт пустой:.*$/i, t.jobs.logTranscriptEmpty],
    [/^Транскрипт слишком короткий.*$/i, t.jobs.logTranscriptTooShort],
    [/^Первый проход вернул 0 сегментов.*$/i, t.jobs.logFirstPassNoSegments],
    [/^Запускаем fallback.*$/i, t.jobs.logFallbackStarted],
    [/^Fallback transcription.*$/i, t.jobs.logFallbackStarted],
  ];

  for (const [pattern, replacement] of exact) {
    if (pattern.test(raw)) {
      return replacement;
    }
  }

  if (/^Job failed:/i.test(raw)) {
    const reason = raw.replace(/^Job failed:\s*/i, "");
    const translatedReason = translateLogMessage(reason, t);
    return `${t.jobs.logJobFailed}: ${translatedReason}`;
  }

  return raw
    .replace(/^Requested format:/i, `${t.jobs.logRequestedFormat}:`)
    .replace(/^Audio prepared:/i, `${t.jobs.logAudioPrepared}:`)
    .replace(/^Detected language:/i, `${t.jobs.logDetectedLanguage}:`)
    .replace(/^Segments created:/i, `${t.jobs.logSegmentsCreated}:`)
    .replace(/^Full text length:/i, `${t.jobs.logFullTextLength}:`)
    .replace(/^Transcript created:/i, `${t.jobs.logTranscriptCreated}:`)
    .replace(/^Job retried and enqueued$/i, t.jobs.logJobRetried)
    .replace(/^Language mode:/i, `${t.jobs.logLanguageMode}:`)
    .replace(/^Audio profile:/i, `${t.jobs.logAudioProfile}:`)
    .replace(/^Whisper params:/i, `${t.jobs.logWhisperParams}:`)
    .replace(/^Model:/i, `${t.jobs.logModel}:`)
    .replace(/^Source path:/i, `${t.jobs.logSourcePath}:`)
    .replace(/^Stored media path:/i, `${t.jobs.logStoredMediaPath}:`)
    .replace(/^Resolved media path:/i, `${t.jobs.logResolvedMediaPath}:`)
    .replace(/^Preparing transcription for media asset:/i, `${t.jobs.logPreparingMediaAsset}:`)
    .replace(/^Export artifact is empty:/i, `${t.jobs.logExportArtifactEmpty}:`);
}

export function JobLogsPanel({ logs }: JobLogsPanelProps) {
  const { t } = useI18n();

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-800 px-5 py-4">
        <div className="text-sm font-semibold text-white">
          {t.jobs.logs}
        </div>
      </div>

      <div className="space-y-3 p-5">
        {logs.map((log) => (
          <div
            key={log.id}
            className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"
          >
            <div className="mb-2 flex flex-wrap items-center gap-3 text-xs">
              <span className="font-semibold text-cyan-300">
                {log.level || "INFO"}
              </span>

              <span className="text-slate-500">
                {log.created_at ? formatDate(log.created_at) : "—"}
              </span>
            </div>

            <div className="text-sm text-slate-200">
              {translateLogMessage(log.message, t)}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
