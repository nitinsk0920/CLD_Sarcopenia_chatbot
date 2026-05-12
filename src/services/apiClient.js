import {
  clearStoredAuthSession,
  dispatchAuthExpired,
  getStoredAuthSession,
} from "../auth/authStorage";

const CHAT_URL =
  import.meta.env.VITE_CHATBOT_API_URL || "http://127.0.0.1:8000/api/chat";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getApiBaseUrl() {
  return CHAT_URL.replace(/\/api\/chat$/, "");
}

async function readErrorDetail(response, fallbackMessage) {
  try {
    const errorData = await response.json();
    if (errorData?.detail) {
      return errorData.detail;
    }
  } catch {
    // Keep fallback message.
  }
  return fallbackMessage;
}

export async function apiFetch(
  path,
  {
    method = "GET",
    headers,
    body,
    auth = true,
    token,
    responseType = "json",
    fallbackMessage = "Request failed.",
    ...rest
  } = {}
) {
  const sessionToken = token || getStoredAuthSession()?.token || "";
  const finalHeaders = new Headers(headers || {});

  if (auth && sessionToken) {
    finalHeaders.set("Authorization", `Bearer ${sessionToken}`);
  }

  if (body && !(body instanceof FormData) && !finalHeaders.has("Content-Type")) {
    finalHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(
    path.startsWith("http") ? path : `${getApiBaseUrl()}${path}`,
    {
      method,
      headers: finalHeaders,
      body:
        body && !(body instanceof FormData) && typeof body !== "string"
          ? JSON.stringify(body)
          : body,
      ...rest,
    }
  );

  if (!response.ok) {
    const detail = await readErrorDetail(response, fallbackMessage);
    if (auth && (response.status === 401 || response.status === 403)) {
      clearStoredAuthSession();
      dispatchAuthExpired(detail);
    }
    throw new ApiError(detail, response.status);
  }

  if (responseType === "blob") {
    return response.blob();
  }

  if (responseType === "text") {
    return response.text();
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
