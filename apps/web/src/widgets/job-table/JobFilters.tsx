import { useI18n } from "@/shared/i18n";

type JobFiltersProps = {
  status: string;
  type: string;
  onStatusChange: (value: string) => void;
  onTypeChange: (value: string) => void;
};

export function JobFilters({
  status,
  type,
  onStatusChange,
  onTypeChange,
}: JobFiltersProps) {
  const { t } = useI18n();

  return (
    <div className="grid min-w-0 gap-4 md:grid-cols-2">
      <label className="block min-w-0">
        <span className="mb-2 block text-sm text-slate-300">
          {t.jobs.status}
        </span>

        <select
          value={status}
          onChange={(event) => onStatusChange(event.target.value)}
          className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
        >
          <option value="">{t.jobs.all}</option>
          <option value="queued">{t.jobs.queued}</option>
          <option value="running">{t.jobs.running}</option>
          <option value="succeeded">{t.jobs.succeeded}</option>
          <option value="failed">{t.jobs.failed}</option>
          <option value="canceled">{t.jobs.canceled}</option>
        </select>
      </label>

      <label className="block min-w-0">
        <span className="mb-2 block text-sm text-slate-300">
          {t.jobs.type}
        </span>

        <select
          value={type}
          onChange={(event) => onTypeChange(event.target.value)}
          className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
        >
          <option value="">{t.jobs.all}</option>
          <option value="download">{t.jobs.download}</option>
          <option value="upload">{t.jobs.upload}</option>
          <option value="transcribe">{t.jobs.transcribe}</option>
        </select>
      </label>
    </div>
  );
}
