import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function AdminReauthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    isAuthenticated,
    isLoading,
    user,
    login,
    markAdminReauthenticated,
  } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="rounded-2xl border border-hospital-200 bg-white px-6 py-5 text-center text-sm text-hospital-700 shadow-soft">
          Verifying hospital access...
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user?.username) {
    return (
      <Navigate
        to="/"
        replace
        state={{ from: location.state?.from || "/admin/dashboard" }}
      />
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!password) {
      setError("Enter your admin password to continue.");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const result = await login({ username: user.username, password });
      if (!result.success) {
        setError(result.error || "Could not verify admin access.");
        return;
      }

      markAdminReauthenticated();
      const requestedPath = location.state?.from;
      const nextPath =
        requestedPath?.startsWith("/admin/") && requestedPath !== "/admin/login"
          ? requestedPath
          : "/admin/dashboard";
      navigate(nextPath, { replace: true });
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Could not verify admin access.");
    } finally {
      setPassword("");
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-hospital-50 px-4 py-8">
      <section className="w-full max-w-xl rounded-3xl border border-hospital-200 bg-white p-6 shadow-soft sm:p-10">
        <p className="mb-3 inline-flex rounded-full border border-care-200 bg-care-50 px-4 py-2 text-sm font-semibold text-care-800">
          ADMIN VERIFICATION
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-hospital-900 sm:text-4xl">
          Re-enter your password
        </h1>
        <p className="mt-3 text-base leading-7 text-hospital-700">
          Confirm it is you before opening the hospital admin reports.
        </p>

        <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
          <div>
            <p className="text-sm font-semibold text-hospital-800">Admin account</p>
            <p className="mt-1 rounded-xl border border-hospital-200 bg-hospital-50 px-4 py-3 text-hospital-700">
              {user.username}
            </p>
          </div>

          <label className="block text-sm font-semibold text-hospital-800" htmlFor="admin-reauth-password">
            Password
            <input
              id="admin-reauth-password"
              className="mt-2 w-full rounded-xl border border-hospital-300 bg-white px-4 py-3 text-base font-normal text-hospital-900 outline-none focus:border-hospital-500 focus:ring-2 focus:ring-hospital-100"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              autoFocus
            />
          </label>

          {error ? <p className="text-sm font-medium text-red-700" role="alert">{error}</p> : null}

          <button className="btn btn-primary w-full" type="submit" disabled={submitting}>
            {submitting ? "Verifying..." : "Unlock Admin Reports"}
          </button>
        </form>
      </section>
    </main>
  );
}
