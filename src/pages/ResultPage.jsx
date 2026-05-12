import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import {
  analysisTopicLabels,
  getReviewItems,
  TOTAL_QUIZ_QUESTIONS,
} from "../data/quizQuestions";
import { normalizeLanguageCode, useLanguage } from "../i18n/LanguageContext";

function getMistakeCount(summary, topic) {
  return summary?.mistakesByTopic?.[topic] ?? 0;
}

export default function ResultPage({
  patient,
  preTestScore,
  postTestScore,
  preTestSummary,
  postTestSummary,
  reportState,
  onPersistFinalReport,
  onRestart,
}) {
  const { t, formatList, language } = useLanguage();
  const navigate = useNavigate();
  const [saveAttempted, setSaveAttempted] = useState(false);
  const total = TOTAL_QUIZ_QUESTIONS;
  const postReviewItems = getReviewItems(postTestSummary, language, "post");
  const improvement =
    preTestScore !== null && postTestScore !== null ? postTestScore - preTestScore : null;
  const hasBothScores = preTestScore !== null && postTestScore !== null;
  const percentImprovement = hasBothScores ? Math.round((improvement / total) * 100) : null;

  const improvedTopics = Object.keys(analysisTopicLabels)
    .map((topic) => {
      const before = getMistakeCount(preTestSummary, topic);
      const after = getMistakeCount(postTestSummary, topic);
      return {
        topic,
        label: t(`quiz.topics.${topic}`),
        before,
        after,
        improvedBy: before - after,
      };
    })
    .filter((item) => item.before > 0 && item.improvedBy > 0)
    .sort((a, b) => b.improvedBy - a.improvedBy);

  const stillWeakTopics = (postTestSummary?.rankedWeakTopics || []).map((item) =>
    t(`quiz.topics.${item.topic}`)
  );
  const improvedTopicLabels = improvedTopics.map((item) => item.label);
  const allWeakAreasCleared =
    (preTestSummary?.rankedWeakTopics || []).length > 0 && stillWeakTopics.length === 0;

  const progressMessage = !hasBothScores
    ? t("result.progressMessages.incomplete")
    : improvement > 0
      ? t("result.progressMessages.improved")
      : improvement === 0
        ? t("result.progressMessages.same")
        : t("result.progressMessages.dropped");

  const preBand = preTestSummary?.scoreBand || "notAvailable";
  const postBand = postTestSummary?.scoreBand || "notAvailable";

  useEffect(() => {
    if (
      saveAttempted ||
      !onPersistFinalReport ||
      preTestScore === null ||
      postTestScore === null ||
      reportState?.finalSaved ||
      reportState?.saving
    ) {
      return;
    }

    let cancelled = false;

    async function persistReport() {
      setSaveAttempted(true);
      const result = await onPersistFinalReport();
      if (!result?.success && !cancelled) {
        setSaveAttempted(false);
      }
    }

    persistReport();

    return () => {
      cancelled = true;
    };
  }, [
    onPersistFinalReport,
    postTestScore,
    preTestScore,
    reportState?.finalSaved,
    reportState?.saving,
    saveAttempted,
  ]);

  function translatePatientValue(type, value) {
    if (!value) return t("result.notEntered");
    if (type === "language") return t(`languages.${normalizeLanguageCode(value)}`);
    return t(`patientForm.options.${value}`) === `patientForm.options.${value}`
      ? value
      : t(`patientForm.options.${value}`);
  }

  function handleRestart() {
    onRestart?.();
    navigate("/");
  }

  return (
    <AppLayout
      title={t("result.title")}
      subtitle={t("result.subtitle")}
      backTo="/post-test"
    >
      <div className="stack">
        <section className="question-card">
          <p className="question-title">{t("result.patient")}</p>
          <p>{t("result.fields.patientId")}: {patient.patientId || t("result.notEntered")}</p>
          <p>{t("result.fields.age")}: {patient.age || t("result.notEntered")}</p>
          <p>{t("result.fields.gender")}: {translatePatientValue("option", patient.gender)}</p>
          <p>
            {t("result.fields.educationalQualification")}:{" "}
            {patient.educationalQualification
              ? translatePatientValue("option", patient.educationalQualification)
              : t("result.notEntered")}
          </p>
          <p>
            {t("result.fields.occupation")}:{" "}
            {patient.occupation
              ? translatePatientValue("option", patient.occupation)
              : t("result.notEntered")}
          </p>
          <p>{t("result.fields.dietType")}: {translatePatientValue("option", patient.dietType)}</p>
          <p>
            {t("result.fields.habits")}:{" "}
            {patient.habits && patient.habits.length
              ? formatList(patient.habits.map((habit) => translatePatientValue("option", habit)))
              : t("result.habitsNone")}
          </p>
          <p>
            {t("result.fields.preferredLanguage")}:{" "}
            {translatePatientValue("language", patient.languagePreference)}
          </p>
          <p>
            {t("result.fields.digitalLiteracy")}:{" "}
            {translatePatientValue("option", patient.digitalLiteracy)}
          </p>
        </section>

        <section className="question-card">
          <p className="question-title">{t("result.preTest")}</p>
          <p>
            {t("quiz.score")}: {preTestScore ?? "-"} / {total}
          </p>
          <p>{t("quiz.level")}: {t(`quiz.bands.${preBand}`)}</p>
        </section>

        <section className="question-card">
          <p className="question-title">{t("result.postTest")}</p>
          <p>
            {t("quiz.score")}: {postTestScore ?? "-"} / {total}
          </p>
          <p>{t("quiz.level")}: {t(`quiz.bands.${postBand}`)}</p>
          {postTestScore !== null ? (
            <p className="muted">{t(`quiz.feedback.${postBand}`)}</p>
          ) : null}
        </section>

        <section className="question-card">
          <p className="question-title">{t("result.progress")}</p>
          <p>{progressMessage}</p>
          {improvement === null ? null : (
            <>
              <p>
                {t("result.improvement")}: <strong>{improvement}</strong> {t("result.points")}
              </p>
              <p>
                {t("result.overallChange")}: <strong>{percentImprovement}%</strong> {t("result.ofTotal")}
              </p>
            </>
          )}
          <p className="muted">{t("result.safeNote")}</p>
        </section>

        <section className="question-card">
          <p className="question-title">Final Report Storage</p>
          {reportState?.saving ? (
            <p className="muted">Saving the completed patient report to the hospital report system.</p>
          ) : reportState?.finalSaved ? (
            <>
              <p>Your final session report has been saved for admin review.</p>
              {reportState?.reportId ? (
                <p className="muted">Report ID: {reportState.reportId}</p>
              ) : null}
            </>
          ) : reportState?.error ? (
            <>
              <p className="error-text">{reportState.error}</p>
              <button type="button" className="btn btn-secondary mt-3" onClick={onPersistFinalReport}>
                Save Report Again
              </button>
            </>
          ) : (
            <p className="muted">The final report will be saved automatically after completion.</p>
          )}
        </section>

        <section className="question-card">
          <p className="question-title">{t("result.weakImproved")}</p>
          {improvedTopics.length ? (
            <ul className="simple-list">
              {improvedTopics.map((item) => (
                <li key={item.topic}>
                  {item.label}: {item.before} -&gt; {item.after} mistakes
                </li>
              ))}
            </ul>
          ) : (
            <p>{t("result.feedbackNone")}</p>
          )}
          {improvedTopicLabels.length ? (
            <p className="muted">{t("result.improvedIn", { topics: formatList(improvedTopicLabels) })}</p>
          ) : null}
          {allWeakAreasCleared ? (
            <p className="muted">{t("result.cleared")}</p>
          ) : null}
          {!allWeakAreasCleared && stillWeakTopics.length ? (
            <p className="muted">{t("result.stillNeed", { topics: formatList(stillWeakTopics) })}</p>
          ) : null}
        </section>

        {postReviewItems.length ? (
          <section className="question-card">
            <p className="question-title">{t("result.reviewAfterPost")}</p>
            <div className="stack-sm">
              {postReviewItems.slice(0, 4).map((item) => (
                <div key={item.id} className="rounded-xl border border-hospital-200 bg-hospital-50 p-4">
                  <p className="font-semibold text-hospital-900">{item.question}</p>
                  <p className="mt-1 text-sm text-hospital-700">
                    {t("weakTopics.correctAnswer")} <strong>{item.correctAnswer}</strong>
                  </p>
                  {item.explanation ? (
                    <p className="mt-1 text-sm text-hospital-700">{item.explanation}</p>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <section className="question-card">
          <p className="question-title">{t("result.completion")}</p>
          <p>{t("result.completionText")}</p>
          <Link to="/mental-support" className="btn btn-secondary btn-block">
            {t("result.optionalSupport")}
          </Link>
        </section>

        <button type="button" className="btn btn-primary btn-block" onClick={handleRestart}>
          {t("result.restart")}
        </button>
      </div>
    </AppLayout>
  );
}
