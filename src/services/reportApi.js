import { apiFetch, getApiBaseUrl } from "./apiClient";

export { getApiBaseUrl };
export const ADMIN_REPORTS_CHANGED_EVENT = "admin:reports-changed";

export function startPatientReportSession(payload) {
  return apiFetch("/session/start", {
    method: "POST",
    body: payload,
    fallbackMessage: "Could not start patient report session.",
  });
}

export function resumePatientReportSession(sessionId) {
  return apiFetch(`/session/${encodeURIComponent(sessionId)}/resume`, {
    fallbackMessage: "Could not restore the active patient session.",
  });
}

export function fetchPatientChatHistory(sessionId) {
  return apiFetch(`/api/chat/session/${encodeURIComponent(sessionId)}/history`, {
    fallbackMessage: "Could not restore the conversation history.",
  });
}

export function clearPatientChatSession(sessionId) {
  return apiFetch(`/api/chat/session/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
    fallbackMessage: "Could not clear the abandoned session.",
  });
}

export function endPatientReportSession(payload) {
  return apiFetch("/session/end", {
    method: "POST",
    body: payload,
    fallbackMessage: "Could not end patient report session.",
  });
}

export function saveFinalPatientReport(payload) {
  return apiFetch("/reports/save-final", {
    method: "POST",
    body: payload,
    fallbackMessage: "Could not save final patient report.",
  });
}

export function fetchAdminReports() {
  return apiFetch("/admin/reports", {
    fallbackMessage: "Could not load admin reports.",
  });
}

export async function deleteAdminPatientData(patientCode) {
  const result = await apiFetch(`/admin/patients/${encodeURIComponent(patientCode)}`, {
    method: "DELETE",
    fallbackMessage: "Could not permanently delete patient data.",
  });
  window.dispatchEvent(new Event(ADMIN_REPORTS_CHANGED_EVENT));
  return result;
}

export function fetchAdminReportDetail(reportId) {
  return apiFetch(`/admin/reports/${reportId}`, {
    fallbackMessage: "Could not load report detail.",
  });
}

export async function downloadAdminReport(reportId) {
  const blob = await apiFetch(`/admin/reports/${reportId}/download`, {
    responseType: "blob",
    fallbackMessage: "Could not download the report PDF.",
  });

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `patient-report-${reportId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
