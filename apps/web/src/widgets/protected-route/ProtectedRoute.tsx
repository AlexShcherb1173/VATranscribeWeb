import { Navigate, Outlet, useLocation } from "react-router-dom";

import { hasAccessToken } from "@/shared/auth/token";
import { saveRedirectAfterLogin } from "@/shared/auth/navigation";
import { useCurrentUserQuery } from "@/shared/hooks/useCurrentUserQuery";
import { Spinner } from "@/shared/ui/Spinner";

export function ProtectedRoute() {
  const location = useLocation();

  if (!hasAccessToken()) {
    const path = `${location.pathname}${location.search}${location.hash}`;
    saveRedirectAfterLogin(path);

    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  const { isLoading, isError } = useCurrentUserQuery();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="flex items-center gap-3">
          <Spinner />
          <span>Loading session...</span>
        </div>
      </div>
    );
  }

  if (isError) {
    const path = `${location.pathname}${location.search}${location.hash}`;
    saveRedirectAfterLogin(path);

    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return <Outlet />;
}