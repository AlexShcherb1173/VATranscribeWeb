import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";

import { loginUser } from "@/features/auth/api/auth";
import { saveRedirectAfterLogin, consumeRedirectAfterLogin } from "@/shared/auth/navigation";
import { saveSession } from "@/shared/auth/session";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";

type LocationState = {
  from?: {
    pathname?: string;
    search?: string;
    hash?: string;
  };
};

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { t } = useI18n();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: loginUser,
    onSuccess: async (data) => {
      saveSession(data.access_token);
      setErrorMessage(null);
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });

      const state = location.state as LocationState | null;
      const fromPath = state?.from?.pathname
        ? `${state.from.pathname || ""}${state.from.search || ""}${state.from.hash || ""}`
        : null;

      const storedRedirect = consumeRedirectAfterLogin();
      const redirectCandidate = storedRedirect || fromPath;
      const redirectTo =
        redirectCandidate && !["/", "/auth"].includes(redirectCandidate)
          ? redirectCandidate
          : "/app/downloads";

      navigate(redirectTo, { replace: true });
    },
    onError: (error: any) => {
      setErrorMessage(extractErrorMessage(error, t));
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim()) {
      setErrorMessage(t.auth.emailRequired);
      return;
    }

    if (!password.trim()) {
      setErrorMessage(t.auth.passwordRequired);
      return;
    }

    const currentPath =
      window.location.pathname + window.location.search + window.location.hash;

    if (!["/", "/auth"].includes(currentPath)) {
      saveRedirectAfterLogin(currentPath);
    }

    mutation.mutate({
      email: email.trim(),
      password,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-sm text-slate-300">{t.auth.email}</label>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-white/5 dark:text-white"
          placeholder="alex@example.com"
          autoComplete="email"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm text-slate-300">{t.auth.password}</label>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-white/5 dark:text-white"
          placeholder="Strong123"
          autoComplete="current-password"
        />
      </div>

      {errorMessage ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 px-3 py-2 text-sm text-rose-200">
          {errorMessage}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="premium-button w-full disabled:cursor-not-allowed disabled:opacity-60"
      >
        {mutation.isPending ? t.auth.signingIn : t.auth.signIn}
      </button>
    </form>
  );
}
