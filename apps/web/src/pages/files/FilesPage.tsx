import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { MediaFile } from "@/entities/media-file/model/types";
import { FilesTable, type UploadPreviewItem } from "@/features/files/ui/FilesTable";
import { deleteMediaFile } from "@/shared/api/files";
import { createTranscriptionJob } from "@/shared/api/transcriptions";
import { useMediaFilesQuery } from "@/shared/hooks/useMediaFilesQuery";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { formatBytes, formatDate } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Spinner } from "@/shared/ui/Spinner";
import { toastError, toastSuccess } from "@/shared/ui/toast";
import { UploaderPanel } from "@/widgets/uploader/UploaderPanel";

type FilesFilter = "all" | "succeeded" | "uploading" | "failed";

type TranscriptionSchemeId = "fast" | "standard" | "accurate" | "content";

type TranscriptionLanguageCode = "auto" | "ru" | "en" | "de" | "tr" | "es" | "fr";

type TranscriptionAudioProfileCode = "speech" | "music_vocal" | "lyrics_music" | "noisy_speech" | "meeting" | "lecture";

type TranscriptionLanguageOption = {
  code: TranscriptionLanguageCode;
  apiValue: string | null;
  getLabel: (language: "en" | "ru") => string;
  getDescription: (language: "en" | "ru") => string;
};

type TranscriptionAudioProfileOption = {
  code: TranscriptionAudioProfileCode;
  apiValue: string;
  getLabel: (language: "en" | "ru") => string;
  getDescription: (language: "en" | "ru") => string;
};

const TRANSCRIPTION_LANGUAGES: TranscriptionLanguageOption[] = [
  {
    code: "auto",
    apiValue: null,
    getLabel: (language) => (language === "ru" ? "Auto · определить язык" : "Auto · detect language"),
    getDescription: (language) =>
      language === "ru"
        ? "Рекомендуется по умолчанию. Подходит для YouTube, музыки, интервью и файлов на неизвестном языке."
        : "Recommended by default. Good for YouTube, music, interviews and files with unknown language.",
  },
  {
    code: "ru",
    apiValue: "ru",
    getLabel: (language) => (language === "ru" ? "Русский" : "Russian"),
    getDescription: (language) =>
      language === "ru" ? "Используйте только если речь точно на русском." : "Use only when the speech is definitely Russian.",
  },
  {
    code: "en",
    apiValue: "en",
    getLabel: (language) => (language === "ru" ? "Английский" : "English"),
    getDescription: (language) =>
      language === "ru" ? "Для англоязычных роликов, песен и интервью." : "For English videos, songs and interviews.",
  },
  {
    code: "de",
    apiValue: "de",
    getLabel: (language) => (language === "ru" ? "Немецкий" : "German"),
    getDescription: (language) => (language === "ru" ? "Для немецкой речи." : "For German speech."),
  },
  {
    code: "tr",
    apiValue: "tr",
    getLabel: (language) => (language === "ru" ? "Турецкий" : "Turkish"),
    getDescription: (language) => (language === "ru" ? "Для турецкой речи." : "For Turkish speech."),
  },
  {
    code: "es",
    apiValue: "es",
    getLabel: (language) => (language === "ru" ? "Испанский" : "Spanish"),
    getDescription: (language) => (language === "ru" ? "Для испанской речи." : "For Spanish speech."),
  },
  {
    code: "fr",
    apiValue: "fr",
    getLabel: (language) => (language === "ru" ? "Французский" : "French"),
    getDescription: (language) => (language === "ru" ? "Для французской речи." : "For French speech."),
  },
];

const TRANSCRIPTION_AUDIO_PROFILES: TranscriptionAudioProfileOption[] = [
  {
    code: "speech",
    apiValue: "speech",
    getLabel: (language) => (language === "ru" ? "Обычная речь" : "Speech"),
    getDescription: (language) =>
      language === "ru"
        ? "Для интервью, обычных видео, разговоров и чистой речи. VAD включён."
        : "For interviews, regular videos, calls and clear speech. VAD is enabled.",
  },
  {
    code: "music_vocal",
    apiValue: "music_vocal",
    getLabel: (language) => (language === "ru" ? "Музыка и вокал" : "Music & vocal"),
    getDescription: (language) =>
      language === "ru"
        ? "Для live-видео и вокала без отделения дорожек. VAD отключается."
        : "For live videos and vocals without source separation. VAD is disabled.",
  },
  {
    code: "lyrics_music",
    apiValue: "lyrics_music",
    getLabel: (language) => (language === "ru" ? "Клип / текст песни" : "Lyrics / music clip"),
    getDescription: (language) =>
      language === "ru"
        ? "Продвинутый режим для песен: отделяет вокал через Demucs, нормализует звук и затем распознаёт текст."
        : "Advanced song mode: isolates vocals with Demucs, normalizes audio and then transcribes lyrics.",
  },
  {
    code: "noisy_speech",
    apiValue: "noisy_speech",
    getLabel: (language) => (language === "ru" ? "Шумная речь" : "Noisy speech"),
    getDescription: (language) =>
      language === "ru"
        ? "Для плохого звука, фонового шума и записей с паузами. VAD работает мягче."
        : "For poor audio, background noise and recordings with pauses. VAD uses softer settings.",
  },
  {
    code: "meeting",
    apiValue: "speech",
    getLabel: (language) => (language === "ru" ? "Созвон" : "Meeting"),
    getDescription: (language) =>
      language === "ru"
        ? "Для созвонов, интервью и рабочих обсуждений."
        : "For calls, interviews and work discussions.",
  },
  {
    code: "lecture",
    apiValue: "speech",
    getLabel: (language) => (language === "ru" ? "Лекция" : "Lecture"),
    getDescription: (language) =>
      language === "ru"
        ? "Для длинных учебных записей и монотонной речи."
        : "For long educational recordings and lecture-style speech.",
  },
];

type TranscriptionScheme = {
  id: TranscriptionSchemeId;
  modelName: string;
  exportFormats: Array<"txt" | "srt" | "vtt" | "json">;
  generateContentPack?: boolean;
  getTitle: (language: "en" | "ru") => string;
  getSubtitle: (language: "en" | "ru") => string;
  getResult: (language: "en" | "ru") => string;
  getBestFor: (language: "en" | "ru") => string;
  getTradeoff: (language: "en" | "ru") => string;
};

const TRANSCRIPTION_SCHEMES: TranscriptionScheme[] = [
  {
    id: "fast",
    modelName: "small",
    exportFormats: ["txt", "srt", "vtt", "json"],
    getTitle: (language) => (language === "ru" ? "Быстрая" : "Fast"),
    getSubtitle: (language) =>
      language === "ru" ? "Whisper small · быстрее, легче" : "Whisper small · faster, lighter",
    getResult: (language) =>
      language === "ru"
        ? "Быстрый черновой транскрипт и базовые субтитры. Подходит для проверки файла и коротких роликов."
        : "Quick draft transcript and basic subtitles. Good for checking a file and short clips.",
    getBestFor: (language) =>
      language === "ru" ? "Черновики, короткие видео, быстрый тест." : "Drafts, short videos, quick tests.",
    getTradeoff: (language) =>
      language === "ru" ? "Меньше времени, но выше риск ошибок в шумной речи." : "Less time, but more errors with noisy speech.",
  },
  {
    id: "standard",
    modelName: "medium",
    exportFormats: ["txt", "srt", "vtt", "json"],
    getTitle: (language) => (language === "ru" ? "Стандартная" : "Standard"),
    getSubtitle: (language) =>
      language === "ru" ? "Whisper medium · баланс качества и скорости" : "Whisper medium · balanced quality and speed",
    getResult: (language) =>
      language === "ru"
        ? "Более аккуратный текст, лучшее распознавание фраз, пунктуации и таймингов для субтитров."
        : "Cleaner text, better phrase recognition, punctuation and subtitle timings.",
    getBestFor: (language) =>
      language === "ru" ? "YouTube, подкасты, созвоны, обычные видео." : "YouTube, podcasts, calls, regular videos.",
    getTradeoff: (language) =>
      language === "ru" ? "Обрабатывается дольше, чем быстрая схема." : "Takes longer than the fast scheme.",
  },
  {
    id: "accurate",
    modelName: "large-v3",
    exportFormats: ["txt", "srt", "vtt", "json"],
    getTitle: (language) => (language === "ru" ? "Точная" : "Accurate"),
    getSubtitle: (language) =>
      language === "ru" ? "Whisper large-v3 · максимальное качество" : "Whisper large-v3 · highest quality",
    getResult: (language) =>
      language === "ru"
        ? "Максимально точный транскрипт для сложного звука, длинных лекций, интервью и профессиональных материалов."
        : "Highest accuracy for difficult audio, long lectures, interviews and professional material.",
    getBestFor: (language) =>
      language === "ru" ? "Длинные видео, плохой звук, интервью, обучение." : "Long videos, poor audio, interviews, training.",
    getTradeoff: (language) =>
      language === "ru" ? "Самая медленная и ресурсная схема." : "Slowest and most resource-heavy scheme.",
  },
  {
    id: "content",
    modelName: "medium",
    exportFormats: ["txt", "srt", "vtt", "json"],
    generateContentPack: true,
    getTitle: (language) => (language === "ru" ? "Контент-пакет" : "Content pack"),
    getSubtitle: (language) =>
      language === "ru" ? "Whisper medium + профиль контента" : "Whisper medium + content profile",
    getResult: (language) =>
      language === "ru"
        ? "Транскрипт и субтитры с JSON-структурой для дальнейшей генерации summary, hooks и SEO-заголовков."
        : "Transcript and subtitles with JSON structure for summary, hooks and SEO title generation.",
    getBestFor: (language) =>
      language === "ru" ? "Creators, фрилансеры, команды, публикации." : "Creators, freelancers, teams, publishing.",
    getTradeoff: (language) =>
      language === "ru" ? "Качество как у стандартной схемы, но задача помечается как content workflow." : "Standard quality, but the job is marked as a content workflow.",
  },
];

function getDefaultTranscriptionScheme(): TranscriptionScheme {
  return TRANSCRIPTION_SCHEMES.find((scheme) => scheme.id === "standard") ?? TRANSCRIPTION_SCHEMES[0];
}

export function FilesPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const deleteFileLabel = t.files.deleteFile || t.files.remove || t.common.delete || "Удалить";
  const deletingFileLabel = t.files.deleting || t.common.processing || "Удаление...";
  const confirmDeleteFileText = t.files.confirmDeleteFile || "Удалить выбранный файл?";
  const deleteFailedText = t.files.deleteFailed || t.common.requestFailed || "Не удалось удалить файл.";
  const transcribeFileLabel = t.files.transcribe || "Транскрибировать";

  const [searchParams, setSearchParams] = useSearchParams();

  const [selectedFileId, setSelectedFileId] = useState<string | null>(
    searchParams.get("fileId"),
  );
  const [uploadItems, setUploadItems] = useState<UploadPreviewItem[]>([]);
  const [filesFilter, setFilesFilter] = useState<FilesFilter>("all");
  const [filesOpen, setFilesOpen] = useState(true);
  const [selectedFileOpen, setSelectedFileOpen] = useState(true);
  const [createdJobByFileId, setCreatedJobByFileId] = useState<Record<string, string>>({});
  const [schemeDialogFile, setSchemeDialogFile] = useState<MediaFile | null>(null);

  const { data, isLoading } = useMediaFilesQuery();
  const files = useMemo(() => data ?? [], [data]);

  const setSelectedFile = useCallback(
    (fileId: string) => {
      setSelectedFileId(fileId);
      setSearchParams({ fileId, source: "files" });
    },
    [setSearchParams],
  );

  const deleteFileMutation = useMutation({
    mutationFn: (file: MediaFile) => deleteMediaFile(file.id),

    onSuccess: async (_data, deletedFile) => {
      await queryClient.invalidateQueries({ queryKey: ["media-files"] });
      await queryClient.invalidateQueries({ queryKey: ["quota", "me"] });

      if (selectedFileId === deletedFile.id) {
        const nextFile = files.find((file) => file.id !== deletedFile.id) ?? null;

        if (nextFile) {
          setSelectedFile(nextFile.id);
        } else {
          setSelectedFileId(null);
          setSearchParams({});
        }
      }

      toastSuccess(t.common.success, t.files.fileDeleted);
    },

    onError: (error: any) => {
      toastError(t.common.failed, extractErrorMessage(error, t) || deleteFailedText);
    },
  });

  const transcribeFileMutation = useMutation({
    mutationFn: ({
      file,
      scheme,
      transcriptionLanguage,
      audioProfile,
    }: {
      file: MediaFile;
      scheme: TranscriptionScheme;
      transcriptionLanguage: TranscriptionLanguageOption;
      audioProfile: TranscriptionAudioProfileOption;
    }) =>
      createTranscriptionJob({
        media_asset_id: file.id,
        model_name: scheme.modelName,
        language: transcriptionLanguage.apiValue,
        export_formats: scheme.exportFormats,
        transcription_scheme: scheme.id,
        audio_profile: audioProfile.apiValue,
        content_profile: scheme.generateContentPack ? "content_pack" : null,
        generate_summary: scheme.generateContentPack || undefined,
        generate_content_pack: scheme.generateContentPack || undefined,
      }),

    onSuccess: async (job: any, variables) => {
      const file = variables.file;

      if (job?.id) {
        setCreatedJobByFileId((prev) => ({ ...prev, [file.id]: job.id }));
      }

      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["quota", "me"] });

      toastSuccess(
        t.common.success,
        job?.id ? `${t.jobs.created}: ${job.id}` : t.jobs.created,
      );

      if (job?.id) {
        navigate(`/app/jobs?jobId=${encodeURIComponent(job.id)}&source=files`);
      } else {
        navigate("/app/jobs?source=files");
      }
    },

    onError: (error: any) => {
      toastError(t.common.failed, extractErrorMessage(error, t));
    },
  });

  useEffect(() => {
    const fileIdFromUrl = searchParams.get("fileId");

    if (fileIdFromUrl && fileIdFromUrl !== selectedFileId) {
      setSelectedFileId(fileIdFromUrl);
    }
  }, [searchParams, selectedFileId]);

  useEffect(() => {
    if (!files.length) {
      setSelectedFileId(null);
      return;
    }

    if (!selectedFileId) {
      setSelectedFile(files[0].id);
      return;
    }

    const exists = files.some((file) => file.id === selectedFileId);

    if (!exists) {
      setSelectedFile(files[0].id);
    }
  }, [files, selectedFileId, setSelectedFile]);

  const selectedFile = files.find((file) => file.id === selectedFileId) ?? null;
  const selectedFileJobId = selectedFileId ? createdJobByFileId[selectedFileId] : null;

  useEffect(() => {
    if (selectedFileId) {
      setSelectedFileOpen(true);
    }
  }, [selectedFileId]);

  const uploadingItems = useMemo(
    () => uploadItems.filter((item) => item.status === "idle" || item.status === "uploading"),
    [uploadItems],
  );

  const failedItems = useMemo(
    () => uploadItems.filter((item) => item.status === "failed"),
    [uploadItems],
  );

  const visibleFiles = useMemo(() => {
    if (filesFilter === "succeeded") {
      return files;
    }

    if (filesFilter === "uploading" || filesFilter === "failed") {
      return [];
    }

    return files;
  }, [files, filesFilter]);

  const visibleUploadItems = useMemo(() => {
    if (filesFilter === "uploading") {
      return uploadingItems;
    }

    if (filesFilter === "failed") {
      return failedItems;
    }

    if (filesFilter === "all") {
      return uploadItems.filter((item) => item.status !== "succeeded");
    }

    return [];
  }, [failedItems, filesFilter, uploadItems, uploadingItems]);

  function handleSummaryClick(nextFilter: FilesFilter) {
    setFilesFilter(nextFilter);
    setFilesOpen(true);
  }

  function handleTranscribeFile(file: MediaFile) {
    setSelectedFile(file.id);
    setSchemeDialogFile(file);
  }

  function handleStartTranscriptionWithScheme(
    file: MediaFile,
    scheme: TranscriptionScheme,
    transcriptionLanguage: TranscriptionLanguageOption,
    audioProfile: TranscriptionAudioProfileOption,
  ) {
    setSelectedFile(file.id);
    setSchemeDialogFile(null);
    transcribeFileMutation.mutate({ file, scheme, transcriptionLanguage, audioProfile });
  }

  function handleDeleteFile(file: MediaFile) {
    const displayName = file.stored_name || file.original_name || file.id;
    const confirmed = window.confirm(
      `${confirmDeleteFileText}\n\n${displayName}`,
    );

    if (!confirmed) {
      return;
    }

    deleteFileMutation.mutate(file);
  }

  return (
    <div>
      <PageHeader title={t.files.title} description={t.files.description} />

      <div className="grid gap-6">
        <section className="grid min-w-0 gap-6 xl:grid-cols-2">
          <UploaderPanel
            showQueue={false}
            showSummary={false}
            suppressToasts
            onQueueChange={setUploadItems}
          />

          <UploadSummaryCard
            activeFilter={filesFilter}
            succeededCount={files.length}
            uploadingCount={uploadingItems.length}
            failedCount={failedItems.length}
            onFilterChange={handleSummaryClick}
          />
        </section>

        {isLoading ? (
          <div className="flex items-center gap-3 text-slate-300">
            <Spinner />
            <span>{t.files.loading}</span>
          </div>
        ) : (
          <section className="grid min-w-0 max-w-full items-start gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.55fr)]">
            <div className="min-w-0 self-start overflow-hidden">
              <CollapsibleFilesPanel
                title={t.files.title}
                count={visibleFiles.length + visibleUploadItems.length}
                open={filesOpen}
                onToggle={() => setFilesOpen((value) => !value)}
              >
                <FilesTable
                  files={visibleFiles}
                  uploadItems={visibleUploadItems}
                  selectedFileId={selectedFileId}
                  deletingFileId={deleteFileMutation.variables?.id ?? null}
                  transcribingFileId={transcribeFileMutation.variables?.file.id ?? null}
                  transcribeFileLabel={transcribeFileLabel}
                  deleteFileLabel={deleteFileLabel}
                  deletingFileLabel={deletingFileLabel}
                  onSelectFile={setSelectedFile}
                  onTranscribeFile={handleTranscribeFile}
                  onDeleteFile={handleDeleteFile}
                />
              </CollapsibleFilesPanel>
            </div>

            <SelectedFileCard
              file={selectedFile}
              helper={t.files.helper}
              open={selectedFileOpen}
              onToggle={() => setSelectedFileOpen((value) => !value)}
              createdJobId={selectedFileJobId}
              onOpenJob={(jobId) => navigate(`/app/jobs?jobId=${encodeURIComponent(jobId)}&source=files`)}
              onStartTranscription={handleTranscribeFile}
              transcribingFileId={transcribeFileMutation.variables?.file.id ?? null}
            />
          </section>
        )}
      </div>

      <TranscriptionSchemeDialog
        file={schemeDialogFile}
        pending={transcribeFileMutation.isPending}
        onClose={() => {
          if (!transcribeFileMutation.isPending) {
            setSchemeDialogFile(null);
          }
        }}
        onSubmit={handleStartTranscriptionWithScheme}
      />
    </div>
  );
}

function UploadSummaryCard({
  activeFilter,
  succeededCount,
  uploadingCount,
  failedCount,
  onFilterChange,
}: {
  activeFilter: FilesFilter;
  succeededCount: number;
  uploadingCount: number;
  failedCount: number;
  onFilterChange: (filter: FilesFilter) => void;
}) {
  const { t } = useI18n();

  return (
    <Card className="min-w-0 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="text-lg font-semibold text-white">
          {t.uploads.summary}
        </div>

        <button
          type="button"
          onClick={() => onFilterChange("all")}
          className={[
            "rounded-full border px-3 py-1 text-xs font-semibold transition",
            activeFilter === "all"
              ? "border-cyan-300/70 bg-cyan-400/10 text-cyan-100"
              : "border-slate-700 text-slate-300 hover:border-cyan-300/60",
          ].join(" ")}
        >
          {t.jobs.all}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryTile
          label={t.uploads.succeeded}
          value={succeededCount}
          active={activeFilter === "succeeded"}
          tone="success"
          onClick={() => onFilterChange("succeeded")}
        />
        <SummaryTile
          label={t.uploads.uploadingLabel}
          value={uploadingCount}
          active={activeFilter === "uploading"}
          tone="info"
          onClick={() => onFilterChange("uploading")}
        />
        <SummaryTile
          label={t.uploads.failed}
          value={failedCount}
          active={activeFilter === "failed"}
          tone="danger"
          onClick={() => onFilterChange("failed")}
        />
      </div>
    </Card>
  );
}

function SummaryTile({
  label,
  value,
  active,
  tone,
  onClick,
}: {
  label: string;
  value: number;
  active: boolean;
  tone: "success" | "info" | "danger";
  onClick: () => void;
}) {
  const valueClass =
    tone === "success"
      ? "text-emerald-300"
      : tone === "danger"
        ? "text-rose-300"
        : "text-cyan-200";

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        "rounded-2xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-300/70",
        active
          ? "border-cyan-300/70 bg-cyan-400/10 shadow-[0_0_0_1px_rgba(103,232,249,0.25)]"
          : "border-slate-800 bg-slate-950/40 hover:border-cyan-400/50 hover:bg-cyan-400/5",
      ].join(" ")}
    >
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div className={`mt-3 text-2xl font-semibold ${valueClass}`}>
        {value}
      </div>
    </button>
  );
}

function CollapsibleFilesPanel({
  title,
  count,
  open,
  onToggle,
  children,
}: {
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <Card className="min-w-0 max-w-full self-start overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-5 py-4 text-left transition hover:bg-white/[0.03]"
        aria-expanded={open}
      >
        <div className="flex min-w-0 items-center gap-3">
          <span className="text-sm font-semibold text-white">
            {title}
          </span>

          <span className="shrink-0 rounded-full border border-slate-700 px-2.5 py-1 text-xs font-semibold text-slate-300">
            {count}
          </span>
        </div>

        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-700 text-sm font-semibold text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="max-h-[320px] min-w-0 max-w-full overflow-y-scroll">
          {children}
        </div>
      ) : null}
    </Card>
  );
}

function SelectedFileCard({
  file,
  helper,
  open,
  onToggle,
  createdJobId,
  onOpenJob,
  onStartTranscription,
  transcribingFileId,
}: {
  file: MediaFile | null;
  helper: string;
  open: boolean;
  onToggle: () => void;
  createdJobId: string | null;
  onOpenJob: (jobId: string) => void;
  onStartTranscription: (file: MediaFile) => void;
  transcribingFileId: string | null;
}) {
  const { t } = useI18n();

  return (
    <Card className="min-w-0 self-start overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-800 px-5 py-4 text-left transition hover:bg-white/[0.03]"
      >
        <span className="text-sm font-semibold text-white">
          {t.files.selected}
        </span>

        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-700 text-sm font-semibold text-slate-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="max-h-[320px] overflow-y-scroll p-5 pr-3">
          {file ? (
            <div className="min-w-0 space-y-5 text-sm text-slate-300">
              <div className="space-y-3">
                <DetailRow label={t.files.name} value={file.stored_name || file.original_name} />
                <DetailRow label={t.files.kind} value={file.kind} />
                <DetailRow label={t.files.size} value={formatBytes(file.size_bytes)} />
                <DetailRow
                  label={t.files.duration}
                  value={file.duration_sec ? `${file.duration_sec} sec` : t.common.unavailable}
                />
                <DetailRow label={t.files.created} value={formatDate(file.created_at)} />
                <DetailRow label={t.files.id} value={file.id} />
              </div>

              <div className="flex flex-wrap gap-2">
                {createdJobId ? (
                  <button
                    type="button"
                    onClick={() => onOpenJob(createdJobId)}
                    className="rounded-xl bg-cyan-500 px-3 py-2 text-xs font-medium text-slate-950 transition hover:bg-cyan-400"
                  >
                    {t.files.openJob}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={transcribingFileId === file.id}
                    onClick={() => onStartTranscription(file)}
                    className="rounded-xl bg-cyan-500 px-3 py-2 text-xs font-medium text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {transcribingFileId === file.id ? t.common.processing : t.files.startProcessing}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-400">{helper}</div>
          )}
        </div>
      ) : null}
    </Card>
  );
}


function TranscriptionSchemeDialog({
  file,
  pending,
  onClose,
  onSubmit,
}: {
  file: MediaFile | null;
  pending: boolean;
  onClose: () => void;
  onSubmit: (
    file: MediaFile,
    scheme: TranscriptionScheme,
    transcriptionLanguage: TranscriptionLanguageOption,
    audioProfile: TranscriptionAudioProfileOption,
  ) => void;
}) {
  const { language, t } = useI18n();
  const [selectedSchemeId, setSelectedSchemeId] = useState<TranscriptionSchemeId>("standard");
  const [selectedLanguageCode, setSelectedLanguageCode] = useState<TranscriptionLanguageCode>("auto");
  const [selectedAudioProfileCode, setSelectedAudioProfileCode] = useState<TranscriptionAudioProfileCode>("speech");

  const fileId = file?.id;

  useEffect(() => {
    if (fileId) {
      setSelectedSchemeId("standard");
      setSelectedLanguageCode("auto");
      setSelectedAudioProfileCode("speech");
    }
  }, [fileId]);

  if (!file) {
    return null;
  }

  const selectedScheme =
    TRANSCRIPTION_SCHEMES.find((scheme) => scheme.id === selectedSchemeId) ??
    getDefaultTranscriptionScheme();
  const selectedTranscriptionLanguage =
    TRANSCRIPTION_LANGUAGES.find((item) => item.code === selectedLanguageCode) ??
    TRANSCRIPTION_LANGUAGES[0];
  const selectedAudioProfile =
    TRANSCRIPTION_AUDIO_PROFILES.find((item) => item.code === selectedAudioProfileCode) ??
    TRANSCRIPTION_AUDIO_PROFILES[0];
  const effectiveModelName = selectedScheme.modelName;

  const fileName = file.stored_name || file.original_name || file.id;
  const title = language === "ru" ? "Выберите схему транскрибации" : "Choose transcription scheme";
  const description =
    language === "ru"
      ? "Схема влияет на модель распознавания, скорость обработки и качество итогового текста/субтитров."
      : "The scheme affects recognition model, processing speed and final transcript/subtitle quality.";
  const modelLabel = language === "ru" ? "Модель" : "Model";
  const formatsLabel = language === "ru" ? "Экспорт" : "Exports";
  const languageLabel = language === "ru" ? "Язык распознавания" : "Recognition language";
  const audioProfileLabel = language === "ru" ? "Профиль аудио" : "Audio profile";
  const cancelLabel = t.common.cancel || (language === "ru" ? "Отмена" : "Cancel");
  const startLabel = pending
    ? t.common.processing
    : language === "ru"
      ? "Запустить транскрибацию"
      : "Start transcription";

  return (
    <div
      className="fixed inset-0 z-[10000] flex items-center justify-center bg-slate-950/80 p-3 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !pending) {
          onClose();
        }
      }}
    >
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-slate-700 bg-slate-950 shadow-2xl shadow-black/60">
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-800 p-4 sm:p-5">
          <div className="min-w-0">
            <div className="text-lg font-semibold text-white">{title}</div>
            <div className="mt-1 max-w-3xl text-xs leading-5 text-slate-300">{description}</div>
            <div className="mt-2 truncate text-xs text-slate-500" title={fileName}>
              {fileName}
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={pending}
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-700 text-lg text-slate-200 transition hover:border-cyan-300 hover:text-cyan-100 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label={t.common.close}
          >
            ×
          </button>
        </div>

        <div className="grid flex-1 gap-4 overflow-y-auto p-4 sm:p-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(300px,0.85fr)]">
          <div className="grid content-start gap-3 sm:grid-cols-2">
            {TRANSCRIPTION_SCHEMES.map((scheme) => {
              const selected = selectedSchemeId === scheme.id;

              return (
                <button
                  key={scheme.id}
                  type="button"
                  disabled={pending}
                  onClick={() => setSelectedSchemeId(scheme.id)}
                  className={[
                    "min-h-[132px] rounded-2xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-300/70 disabled:cursor-not-allowed disabled:opacity-70",
                    selected
                      ? "border-cyan-300/80 bg-cyan-400/10 shadow-[0_0_0_1px_rgba(103,232,249,0.25)]"
                      : "border-slate-800 bg-slate-900/60 hover:border-cyan-400/60 hover:bg-cyan-400/5",
                  ].join(" ")}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-base font-semibold text-white">
                        {scheme.getTitle(language)}
                      </div>
                      <div className="mt-1 text-xs text-cyan-200">
                        {scheme.getSubtitle(language)}
                      </div>
                    </div>

                    <span className={[
                      "mt-1 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-xs",
                      selected ? "border-cyan-300 bg-cyan-300 text-slate-950" : "border-slate-700 text-slate-500",
                    ].join(" ")}
                    >
                      {selected ? "✓" : ""}
                    </span>
                  </div>

                  <div className="mt-3 text-sm leading-5 text-slate-300">
                    {scheme.getResult(language)}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="text-lg font-semibold text-white">
              {selectedScheme.getTitle(language)}
            </div>
            <div className="mt-1 text-sm text-cyan-200">
              {selectedScheme.getSubtitle(language)}
            </div>

            <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/50 p-3">
              <label className="text-xs uppercase tracking-wide text-slate-500" htmlFor="transcription-language-select">
                {languageLabel}
              </label>
              <select
                id="transcription-language-select"
                value={selectedLanguageCode}
                disabled={pending}
                onChange={(event) => setSelectedLanguageCode(event.target.value as TranscriptionLanguageCode)}
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm font-semibold text-slate-100 outline-none transition focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/30 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {TRANSCRIPTION_LANGUAGES.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.getLabel(language)}
                  </option>
                ))}
              </select>
              <div className="mt-2 text-xs leading-5 text-slate-400">
                {selectedTranscriptionLanguage.getDescription(language)}
              </div>
            </div>

            <div className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/50 p-3">
              <label className="text-xs uppercase tracking-wide text-slate-500" htmlFor="transcription-audio-profile-select">
                {audioProfileLabel}
              </label>
              <select
                id="transcription-audio-profile-select"
                value={selectedAudioProfileCode}
                disabled={pending}
                onChange={(event) => {
                  const nextProfile = event.target.value as TranscriptionAudioProfileCode;
                  setSelectedAudioProfileCode(nextProfile);

                  if (nextProfile === "lyrics_music" && selectedSchemeId !== "accurate") {
                    setSelectedSchemeId("fast");
                  }
                }}
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm font-semibold text-slate-100 outline-none transition focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/30 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {TRANSCRIPTION_AUDIO_PROFILES.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.getLabel(language)}
                  </option>
                ))}
              </select>
              <div className="mt-2 text-xs leading-5 text-slate-400">
                {selectedAudioProfile.getDescription(language)}
              </div>
            </div>

            <div className="mt-4 grid gap-3 text-sm leading-5 text-slate-300 sm:grid-cols-2">
              <InfoPill label={modelLabel} value={effectiveModelName} />
              <InfoPill label={formatsLabel} value={selectedScheme.exportFormats.join(", ")} />
              <InfoPill label={languageLabel} value={selectedTranscriptionLanguage.getLabel(language)} />
              <InfoPill label={audioProfileLabel} value={selectedAudioProfile.getLabel(language)} />
            </div>
          </div>
        </div>

        <div className="flex shrink-0 flex-col-reverse gap-3 border-t border-slate-800 bg-slate-950 p-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={pending}
            className="rounded-xl border border-slate-700 px-5 py-2.5 text-sm font-semibold text-slate-200 transition hover:border-cyan-300/70 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cancelLabel}
          </button>

          <button
            type="button"
            disabled={pending}
            onClick={() =>
              onSubmit(
                file,
                selectedScheme,
                selectedTranscriptionLanguage,
                selectedAudioProfile,
              )
            }
            className="rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {startLabel}
          </button>
        </div>
      </div>
    </div>
  );
}


function InfoPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 break-words font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="min-w-0">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div className="mt-1 break-words font-semibold text-slate-100">
        {value || "—"}
      </div>
    </div>
  );
}
