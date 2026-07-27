import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-16 text-slate-100">
      <section className="w-full max-w-2xl rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl shadow-cyan-950/30">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-cyan-300">404</p>
        <h1 className="mt-4 text-3xl font-semibold text-white md:text-4xl">Page not found</h1>
        <p className="mt-4 text-sm leading-7 text-slate-300 md:text-base">
          The requested workspace page does not exist or is unavailable for the current account.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            to="/app"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Open dashboard
          </Link>
          <Link
            to="/"
            className="rounded-2xl border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:border-cyan-300 hover:text-cyan-200"
          >
            Open start page
          </Link>
        </div>
      </section>
    </main>
  );
}
