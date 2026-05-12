import { getImageForTopic, getTopicLabel } from "../data/topicMedia";
import { useLanguage } from "../i18n/LanguageContext";

export default function CourseModuleCard({
  module,
  index,
  total,
  isPlayingAudio,
  onPlayAudio,
}) {
  const { t } = useLanguage();
  const imageUrl = getImageForTopic(module.imageTopic);
  const topicLabel = module.topicKey
    ? t(`quiz.topics.${module.topicKey}`)
    : getTopicLabel(module.imageTopic);

  return (
    <section id={module.id} className="question-card scroll-mt-24">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-hospital-600">
            {t("course.module.heading", { current: index + 1, total })}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-hospital-900 sm:text-2xl">
            {module.title}
          </h2>
        </div>
        {topicLabel ? <span className="topic-chip">{topicLabel}</span> : null}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
        <div className="grid gap-3">
          {module.contentParagraphs.length ? (
            <div className="grid gap-3">
              {module.contentParagraphs.map((paragraph, paragraphIndex) => (
                <p
                  key={`${module.id}-paragraph-${paragraphIndex}`}
                  className="text-base leading-relaxed text-hospital-800"
                >
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-base leading-relaxed text-hospital-800">
              {module.content || t("course.module.noVisual")}
            </p>
          )}

          {module.fallbackNotice ? (
            <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {module.fallbackNotice}
            </p>
          ) : null}

          <div className="answer-actions">
            <button type="button" className="btn btn-secondary btn-audio" onClick={onPlayAudio}>
              {isPlayingAudio ? t("course.module.playingAudio") : t("course.module.playAudio")}
            </button>
          </div>
        </div>

        <div className="grid gap-3">
          {imageUrl ? (
            <img className="answer-image sm:max-w-full" src={imageUrl} alt={`${module.title} visual`} />
          ) : (
            <div className="flex min-h-[220px] items-center justify-center rounded-xl border border-dashed border-hospital-200 bg-hospital-50 p-4 text-center text-sm text-hospital-600">
              {t("course.module.noVisual")}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
