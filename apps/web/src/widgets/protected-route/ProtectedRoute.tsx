import { Navigate, Outlet, useLocation } from "react-router-dom";

import { saveRedirectAfterLogin } from "@/shared/auth/navigation";
import { useCurrentUserQuery } from "@/shared/hooks/useCurrentUserQuery";

export function ProtectedRoute() {
  const location = useLocation();
  const { data: user, isLoading, isFetching } = useCurrentUserQuery();

  if (isLoading || isFetching) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-sm text-slate-300">
        Loading secure session...
      </div>
    );
  }

  if (!user) {
    const currentPath = `${location.pathname || ""}${location.search || ""}${location.hash || ""}`;
    if (currentPath && currentPath !== "/" && currentPath !== "/auth") {
      saveRedirectAfterLogin(currentPath);
    }
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
