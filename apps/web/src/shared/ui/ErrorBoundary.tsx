import React, { PropsWithChildren } from "react";

import { captureFrontendException } from "@/shared/observability/sentry";

const isDevelopment = import.meta.env.DEV;

type ErrorBoundaryState = {
  hasError: boolean;
  message: string | null;
};

export class ErrorBoundary extends React.Component<
  PropsWithChildren,
  ErrorBoundaryState
> {
  constructor(props: PropsWithChildren) {
    super(props);

    this.state = {
      hasError: false,
      message: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      message: error.message,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    captureFrontendException(error);
    console.error("VATranscribe runtime error:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-100">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900/80 p-8">
            <div className="text-sm font-medium uppercase tracking-[0.22em] text-rose-400">
              VATranscribe
            </div>
            <h1 className="mt-3 text-2xl font-semibold text-white">
              Interface temporarily unavailable
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              The workspace could not render this view. Reload the page or return to the dashboard.
            </p>

            {isDevelopment && this.state.message ? (
              <pre className="mt-4 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-300">
                {this.state.message}
              </pre>
            ) : null}

            <button
              type="button"
              onClick={this.handleReload}
              className="mt-6 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-400"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
