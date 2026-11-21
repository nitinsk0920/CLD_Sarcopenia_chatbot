import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute({
  allowedRoles = [],
  redirectTo = "/",
  requireAdminReauth = false,
}) {
  const location = useLocation();
  const { isAuthenticated, hasRole, isLoading, adminReauthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="rounded-2xl border border-hospital-200 bg-white px-6 py-5 text-center text-sm text-hospital-700 shadow-soft">
          Verifying hospital access...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace state={{ from: location.pathname }} />;
  }

  if (allowedRoles.length && !hasRole(allowedRoles)) {
    const nextPath = "/";
    return <Navigate to={nextPath} replace state={{ from: location.pathname }} />;
  }

  if (requireAdminReauth && !adminReauthenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
