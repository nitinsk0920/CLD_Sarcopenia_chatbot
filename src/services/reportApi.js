import { apiFetch, getApiBaseUrl } from "./apiClient";

export { getApiBaseUrl };

export function startPatientReportSession(payload) {
  return apiFetch("/session/start", {
    method: "POST",
    body: payload,
    fallbackMessage: "Could not start patient report session.",
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
