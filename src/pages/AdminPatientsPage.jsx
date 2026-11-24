import { useEffect, useMemo, useState } from "react";
import AdminLayout from "../components/AdminLayout";
import {
  deleteAdminPatientData,
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
  if (!values?.length) return "Not recorded";
  return values.map(formatValue).join(", ");
}

const readableValues = {
  en: "English", hi: "Hindi", kn: "Kannada", mr: "Marathi", notSure: "Not sure",
  cld: "Chronic Liver Disease", sarcopenia: "Sarcopenia", diet: "Diet and nutrition", exercise: "Exercise and movement", safety: "Safety",
  beginner: "Beginner", developing: "Developing", good: "Good", excellent: "Excellent",
  age_18_30: "18–30 years", age_31_45: "31–45 years", age_46_60: "46–60 years", age_61_plus: "61 years and above",
  male: "Male", female: "Female", other: "Other", married: "Married", unmarried: "Unmarried", widowed: "Widowed", divorced_separated: "Divorced / Separated",
  noFormalEducation: "No formal education", primaryEducation: "Primary education", secondaryEducation: "Secondary education", higherSecondary: "Higher secondary", graduateAndAbove: "Graduate and above",
  employed: "Employed", unemployed: "Unemployed", homemaker: "Homemaker", retired: "Retired", nuclear: "Nuclear", joint: "Joint", extended: "Extended", rural: "Rural", urban: "Urban", hindu: "Hindu", muslim: "Muslim", christian: "Christian", religion_other: "Other", socioeconomic_lower: "Lower", socioeconomic_middle: "Middle", socioeconomic_upper: "Upper",
  vegetarian: "Vegetarian", mixed: "Mixed (vegetarian and non-vegetarian)", nonVegetarian: "Non-vegetarian (legacy response)", alcohol: "Alcohol consumption", smoking: "Smoking", tobacco: "Tobacco chewing", tobacco_chewing: "Tobacco chewing", none: "None",
  less_than_1_year: "Less than 1 year", one_to_five_years: "1–5 years", six_to_ten_years: "6–10 years", more_than_10_years: "More than 10 years",
  alcohol_related: "Alcohol-related liver disease", viral_hepatitis: "Viral hepatitis (Hepatitis B/C)", fatty_liver: "Fatty liver disease (MASLD/MASH)", etiology_other: "Other documented cause",
  compensated_cirrhosis: "Compensated cirrhosis", decompensated_cirrhosis: "Decompensated cirrhosis", stage_other: "Other documented CLD stage", not_documented: "Not documented / unknown",
  diabetes: "Diabetes mellitus", hypertension: "Hypertension", comorbidity_other: "Other comorbidity", no_known_comorbidities: "No known comorbidities",
  less_than_6_months: "Less than 6 months", six_to_twelve_months: "6–12 months", more_than_1_year: "More than 1 year",
  medical_management_only: "Medical management only", medical_nutrition: "Medical management with nutritional supplementation", treatment_other: "Other treatment", complications_management: "Management of CLD complications",
  never: "Never", once: "Once", twice: "Twice", three_or_more: "Three or more times", yes: "Yes", no: "No", not_sure: "Not sure",
  education_none: "No previous education", education_cld: "Education about CLD only", education_sarcopenia: "Education about sarcopenia only", education_both: "Education about both CLD and sarcopenia",
};

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not recorded";
  if (Array.isArray(value)) return value.length ? value.map(formatValue).join(", ") : "Not recorded";
  return readableValues[value] || String(value).replaceAll("_", " ");
}

const socioFields = [
  ["Age group", "ageGroup"], ["Gender", "gender"], ["Marital status", "maritalStatus"],
  ["Educational status", "educational_qualification"], ["Occupation", "occupation"],
  ["Type of family", "familyType"], ["Place of residence", "residence"], ["Religion", "religion"],
  ["Dietary pattern", "diet_type"], ["Habits", "habits"], ["Socioeconomic status", "socioeconomicStatus"],
];
const clinicalFields = [
  ["CLD duration", "cldDuration"], ["CLD etiology", "cldEtiology", "cldEtiologyOther"],
  ["CLD stage", "cldStage", "cldStageOther"], ["Comorbidities", "comorbidities", "comorbiditiesOther"],
  ["Sarcopenia duration", "sarcopeniaDuration"], ["Current CLD treatment", "cldTreatment", "cldTreatmentOther"],
  ["Hospitalizations due to CLD", "hospitalizationHistory"], ["Nutritional counselling", "nutritionalCounselling"],
  ["Previous health education", "previousHealthEducation"],
];

function ProfileSection({ title, fields, patient }) {
  return (
    <div className="rounded-xl border border-hospital-200 bg-white p-4">
      <p className="font-semibold text-hospital-900">{title}</p>
      <div className="mt-3 grid gap-2 text-sm text-hospital-800 sm:grid-cols-2">
        {fields.map(([label, key, detailKey]) => {
          const value = patient[key];
          const detail = detailKey ? patient[detailKey] : "";
          const rendered = key === "habits" || key === "comorbidities" ? formatList(value) : formatValue(value);
          return <p key={key}><strong>{label}:</strong> {detail ? `${rendered} — ${detail}` : rendered}</p>;
        })}
      </div>
    </div>
  );
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

      <div className="grid gap-4">
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Patient Information</p>
          <div className="mt-3 grid gap-2 text-sm text-hospital-800">
            <p><strong>Patient ID:</strong> {detail.patient.patient_id}</p>
            <p><strong>Patient ID:</strong> {detail.patient.patient_id}</p>
            <p><strong>Recorded age (legacy):</strong> {formatValue(detail.patient.age)}</p>
            <p><strong>Language:</strong> {formatValue(detail.patient.language)}</p>
            <p><strong>CLD with Sarcopenia:</strong> {formatValue(detail.patient.cld_status)}</p>
            <p><strong>Exercise habit:</strong> {formatValue(detail.patient.exercise_habit)}</p>
            <p><strong>Symptoms:</strong> {formatList(detail.patient.symptoms)}</p>
          </div>
        </div>

        <ProfileSection title="Socio-Demographic Information" fields={socioFields} patient={detail.patient} />
        <ProfileSection title="Clinical Information" fields={clinicalFields} patient={detail.patient} />

        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Session and Score Summary</p>
          <div className="mt-3 grid gap-2 text-sm text-hospital-800">
            <p><strong>Pre-test score:</strong> {detail.pre_test ? `${detail.pre_test.score} / ${detail.pre_test.total_questions}` : "Not recorded"}</p>
            <p><strong>Post-test score:</strong> {detail.post_test ? `${detail.post_test.score} / ${detail.post_test.total_questions}` : "Not recorded"}</p>
            <p><strong>Score improvement:</strong> {formatValue(detail.report.improvement)}</p>
            <p><strong>Post-test performance level:</strong> {formatValue(detail.report.post_score_level)}</p>
          </div>
        </div>

        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Programme Completion</p>
          <div className="mt-3 grid gap-2 text-sm text-hospital-800">
            <p><strong>Status:</strong> {formatValue(detail.report.completion_status)}</p>
            <p><strong>Session start:</strong> {formatDateTime(detail.session.session_start_time)}</p>
            <p><strong>Session end:</strong> {formatDateTime(detail.session.session_end_time)}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Educational Improvement</p>
          <p className="mt-3 text-sm text-hospital-800">
            Pre-test {detail.report.pre_test_score ?? "Not recorded"} → Post-test {detail.report.post_test_score ?? "Not recorded"}
          </p>
          <p className="mt-2 text-sm text-hospital-800">
            <strong>Weak topics requiring further education:</strong> {formatList(detail.report.weak_topics)}
          </p>
        </div>
        <div className="rounded-xl border border-hospital-200 bg-white p-4">
          <p className="font-semibold text-hospital-900">Learning Summary</p>
          <p className="mt-3 text-sm text-hospital-800">{detail.report.learning_summary || "No summary saved."}</p>
          <p className="mt-3 text-sm text-hospital-800">
            <strong>Weak topics:</strong> {formatList(detail.report.weak_topics)}
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
  const [deletingPatientId, setDeletingPatientId] = useState("");
  const [error, setError] = useState("");
  const [deletionError, setDeletionError] = useState("");
  const [deletionSuccess, setDeletionSuccess] = useState("");
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

  async function handleDeletePatient(patientId) {
    const normalizedPatientId = String(patientId || "").trim();
    if (!normalizedPatientId) {
      setDeletionError("This report does not include a patient ID, so it cannot be deleted here.");
      return;
    }
    const confirmed = window.confirm(
      `Permanently delete all data for Patient ID ${normalizedPatientId}?\n\n` +
        "This includes the patient profile, sessions, quiz results, reports, chat history, and generated session audio. This action cannot be undone."
    );
    if (!confirmed) return;

    setDeletingPatientId(normalizedPatientId);
    setDeletionError("");
    setDeletionSuccess("");
    try {
      await deleteAdminPatientData(normalizedPatientId);
      const belongsToDeletedPatient = (report) =>
        String(report.patient_code || report.patient_id || "") === normalizedPatientId;
      setReports((current) => current.filter((report) => !belongsToDeletedPatient(report)));
      if (expandedReportId && reports.some((report) =>
        report.report_id === expandedReportId && belongsToDeletedPatient(report)
      )) {
        setExpandedReportId("");
        setReportDetail(null);
      }
      setDeletionSuccess(`Patient ${normalizedPatientId} and associated data were deleted.`);
      try {
        setReports(await fetchAdminReports());
      } catch {
        setDeletionError("The patient was deleted, but the list could not refresh. Reload this page to verify.");
      }
    } catch (deleteError) {
      setDeletionError(
        deleteError instanceof Error ? deleteError.message : "Could not delete this patient. Please try again."
      );
    } finally {
      setDeletingPatientId("");
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
          {deletionError ? <p className="mt-4 error-text" role="alert">{deletionError}</p> : null}
          {deletionSuccess ? <p className="mt-4 text-sm font-medium text-care-700" role="status">{deletionSuccess}</p> : null}

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
                      <th className="px-4 py-3 font-semibold">Actions</th>
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
                            <div className="flex flex-wrap gap-2">
                              <button
                                type="button"
                                className="btn btn-secondary !min-h-10 !px-3 !py-2 text-sm"
                                onClick={() => toggleExpand(report.report_id)}
                              >
                                {isOpen ? "Hide Report" : "View Report"}
                              </button>
                              <button
                                type="button"
                                className="btn !min-h-10 !border-red-200 !bg-red-50 !px-3 !py-2 text-sm !text-red-700 hover:!bg-red-100"
                                onClick={() => handleDeletePatient(report.patient_code || report.patient_id)}
                                disabled={Boolean(deletingPatientId)}
                              >
                                {deletingPatientId === String(report.patient_code || report.patient_id || "")
                                  ? "Deleting..."
                                  : "Delete Patient"}
                              </button>
                            </div>
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
