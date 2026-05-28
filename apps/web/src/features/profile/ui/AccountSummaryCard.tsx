import { useI18n } from "@/shared/i18n";

type AccountSummaryCardProps = {
  user: {
    email: string;
    role?: string;
  };
  profile: {
    full_name?: string | null;
    company?: string | null;
    timezone?: string | null;
    locale?: string | null;
  };
};

export function AccountSummaryCard({ user, profile }: AccountSummaryCardProps) {
  const { t } = useI18n();

  const empty = t.common.unavailable;

  return (
    <section className="premium-card border-slate-600/60 p-6">
      <h2 className="text-sm font-medium text-slate-300">
        {t.profile.accountSummary}
      </h2>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.email}
          </div>
          <div className="mt-2 text-sm text-white">{user.email}</div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.fullName}
          </div>
          <div className="mt-2 text-sm text-white">
            {profile.full_name || empty}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.company}
          </div>
          <div className="mt-2 text-sm text-white">
            {profile.company || empty}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.timezone}
          </div>
          <div className="mt-2 text-sm text-white">
            {profile.timezone || empty}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.locale}
          </div>
          <div className="mt-2 text-sm text-white">
            {profile.locale || empty}
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {t.profile.role}
          </div>
          <div className="mt-2 text-sm text-white">
            {user.role || t.profile.user}
          </div>
        </div>
      </div>
    </section>
  );
}