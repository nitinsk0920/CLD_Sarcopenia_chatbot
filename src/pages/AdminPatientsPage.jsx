import { useEffect, useMemo, useState } from "react";
import AdminLayout from "../components/AdminLayout";
import {
  downloadAdminReport,
  fetchAdminReportDetail,
  fetchAdminReports,
} from "../services/reportApi";

function formatDateTime(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatList(values) {
  if (!values?.length) return "None";
  return values.join(", ");
}

function ReportDetailCard({ detail, onDownload, downloading }) {
  if (!detail) return null;

  return (
    <div className="grid gap-4 rounded-2xl border border-hospital-200 bg-hospital-50 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-hospital-900">Detailed Patient Report</p>
          <p className="text-sm text-hospital-700">
            Session ID: {detail.session_id} | Generated: {formatDateTime(detail.report.report_generated_at)}
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onDownload}
          disabled={downloading}
        >
          {downloading ? "Preparing PDF..." : "Download Report"}
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Patient Information</p>
          <div className="mt-3 grid gap-2 text-sm text-hospital-800">
            <p><strong>Patient ID:</strong> {detail.patient.patient_id}</p>
            <p><strong>Age:</strong> {detail.patient.age || "-"}</p>
            <p><strong>Gender:</strong> {detail.patient.gender || "-"}</p>
            <p><strong>Educational Qualification:</strong> {detail.patient.educational_qualification || "-"}</p>
            <p><strong>Occupation:</strong> {detail.patient.occupation || "-"}</p>
            <p><strong>Language:</strong> {detail.patient.language || "-"}</p>
            <p><strong>Diet Type:</strong> {detail.patient.diet_type || "-"}</p>
            <p><strong>Alcohol Habit:</strong> {detail.patient.alcohol_habit || "-"}</p>
            <p><strong>Smoking Habit:</strong> {detail.patient.smoking_habit || "-"}</p>
            <p><strong>CLD with Sarcopenia:</strong> {detail.patient.cld_status || "-"}</p>
            <p><strong>Exercise Habit:</strong> {detail.patient.exercise_habit || "-"}</p>
            <p><strong>Symptoms:</strong> {formatList(detail.patient.symptoms)}</p>
          </div>
        </div>

        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Session and Score Summary</p>
          <div className="mt-3 grid gap-2 text-sm text-hospital-800">
            <p><strong>Session start:</strong> {formatDateTime(detail.session.session_start_time)}</p>
            <p><strong>Session end:</strong> {formatDateTime(detail.session.session_end_time)}</p>
            <p><strong>Completion status:</strong> {detail.report.completion_status}</p>
            <p><strong>Pre-test score:</strong> {detail.report.pre_test_score ?? "-"}</p>
            <p><strong>Post-test score:</strong> {detail.report.post_test_score ?? "-"}</p>
            <p><strong>Improvement:</strong> {detail.report.improvement ?? 0}</p>
            <p><strong>Score level:</strong> {detail.report.score_level || "-"}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Learning Summary</p>
          <p className="mt-3 text-sm text-hospital-800">{detail.report.learning_summary || "No summary saved."}</p>
          <p className="mt-3 text-sm text-hospital-800">
            <strong>Weak topics:</strong> {formatList(detail.report.weak_topics)}
          </p>
        </div>

        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Chat Summary</p>
          <p className="mt-3 text-sm text-hospital-800">
            <strong>Short chat summary:</strong> {detail.report.short_chat_summary || "No chat summary saved."}
          </p>
          <p className="mt-3 text-sm text-hospital-800">
            <strong>Completion status:</strong> {detail.report.completion_status || "-"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Pre-test Review</p>
          {detail.pre_test ? (
            <div className="mt-3 grid gap-2 text-sm text-hospital-800">
              <p><strong>Weak topics:</strong> {formatList(detail.pre_test.weak_topics)}</p>
              <p><strong>Submitted:</strong> {formatDateTime(detail.pre_test.submitted_at)}</p>
            </div>
          ) : (
            <p className="mt-3 text-sm text-hospital-800">Pre-test detail is not available.</p>
          )}
        </div>

        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Post-test Review</p>
          {detail.post_test ? (
            <div className="mt-3 grid gap-2 text-sm text-hospital-800">
              <p><strong>Weak topics:</strong> {formatList(detail.post_test.weak_topics)}</p>
              <p><strong>Submitted:</strong> {formatDateTime(detail.post_test.submitted_at)}</p>
            </div>
          ) : (
            <p className="mt-3 text-sm text-hospital-800">Post-test detail is not available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AdminPatientsPage({ onAdminLogout }) {
  const [reports, setReports] = useState([]);
  const [expandedReportId, setExpandedReportId] = useState("");
  const [reportDetail, setReportDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadReports() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchAdminReports();
        if (active) {
          setReports(data);
        }
      } catch (loadError) {
        if (active) {
          const message =
            loadError instanceof Error ? loadError.message : "Could not load patient reports.";
          setError(message);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadReports();
    return () => {
      active = false;
    };
  }, []);

  const reportRows = useMemo(() => reports, [reports]);

  async function toggleExpand(reportId) {
    if (expandedReportId === reportId) {
      setExpandedReportId("");
      setReportDetail(null);
      setDetailError("");
      return;
    }

    setExpandedReportId(reportId);
    setDetailLoading(true);
    setDetailError("");
    try {
      const detail = await fetchAdminReportDetail(reportId);
      setReportDetail(detail);
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : "Could not load report detail.";
      setDetailError(message);
      setReportDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleDownload(reportId) {
    setDownloading(true);
    setDetailError("");
    try {
      await downloadAdminReport(reportId);
    } catch (downloadError) {
      const message =
        downloadError instanceof Error ? downloadError.message : "Could not download report PDF.";
      setDetailError(message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <AdminLayout
      title="Patient Reports"
      subtitle="Open any saved session report for detailed clinical education review and PDF export."
      onLogout={onAdminLogout}
    >
      <div className="stack">
        <section className="question-card">
          <p className="question-title">Stored Report List</p>
          <p className="muted">
            Only completed patient education sessions are shown here for admin review.
          </p>

          {loading ? <p className="mt-4 muted">Loading patient reports...</p> : null}
          {error ? <p className="mt-4 error-text">{error}</p> : null}

          {!loading && !error ? (
            reportRows.length ? (
              <div className="mt-4 overflow-x-auto rounded-xl border border-hospital-200">
                <table className="min-w-full divide-y divide-hospital-200 text-sm">
                  <thead className="bg-hospital-50 text-left text-hospital-700">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Patient ID</th>
                      <th className="px-4 py-3 font-semibold">Age</th>
                      <th className="px-4 py-3 font-semibold">Language</th>
                      <th className="px-4 py-3 font-semibold">Pre-test</th>
                      <th className="px-4 py-3 font-semibold">Post-test</th>
                      <th className="px-4 py-3 font-semibold">Improvement</th>
                      <th className="px-4 py-3 font-semibold">Completion</th>
                      <th className="px-4 py-3 font-semibold">Report</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hospital-100 bg-white">
                    {reportRows.map((report) => {
                      const isOpen = expandedReportId === report.report_id;
                      return (
                        <tr key={report.report_id}>
                          <td className="px-4 py-3 font-semibold text-hospital-900">{report.patient_id}</td>
                          <td className="px-4 py-3 text-hospital-700">{report.age ?? "-"}</td>
                          <td className="px-4 py-3 text-hospital-700">{report.language || "-"}</td>
                          <td className="px-4 py-3 text-hospital-700">{report.pre_test_score ?? "-"}</td>
                          <td className="px-4 py-3 text-hospital-700">{report.post_test_score ?? "-"}</td>
                          <td className="px-4 py-3 font-semibold text-care-700">{report.improvement ?? 0}</td>
                          <td className="px-4 py-3 text-hospital-700">{report.completion_status}</td>
                          <td className="px-4 py-3">
                            <button
                              type="button"
                              className="btn btn-secondary !min-h-10 !px-3 !py-2 text-sm"
                              onClick={() => toggleExpand(report.report_id)}
                            >
                              {isOpen ? "Hide Report" : "View Report"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 muted">
                No reports have been saved yet. Complete a patient journey to generate the first report.
              </p>
            )
          ) : null}
        </section>

        {expandedReportId ? (
          <section className="question-card">
            {detailLoading ? <p className="muted">Loading full report detail...</p> : null}
            {detailError ? <p className="error-text">{detailError}</p> : null}
            {!detailLoading && !detailError && reportDetail ? (
              <ReportDetailCard
                detail={reportDetail}
                downloading={downloading}
                onDownload={() => handleDownload(reportDetail.report_id)}
              />
            ) : null}
          </section>
        ) : null}
      </div>
    </AdminLayout>
  );
}
