import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  analyzeDownloadUrl,
  createDownloadJob,
} from "@/features/downloads/api/downloads";
import type {
  CreateDownloadJobRequest,
  CreatedJobResponse,
  DownloadAnalyzeResponse,
  DownloadMode,
} from "@/features/downloads/model/types";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { toastError, toastInfo, toastSuccess } from "@/shared/ui/toast";

type DownloadFlowContextValue = {
  analysis: DownloadAnalyzeResponse | null;
  analysisUrl: string;
  selectedFormatId: string;
  selectedVideoFormatId: string;
  selectedAudioFormatId: string;
  requestedFileName: string;
  downloadMode: DownloadMode;
  jobResultMessage: string | null;
  errorMessage: string | null;
  activeJobId: string | null;
  isAnalyzing: boolean;
  isCreatingJob: boolean;
  setAnalysisUrl: (url: string) => void;
  setSelectedFormatId: (formatId: string) => void;
  setSelectedVideoFormatId: (formatId: string) => void;
  setSelectedAudioFormatId: (formatId: string) => void;
  setRequestedFileName: (fileName: string) => void;
  setDownloadMode: (mode: DownloadMode) => void;
  analyzeUrl: (url: string) => Promise<DownloadAnalyzeResponse | null>;
  createJob: (payload: CreateDownloadJobRequest) => Promise<CreatedJobResponse | null>;
  clearError: () => void;
  clearJobResult: () => void;
  resetFlow: () => void;
};

type PersistedDownloadFlowState = {
  analysis: DownloadAnalyzeResponse | null;
  analysisUrl: string;
  selectedFormatId: string;
  selectedVideoFormatId: string;
  selectedAudioFormatId: string;
  requestedFileName: string;
  downloadMode: DownloadMode;
  activeJobId: string | null;
  jobResultMessage: string | null;
  errorMessage: string | null;
};

const STORAGE_KEY = "vatranscribe.downloadFlow.v1";

const defaultPersistedState: PersistedDownloadFlowState = {
  analysis: null,
  analysisUrl: "",
  selectedFormatId: "",
  selectedVideoFormatId: "",
  selectedAudioFormatId: "",
  requestedFileName: "",
  downloadMode: "video_mp4_compatible",
  activeJobId: null,
  jobResultMessage: null,
  errorMessage: null,
};

const DownloadFlowContext = createContext<DownloadFlowContextValue | null>(null);

function readPersistedState(): PersistedDownloadFlowState {
  if (typeof window === "undefined") {
    return defaultPersistedState;
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return defaultPersistedState;
    }

    const parsed = JSON.parse(raw) as Partial<PersistedDownloadFlowState>;

    return {
      ...defaultPersistedState,
      ...parsed,
      analysis: parsed.analysis ?? null,
      analysisUrl: parsed.analysisUrl ?? "",
      selectedFormatId: parsed.selectedFormatId ?? "",
      selectedVideoFormatId: parsed.selectedVideoFormatId ?? "",
      selectedAudioFormatId: parsed.selectedAudioFormatId ?? "",
      requestedFileName: parsed.requestedFileName ?? "",
      downloadMode: parsed.downloadMode ?? "video_mp4_compatible",
      activeJobId: parsed.activeJobId ?? null,
      jobResultMessage: parsed.jobResultMessage ?? null,
      errorMessage: parsed.errorMessage ?? null,
    };
  } catch {
    return defaultPersistedState;
  }
}

function persistState(state: PersistedDownloadFlowState) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // sessionStorage can be unavailable in restricted browser modes.
  }
}

function findDefaultFormatIds(analysis: DownloadAnalyzeResponse) {
  const firstFormat = analysis.formats.find((item) => item.format_id);

  const bestAudio = analysis.formats.find(
    (item) => item.audio_only || item.vcodec === "none",
  );

  const bestVideo = analysis.formats.find(
    (item) => !item.audio_only && item.vcodec !== "none",
  );

  return {
    selectedFormatId: firstFormat?.format_id || "",
    selectedAudioFormatId: bestAudio?.format_id || "",
    selectedVideoFormatId: bestVideo?.format_id || "",
  };
}

export function DownloadFlowProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const initialState = useMemo(readPersistedState, []);

  const [analysis, setAnalysis] = useState<DownloadAnalyzeResponse | null>(
    initialState.analysis,
  );
  const [analysisUrl, setAnalysisUrlState] = useState(initialState.analysisUrl);
  const [selectedFormatId, setSelectedFormatId] = useState(
    initialState.selectedFormatId,
  );
  const [selectedVideoFormatId, setSelectedVideoFormatId] = useState(
    initialState.selectedVideoFormatId,
  );
  const [selectedAudioFormatId, setSelectedAudioFormatId] = useState(
    initialState.selectedAudioFormatId,
  );
  const [requestedFileName, setRequestedFileName] = useState(
    initialState.requestedFileName,
  );
  const [downloadMode, setDownloadMode] = useState<DownloadMode>(
    initialState.downloadMode,
  );
  const [jobResultMessage, setJobResultMessage] = useState<string | null>(
    initialState.jobResultMessage,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(
    initialState.errorMessage,
  );
  const [activeJobId, setActiveJobId] = useState<string | null>(
    initialState.activeJobId,
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isCreatingJob, setIsCreatingJob] = useState(false);

  useEffect(() => {
    persistState({
      analysis,
      analysisUrl,
      selectedFormatId,
      selectedVideoFormatId,
      selectedAudioFormatId,
      requestedFileName,
      downloadMode,
      activeJobId,
      jobResultMessage,
      errorMessage,
    });
  }, [
    activeJobId,
    analysis,
    analysisUrl,
    downloadMode,
    errorMessage,
    jobResultMessage,
    requestedFileName,
    selectedAudioFormatId,
    selectedFormatId,
    selectedVideoFormatId,
  ]);

  const setAnalysisUrl = useCallback((url: string) => {
    setAnalysisUrlState(url);
  }, []);

  const analyzeUrl = useCallback(
    async (url: string) => {
      const normalizedUrl = url.trim();

      if (!normalizedUrl) {
        return null;
      }

      setIsAnalyzing(true);
      setErrorMessage(null);
      setJobResultMessage(null);
      setAnalysisUrlState(normalizedUrl);

      try {
        const data = await analyzeDownloadUrl({ url: normalizedUrl });
        const defaultIds = findDefaultFormatIds(data);

        setAnalysis(data);
        setSelectedFormatId(defaultIds.selectedFormatId);
        setSelectedAudioFormatId(defaultIds.selectedAudioFormatId);
        setSelectedVideoFormatId(defaultIds.selectedVideoFormatId);
        setActiveJobId(null);
        setErrorMessage(null);
        setJobResultMessage(null);

        return data;
      } catch (error: any) {
        const message = extractErrorMessage(error, t) || t.downloads.failedAnalyze;

        setAnalysis(null);
        setSelectedFormatId("");
        setSelectedAudioFormatId("");
        setSelectedVideoFormatId("");
        setActiveJobId(null);
        setJobResultMessage(null);
        setErrorMessage(message);
        toastError(t.common.error, message);

        return null;
      } finally {
        setIsAnalyzing(false);
      }
    },
    [t],
  );

  const createJob = useCallback(
    async (payload: CreateDownloadJobRequest) => {
      setIsCreatingJob(true);
      setErrorMessage(null);
      setJobResultMessage(null);

      try {
        const job = await createDownloadJob(payload);
        const message = t.downloads.created ?? t.common.success;

        setActiveJobId(job.id);
        setJobResultMessage(message);
        setErrorMessage(null);
        toastSuccess(t.common.success, message);

        await queryClient.invalidateQueries({ queryKey: ["jobs"] });
        await queryClient.invalidateQueries({ queryKey: ["media-files"] });
        await queryClient.invalidateQueries({ queryKey: ["quota", "me"] });

        return job;
      } catch (error: any) {
        const message = extractErrorMessage(error, t) || t.downloads.failedCreate;

        setJobResultMessage(null);
        setErrorMessage(message);
        toastError(t.common.error, message);

        return null;
      } finally {
        setIsCreatingJob(false);
      }
    },
    [queryClient, t],
  );

  const clearError = useCallback(() => setErrorMessage(null), []);
  const clearJobResult = useCallback(() => setJobResultMessage(null), []);

  const resetFlow = useCallback(() => {
    setAnalysis(null);
    setAnalysisUrlState("");
    setSelectedFormatId("");
    setSelectedVideoFormatId("");
    setSelectedAudioFormatId("");
    setRequestedFileName("");
    setDownloadMode("video_mp4_compatible");
    setJobResultMessage(null);
    setErrorMessage(null);
    setActiveJobId(null);

    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo<DownloadFlowContextValue>(
    () => ({
      analysis,
      analysisUrl,
      selectedFormatId,
      selectedVideoFormatId,
      selectedAudioFormatId,
      requestedFileName,
      downloadMode,
      jobResultMessage,
      errorMessage,
      activeJobId,
      isAnalyzing,
      isCreatingJob,
      setAnalysisUrl,
      setSelectedFormatId,
      setSelectedVideoFormatId,
      setSelectedAudioFormatId,
      setRequestedFileName,
      setDownloadMode,
      analyzeUrl,
      createJob,
      clearError,
      clearJobResult,
      resetFlow,
    }),
    [
      activeJobId,
      analysis,
      analysisUrl,
      analyzeUrl,
      clearError,
      clearJobResult,
      createJob,
      downloadMode,
      errorMessage,
      isAnalyzing,
      isCreatingJob,
      jobResultMessage,
      requestedFileName,
      resetFlow,
      selectedAudioFormatId,
      selectedFormatId,
      selectedVideoFormatId,
      setAnalysisUrl,
    ],
  );

  return (
    <DownloadFlowContext.Provider value={value}>
      {children}
    </DownloadFlowContext.Provider>
  );
}

export function useDownloadFlow() {
  const context = useContext(DownloadFlowContext);

  if (!context) {
    throw new Error("useDownloadFlow must be used inside DownloadFlowProvider");
  }

  return context;
}

