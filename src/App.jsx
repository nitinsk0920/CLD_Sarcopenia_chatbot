import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import WelcomePage from "./pages/WelcomePage";
import LockScreenPage from "./pages/LockScreenPage";
import PatientFormPage from "./pages/PatientFormPage";
import PreTestPage from "./pages/PreTestPage";
import WeakTopicSummaryPage from "./pages/WeakTopicSummaryPage";
import WeakTopicLearningPage from "./pages/WeakTopicLearningPage";
import TeachingChatbotPage from "./pages/TeachingChatbotPage";
import LearningTopicPage from "./pages/LearningTopicPage";
import FreeTextQAPage from "./pages/FreeTextQAPage";
import MentalSupportPage from "./pages/MentalSupportPage";
import PostTestPage from "./pages/PostTestPage";
import ResultPage from "./pages/ResultPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import AdminPatientsPage from "./pages/AdminPatientsPage";
import AdminReauthPage from "./pages/AdminReauthPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { buildFinalReportPayload } from "./data/reportPayload";
import { useAuth } from "./auth/AuthContext";
import { getStoredAuthSession, parseJwtToken } from "./auth/authStorage";
import {
  clearPatientChatSession,
  endPatientReportSession,
  saveFinalPatientReport,
  resumePatientReportSession,
  startPatientReportSession,
} from "./services/reportApi";
import { initializeGlobalMicroInteractions } from "./utils/uiAnimations";
import { useLanguage } from "./i18n/LanguageContext";

function createInitialPatient() {
  return {
    patientId: "",
    age: null,
    ageGroup: "",
    gender: "",
    maritalStatus: "",
    educationalQualification: "",
    occupation: "",
    familyType: "",
    residence: "",
    religion: "",
    socioeconomicStatus: "",
    cldStatus: "",
    cldDuration: "",
    cldEtiology: "",
    cldEtiologyOther: "",
    cldStage: "",
    cldStageOther: "",
    comorbidities: [],
    comorbiditiesOther: "",
    sarcopeniaDuration: "",
    cldTreatment: "",
    cldTreatmentOther: "",
    hospitalizationHistory: "",
    nutritionalCounselling: "",
    previousHealthEducation: "",
    illnessDuration: "",
    weaknessFatigue: "",
    recentWeightLoss: "",
    dietType: "",
    appetiteLevel: "",
    proteinAwareness: "",
    exerciseRegular: "",
    exerciseType: "",
    exerciseFrequency: "",
    symptoms: [],
    habits: [],
    languagePreference: "",
    digitalLiteracy: "",
  };
}

function createInitialQuizSummary() {
  return {
    score: 0,
    total: 0,
    wrongAnswers: [],
    mistakesByTopic: {
      cld: 0,
      sarcopenia: 0,
      diet: 0,
      exercise: 0,
      safety: 0,
    },
    rankedWeakTopics: [],
    weakTopics: [],
  };
}

function createSessionId() {
  return globalThis.crypto?.randomUUID?.() || `session-${Date.now()}-${Math.round(Math.random() * 1000)}`;
}

function sessionStorageKey(adminId) {
  return `cld-active-patient-session:${adminId}`;
}

function getRememberedSessionId() {
  const token = getStoredAuthSession()?.token;
  const claims = parseJwtToken(token);
  const adminId = claims?.admin_id || claims?.sub;
  return adminId ? window.sessionStorage.getItem(sessionStorageKey(adminId)) || "" : "";
}

function ClearAdminReauthenticationOnExit() {
  const location = useLocation();
  const { clearAdminReauthentication } = useAuth();

  useEffect(() => {
    if (!location.pathname.startsWith("/admin/")) {
      clearAdminReauthentication();
    }
  }, [clearAdminReauthentication, location.pathname]);

  return null;
}

function createInitialReportState(sessionId = createSessionId()) {
  return {
    sessionId,
    startedAt: "",
    started: false,
    reportId: "",
    finalSaved: false,
    saving: false,
    error: "",
  };
}

export default function App() {
  const { logout, user, isLoading: authLoading } = useAuth();
  const { setLanguage } = useLanguage();
  const [patient, setPatient] = useState(createInitialPatient);
  const [preTestScore, setPreTestScore] = useState(null);
  const [weakTopicSummary, setWeakTopicSummary] = useState(createInitialQuizSummary);
  const [postTestScore, setPostTestScore] = useState(null);
  const [postTestSummary, setPostTestSummary] = useState(createInitialQuizSummary);
  const [preTestAnswers, setPreTestAnswers] = useState({});
  const [postTestAnswers, setPostTestAnswers] = useState({});
  const [reportState, setReportState] = useState(() =>
    createInitialReportState(getRememberedSessionId() || undefined)
  );
  const [sessionReady, setSessionReady] = useState(false);
  const [sessionRestoreFailed, setSessionRestoreFailed] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user?.id) {
      setSessionReady(true);
      return;
    }

    const key = sessionStorageKey(user.id);
    const storedSessionId = window.sessionStorage.getItem(key);
    if (!storedSessionId) {
      setSessionRestoreFailed(false);
      setSessionReady(true);
      return;
    }

    let active = true;
    setSessionReady(false);
    resumePatientReportSession(storedSessionId)
      .then((saved) => {
        if (!active) return;
        setPatient({ ...createInitialPatient(), ...(saved.patient || {}) });
        if (saved.patient?.languagePreference) setLanguage(saved.patient.languagePreference);
        setReportState({
          ...createInitialReportState(saved.session_id),
          startedAt: saved.started_at || "",
          started: true,
        });
        setSessionRestoreFailed(false);
      })
      .catch(() => {
        if (!active) return;
        window.sessionStorage.removeItem(key);
        setPatient(createInitialPatient());
        setReportState(createInitialReportState());
        setSessionRestoreFailed(true);
      })
      .finally(() => {
        if (active) setSessionReady(true);
      });

    return () => {
      active = false;
    };
  }, [authLoading, user?.id]);

  useEffect(() => {
    return initializeGlobalMicroInteractions();
  }, []);

  async function handleSessionStart(patientProfile) {
    if (reportState.started) {
      return { success: true };
    }

    const startedAt = new Date().toISOString();
    try {
      await startPatientReportSession({
        session_id: reportState.sessionId,
        started_at: startedAt,
        patient: patientProfile,
      });
      if (user?.id) {
        window.sessionStorage.setItem(sessionStorageKey(user.id), reportState.sessionId);
      }
      setReportState((prev) => ({ ...prev, startedAt, started: true, error: "" }));
      return { success: true };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not start the patient session.";
      setReportState((prev) => ({ ...prev, error: message }));
      return { success: false, error: message };
    }
  }

  async function handlePersistFinalReport() {
    if (reportState.finalSaved || reportState.saving) {
      return { success: true, reportId: reportState.reportId };
    }

    setReportState((prev) => ({ ...prev, saving: true, error: "" }));
    try {
      const payload = buildFinalReportPayload({
        sessionId: reportState.sessionId,
        sessionStartedAt: reportState.startedAt,
        patient,
        preTestSummary: weakTopicSummary,
        postTestSummary,
        preTestAnswers,
        postTestAnswers,
      });
      const result = await saveFinalPatientReport(payload);
      await endPatientReportSession({
        session_id: reportState.sessionId,
        ended_at: new Date().toISOString(),
        completion_status: "completed",
      }).catch(() => null);
      if (user?.id) {
        window.sessionStorage.removeItem(sessionStorageKey(user.id));
      }

      setReportState((prev) => ({
        ...prev,
        saving: false,
        finalSaved: true,
        reportId: result.report_id,
        error: "",
      }));
      return { success: true, reportId: result.report_id };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not save final report.";
      setReportState((prev) => ({
        ...prev,
        saving: false,
        error: message,
      }));
      return { success: false, error: message };
    }
  }

  function resetDemoFlow() {
    if (user?.id) {
      window.sessionStorage.removeItem(sessionStorageKey(user.id));
    }
    setSessionRestoreFailed(false);
    setPatient(createInitialPatient());
    setPreTestScore(null);
    setWeakTopicSummary(createInitialQuizSummary());
    setPostTestScore(null);
    setPostTestSummary(createInitialQuizSummary());
    setPreTestAnswers({});
    setPostTestAnswers({});
    setReportState(createInitialReportState());
  }

  async function discardPatientFlow() {
    const abandonedSessionId = reportState.sessionId;
    try {
      await clearPatientChatSession(abandonedSessionId);
    } catch {
      // The local patient flow is still discarded if server cleanup is unavailable.
    }
    if (user?.id) {
      window.sessionStorage.removeItem(sessionStorageKey(user.id));
    }
    resetDemoFlow();
  }

  if (!sessionReady) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="rounded-2xl border border-hospital-200 bg-white px-6 py-5 text-center text-sm text-hospital-700 shadow-soft">
          Restoring the patient session...
        </div>
      </div>
    );
  }

  const requireActiveSession = (element) =>
    reportState.started && !sessionRestoreFailed ? element : <Navigate to="/welcome" replace />;

  return (
    <BrowserRouter>
      <ClearAdminReauthenticationOnExit />
      <Routes>
        <Route path="/" element={<LockScreenPage />} />
        <Route path="/admin/login" element={<AdminReauthPage />} />
        <Route
          path="/admin-dashboard"
          element={<Navigate to="/admin/dashboard" replace />}
        />
        <Route element={<ProtectedRoute allowedRoles={["admin"]} redirectTo="/" />}>
          <Route path="/welcome" element={<WelcomePage />} />
        </Route>
        <Route
          element={
            <ProtectedRoute
              allowedRoles={["admin"]}
              redirectTo="/"
              requireAdminReauth
            />
          }
        >
          <Route
            path="/admin/dashboard"
            element={
              <AdminDashboardPage onAdminLogout={logout} />
            }
          />
          <Route
            path="/admin/patients"
            element={
              <AdminPatientsPage onAdminLogout={logout} />
            }
          />
        </Route>
        <Route element={<ProtectedRoute allowedRoles={["admin"]} redirectTo="/" />}>
          <Route
            path="/patient-form"
            element={
              <PatientFormPage
                patient={patient}
                setPatient={setPatient}
                onSessionStart={handleSessionStart}
                onExitFlow={discardPatientFlow}
              />
            }
          />
          <Route
            path="/pre-test"
            element={requireActiveSession(<PreTestPage
                patient={patient}
                setPreTestScore={setPreTestScore}
                setWeakTopicSummary={setWeakTopicSummary}
                answers={preTestAnswers}
                setAnswers={setPreTestAnswers}
                onExitFlow={discardPatientFlow}
              />)}
          />
          <Route
            path="/weak-topics"
            element={requireActiveSession(<WeakTopicSummaryPage weakTopicSummary={weakTopicSummary} onExitFlow={discardPatientFlow} />)}
          />
          <Route
            path="/weak-topic-learning"
            element={requireActiveSession(<WeakTopicLearningPage patient={patient} weakTopicSummary={weakTopicSummary} onExitFlow={discardPatientFlow} />)}
          />
          <Route
            path="/teaching-chatbot"
            element={requireActiveSession(<TeachingChatbotPage patient={patient} weakTopicSummary={weakTopicSummary} onExitFlow={discardPatientFlow} />)}
          />
          <Route
            path="/learning/:topicId"
            element={requireActiveSession(<LearningTopicPage onExitFlow={discardPatientFlow} />)}
          />
          <Route
            path="/free-qa"
            element={requireActiveSession(<FreeTextQAPage
                patient={patient}
                weakTopicSummary={weakTopicSummary}
                sessionId={reportState.sessionId}
                onExitFlow={discardPatientFlow}
              />)}
          />
          <Route
            path="/post-test"
            element={requireActiveSession(<PostTestPage
                setPostTestScore={setPostTestScore}
                setPostTestSummary={setPostTestSummary}
                answers={postTestAnswers}
                setAnswers={setPostTestAnswers}
                onExitFlow={discardPatientFlow}
              />)}
          />
          <Route
            path="/result"
            element={requireActiveSession(<ResultPage
                patient={patient}
                preTestScore={preTestScore}
                postTestScore={postTestScore}
                preTestSummary={weakTopicSummary}
                postTestSummary={postTestSummary}
                reportState={reportState}
                onPersistFinalReport={handlePersistFinalReport}
                onRestart={resetDemoFlow}
              />)}
          />
          <Route
            path="/mental-support"
            element={requireActiveSession(<MentalSupportPage onRestart={resetDemoFlow} />)}
          />
        </Route>
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
