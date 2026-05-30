import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { loginUser, registerUser } from "@/features/auth/api/auth";
import { useI18n } from "@/shared/i18n";
import { extractErrorMessage } from "@/shared/lib/auth-errors";
import { saveSession } from "@/shared/auth/session";

type RegisterFormProps = {
  onRegistered?: () => void;
  redirectTo?: string;
};

export function RegisterForm({ onRegistered, redirectTo }: RegisterFormProps) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function validatePassword(value: string): string | null {
    if (value.length < 8) return t.auth.passwordMin;
    if (!/[a-z]/.test(value)) return t.auth.passwordLower;
    if (!/[A-Z]/.test(value)) return t.auth.passwordUpper;
    if (!/\d/.test(value)) return t.auth.passwordDigit;
    if (/\s/.test(value)) return t.auth.passwordSpaces;
    return null;
  }

  const mutation = useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      await registerUser(payload);

      if (!redirectTo) {
        return null;
      }

      return loginUser(payload);
    },
    onSuccess: async (data) => {
      setSuccessMessage(t.auth.created);
      setErrorMessage(null);
      setPassword("");
      setConfirmPassword("");

      if (data?.access_token && redirectTo) {
        saveSession(data.access_token);
        await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
        navigate(redirectTo, { replace: true });
        return;
      }

      window.setTimeout(() => onRegistered?.(), 700);
    },
    onError: (error: any) => {
      setSuccessMessage(null);
      setErrorMessage(extractErrorMessage(error, t));
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim()) {
      setErrorMessage(t.auth.emailRequired);
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      setErrorMessage(passwordError);
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage(t.auth.passwordMismatch);
      return;
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
          autoComplete="new-password"
        />
        <div className="mt-1 text-xs text-slate-500">{t.auth.passwordHint}</div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm text-slate-300">{t.auth.confirmPassword}</label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-white/5 dark:text-white"
          placeholder="Strong123"
          autoComplete="new-password"
        />
      </div>

      {errorMessage ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 px-3 py-2 text-sm text-rose-200">
          {errorMessage}
        </div>
      ) : null}

      {successMessage ? (
        <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/30 px-3 py-2 text-sm text-emerald-200">
          {successMessage}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="secondary-button w-full disabled:cursor-not-allowed disabled:opacity-60"
      >
        {mutation.isPending ? t.auth.creating : t.auth.register}
      </button>
    </form>
  );
}
