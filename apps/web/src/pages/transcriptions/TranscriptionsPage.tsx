import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { ExportArtifact, Transcript } from "@/entities/transcript/model/types";
import { TranscriptCard } from "@/features/transcriptions/ui/TranscriptCard";
import { TranscriptExports } from "@/features/transcriptions/ui/TranscriptExports";
import { SubtitleGenerator } from "@/features/transcriptions/ui/SubtitleGenerator";
import { TranscriptSegmentsTable } from "@/features/transcriptions/ui/TranscriptSegmentsTable";
import { TranscriptsTable } from "@/features/transcriptions/ui/TranscriptsTable";
import {
  createTranscriptSubtitles,
  deleteExportArtifact,
  deleteTranscript,
  downloadExportArtifact,
  getExportArtifactFileName,
  saveBlob,
} from "@/shared/api/transcriptions";
import { useI18n } from "@/shared/i18n";
import { useTranscriptDetailsQuery } from "@/shared/hooks/useTranscriptDetailsQuery";
import { useTranscriptsQuery } from "@/shared/hooks/useTranscriptsQuery";
import { Card } from "@/shared/ui/Card";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Spinner } from "@/shared/ui/Spinner";
import { toastError, toastSuccess } from "@/shared/ui/toast";

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

export function TranscriptionsPage() {
  const { t } = useI18n();
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
      toastSuccess(t.transcriptions.deletedTitle, t.transcriptions.deletedTranscriptMessage);
    },
    onError: (error: any) => {
      toastError(t.common.error, error?.message || t.transcriptions.deleteTranscriptFailed);
    },
  });

  const deleteExportMutation = useMutation({
    mutationFn: deleteExportArtifact,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["transcript", selectedTranscriptId] });
      toastSuccess(t.transcriptions.deletedTitle, t.transcriptions.deletedFileMessage);
    },
    onError: (error: any) => {
      toastError(t.common.error, error?.message || t.transcriptions.deleteFileFailed);
    },
  });

  const createSubtitlesMutation = useMutation({
    mutationFn: ({
      transcriptId,
      formats,
    }: {
      transcriptId: string;
      formats: Array<"srt" | "vtt" | "txt">;
    }) => createTranscriptSubtitles(transcriptId, { formats, overwrite: true }),
    onSuccess: async (_result, variables) => {
      await queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      await queryClient.invalidateQueries({ queryKey: ["transcript", variables.transcriptId] });
      toastSuccess(t.transcriptions.subtitlesCreatedTitle, t.transcriptions.subtitlesCreatedMessage);
    },
    onError: (error: any) => {
      toastError(t.common.error, error?.message || t.transcriptions.createSubtitlesFailed);
    },
  });

  function handleGenerateSubtitles(transcript: Transcript, formats: Array<"srt" | "vtt" | "txt">) {
    createSubtitlesMutation.mutate({ transcriptId: transcript.id, formats });
  }

  async function handleDownloadArtifact(transcript: Transcript, artifact: ExportArtifact) {
    try {
      const blob = await downloadExportArtifact(artifact);
      saveBlob(blob, getExportArtifactFileName(artifact, getTranscriptName(transcript)));
    } catch (error: any) {
      toastError(t.common.error, error?.message || t.transcriptions.downloadFileFailed);
    }
  }

  function handleDownloadFormat(transcript: Transcript, format: string) {
    const artifact = findExport(transcript, format);

    if (!artifact) {
      toastError(
        t.transcriptions.fileNotFound,
        t.transcriptions.missingFormat.replace("{format}", format.toUpperCase()),
      );
      return;
    }

    void handleDownloadArtifact(transcript, artifact);
  }

  function handleDeleteTranscript(transcript: Transcript) {
    const confirmed = window.confirm(
      t.transcriptions.deleteTranscriptConfirm.replace("{name}", getTranscriptName(transcript)),
    );

    if (!confirmed) {
      return;
    }

    deleteTranscriptMutation.mutate(transcript.id);
  }

  function handleDeleteExport(artifact: ExportArtifact) {
    const confirmed = window.confirm(
      t.transcriptions.deleteFileConfirm.replace("{format}", artifact.format.toUpperCase()),
    );

    if (!confirmed) {
      return;
    }

    deleteExportMutation.mutate(artifact.id);
  }

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        title={t.transcriptions.title}
        description={t.transcriptions.description}
      />

      {isLoading ? (
        <div className="flex items-center gap-3 text-slate-300">
          <Spinner />
          <span>{t.transcriptions.loadingResults}</span>
        </div>
      ) : (
        <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
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
                  {t.transcriptions.noResultsTitle}
                </div>

                <p className="mt-3 text-sm text-slate-400">
                  {t.transcriptions.noResultsDescription}
                </p>
              </Card>
            )}
          </div>

          <aside className="grid min-w-0 content-start gap-6 overflow-hidden">
            {transcriptDetailsQuery.isLoading ? (
              <Card className="p-5">
                <div className="flex items-center gap-3 text-slate-300">
                  <Spinner />
                  <span>{t.transcriptions.loadingResult}</span>
                </div>
              </Card>
            ) : selectedTranscript ? (
              <>
                <TranscriptCard transcript={selectedTranscript} />

                <SubtitleGenerator
                  transcript={selectedTranscript}
                  isGenerating={createSubtitlesMutation.isPending}
                  onGenerate={(formats) => handleGenerateSubtitles(selectedTranscript, formats)}
                />

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
                {t.transcriptions.selectResult}
              </Card>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
