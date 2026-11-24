import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AdminLayout from "../components/AdminLayout";
import {
  ADMIN_REPORTS_CHANGED_EVENT,
  fetchAdminReports,
} from "../services/reportApi";

function getAverage(values) {
  if (!values.length) return "0.0";
  const total = values.reduce((sum, value) => sum + value, 0);
  return (total / values.length).toFixed(1);
}

export default function AdminDashboardPage({ onAdminLogout }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
            loadError instanceof Error ? loadError.message : "Could not load admin reports.";
          setError(message);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    window.addEventListener(ADMIN_REPORTS_CHANGED_EVENT, loadReports);
    loadReports();
    return () => {
      active = false;
      window.removeEventListener(ADMIN_REPORTS_CHANGED_EVENT, loadReports);
    };
  }, []);

  const metrics = useMemo(() => {
    const completed = reports.filter((item) => item.completion_status === "completed");
    return {
      totalPatients: reports.length,
      completedSessions: completed.length,
      averagePre: getAverage(reports.map((item) => item.pre_test_score || 0)),
      averagePost: getAverage(reports.map((item) => item.post_test_score || 0)),
      averageImprovement: getAverage(reports.map((item) => item.improvement || 0)),
      topImprovement: reports
        .slice()
        .sort((a, b) => (b.improvement || 0) - (a.improvement || 0))
        .slice(0, 3),
    };
  }, [reports]);

  return (
    <AdminLayout
      title="Admin Reports Dashboard"
      subtitle="Review completed patient education sessions stored in Supabase PostgreSQL."
      onLogout={onAdminLogout}
    >
      <div className="stack">
        <section className="admin-grid">
          <article className="admin-stat">
            <p className="admin-stat-label">Total patient reports</p>
            <p className="admin-stat-value">{metrics.totalPatients}</p>
          </article>
          <article className="admin-stat">
            <p className="admin-stat-label">Completed sessions</p>
            <p className="admin-stat-value">{metrics.completedSessions}</p>
          </article>
          <article className="admin-stat">
            <p className="admin-stat-label">Average improvement</p>
            <p className="admin-stat-value">{metrics.averageImprovement}</p>
          </article>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="question-card">
            <p className="question-title">Average quiz scores</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-hospital-200 bg-hospital-50 p-4">
                <p className="admin-stat-label">Average pre-test</p>
                <p className="mt-2 text-2xl font-bold text-hospital-900">{metrics.averagePre}</p>
              </div>
              <div className="rounded-xl border border-care-200 bg-care-50 p-4">
                <p className="admin-stat-label">Average post-test</p>
                <p className="mt-2 text-2xl font-bold text-hospital-900">{metrics.averagePost}</p>
              </div>
            </div>
          </article>

          <article className="question-card">
            <p className="question-title">Improvement snapshot</p>
            {metrics.topImprovement.length ? (
              <ul className="simple-list">
                {metrics.topImprovement.map((item) => (
                  <li key={item.report_id}>
                    {item.patient_id}: improved by {item.improvement || 0} points
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Completed reports will appear here after patient sessions finish.</p>
            )}
          </article>
        </section>

        <section className="question-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="question-title">Recent stored reports</p>
              <p className="muted">
                Open the report list to review full patient detail, quiz summary, and PDF download.
              </p>
            </div>
            <Link to="/admin/patients" className="btn btn-primary">
              Open Report List
            </Link>
          </div>

          {loading ? <p className="mt-4 muted">Loading reports...</p> : null}
          {error ? <p className="mt-4 error-text">{error}</p> : null}

          {!loading && !error ? (
            reports.length ? (
              <div className="mt-4 overflow-x-auto rounded-xl border border-hospital-200">
                <table className="min-w-full divide-y divide-hospital-200 text-sm">
                  <thead className="bg-hospital-50 text-left text-hospital-700">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Patient ID</th>
                      <th className="px-4 py-3 font-semibold">Session</th>
                      <th className="px-4 py-3 font-semibold">Pre-test</th>
                      <th className="px-4 py-3 font-semibold">Post-test</th>
                      <th className="px-4 py-3 font-semibold">Improvement</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hospital-100 bg-white">
                    {reports.slice(0, 6).map((item) => (
                      <tr key={item.report_id}>
                        <td className="px-4 py-3 font-semibold text-hospital-900">{item.patient_id}</td>
                        <td className="px-4 py-3 text-hospital-700">{item.session_id}</td>
                        <td className="px-4 py-3 text-hospital-700">{item.pre_test_score ?? "-"}</td>
                        <td className="px-4 py-3 text-hospital-700">{item.post_test_score ?? "-"}</td>
                        <td className="px-4 py-3 font-semibold text-care-700">{item.improvement ?? 0}</td>
                        <td className="px-4 py-3 text-hospital-700">{item.completion_status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 muted">
                No saved reports yet. Once a patient completes the full flow, the report will appear here.
              </p>
            )
          ) : null}
        </section>
      </div>
    </AdminLayout>
  );
}
