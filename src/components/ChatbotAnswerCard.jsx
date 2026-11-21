import { getImageForTopic, getTopicForMessage, getTopicLabel } from "../data/topicMedia";
import { useLanguage } from "../i18n/LanguageContext";

export default function ChatbotAnswerCard({
  text,
  topics = [],
  onPlayAudio,
  isPlayingAudio,
  showMedia = true,
}) {
  const { t } = useLanguage();
  const topic = getTopicForMessage(topics, text);
  const imageUrl = showMedia ? getImageForTopic(topic) : "";
  const topicLabel =
    t(`quiz.topics.${topic}`) === `quiz.topics.${topic}` ? getTopicLabel(topic) : t(`quiz.topics.${topic}`);

  return (
    <article className="bubble bubble-bot bubble-rich" data-chat-message>
      <p className="bubble-text">{text}</p>
      <footer className="answer-actions" aria-label="Answer controls">
        <button
          type="button"
          className="btn btn-secondary btn-audio"
          onClick={onPlayAudio}
          aria-label={isPlayingAudio ? t("course.module.playingAudio") : t("course.module.playAudio")}
        >
          {isPlayingAudio ? t("course.module.playingAudio") : t("course.module.playAudio")}
        </button>
        {topicLabel ? <span className="topic-chip">{topicLabel}</span> : null}
      </footer>
      {imageUrl ? (
        <img className="answer-image" src={imageUrl} alt={`${topicLabel || "Education"} visual`} />
      ) : showMedia && topic && import.meta.env.DEV ? (
        <p className="muted">No local image found for this topic in `chatbot_imgs` or `chat_imgs`.</p>
      ) : null}
    </article>
  );
}
