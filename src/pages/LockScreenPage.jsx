import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import LockScreen from "../components/LockScreen";
import { useAuth } from "../auth/AuthContext";

export default function LockScreenPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    authError,
    clearAuthError,
    isAuthenticated,
    isLoading,
    login,
  } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      const nextPath = location.state?.from || "/welcome";
      navigate(nextPath, { replace: true });
    }
  }, [isAuthenticated, location.state, navigate]);

  async function handleSubmit(form) {
    setSubmitting(true);
    setLocalError("");
    clearAuthError();

    try {
      const result = await login(form);
      if (result.success) {
        const nextPath = location.state?.from || "/welcome";
        navigate(nextPath, { replace: true });
      } else if (result.error) {
        setLocalError(result.error);
      }
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Could not sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="rounded-2xl border border-hospital-200 bg-white px-6 py-5 text-center text-sm text-hospital-700 shadow-soft">
          Checking saved hospital access...
        </div>
      </div>
    );
  }

  return (
    <LockScreen
      onSubmit={handleSubmit}
      loading={submitting}
      error={localError || authError}
    />
  );
}
