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

export function RegisterForm({ onRegistered, redirectTo }: RegisterFormProps) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [acceptedLegalDocuments, setAcceptedLegalDocuments] = useState(false);

  function validatePassword(value: string): string | null {
    if (value.length < 8) return t.auth.passwordMin;
    if (!/[a-z]/.test(value)) return t.auth.passwordLower;
    if (!/[A-Z]/.test(value)) return t.auth.passwordUpper;
    if (!/\d/.test(value)) return t.auth.passwordDigit;
    if (/\s/.test(value)) return t.auth.passwordSpaces;
    return null;
  }

  const mutation = useMutation({
    mutationFn: async (payload: { email: string; password: string; accepted_legal_documents: { document_type: string; document_version: string; accepted: boolean }[] }) => {
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
      setShowPassword(false);
      setShowConfirmPassword(false);

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

    setSuccessMessage(null);

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

    if (!acceptedLegalDocuments) {
      setErrorMessage("Необходимо принять условия сервиса и политику конфиденциальности.");
      return;
    }

    setErrorMessage(null);

    mutation.mutate({
      email: email.trim(),
      password,
      accepted_legal_documents: [
        { document_type: "terms", document_version: "2.0", accepted: true },
        { document_type: "privacy", document_version: "2.0", accepted: true },
        { document_type: "personal_data", document_version: "2.0", accepted: true },
      ],
    });
  }

  const showPasswordLabel = t.auth.showPassword ?? "Show password";
  const hidePasswordLabel = t.auth.hidePassword ?? "Hide password";
  const showConfirmPasswordLabel = t.auth.showConfirmPassword ?? showPasswordLabel;
  const hideConfirmPasswordLabel = t.auth.hideConfirmPassword ?? hidePasswordLabel;

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
            autoComplete="new-password"
          />
          <PasswordVisibilityButton
            visible={showPassword}
            labelShow={showPasswordLabel}
            labelHide={hidePasswordLabel}
            onToggle={() => setShowPassword((value) => !value)}
          />
        </div>
        <div className="mt-1 text-xs text-slate-500">{t.auth.passwordHint}</div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm text-slate-300">{t.auth.confirmPassword}</label>
        <div className="relative">
          <input
            type={showConfirmPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-950 outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-white/5 dark:text-white"
            placeholder="Strong123"
            autoComplete="new-password"
          />
          <PasswordVisibilityButton
            visible={showConfirmPassword}
            labelShow={showConfirmPasswordLabel}
            labelHide={hideConfirmPasswordLabel}
            onToggle={() => setShowConfirmPassword((value) => !value)}
          />
        </div>
      </div>

      <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 text-xs leading-5 text-slate-300">
        <input
          type="checkbox"
          checked={acceptedLegalDocuments}
          onChange={(event) => setAcceptedLegalDocuments(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-950"
        />
        <span>
          Я принимаю условия сервиса, политику конфиденциальности и согласие на обработку персональных данных.
        </span>
      </label>

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
        className="flex w-full items-center justify-center rounded-2xl bg-cyan-300 px-5 py-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 focus:outline-none focus:ring-2 focus:ring-cyan-200/80 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {mutation.isPending ? t.auth.creating : t.auth.register}
      </button>
    </form>
  );
}
