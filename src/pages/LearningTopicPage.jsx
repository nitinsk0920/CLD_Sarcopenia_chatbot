import { useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import {
  getLearningTopicById,
  getLearningTopicIndex,
  LEARNING_TOPIC_ORDER,
} from "../data/courseContent";
import { getLearningAudioUrls } from "../data/learningAudio";
import { useLanguage } from "../i18n/LanguageContext";
import { fetchLearningTopicMedia } from "../services/learningApi";
import {
  animateLearningMediaCards,
  observeAnimatedTitles,
} from "../utils/uiAnimations";

const learningLanguages = ["en", "hi", "kn", "mr"];

function MediaUnavailable({ title, type }) {
  return (
    <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed border-hospital-300 bg-white px-6 py-8 text-center">
      <div className="max-w-md">
        <p className="text-base font-semibold text-hospital-800">{title}</p>
        <p className="mt-2 text-sm leading-7 text-hospital-600">
          This {type === "video" ? "video" : "image"} could not be displayed right now.
        </p>
      </div>
    </div>
  );
}

function LearningMediaFrame({ item }) {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return <MediaUnavailable title={item.title} type={item.media_type} />;
  }

  if (item.media_type === "video") {
    return (
      <div className="overflow-hidden rounded-2xl border border-hospital-200 bg-slate-950">
        <div className="aspect-video w-full">
          <video
            controls
            playsInline
            preload="metadata"
            className="h-full w-full bg-black object-contain"
            onError={() => setHasError(true)}
          >
            <source src={item.media_url} />
          </video>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[260px] items-center justify-center overflow-hidden rounded-2xl border border-hospital-200 bg-white p-4 sm:min-h-[320px]">
      <img
        src={item.media_url}
        alt={item.title}
        loading="lazy"
        onError={() => setHasError(true)}
        className="max-h-[460px] max-w-full rounded-xl object-contain"
      />
    </div>
  );
}

function LearningParagraphAudioButton({
  audioKey,
  isLoading,
  isPlaying,
  hasError,
  onPlay,
  t,
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        className="btn btn-secondary btn-audio gap-2"
        onClick={() => onPlay(audioKey)}
        disabled={isLoading}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M11 5 6 9H2v6h4l5 4V5Z" />
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
        </svg>
        <span>
          {isLoading
            ? t("course.module.loadingAudio")
            : isPlaying
              ? t("course.module.playingAudio")
              : t("course.module.playAudio")}
        </span>
      </button>
      {hasError ? (
        <span className="text-sm font-medium text-red-700">{t("course.module.audioUnavailable")}</span>
      ) : null}
    </div>
  );
}

function buildNextRoute(topicId) {
  const currentIndex = getLearningTopicIndex(topicId);
  if (currentIndex === -1) return "/teaching-chatbot";
  if (currentIndex === LEARNING_TOPIC_ORDER.length - 1) return "/free-qa";
  return `/learning/${LEARNING_TOPIC_ORDER[currentIndex + 1]}`;
}

function buildPreviousRoute(topicId) {
  const currentIndex = getLearningTopicIndex(topicId);
  if (currentIndex <= 0) return "/teaching-chatbot";
  return `/learning/${LEARNING_TOPIC_ORDER[currentIndex - 1]}`;
}

export default function LearningTopicPage() {
  const { topicId = "" } = useParams();
  const { language, setLanguage, t } = useLanguage();
  const topic = getLearningTopicById(topicId, language);
  const [mediaState, setMediaState] = useState({
    loading: true,
    error: "",
    items: [],
  });
  const [audioState, setAudioState] = useState({
    loadingKey: "",
    playingKey: "",
    errorKey: "",
  });
  const activeAudioRef = useRef(null);
  const playbackAttemptRef = useRef(0);
  const contentRef = useRef(null);

  useEffect(() => {
    let isActive = true;

    async function loadMedia() {
      setMediaState((prev) => ({
        ...prev,
        loading: true,
        error: "",
      }));

      try {
        const response = await fetchLearningTopicMedia(topicId);
        if (!isActive) return;
        setMediaState({
          loading: false,
          error: "",
          items: response?.items || [],
        });
      } catch (error) {
        if (!isActive) return;
        setMediaState({
          loading: false,
          error:
            error instanceof Error ? error.message : "Could not load learning media.",
          items: [],
        });
      }
    }

    loadMedia();
    return () => {
      isActive = false;
    };
  }, [topicId]);

  const tabs = useMemo(
    () =>
      LEARNING_TOPIC_ORDER.map((id) => ({
        id,
        topic: getLearningTopicById(id, language),
      })).filter((item) => item.topic),
    [language]
  );

  useEffect(() => {
    return observeAnimatedTitles(contentRef.current);
  }, [topicId, language, topic?.sections?.length]);

  useEffect(() => {
    animateLearningMediaCards(contentRef.current);
  }, [topicId, mediaState.items.length]);

  function stopCurrentAudio() {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }
  }

  useEffect(() => {
    playbackAttemptRef.current += 1;
    stopCurrentAudio();
    setAudioState({
      loadingKey: "",
      playingKey: "",
      errorKey: "",
    });

    return () => {
      playbackAttemptRef.current += 1;
      stopCurrentAudio();
    };
  }, [topicId, language]);

  async function playLearningAudio(sectionNumber, audioKey) {
    if (audioState.playingKey === audioKey && activeAudioRef.current) {
      playbackAttemptRef.current += 1;
      stopCurrentAudio();
      setAudioState({
        loadingKey: "",
        playingKey: "",
        errorKey: "",
      });
      return;
    }

    const audioUrls = getLearningAudioUrls(language, sectionNumber);
    const currentAttempt = playbackAttemptRef.current + 1;
    playbackAttemptRef.current = currentAttempt;
    stopCurrentAudio();
    setAudioState({
      loadingKey: audioKey,
      playingKey: "",
      errorKey: "",
    });

    for (const audioUrl of audioUrls) {
      const audio = new Audio(audioUrl);
      audio.preload = "none";

      try {
        // eslint-disable-next-line no-await-in-loop
        await audio.play();
        if (playbackAttemptRef.current !== currentAttempt) {
          audio.pause();
          return;
        }

        activeAudioRef.current = audio;
        audio.onended = () => {
          if (activeAudioRef.current !== audio) return;
          activeAudioRef.current = null;
          setAudioState({
            loadingKey: "",
            playingKey: "",
            errorKey: "",
          });
        };
        setAudioState({
          loadingKey: "",
          playingKey: audioKey,
          errorKey: "",
        });
        return;
      } catch {
        audio.pause();
      }
    }

    if (playbackAttemptRef.current === currentAttempt) {
      setAudioState({
        loadingKey: "",
        playingKey: "",
        errorKey: audioKey,
      });
    }
  }

  if (!topic) {
    return <Navigate to="/teaching-chatbot" replace />;
  }

  return (
    <AppLayout
      title={topic.title}
      subtitle={topic.intro}
      backTo={buildPreviousRoute(topicId)}
      backLabel={topicId === LEARNING_TOPIC_ORDER[0] ? "Back to Hub" : "Previous Topic"}
      nextTo={buildNextRoute(topicId)}
      nextLabel={
        topicId === LEARNING_TOPIC_ORDER[LEARNING_TOPIC_ORDER.length - 1]
          ? "Continue to Free Q&A"
          : "Next Topic"
      }
    >
      <div ref={contentRef} className="stack">
        <section className="rounded-2xl border border-hospital-200 bg-white p-4 shadow-sm sm:p-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="grid gap-3">
              <p className="m-0 text-sm font-semibold uppercase tracking-wide text-hospital-600">
                Topic navigation
              </p>
              <div className="flex flex-wrap gap-2">
                {tabs.map(({ id, topic: tabTopic }) => {
                  const isActive = id === topicId;
                  return (
                    <Link
                      key={id}
                      to={`/learning/${id}`}
                      className={`rounded-full border px-4 py-2 text-sm font-semibold no-underline transition ${
                        isActive
                          ? "border-care-600 bg-care-600 text-white"
                          : "border-hospital-300 bg-white text-hospital-700 hover:bg-hospital-50"
                      }`}
                      data-ui-button
                    >
                      {tabTopic.title}
                    </Link>
                  );
                })}
              </div>
            </div>

            <div className="grid gap-2">
              <p className="m-0 text-sm font-semibold uppercase tracking-wide text-hospital-600">
                Language
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
          </div>
        </section>

        <section className="rounded-3xl border border-hospital-200 bg-hospital-50 p-5 shadow-sm">
          <p className="m-0 text-sm font-semibold uppercase tracking-wide text-hospital-600">
            Topic overview
          </p>
          <p className="mt-3 text-base leading-8 text-hospital-800 sm:text-lg">
            {topic.intro}
          </p>
          {topic.allSections[0]?.order ? (
            <div className="mt-4">
              <LearningParagraphAudioButton
                audioKey={`${topicId}-overview-${topic.allSections[0].order}`}
                isLoading={audioState.loadingKey === `${topicId}-overview-${topic.allSections[0].order}`}
                isPlaying={audioState.playingKey === `${topicId}-overview-${topic.allSections[0].order}`}
                hasError={audioState.errorKey === `${topicId}-overview-${topic.allSections[0].order}`}
                onPlay={() =>
                  playLearningAudio(
                    topic.allSections[0].order,
                    `${topicId}-overview-${topic.allSections[0].order}`
                  )
                }
                t={t}
              />
            </div>
          ) : null}
        </section>

        {topic.sections.map((section, index) => (
          <section
            key={section.id}
            className="rounded-3xl border border-hospital-200 bg-white p-5 shadow-soft"
            data-hover-card
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="m-0 text-xs font-semibold uppercase tracking-wide text-hospital-600">
                  Learning block {index + 1}
                </p>
                <h2 className="mt-2 text-xl font-semibold text-hospital-900" data-animate-title>
                  {section.title}
                </h2>
              </div>
            </div>

            <div className="mt-4 grid gap-4">
              {section.paragraphs.map((paragraph, paragraphIndex) => {
                const audioKey = `${topicId}-${section.order}-${paragraphIndex}`;

                return (
                  <div key={`${section.id}-${paragraphIndex}`} className="grid gap-3">
                    <p className="m-0 text-base leading-8 text-hospital-800">
                      {paragraph}
                    </p>
                    <LearningParagraphAudioButton
                      audioKey={audioKey}
                      isLoading={audioState.loadingKey === audioKey}
                      isPlaying={audioState.playingKey === audioKey}
                      hasError={audioState.errorKey === audioKey}
                      onPlay={() => playLearningAudio(section.order, audioKey)}
                      t={t}
                    />
                  </div>
                );
              })}
            </div>
          </section>
        ))}

        <section className="rounded-3xl border border-hospital-200 bg-white p-5 shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="m-0 text-xs font-semibold uppercase tracking-wide text-hospital-600">
                Images and videos
              </p>
              <h2 className="mt-2 text-xl font-semibold text-hospital-900">
                Learning media for this topic
              </h2>
            </div>
            <span className="topic-chip">{mediaState.items.length} items</span>
          </div>

          {mediaState.loading ? (
            <p className="mt-4 text-sm text-hospital-600">Loading topic media...</p>
          ) : null}

          {mediaState.error ? (
            <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {mediaState.error}
            </p>
          ) : null}

          {!mediaState.loading && !mediaState.error && !mediaState.items.length ? (
            <div className="mt-4 rounded-2xl border border-dashed border-hospital-300 bg-hospital-50 p-5 text-sm leading-relaxed text-hospital-700">
              No active media was found for this topic yet. The text lesson is still available.
            </div>
          ) : null}

          <div className="mt-5 grid gap-4">
            {mediaState.items.map((item) => (
              <article
                key={item.id}
                className="overflow-hidden rounded-3xl border border-hospital-200 bg-hospital-50"
                data-media-card
                data-hover-card
              >
                <div className="border-b border-hospital-200 bg-white px-4 py-3">
                  <p className="m-0 text-base font-semibold text-hospital-900">{item.title}</p>
                  <p className="mt-1 text-sm text-hospital-600">
                    {item.media_type === "video" ? "Video lesson" : "Image support"}
                  </p>
                </div>

                <div className="p-4">
                  <LearningMediaFrame item={item} />
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
