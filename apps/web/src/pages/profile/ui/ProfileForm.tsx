import { FormEvent, useEffect, useState } from "react";

import type { UserProfile } from "@/entities/profile/model/types";
import { useUpdateProfileMutation } from "@/shared/hooks/useUpdateProfileMutation";
import { useI18n } from "@/shared/i18n";

type ProfileFormProps = {
  profile: UserProfile;
};

export function ProfileForm({ profile }: ProfileFormProps) {
  const { t } = useI18n();
  const mutation = useUpdateProfileMutation();

  const [fullName, setFullName] = useState(profile.full_name || "");
  const [companyName, setCompanyName] = useState(profile.company_name || "");
  const [timezone, setTimezone] = useState(profile.timezone || "");
  const [locale, setLocale] = useState(profile.locale || "");
  const [avatarUrl, setAvatarUrl] = useState(profile.avatar_url || "");

  useEffect(() => {
    setFullName(profile.full_name || "");
    setCompanyName(profile.company_name || "");
    setTimezone(profile.timezone || "");
    setLocale(profile.locale || "");
    setAvatarUrl(profile.avatar_url || "");
  }, [profile]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    mutation.mutate({
      full_name: fullName.trim() || null,
      company_name: companyName.trim() || null,
      timezone: timezone.trim() || null,
      locale: locale.trim() || null,
      avatar_url: avatarUrl.trim() || null,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="premium-card border-slate-600/60 p-5"
    >
      <div className="mb-4">
        <div className="text-lg font-semibold text-white">
          {t.profile.profileSettings}
        </div>

        <div className="mt-1 text-sm text-slate-400">
          {t.profile.profileSettingsDescription}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-sm text-slate-300">
            {t.profile.fullName}
          </label>

          <input
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="w-full rounded-xl border border-slate-600 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500"
            placeholder="Alex Developer"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-slate-300">
            {t.profile.company}
          </label>

          <input
            type="text"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            className="w-full rounded-xl border border-slate-600 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500"
            placeholder="VAT Studio"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-slate-300">
            {t.profile.timezone}
          </label>

          <input
            type="text"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            className="w-full rounded-xl border border-slate-600 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500"
            placeholder="Europe/Istanbul"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-slate-300">
            {t.profile.locale}
          </label>

          <input
            type="text"
            value={locale}
            onChange={(event) => setLocale(event.target.value)}
            className="w-full rounded-xl border border-slate-600 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500"
            placeholder="ru"
          />
        </div>

        <div className="md:col-span-2">
          <label className="mb-1.5 block text-sm text-slate-300">
            {t.profile.avatarUrl}
          </label>

          <input
            type="url"
            value={avatarUrl}
            onChange={(event) => setAvatarUrl(event.target.value)}
            className="w-full rounded-xl border border-slate-600 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500"
            placeholder="https://..."
          />
        </div>
      </div>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="premium-button disabled:cursor-not-allowed disabled:opacity-60"
        >
          {mutation.isPending ? t.common.processing : t.profile.saveChanges}
        </button>

        <div className="text-xs text-slate-500">
          {t.profile.updated}: {new Date(profile.updated_at).toLocaleString()}
        </div>
      </div>
    </form>
  );
}