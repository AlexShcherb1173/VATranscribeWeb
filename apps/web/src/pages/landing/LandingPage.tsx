import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { RegisterForm } from "@/features/auth/ui/RegisterForm";
import { LoginForm } from "@/features/auth/ui/LoginForm";
import { savePendingStartUrl } from "@/shared/lib/pendingStartUrl";
import { useI18n } from "@/shared/i18n";

export function LandingPage() {
  const { language, setLanguage, t } = useI18n();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const requestedPlan = searchParams.get("plan");
  const initialTab =
    location.pathname.includes("/auth/register") || requestedPlan ? "register" : "login";

  const [url, setUrl] = useState("");
  const [tab, setTab] = useState<"login" | "register">(initialTab);
  const [showAuthNotice, setShowAuthNotice] = useState(false);
  const [showAuthTabs, setShowAuthTabs] = useState(true);

  const registerRedirectTo = requestedPlan
    ? `/app/billing?plan=${encodeURIComponent(requestedPlan)}`
    : "/app/downloads";

  useEffect(() => {
    if (location.pathname.includes("/auth/register") || requestedPlan) {
      setTab("register");
      return;
    }

    if (location.pathname.includes("/auth/login")) {
      setTab("login");
    }
  }, [location.pathname, requestedPlan]);

  function handleStart(event?: FormEvent) {
    event?.preventDefault();

    savePendingStartUrl(url);
    setTab("register");
    setShowAuthNotice(true);
    setShowAuthTabs(false);

    window.setTimeout(() => {
      document
        .getElementById("landing-auth-card")
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="mx-auto flex max-w-7xl items-center px-6 py-6">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-300 font-bold text-slate-950">
            VA
          </div>

          <div>
            <div className="font-semibold">VATranscribe</div>
            <div className="text-xs text-slate-400">{t.common.creatorOs}</div>
          </div>
        </Link>
      </header>

      <main className="mx-auto grid max-w-7xl items-stretch gap-8 px-6 py-20 lg:grid-cols-[minmax(0,1fr)_430px] 2xl:max-w-[104rem] 2xl:grid-cols-[minmax(420px,1fr)_minmax(480px,520px)_430px]">
        <section className="flex h-full flex-col justify-center">
          <h1 className="max-w-3xl whitespace-pre-line text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
            {t.landing.headline}
          </h1>

          <p className="mt-8 max-w-2xl whitespace-pre-line text-lg leading-8 text-slate-300">
            {t.landing.subhead}
          </p>

          <form
            onSubmit={handleStart}
            className="mt-10 flex max-w-2xl gap-2 rounded-[1.75rem] border border-white/10 bg-white/5 p-2"
          >
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder={t.landing.urlPlaceholder}
              className="min-w-0 flex-1 rounded-2xl bg-slate-950/80 px-5 py-4 text-sm text-white outline-none placeholder:text-slate-400"
            />

            <button type="submit" className="premium-button shrink-0">
              {t.landing.primary}
            </button>
          </form>

          <div className="mt-6 flex flex-wrap gap-2 text-sm text-slate-400">
            <span>{t.result.transcript}</span>
            <span>·</span>
            <span>{t.result.subtitles}</span>
            <span>·</span>
            <span>{t.result.contentIdeas}</span>
            <span>·</span>
            <span>{t.result.export}</span>
            <span>·</span>
            <Link to="/pricing" className="font-semibold text-cyan-300 hover:text-cyan-200">
              {t.nav.billing}
            </Link>
          </div>
        </section>



        <section className="flex h-full w-full flex-col justify-between gap-5 rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-slate-950/20">
          <div className="rounded-[1.5rem] border border-white/10 bg-slate-950/50 p-6">
            <h2 className="text-2xl font-semibold tracking-tight">
              {t.landing.contentPack}
            </h2>

            <div className="mt-7 space-y-3">
              {t.landing.checks.map((item) => (
                <div
                  key={item}
                  className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm font-medium"
                >
                  <span>{item}</span>
                  <span className="text-cyan-300">✓</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="aspect-square rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <div className="font-semibold">{t.landing.creator}</div>
              <p className="mt-4 text-sm leading-6 text-slate-300">{t.landing.creatorText}</p>
            </div>

            <div className="aspect-square rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <div className="font-semibold">{t.landing.agency}</div>
              <p className="mt-4 text-sm leading-6 text-slate-300">{t.landing.agencyText}</p>
            </div>

            <div className="aspect-square rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <div className="font-semibold">{t.landing.education}</div>
              <p className="mt-4 text-sm leading-6 text-slate-300">{t.landing.educationText}</p>
            </div>
          </div>
        </section>

        <section
          id="landing-auth-card"
          className="flex h-full w-full flex-col rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-slate-950/20"
        >
          <div className="mb-6 flex items-center justify-between gap-3">
            <Link to="/pricing" className="premium-button px-4 py-2.5 text-sm">
              {t.common.goToSubscriptions}
            </Link>

            <div className="flex rounded-full border border-white/10 bg-white/5 p-1 text-xs font-semibold">
              {(["en", "ru"] as const).map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setLanguage(item)}
                  className={[
                    "rounded-full px-2.5 py-1 transition",
                    language === item
                      ? "bg-cyan-300 text-slate-950"
                      : "text-slate-400 hover:text-white",
                  ].join(" ")}
                >
                  {item.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">
              VATranscribe
            </div>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              {tab === "login" ? t.auth.signIn : t.auth.createAccount}
            </h2>
          </div>

          {showAuthNotice ? (
            <div className="mt-5 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 p-4 text-sm text-slate-100 shadow-lg shadow-cyan-950/20">
              <div className="font-semibold text-cyan-200">
                {t.landing.authRequiredTitle}
              </div>
              <p className="mt-2 leading-6 text-slate-300">
                {t.landing.authRequiredText}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setTab("login");
                    setShowAuthNotice(false);
                    setShowAuthTabs(false);
                  }}
                  className="rounded-xl border border-white/10 bg-white px-3 py-2 text-xs font-semibold text-slate-950 transition hover:bg-cyan-100"
                >
                  {t.auth.login}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setTab("register");
                    setShowAuthNotice(false);
                    setShowAuthTabs(false);
                  }}
                  className="rounded-xl border border-cyan-300/40 bg-cyan-300/15 px-3 py-2 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/25"
                >
                  {t.auth.register}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowAuthNotice(false);
                    setShowAuthTabs(true);
                  }}
                  className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
                >
                  {t.common.close}
                </button>
              </div>
            </div>
          ) : null}

          {showAuthTabs && !showAuthNotice ? (
            <div className="mt-6 grid grid-cols-2 rounded-2xl border border-white/10 bg-white/5 p-1">
              <button
                type="button"
                onClick={() => {
                  setTab("login");
                  setShowAuthNotice(false);
                }}
                className={[
                  "rounded-xl px-3 py-2.5 text-sm font-semibold transition",
                  tab === "login"
                    ? "bg-white text-slate-950"
                    : "text-slate-400 hover:text-white",
                ].join(" ")}
              >
                {t.auth.login}
              </button>

              <button
                type="button"
                onClick={() => {
                  setTab("register");
                  setShowAuthNotice(false);
                }}
                className={[
                  "rounded-xl px-3 py-2.5 text-sm font-semibold transition",
                  tab === "register"
                    ? "bg-white text-slate-950"
                    : "text-slate-400 hover:text-white",
                ].join(" ")}
              >
                {t.auth.register}
              </button>
            </div>
          ) : null}

          {!showAuthNotice ? (
            <div className="mt-6">
              {tab === "login" ? (
                <LoginForm />
              ) : (
                <RegisterForm redirectTo={registerRedirectTo} />
              )}
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}
