import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";

import type { DownloadMode } from "@/features/downloads/model/types";
import { useDownloadFlow } from "@/features/downloads/model/DownloadFlowProvider";
import { AnalyzeUrlForm } from "@/features/downloads/ui/AnalyzeUrlForm";
import { DownloadJobForm } from "@/features/downloads/ui/DownloadJobForm";
import { FormatsTable } from "@/features/downloads/ui/FormatsTable";
import { useI18n } from "@/shared/i18n";
import {
  clearPendingStartUrl,
  getPendingStartUrl,
} from "@/shared/lib/pendingStartUrl";
import { Card } from "@/shared/ui/Card";
import { PageHeader } from "@/shared/ui/PageHeader";

export function DownloadsPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const downloadFlow = useDownloadFlow();

  const {
    activeJobId,
    analysis,
    analysisUrl,
    downloadMode,
    errorMessage,
    isAnalyzing,
    isCreatingJob,
    jobResultMessage,
    requestedFileName,
    selectedAudioFormatId,
    selectedFormatId,
    selectedVideoFormatId,
    analyzeUrl,
    clearError,
    clearJobResult,
    createJob,
    setAnalysisUrl,
    setDownloadMode,
    setRequestedFileName,
    setSelectedAudioFormatId,
    setSelectedFormatId,
    setSelectedVideoFormatId,
  } = downloadFlow;

  useEffect(() => {
    const pendingUrl = getPendingStartUrl();

    if (pendingUrl) {
      setAnalysisUrl(pendingUrl);
      clearPendingStartUrl();
    }
  }, [setAnalysisUrl]);

  const selectedFormat = useMemo(() => {
    if (!analysis || !selectedFormatId) {
      return null;
    }

    return analysis.formats.find((item) => item.format_id === selectedFormatId) ?? null;
  }, [analysis, selectedFormatId]);

  const formatsCount = useMemo(() => analysis?.formats.length ?? 0, [analysis]);

  return (
    <div>
      <PageHeader title={t.downloads.title} description={t.downloads.description} />

      <div className="grid gap-6">
        <AnalyzeUrlForm
          isLoading={isAnalyzing}
          initialUrl={analysisUrl}
          onUrlChange={(url) => {
            setAnalysisUrl(url);
            if (errorMessage) clearError();
            if (jobResultMessage) clearJobResult();
          }}
          onAnalyze={(url) => {
            void analyzeUrl(url);
          }}
        />

        {errorMessage ? (
          <Card className="border-rose-900/60 bg-rose-950/30 p-4">
            <div className="text-sm font-medium text-rose-300">
              {t.common.error}
            </div>

            <div className="mt-1 text-sm text-rose-200">
              {errorMessage}
            </div>
          </Card>
        ) : null}

        {jobResultMessage ? (
          <Card className="border-emerald-900/60 bg-emerald-950/30 p-4">
            <div className="text-sm font-medium text-emerald-300">
              {t.common.success}
            </div>

            <div className="mt-1 text-sm text-emerald-200">
              {jobResultMessage}
            </div>

            {activeJobId ? (
              <button
                type="button"
                onClick={() => navigate(`/app/jobs?jobId=${activeJobId}&source=downloads`)}
                className="mt-3 rounded-xl border border-emerald-400/30 px-4 py-2 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-400/10"
              >
                {t.jobs?.title ?? "Jobs"}
              </button>
            ) : null}
          </Card>
        ) : null}

        {analysis ? (
          <>
            <Card className="p-5">
              <div className="grid gap-4 lg:grid-cols-4">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    {t.downloads.titleLabel}
                  </div>

                  <div className="mt-1 text-sm text-white">
                    {analysis.title || t.common.unavailable}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    {t.downloads.platform}
                  </div>

                  <div className="mt-1 text-sm text-white">
                    {analysis.extractor || t.common.unavailable}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    {t.downloads.duration}
                  </div>

                  <div className="mt-1 text-sm text-white">
                    {analysis.duration ? `${analysis.duration} sec` : t.common.unavailable}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    {t.downloads.formats}
                  </div>

                  <div className="mt-1 text-sm text-white">
                    {formatsCount}
                  </div>
                </div>
              </div>
            </Card>

            <FormatsTable
              formats={analysis.formats}
              selectedFormatId={selectedFormatId}
              selectedVideoFormatId={selectedVideoFormatId}
              selectedAudioFormatId={selectedAudioFormatId}
              onSelectFormat={setSelectedFormatId}
              onSelectVideoFormat={(formatId) => {
                setSelectedVideoFormatId(formatId);
                setSelectedFormatId(formatId);
              }}
              onSelectAudioFormat={(formatId) => {
                setSelectedAudioFormatId(formatId);
                setSelectedFormatId(formatId);
              }}
            />

            <DownloadJobForm
              url={analysisUrl}
              title={analysis.title}
              isSubmitting={isCreatingJob}
              selectedFormat={selectedFormat}
              selectedVideoFormatId={selectedVideoFormatId}
              selectedAudioFormatId={selectedAudioFormatId}
              initialDownloadMode={downloadMode}
              initialRequestedFileName={requestedFileName}
              onDraftChange={(draft) => {
                if (draft.downloadMode) {
                  setDownloadMode(draft.downloadMode);
                }

                if (typeof draft.requestedFileName === "string") {
                  setRequestedFileName(draft.requestedFileName);
                }
              }}
              onSubmit={(payload) => {
                void createJob({
                  url: analysisUrl,
                  download_mode: payload.downloadMode as DownloadMode,
                  requested_format: payload.requestedFormat,
                  requested_file_name: payload.requestedFileName,
                  mp4_mode: payload.mp4Mode,
                  selected_format_id: payload.selectedFormatId,
                  selected_video_format_id: payload.selectedVideoFormatId,
                  selected_audio_format_id: payload.selectedAudioFormatId,
                }).then((job) => {
                  if (job) {
                    navigate(`/app/jobs?jobId=${job.id}&source=downloads`);
                  }
                });
              }}
            />
          </>
        ) : (
          <Card className="p-6">
            <div className="text-lg font-medium text-white">
              {isAnalyzing ? t.downloads.analyzing : t.downloads.waitingTitle}
            </div>

            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              {isAnalyzing ? t.downloads.analyzeText : t.downloads.waitingText}
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
