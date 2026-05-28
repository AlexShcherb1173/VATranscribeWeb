import type { useI18n } from "@/shared/i18n";

type T = ReturnType<typeof useI18n>["t"];

export function mapJobStatus(status: string | null | undefined, t: T): string {
  switch ((status || "").toLowerCase()) {
    case "queued":
      return t.jobs.queued;
    case "running":
    case "processing":
    case "started":
      return t.jobs.running;
    case "succeeded":
    case "success":
    case "completed":
      return t.jobs.succeeded;
    case "failed":
    case "error":
      return t.jobs.failed;
    case "canceled":
    case "cancelled":
      return t.jobs.canceled;
    default:
      return status || t.common.unavailable;
  }
}

export function mapJobType(type: string | null | undefined, t: T): string {
  switch ((type || "").toLowerCase()) {
    case "download":
      return t.jobs.download;
    case "transcribe":
    case "transcription":
      return t.jobs.transcribe;
    case "upload":
      return t.jobs.upload;
    default:
      return type || t.common.unavailable;
  }
}

export function mapSourceType(sourceType: string | null | undefined, t: T): string {
  switch ((sourceType || "").toLowerCase()) {
    case "url":
      return t.jobs.url;
    case "file":
    case "media_asset":
      return t.jobs.file;
    default:
      return sourceType || t.common.unavailable;
  }
}

export function getJobStatusClass(status: string | null | undefined): string {
  switch ((status || "").toLowerCase()) {
    case "queued":
      return "bg-blue-500/15 text-blue-200 ring-1 ring-blue-400/20";
    case "running":
    case "processing":
    case "started":
      return "bg-amber-500/15 text-amber-200 ring-1 ring-amber-400/20";
    case "succeeded":
    case "success":
    case "completed":
      return "bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-400/20";
    case "failed":
    case "error":
      return "bg-rose-500/15 text-rose-200 ring-1 ring-rose-400/20";
    case "canceled":
    case "cancelled":
      return "bg-slate-500/15 text-slate-200 ring-1 ring-slate-400/20";
    default:
      return "bg-slate-500/15 text-slate-200 ring-1 ring-slate-400/20";
  }
}