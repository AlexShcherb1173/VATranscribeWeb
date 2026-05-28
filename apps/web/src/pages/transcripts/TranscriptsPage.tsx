import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { ExportArtifact, Transcript } from "@/entities/transcript/model/types";
import { TranscriptCard } from "@/features/transcriptions/ui/TranscriptCard";
import { TranscriptExports } from "@/features/transcriptions/ui/TranscriptExports";
import { TranscriptSegmentsTable } from "@/features/transcriptions/ui/TranscriptSegmentsTable";
import { TranscriptsTable } from "@/features/transcriptions/ui/TranscriptsTable";
import {
  deleteExportArtifact,
  deleteTranscript,
  downloadExportArtifact,
  getExportArtifactFileName,
  saveBlob,
} from "@/shared/api/transcriptions";
import { useTranscriptDetailsQuery } from "@/shared/hooks/useTranscriptDetailsQuery";
import { useTranscriptsQuery } from "@/shared/hooks/useTranscriptsQuery";
import { Card } from "@/shared/ui/Card";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Spinner } from "@/shared/ui/Spinner";

function notifySuccess(title: string, message?: string) {
  console.log(`${title}${message ? `: ${message}` : ""}`);
}

function notifyError(title: string, message?: string) {
  console.error(`${title}${message ? `: ${message}` : ""}`);
  window.alert(`${title}${message ? `\n${message}` : ""}`);
}

function getTranscriptName(transcript: Transcript): string {
  return (
    transcript.display_name ||
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.id
  );
}

function findExport(transcript: Transcript, format: string): ExportArtifact | undefined {
  return (transcript.exports || []).find(
    (artifact) => artifact.format.toLowerCase() === format.toLowerCase(),
  );
}

export function TranscriptsPage() {
  const queryClient = useQueryClient();

  const [selectedTranscriptId, setSelectedTranscriptId] = useState<string | null>(null);

  const { data, isLoading } = useTranscriptsQuery();
  const transcripts = useMemo(() => data ?? [], [data]);

  useEffect(() => {
    if (!transcripts.length) {
      setSelectedTranscriptId(null);
      return;
    }

    if (!selectedTranscriptId) {
      setSelectedTranscriptId(transcripts[0].id);
      return;
    }

    const exists = transcripts.some((item) => item.id === selectedTranscriptId);

    if (!exists) {
      setSelectedTranscriptId(transcripts[0].id);
    }
  }, [transcripts, selectedTranscriptId]);

  const transcriptDetailsQuery = useTranscriptDetailsQuery(selectedTranscriptId);
  const selectedTranscript = transcriptDetailsQuery.data || null;

  const deleteTranscriptMutation = useMutation({
    mutationFn: deleteTranscript,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["transcript"] });
      notifySuccess("Удалено", "Результат транскрибации удалён.");
    },
    onError: (error: any) => {
      notifyError("Ошибка", error?.message || "Не удалось удалить результат.");
    },
  });

  const deleteExportMutation = useMutation({
    mutationFn: deleteExportArtifact,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["transcript", selectedTranscriptId] });
      notifySuccess("Удалено", "Файл результата удалён.");
    },
    onError: (error: any) => {
      notifyError("Ошибка", error?.message || "Не удалось удалить файл.");
    },
  });

  async function handleDownloadArtifact(transcript: Transcript, artifact: ExportArtifact) {
    try {
      const blob = await downloadExportArtifact(artifact);
      saveBlob(blob, getExportArtifactFileName(artifact, getTranscriptName(transcript)));
    } catch (error: any) {
      notifyError("Ошибка", error?.message || "Не удалось скачать файл.");
    }
  }

  function handleDownloadFormat(transcript: Transcript, format: string) {
    const artifact = findExport(transcript, format);

    if (!artifact) {
      notifyError("Файл не найден", `Для этого результата нет файла ${format.toUpperCase()}.`);
      return;
    }

    void handleDownloadArtifact(transcript, artifact);
  }

  function handleDeleteTranscript(transcript: Transcript) {
    const confirmed = window.confirm(
      `Удалить результат "${getTranscriptName(transcript)}" и все файлы экспорта?`,
    );

    if (!confirmed) {
      return;
    }

    deleteTranscriptMutation.mutate(transcript.id);
  }

  function handleDeleteExport(artifact: ExportArtifact) {
    const confirmed = window.confirm(`Удалить файл ${artifact.format.toUpperCase()}?`);

    if (!confirmed) {
      return;
    }

    deleteExportMutation.mutate(artifact.id);
  }

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title="Транскрипты"
        description="Результаты транскрибации."
      />

      {isLoading ? (
        <div className="flex items-center gap-3 text-slate-300">
          <Spinner />
          <span>Загрузка результатов...</span>
        </div>
      ) : (
        <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)]">
          <div className="min-w-0 overflow-hidden">
            {transcripts.length ? (
              <TranscriptsTable
                transcripts={transcripts}
                selectedTranscriptId={selectedTranscriptId}
                onSelectTranscript={setSelectedTranscriptId}
                onDownloadExport={handleDownloadFormat}
                onDeleteTranscript={handleDeleteTranscript}
              />
            ) : (
              <Card className="p-8 text-center">
                <div className="text-lg font-semibold text-white">
                  Результатов пока нет
                </div>

                <p className="mt-3 text-sm text-slate-400">
                  Создай транскрибацию из файла или ссылки.
                </p>
              </Card>
            )}
          </div>

          <aside className="grid min-w-0 content-start gap-6 overflow-hidden">
            {transcriptDetailsQuery.isLoading ? (
              <Card className="p-5">
                <div className="flex items-center gap-3 text-slate-300">
                  <Spinner />
                  <span>Загрузка результата...</span>
                </div>
              </Card>
            ) : selectedTranscript ? (
              <>
                <TranscriptCard transcript={selectedTranscript} />

                <TranscriptExports
                  transcript={selectedTranscript}
                  exportsList={selectedTranscript.exports ?? []}
                  onDownloadExport={handleDownloadArtifact}
                  onDeleteExport={handleDeleteExport}
                />

                <TranscriptSegmentsTable
                  segments={selectedTranscript.segments ?? []}
                />
              </>
            ) : (
              <Card className="p-5 text-sm text-slate-400">
                Выбери результат слева.
              </Card>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
