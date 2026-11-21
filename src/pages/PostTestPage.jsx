import QuizForm from "../components/QuizForm";
import { getPostTestQuestionBank } from "../data/quizQuestions";
import { useLanguage } from "../i18n/LanguageContext";

export default function PostTestPage({
  setPostTestScore,
  setPostTestSummary,
  answers,
  setAnswers,
  onExitFlow,
}) {
  const { t, language } = useLanguage();
  const questions = getPostTestQuestionBank(language);

  return (
    <QuizForm
      title={t("quiz.postTitle")}
      subtitle={t("quiz.postSubtitle")}
      questions={questions}
      quizSessionKey={`post-${language}`}
      backTo="/free-qa"
      nextPath="/result"
      answers={answers}
      setAnswers={setAnswers}
      setScore={setPostTestScore}
      onComplete={setPostTestSummary}
      buttonLabel={t("quiz.submitPost")}
      onExitFlow={onExitFlow}
    />
  );
}
