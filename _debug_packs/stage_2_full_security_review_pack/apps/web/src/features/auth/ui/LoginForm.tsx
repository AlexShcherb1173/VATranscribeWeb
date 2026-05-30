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

type PasswordVisibilityButtonProps = {
  visible: boolean;
  labelShow: string;
  labelHide: string;
  onToggle: () => void;
};

function PasswordVisibilityButton({
  visible,
  labelShow,
  labelHide,
  onToggle,
}: PasswordVisibilityButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-500 transition hover:bg-slate-200/70 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-300/70 dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white"
      aria-label={visible ? labelHide : labelShow}
      title={visible ? labelHide : labelShow}
    >
      {visible ? (
        <svg
          aria-hidden="true"
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 3l18 18" />
          <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
          <path d="M9.9 4.24A10.7 10.7 0 0 1 12 4c6 0 9.5 6 9.5 6s-1.03 1.76-2.9 3.4" />
          <path d="M6.52 6.53C3.99 8.13 2.5 11 2.5 11s3.5 6 9.5 6a10.9 10.9 0 0 0 4.1-.78" />
        </svg>
      ) : (
        <svg
          aria-hidden="true"
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
    </button>
  );
}

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { t } = useI18n();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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

  const showPasswordLabel = t.auth.showPassword ?? "Show password";
  const hidePasswordLabel = t.auth.hidePassword ?? "Hide password";

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
        <div className="relative">
          <input
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-950 outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-white/5 dark:text-white"
            placeholder="Strong123"
            autoComplete="current-password"
          />
          <PasswordVisibilityButton
            visible={showPassword}
            labelShow={showPasswordLabel}
            labelHide={hidePasswordLabel}
            onToggle={() => setShowPassword((value) => !value)}
          />
        </div>
      </div>

      {errorMessage ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 px-3 py-2 text-sm text-rose-200">
          {errorMessage}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex w-full items-center justify-center rounded-2xl bg-cyan-300 px-5 py-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 focus:outline-none focus:ring-2 focus:ring-cyan-200/80 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {mutation.isPending ? t.auth.signingIn : t.auth.signIn}
      </button>
    </form>
  );
}
