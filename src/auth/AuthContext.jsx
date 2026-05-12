import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  AUTH_SESSION_EXPIRED_EVENT,
  clearStoredAuthSession,
  getStoredAuthSession,
  isTokenExpired,
  parseJwtToken,
  persistAuthSession,
} from "./authStorage";
import { fetchSubscriptionStatus, loginAdmin } from "../services/authApi";

const AuthContext = createContext(null);

function buildSession(token, subscription = null) {
  if (!token || isTokenExpired(token)) return null;

  const payload = parseJwtToken(token);
  if (!payload?.sub) return null;

  return {
    token,
    role: payload.role || "admin",
    user: {
      id: payload.admin_id || payload.sub,
      username: payload.sub,
      role: payload.role || "admin",
    },
    payload,
    subscription,
  };
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const storedSession = getStoredAuthSession();
      const token = storedSession?.token;
      const nextSession = buildSession(token, storedSession?.subscription || null);

      if (!nextSession) {
        clearStoredAuthSession();
        if (active) {
          setSession(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const subscription = await fetchSubscriptionStatus(nextSession.token);
        if (!subscription?.can_access) {
          clearStoredAuthSession();
          if (active) {
            setSession(null);
            setAuthError("Subscription expired. Please renew access to continue.");
          }
          return;
        }

        if (active) {
          setSession({
            ...nextSession,
            subscription,
          });
        }
      } catch (error) {
        clearStoredAuthSession();
        if (active) {
          setSession(null);
          setAuthError(
            error instanceof Error ? error.message : "Please sign in to continue."
          );
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    function handleAuthExpired(event) {
      clearStoredAuthSession();
      setSession(null);
      setAuthError(event.detail?.message || "Your session has expired. Please sign in again.");
      setIsLoading(false);
    }

    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handleAuthExpired);
    restoreSession();

    return () => {
      active = false;
      window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handleAuthExpired);
    };
  }, []);

  useEffect(() => {
    if (!session) {
      clearStoredAuthSession();
      return;
    }

    persistAuthSession({
      token: session.token,
      subscription: session.subscription,
    });
  }, [session]);

  async function login(credentials) {
    setAuthError("");
    const response = await loginAdmin(credentials);
    const nextSession = buildSession(response.access_token);

    if (!nextSession) {
      throw new Error("Received an invalid login token.");
    }

    const subscription = await fetchSubscriptionStatus(nextSession.token);
    if (!subscription?.can_access) {
      clearStoredAuthSession();
      setSession(null);
      setAuthError("Subscription expired. Please renew access to continue.");
      return {
        success: false,
        error: "Subscription expired. Please renew access to continue.",
      };
    }

    setSession({
      ...nextSession,
      subscription,
    });

    return {
      success: true,
      session: {
        ...nextSession,
        subscription,
      },
    };
  }

  function logout() {
    clearStoredAuthSession();
    setAuthError("");
    setSession(null);
  }

  function clearAuthError() {
    setAuthError("");
  }

  function hasRole(allowedRoles) {
    if (!session?.role) return false;
    return allowedRoles.includes(session.role);
  }

  const value = useMemo(
    () => ({
      token: session?.token || null,
      role: session?.role || null,
      user: session?.user || null,
      payload: session?.payload || null,
      subscription: session?.subscription || null,
      isAuthenticated: Boolean(session?.token),
      isAdmin: session?.role === "admin",
      isLoading,
      authError,
      login,
      logout,
      hasRole,
      clearAuthError,
    }),
    [authError, isLoading, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
