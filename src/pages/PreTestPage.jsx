import QuizForm from "../components/QuizForm";
import { getPreTestQuestionBank } from "../data/quizQuestions";
import { useLanguage } from "../i18n/LanguageContext";

export default function PreTestPage({
  patient,
  setPreTestScore,
  setWeakTopicSummary,
  answers,
  setAnswers,
  onExitFlow,
}) {
  const { t, language } = useLanguage();
  const questions = getPreTestQuestionBank(language);

  return (
    <QuizForm
      title={t("quiz.preTitle")}
      subtitle={t("quiz.preSubtitle", { age: patient.age || "-" })}
      questions={questions}
      quizSessionKey={`pre-${language}`}
      backTo="/patient-form"
      nextPath="/weak-topics"
      answers={answers}
      setAnswers={setAnswers}
      setScore={setPreTestScore}
      onComplete={setWeakTopicSummary}
      buttonLabel={t("quiz.submitPre")}
      onExitFlow={onExitFlow}
    />
  );
}
