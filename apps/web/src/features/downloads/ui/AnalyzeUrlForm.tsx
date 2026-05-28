import { FormEvent, useEffect, useState } from "react";

import { useI18n } from "@/shared/i18n";

type AnalyzeUrlFormProps = {
  initialUrl?: string;
  isLoading: boolean;
  onAnalyze: (url: string) => void;
  onUrlChange?: (url: string) => void;
};

export function AnalyzeUrlForm({
  initialUrl = "",
  isLoading,
  onAnalyze,
  onUrlChange,
}: AnalyzeUrlFormProps) {
  const { t } = useI18n();
  const [url, setUrl] = useState(initialUrl);

  useEffect(() => {
    setUrl(initialUrl);
  }, [initialUrl]);

  function handleUrlChange(value: string) {
    setUrl(value);
    onUrlChange?.(value);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalized = url.trim();

    if (!normalized) {
      return;
    }

    onAnalyze(normalized);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
    >
      <div className="mb-3">
        <h2 className="text-lg font-medium text-white">
          {t.downloads.analyzeTitle}
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          {t.downloads.analyzeText}
        </p>
      </div>

      <div className="flex flex-col gap-3 xl:flex-row">
        <input
          type="text"
          value={url}
          onChange={(event) => handleUrlChange(event.target.value)}
          placeholder="https://..."
          className="min-h-12 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-500"
        />

        <button
          type="submit"
          disabled={isLoading || !url.trim()}
          className="inline-flex min-h-12 min-w-[170px] items-center justify-center rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? t.downloads.analyzing : t.downloads.analyze}
        </button>
      </div>
    </form>
  );
}
