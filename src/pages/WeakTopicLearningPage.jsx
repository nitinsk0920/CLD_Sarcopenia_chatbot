import { useMemo } from "react";
import AppLayout from "../components/AppLayout";
import { groupWrongQuestionsByTopic } from "../data/weakTopicLearning";
import { useLanguage } from "../i18n/LanguageContext";

export default function WeakTopicLearningPage({ weakTopicSummary, onExitFlow }) {
  const { t, language } = useLanguage();
  const topicGroups = useMemo(
    () => groupWrongQuestionsByTopic(weakTopicSummary, language),
    [language, weakTopicSummary]
  );
  const totalWrong = weakTopicSummary?.wrongAnswers?.length || 0;
  const summaryText =
    totalWrong <= 2 ? t("weakTopicLearning.shortSupport") : t("weakTopicLearning.longSupport");

  return (
    <AppLayout
      title={t("weakTopicLearning.title")}
      subtitle={t("weakTopicLearning.subtitle")}
      backTo="/weak-topics"
      nextTo="/teaching-chatbot"
      nextLabel={t("weakTopicLearning.continue")}
      onExitFlow={onExitFlow}
    >
      <div className="stack">
        <section className="question-card">
          <p className="question-title">{t("weakTopicLearning.reviewTitle")}</p>
          <p>{summaryText}</p>
          <p className="muted">
            {t("weakTopicLearning.wrongCount", {
              count: totalWrong,
            })}
          </p>
        </section>

        {topicGroups.length ? (
          topicGroups.map((group, groupIndex) => (
            <section key={group.topic} className="question-card">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-hospital-600">
                    {t("weakTopicLearning.topicOrder", { index: groupIndex + 1 })}
                  </p>
                  <p className="question-title mb-0 mt-1">{t(`quiz.topics.${group.topic}`)}</p>
                </div>
                <span className="topic-chip">
                  {t("weakTopicLearning.questionsToReview", { count: group.items.length })}
                </span>
              </div>

              <div className="stack-sm">
                {group.items.map((item) => (
                  <article
                    key={item.id}
                    className="rounded-2xl border border-hospital-200 bg-hospital-50 p-4 sm:p-5"
                  >
                    <p className="text-base font-semibold leading-relaxed text-hospital-900 sm:text-lg">
                      {item.question}
                    </p>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                        <p className="text-sm font-semibold text-red-700">
                          {t("weakTopicLearning.yourAnswer")}
                        </p>
                        <p className="mt-1 text-sm leading-relaxed text-red-900">
                          {item.selectedAnswer || t("weakTopicLearning.notAnswered")}
                        </p>
                      </div>
                      <div className="rounded-xl border border-care-200 bg-care-50 px-4 py-3">
                        <p className="text-sm font-semibold text-care-700">
                          {t("weakTopicLearning.correctAnswer")}
                        </p>
                        <p className="mt-1 text-sm leading-relaxed text-care-900">
                          {item.correctAnswer}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 rounded-xl border border-hospital-200 bg-white px-4 py-3">
                      <p className="text-sm font-semibold text-hospital-800">
                        {t("weakTopicLearning.simpleExplain")}
                      </p>
                      <p className="mt-1 text-sm leading-7 text-hospital-700 sm:text-base">
                        {item.explanation}
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))
        ) : (
          <section className="question-card">
            <p className="question-title">{t("weakTopicLearning.noReviewTitle")}</p>
            <p>{t("weakTopicLearning.noReviewText")}</p>
          </section>
        )}
      </div>
    </AppLayout>
  );
}
