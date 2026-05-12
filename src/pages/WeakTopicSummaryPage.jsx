import { Link } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import { getReviewItems } from "../data/quizQuestions";
import { useLanguage } from "../i18n/LanguageContext";

export default function WeakTopicSummaryPage({ weakTopicSummary }) {
  const { t, formatList, language } = useLanguage();
  const ranked = weakTopicSummary?.rankedWeakTopics || [];
  const reviewItems = getReviewItems(weakTopicSummary, language, "pre");
  const topLabels = ranked.slice(0, 2).map((item) => t(`quiz.topics.${item.topic}`));
  const helperText = topLabels.length
    ? t("weakTopics.helper", { topics: formatList(topLabels) })
    : t("weakTopics.noWeak");
  const total = weakTopicSummary?.total || 0;
  const score = weakTopicSummary?.score ?? 0;
  const scoreBand = weakTopicSummary?.scoreBand || "notAvailable";
  const scoreInterpretation = t(`quiz.bands.${scoreBand}`);
  const feedbackMessage = t(`quiz.feedback.${scoreBand === "notAvailable" ? "empty" : scoreBand}`);

  return (
    <AppLayout
      title={t("weakTopics.title")}
      subtitle={t("weakTopics.subtitle")}
      backTo="/pre-test"
    >
      <div className="stack">
        <section className="question-card">
          <p className="question-title">{t("weakTopics.summary")}</p>
          <p>
            {t("quiz.score")}: <strong>{score}</strong> / {total}
          </p>
          <p>
            {t("quiz.level")}: <strong>{scoreInterpretation}</strong>
          </p>
          <p>{helperText}</p>
          {feedbackMessage ? <p className="muted">{feedbackMessage}</p> : null}
        </section>

        {ranked.length ? (
          <section className="question-card">
            <p className="question-title">{t("weakTopics.rankedTitle")}</p>
            <ul className="simple-list">
              {ranked.map((item) => (
                <li key={item.topic}>
                  {t("weakTopics.rankedItem", {
                    label: t(`quiz.topics.${item.topic}`),
                    mistakes: item.mistakes,
                    total: item.totalQuestions,
                  })}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {reviewItems.length ? (
          <section className="question-card">
            <p className="question-title">{t("weakTopics.reviewTitle")}</p>
            <div className="stack-sm">
              {reviewItems.slice(0, 4).map((item) => (
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

        <Link className="btn btn-primary btn-block" to="/weak-topic-learning">
          {t("weakTopics.startLearning")}
        </Link>
      </div>
    </AppLayout>
  );
}
