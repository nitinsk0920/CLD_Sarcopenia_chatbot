import { apiFetch } from "./apiClient";

export function loginAdmin({ username, password }) {
  return apiFetch("/auth/login", {
    method: "POST",
    auth: false,
    body: {
      username,
      password,
    },
    fallbackMessage: "Could not sign in.",
  });
}

export function fetchSubscriptionStatus(token) {
  return apiFetch("/subscription/status", {
    token,
    fallbackMessage: "Could not verify subscription status.",
  });
}
