import type { Transcript } from "@/entities/transcript/model/types";
import { formatDate } from "@/shared/lib/format";

function getTranscriptName(transcript: Transcript): string {
  return (
    transcript.display_name ||
    transcript.source_file_name ||
    transcript.media_asset?.original_name ||
    transcript.media_asset?.stored_name ||
    transcript.id
  );
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>

      <div className="mt-1 min-w-0 break-words text-sm font-semibold text-slate-100 [overflow-wrap:anywhere]">
        {value || "—"}
      </div>
    </div>
  );
}

export function TranscriptCard({ transcript }: { transcript: Transcript }) {
  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-5 min-w-0">
        <h2 className="text-lg font-semibold text-white">Транскрипт</h2>

        <div className="mt-2 min-w-0 break-words text-xl font-semibold text-white [overflow-wrap:anywhere]">
          {getTranscriptName(transcript)}
        </div>

        <div className="mt-2 break-all text-xs text-slate-500">
          ID: {transcript.id}
        </div>
      </div>

      <div className="grid min-w-0 gap-5 sm:grid-cols-3">
        <DetailItem label="Язык" value={transcript.language} />
        <DetailItem label="Модель" value={transcript.model_name} />
        <DetailItem label="Движок" value={transcript.engine} />
        <DetailItem label="ID задачи" value={transcript.job_id} />
        <DetailItem label="ID медиафайла" value={transcript.media_asset_id} />
        <DetailItem
          label="Создано"
          value={transcript.created_at ? formatDate(transcript.created_at) : null}
        />
      </div>

      <div className="mt-6">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Полный текст
        </div>

        <div className="max-h-[360px] min-w-0 overflow-auto whitespace-pre-wrap rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-sm leading-6 text-slate-100">
          {transcript.full_text || "—"}
        </div>
      </div>
    </section>
  );
}
