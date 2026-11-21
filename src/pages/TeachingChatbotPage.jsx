import { Link } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import {
  getLearningTopics,
  getRecommendedLearningTopicId,
} from "../data/courseContent";
import { useLanguage } from "../i18n/LanguageContext";

const learningLanguages = ["en", "hi", "kn", "mr"];

export default function TeachingChatbotPage({ weakTopicSummary, onExitFlow }) {
  const { language, setLanguage, t } = useLanguage();
  const topics = getLearningTopics(language);
  const recommendedTopicId = getRecommendedLearningTopicId(weakTopicSummary);
  const weakTopicLabels = (weakTopicSummary?.rankedWeakTopics || [])
    .map((item) => t(`quiz.topics.${item.topic}`))
    .filter(Boolean);

  return (
    <AppLayout
      title="Learning Hub"
      subtitle="Open one topic at a time. The text changes with your selected language, and your learning path stays simple from here."
      backTo="/weak-topic-learning"
      onExitFlow={onExitFlow}
    >
      <div className="stack">
        <section className="rounded-2xl border border-hospital-200 bg-hospital-50 p-4 sm:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="grid gap-2">
              <p className="m-0 text-lg font-semibold text-hospital-900">
                Recommended course path
              </p>
              <p className="m-0 text-sm leading-relaxed text-hospital-700 sm:text-base">
                {weakTopicLabels.length
                  ? `Based on the pre-test, start with ${weakTopicLabels.join(", ")} and then continue through the remaining topics.`
                  : "No major weak topic was detected, so you can start anywhere and move topic by topic."}
              </p>
            </div>

            <Link
              to={`/learning/${recommendedTopicId}`}
              className="btn btn-primary min-w-52"
              data-ui-button
            >
              Start Recommended Topic
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-care-200 bg-care-50 p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="m-0 text-lg font-semibold text-care-900">Start the full learning course</p>
              <p className="mt-1 mb-0 text-sm leading-relaxed text-care-800">
                Watch the introduction video first, then continue through each topic in order.
              </p>
            </div>
            <Link to="/learning/introduction" className="btn btn-primary min-w-52" data-ui-button>
              Start with introduction
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-hospital-200 bg-white p-4 shadow-sm sm:p-5">
          <div className="flex flex-wrap items-center gap-3">
            <p className="m-0 text-sm font-semibold uppercase tracking-wide text-hospital-600">
              Course language
            </p>
            <div className="flex flex-wrap gap-2">
              {learningLanguages.map((code) => {
                const isActive = language === code;
                return (
                  <button
                    key={code}
                    type="button"
                    onClick={() => setLanguage(code)}
                    className={`rounded-full border px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "border-care-600 bg-care-600 text-white"
                        : "border-hospital-300 bg-white text-hospital-700 hover:bg-hospital-50"
                    }`}
                  >
                    {t(`languages.${code}`)}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {topics.map((topic, index) => {
            const isRecommended = topic.id === recommendedTopicId;
            return (
              <article
                key={topic.id}
                className="rounded-3xl border border-hospital-200 bg-white p-5 shadow-soft"
                data-hover-card
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="m-0 text-xs font-semibold uppercase tracking-wide text-hospital-600">
                      Topic {index + 1}
                    </p>
                    <h2 className="mt-2 text-xl font-semibold text-hospital-900">
                      {topic.title}
                    </h2>
                  </div>
                  {isRecommended ? <span className="topic-chip">Recommended</span> : null}
                </div>

                <p className="mt-4 text-sm leading-7 text-hospital-700 sm:text-base">
                  {topic.intro || "Learning content will appear here for the selected language."}
                </p>

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
                  <span className="text-sm text-hospital-600">
                    {topic.allSections.length} learning sections
                  </span>
                  <Link to={`/learning/${topic.id}`} className="btn btn-secondary" data-ui-button>
                    Open Topic
                  </Link>
                </div>
              </article>
            );
          })}
        </section>

        <section className="rounded-2xl border border-care-200 bg-care-50 p-4 sm:p-5">
          <p className="m-0 text-sm leading-relaxed text-care-900 sm:text-base">
            After the last topic, use the next button to continue to Free Q&amp;A without changing the rest of the chatbot flow.
          </p>
        </section>
      </div>
    </AppLayout>
  );
}
