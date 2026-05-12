import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
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
import ProtectedRoute from "./components/ProtectedRoute";
import { buildFinalReportPayload } from "./data/reportPayload";
import { useAuth } from "./auth/AuthContext";
import {
  endPatientReportSession,
  saveFinalPatientReport,
  startPatientReportSession,
} from "./services/reportApi";
import { initializeGlobalMicroInteractions } from "./utils/uiAnimations";

function createInitialPatient() {
  return {
    patientId: "",
    age: "",
    gender: "",
    educationalQualification: "",
    occupation: "",
    cldStatus: "",
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

function createInitialReportState() {
  const sessionId =
    globalThis.crypto?.randomUUID?.() || `session-${Date.now()}-${Math.round(Math.random() * 1000)}`;
  return {
    sessionId,
    startedAt: "",
    started: false,
    reportId: "",
    finalSaved: false,
    saving: false,
    error: "",
    shortChatSummary: "",
  };
}

export default function App() {
  const { logout } = useAuth();
  const [patient, setPatient] = useState(createInitialPatient);
  const [preTestScore, setPreTestScore] = useState(null);
  const [weakTopicSummary, setWeakTopicSummary] = useState(createInitialQuizSummary);
  const [postTestScore, setPostTestScore] = useState(null);
  const [postTestSummary, setPostTestSummary] = useState(createInitialQuizSummary);
  const [preTestAnswers, setPreTestAnswers] = useState({});
  const [postTestAnswers, setPostTestAnswers] = useState({});
  const [reportState, setReportState] = useState(createInitialReportState);

  useEffect(() => {
    return initializeGlobalMicroInteractions();
  }, []);

  async function handleSessionStart(patientData) {
    if (reportState.started) {
      return { success: true };
    }

    const startedAt = new Date().toISOString();
    try {
      await startPatientReportSession({
        session_id: reportState.sessionId,
        started_at: startedAt,
        patient: patientData,
      });
      setReportState((prev) => ({
        ...prev,
        startedAt,
        started: true,
        error: "",
      }));
      return { success: true };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not start report session.";
      setReportState((prev) => ({
        ...prev,
        startedAt,
        error: message,
      }));
      return {
        success: true,
        warning: message,
      };
    }
  }

  function handleChatSummaryChange(summary) {
    setReportState((prev) => ({
      ...prev,
      shortChatSummary: summary || prev.shortChatSummary,
    }));
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
        shortChatSummary: reportState.shortChatSummary,
      });
      const result = await saveFinalPatientReport(payload);
      await endPatientReportSession({
        session_id: reportState.sessionId,
        ended_at: new Date().toISOString(),
        completion_status: "completed",
      }).catch(() => null);

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
    setPatient(createInitialPatient());
    setPreTestScore(null);
    setWeakTopicSummary(createInitialQuizSummary());
    setPostTestScore(null);
    setPostTestSummary(createInitialQuizSummary());
    setPreTestAnswers({});
    setPostTestAnswers({});
    setReportState(createInitialReportState());
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LockScreenPage />} />
        <Route path="/admin/login" element={<LockScreenPage />} />
        <Route
          path="/admin-dashboard"
          element={<Navigate to="/admin/dashboard" replace />}
        />
        <Route element={<ProtectedRoute allowedRoles={["admin"]} redirectTo="/" />}>
          <Route path="/welcome" element={<WelcomePage />} />
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
              />
            }
          />
          <Route
            path="/pre-test"
            element={
              <PreTestPage
                patient={patient}
                setPreTestScore={setPreTestScore}
                setWeakTopicSummary={setWeakTopicSummary}
                answers={preTestAnswers}
                setAnswers={setPreTestAnswers}
              />
            }
          />
          <Route
            path="/weak-topics"
            element={<WeakTopicSummaryPage weakTopicSummary={weakTopicSummary} />}
          />
          <Route
            path="/weak-topic-learning"
            element={<WeakTopicLearningPage patient={patient} weakTopicSummary={weakTopicSummary} />}
          />
          <Route
            path="/teaching-chatbot"
            element={<TeachingChatbotPage patient={patient} weakTopicSummary={weakTopicSummary} />}
          />
          <Route
            path="/learning/:topicId"
            element={<LearningTopicPage />}
          />
          <Route
            path="/free-qa"
            element={
              <FreeTextQAPage
                patient={patient}
                weakTopicSummary={weakTopicSummary}
                sessionId={reportState.sessionId}
                onSessionSummaryChange={handleChatSummaryChange}
              />
            }
          />
          <Route
            path="/post-test"
            element={
              <PostTestPage
                setPostTestScore={setPostTestScore}
                setPostTestSummary={setPostTestSummary}
                answers={postTestAnswers}
                setAnswers={setPostTestAnswers}
              />
            }
          />
          <Route
            path="/result"
            element={
              <ResultPage
                patient={patient}
                preTestScore={preTestScore}
                postTestScore={postTestScore}
                preTestSummary={weakTopicSummary}
                postTestSummary={postTestSummary}
                reportState={reportState}
                onPersistFinalReport={handlePersistFinalReport}
                onRestart={resetDemoFlow}
              />
            }
          />
          <Route
            path="/mental-support"
            element={<MentalSupportPage onRestart={resetDemoFlow} />}
          />
        </Route>
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
