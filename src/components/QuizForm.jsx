import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "./AppLayout";
import { evaluateQuiz, prepareQuizQuestions } from "../data/quizQuestions";
import { useLanguage } from "../i18n/LanguageContext";

export default function QuizForm({
  title,
  subtitle,
  questions,
  backTo,
  nextPath,
  answers,
  setAnswers,
  setScore,
  onComplete,
  buttonLabel,
  quizSessionKey,
  onExitFlow,
}) {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const { t } = useLanguage();
  const [shuffledQuestions, setShuffledQuestions] = useState(() => prepareQuizQuestions(questions));

  useEffect(() => {
    setShuffledQuestions(prepareQuizQuestions(questions));
    setCurrentIndex(0);
    setAnswers({});
  }, [quizSessionKey, setAnswers]);

  const currentQuestion = shuffledQuestions[currentIndex];
  const selectedAnswer = answers[currentQuestion.id];
  const selectedAnswerIndex =
    selectedAnswer && typeof selectedAnswer === "object"
      ? selectedAnswer.selectedIndex
      : selectedAnswer;
  const isLastQuestion = currentIndex === shuffledQuestions.length - 1;
  const progressPercent = Math.round(((currentIndex + 1) / shuffledQuestions.length) * 100);

  function handleOptionChange(question, optionIndex) {
    const option = question.shuffledOptions?.[optionIndex];

    setAnswers((prev) => ({
      ...prev,
      [question.id]: {
        selectedIndex: optionIndex,
        selectedText: option?.text || question.options?.[optionIndex] || "",
        originalIndex:
          typeof option?.originalIndex === "number" ? option.originalIndex : optionIndex,
        isCorrect: Boolean(option?.isCorrect),
      },
    }));
  }

  function nextQuestion() {
    if (currentIndex < shuffledQuestions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  }

  function previousQuestion() {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    const result = evaluateQuiz(answers, shuffledQuestions);
    setScore(result.score);
    if (onComplete) onComplete(result);
    navigate(nextPath);
  }

  return (
    <AppLayout title={title} subtitle={subtitle} backTo={backTo} onExitFlow={onExitFlow}>
      <form onSubmit={handleSubmit} className="stack">
        <section className="question-card">
          <p className="muted">
            {t("quiz.questionOf", { current: currentIndex + 1, total: shuffledQuestions.length })}
          </p>
          <div className="mt-2 h-2.5 w-full rounded-full bg-hospital-100">
            <div
              className="h-2.5 rounded-full bg-care-500 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progressPercent}
              aria-label={t("quiz.progressLabel")}
            />
          </div>
        </section>

        <section className="question-card" key={currentQuestion.id}>
          <p className="question-title">{currentQuestion.question}</p>
          <div className="stack-sm">
            {currentQuestion.options.map((option, idx) => {
              const checked = selectedAnswerIndex === idx;
              return (
                <label className={`option ${checked ? "option-selected" : ""}`} key={option}>
                  <input
                    type="radio"
                    name={`q-${currentQuestion.id}`}
                    checked={checked}
                    onChange={() => handleOptionChange(currentQuestion, idx)}
                  />
                  <span>{option}</span>
                </label>
              );
            })}
          </div>
        </section>

        <div className="nav-row">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={previousQuestion}
            disabled={currentIndex === 0}
          >
            {t("quiz.previous")}
          </button>

          {!isLastQuestion ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={nextQuestion}
              disabled={typeof selectedAnswerIndex !== "number"}
            >
              {t("quiz.next")}
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              disabled={typeof selectedAnswerIndex !== "number"}
            >
              {buttonLabel}
            </button>
          )}
        </div>
      </form>
    </AppLayout>
  );
}
