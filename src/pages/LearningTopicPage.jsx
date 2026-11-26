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
const supabaseUrl = (
  import.meta.env.VITE_SUPABASE_URL || "https://gynjgfoxpdqzwbpvckwf.supabase.co"
).replace(/\/$/, "");
const learningMediaBaseUrl = (
  import.meta.env.VITE_LEARNING_MEDIA_BASE_URL ||
  `${supabaseUrl}/storage/v1/object/public/learning-media`
).replace(/\/$/, "");
const topicVideos = {
  introduction: {
    path: "Introduction/Intro.mp4",
    title: "Introduction video",
    audio: {
      hi: "Introduction/intro_hin.MP3",
      kn: "Introduction/intro_kn.MP3",
      mr: "Introduction/intro_mar.MP3",
    },
  },
  cld: {
    path: "CLD/cld_video.mp4",
    title: "CLD video",
    audio: {
      hi: "CLD/CLD_HIN.MP3",
      kn: "CLD/CLD_KAN.MP3",
      mr: "CLD/CLD_MAR.MP3",
    },
  },
  diet: {
    path: "diet/diet and nutrition.mp4",
    title: "Diet and nutrition",
    audio: {
      hi: "diet/diet_hin.MP3",
      kn: "diet/diet_kan.MP3",
      mr: "diet/diet_marati.MP3",
    },
  },
  exercise: {
    path: "exercises/exercise and movement.mp4",
    title: "Exercise and movement",
    audio: {
      hi: "exercises/excer-hin.MP3",
      kn: "exercises/excer-kan.MP3",
      mr: "exercises/excer-ma.MP3",
    },
  },
  safety: {
    path: "Safety and Warnings/safety and warning signs.mp4",
    title: "Safety and warning signs",
    audio: {
      hi: "Safety and Warnings/safety_hin_audio.MP3",
      kn: "Safety and Warnings/safety_kan_audio.MP3",
      mr: "Safety and Warnings/safety_mar_audio.MP3",
    },
  },
  sarcopenia: {
    path: "sarcopenia/sarcopenia_video.mp4",
    title: "Sarcopenia video",
    audio: {
      hi: "sarcopenia/sarco_Hin.MP3",
      kn: "sarcopenia/sarcopenia_kan.MP3",
      mr: "sarcopenia/sarco_mar.MP3",
    },
  },
};
const videoAudioLanguages = [
  { code: "en", label: "English (Original)" },
  { code: "hi", label: "हिन्दी (Hindi)" },
  { code: "kn", label: "ಕನ್ನಡ (Kannada)" },
  { code: "mr", label: "मराठी (Marathi)" },
];

function getVideoAudioUrl(topicId, languageCode) {
  const path = topicVideos[topicId]?.audio?.[languageCode];
  if (!path) return "";
  const encodedPath = path.split("/").map(encodeURIComponent).join("/");
  return `${learningMediaBaseUrl}/${encodedPath}`;
}

function mediaForCourseTopic(items, topicId) {
  const images = (items || []).filter((item) => item.media_type !== "video");
  const video = topicVideos[topicId];
  if (!video) return images;

  const encodedPath = video.path.split("/").map(encodeURIComponent).join("/");
  const poster = images.find((item) => item.media_url)?.media_url;
  return [
    ...images,
    {
      id: `storage-video-${topicId}`,
      topic: topicId,
      media_type: "video",
      title: video.title,
      media_url: `${learningMediaBaseUrl}/${encodedPath}`,
      poster_url: poster || "",
      display_order: 999,
    },
  ];
}

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
  const [videoActivated, setVideoActivated] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [selectedAudioLanguage, setSelectedAudioLanguage] = useState("en");
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState(false);
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const selectedAudioLanguageRef = useRef("en");
  const audioAttemptRef = useRef(0);

  useEffect(() => () => {
    audioAttemptRef.current += 1;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.removeAttribute("src");
      audioRef.current.load();
      audioRef.current = null;
    }
  }, []);

  function pauseExternalAudio() {
    audioAttemptRef.current += 1;
    if (!audioRef.current) return;
    audioRef.current.pause();
  }

  async function playExternalAudio() {
    const video = videoRef.current;
    const languageCode = selectedAudioLanguageRef.current;
    if (!video || languageCode === "en") return;

    const sourceUrl = getVideoAudioUrl(item.topic, languageCode);
    if (!sourceUrl) {
      video.muted = true;
      setAudioError(true);
      setAudioLoading(false);
      return;
    }

    const attempt = audioAttemptRef.current + 1;
    audioAttemptRef.current = attempt;
    const audio = audioRef.current || new Audio();
    audioRef.current = audio;
    audio.preload = "none";
    audio.pause();
    audio.onended = null;
    audio.onerror = null;

    const syncToVideo = () => {
      if (
        audioAttemptRef.current !== attempt ||
        selectedAudioLanguageRef.current !== languageCode
      ) return;
      try {
        audio.currentTime = Math.min(video.currentTime, Number.isFinite(audio.duration) ? audio.duration : video.currentTime);
      } catch {
        // The media element will apply the pending seek when its metadata is ready.
      }
    };

    audio.onloadedmetadata = syncToVideo;
    audio.onerror = () => {
      if (audioAttemptRef.current !== attempt) return;
      audio.pause();
      video.muted = true;
      setAudioLoading(false);
      setAudioError(true);
    };
    audio.onended = () => {
      if (audioAttemptRef.current !== attempt) return;
      setAudioLoading(false);
    };
    if (audio.src !== sourceUrl) {
      audio.src = sourceUrl;
      audio.load();
    }
    audio.playbackRate = video.playbackRate;
    syncToVideo();
    setAudioError(false);
    setAudioLoading(true);

    try {
      await audio.play();
      if (audioAttemptRef.current !== attempt || video.paused) {
        audio.pause();
        return;
      }
      setAudioLoading(false);
    } catch {
      if (audioAttemptRef.current !== attempt) return;
      audio.pause();
      video.muted = true;
      setAudioLoading(false);
      setAudioError(true);
    }
  }

  function selectAudioLanguage(languageCode) {
    selectedAudioLanguageRef.current = languageCode;
    setSelectedAudioLanguage(languageCode);
    setAudioError(false);
    setAudioLoading(false);
    pauseExternalAudio();

    const video = videoRef.current;
    if (!video) return;

    if (languageCode === "en") {
      video.muted = false;
      if (audioRef.current) {
        audioRef.current.onloadedmetadata = null;
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        audioRef.current.removeAttribute("src");
        audioRef.current.load();
      }
      return;
    }

    video.muted = true;
    if (!getVideoAudioUrl(item.topic, languageCode)) {
      setAudioError(true);
      return;
    }
    if (!video.paused) void playExternalAudio();
  }

  function handleVideoPause() {
    if (selectedAudioLanguageRef.current === "en") return;
    pauseExternalAudio();
    setAudioLoading(false);
  }

  function handleVideoSeek() {
    if (selectedAudioLanguageRef.current === "en") return;
    pauseExternalAudio();
  }

  function handleVideoSeeked() {
    if (selectedAudioLanguageRef.current === "en") return;
    if (videoRef.current && !videoRef.current.paused) void playExternalAudio();
  }

  function handleVideoTimeUpdate() {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (
      selectedAudioLanguageRef.current === "en" ||
      !video ||
      !audio ||
      audio.paused ||
      audio.readyState < 1
    ) return;

    if (Math.abs(audio.currentTime - video.currentTime) > 0.35) {
      try {
        audio.currentTime = Math.min(video.currentTime, Number.isFinite(audio.duration) ? audio.duration : video.currentTime);
      } catch {
        // Ignore transient seek errors; the next video time update will resync.
      }
    }
  }

  function activateVideo() {
    const video = videoRef.current;
    if (!video) return;

    setVideoActivated(true);
    setVideoReady(false);
    video.src = item.media_url;
    video.load();
    video.play().catch((error) => {
      if (error?.name === "NotAllowedError" || error?.name === "AbortError") {
        setVideoActivated(false);
        setVideoReady(false);
        return;
      }
      setHasError(true);
    });
  }

  if (hasError && item.media_type !== "video") {
    return <MediaUnavailable title={item.title} type={item.media_type} />;
  }

  if (item.media_type === "video") {
    return (
      <div className="overflow-hidden rounded-2xl border border-hospital-200 bg-slate-950">
        <div className="relative aspect-video w-full">
          <video
            ref={videoRef}
            controls
            playsInline
            preload="none"
            poster={item.poster_url || undefined}
            muted={selectedAudioLanguage !== "en"}
            className="h-full w-full bg-black object-contain"
            onError={() => {
              pauseExternalAudio();
              setHasError(true);
            }}
            onLoadedData={() => {
              setHasError(false);
              setVideoReady(true);
            }}
            onPlay={() => {
              if (selectedAudioLanguageRef.current !== "en") void playExternalAudio();
            }}
            onPlaying={() => setVideoReady(true)}
            onPause={handleVideoPause}
            onSeeking={handleVideoSeek}
            onSeeked={handleVideoSeeked}
            onTimeUpdate={handleVideoTimeUpdate}
            onRateChange={() => {
              if (audioRef.current && videoRef.current) {
                audioRef.current.playbackRate = videoRef.current.playbackRate;
              }
            }}
            onEnded={() => {
              pauseExternalAudio();
              setAudioLoading(false);
            }}
          />
          {!videoActivated && !hasError ? (
            <button
              type="button"
              className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-br from-sky-100 via-white to-emerald-100 text-hospital-800"
              onClick={activateVideo}
              aria-label={`Play ${item.title}`}
            >
              <span className="flex h-16 w-16 items-center justify-center rounded-full border border-white bg-white/90 text-2xl text-care-700 shadow-lg">
                <svg viewBox="0 0 24 24" className="ml-1 h-7 w-7" fill="currentColor" aria-hidden="true">
                  <path d="M8 5.5v13l10-6.5-10-6.5Z" />
                </svg>
              </span>
              <span className="rounded-full border border-white/80 bg-white/80 px-4 py-2 text-sm font-semibold shadow-sm">
                Play video
              </span>
            </button>
          ) : null}
          {hasError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-slate-950/90 px-5 text-center text-white" role="alert">
              <p className="m-0 text-sm font-medium">This video could not be loaded. Check your connection and try again.</p>
              <button
                type="button"
                className="rounded-full border border-white/70 px-4 py-2 text-sm font-semibold hover:bg-white/10"
                onClick={() => {
                  setHasError(false);
                  setVideoActivated(false);
                  setVideoReady(false);
                }}
              >
                Try again
              </button>
            </div>
          ) : null}
          {videoActivated && !videoReady && !hasError ? (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/35 text-sm font-medium text-white" role="status">
              Loading video…
            </div>
          ) : null}
        </div>
        <div className="grid gap-2 bg-white p-3 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-center sm:gap-4 sm:px-4">
          <label htmlFor={`video-audio-${item.id}`} className="text-sm font-semibold text-hospital-700">
            Audio language
          </label>
          <select
            id={`video-audio-${item.id}`}
            value={selectedAudioLanguage}
            onChange={(event) => selectAudioLanguage(event.target.value)}
            className="w-full min-w-0 rounded-xl border border-hospital-300 bg-white px-3 py-2 text-sm text-hospital-800 outline-none focus:border-care-600 focus:ring-2 focus:ring-care-200 sm:max-w-xs"
          >
            {videoAudioLanguages.map(({ code, label }) => (
              <option key={code} value={code}>{label}</option>
            ))}
          </select>
          <p className="m-0 text-sm text-hospital-600 sm:col-span-2">
            Selected: {videoAudioLanguages.find(({ code }) => code === selectedAudioLanguage)?.label}
          </p>
          {audioLoading ? (
            <p className="m-0 text-sm text-hospital-600 sm:col-span-2" role="status" aria-live="polite">
              Loading {videoAudioLanguages.find(({ code }) => code === selectedAudioLanguage)?.label} audio…
            </p>
          ) : null}
          {audioError ? (
            <p className="m-0 text-sm font-medium text-red-700 sm:col-span-2" role="alert">
              Could not load the selected audio. Choose English (Original) to restore the video’s original sound.
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[280px] w-full items-center justify-center overflow-hidden rounded-2xl border border-hospital-200 bg-white p-4 sm:h-[360px]">
      <img
        src={item.media_url}
        alt={item.title}
        loading="lazy"
        decoding="async"
        onError={() => setHasError(true)}
        className="h-full w-full rounded-xl object-contain"
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

export default function LearningTopicPage({ onExitFlow }) {
  const { topicId = "" } = useParams();
  const { language, setLanguage, t } = useLanguage();
  const topic = getLearningTopicById(topicId, language);
  const [mediaState, setMediaState] = useState({
    loading: true,
    error: "",
    items: [],
  });
  const mediaItems = useMemo(
    () => mediaForCourseTopic(mediaState.items, topicId),
    [mediaState.items, topicId]
  );
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
  }, [topicId, mediaItems.length]);

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
      onExitFlow={onExitFlow}
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
            <span className="topic-chip">{mediaItems.length} items</span>
          </div>

          {mediaState.loading ? (
            <p className="mt-4 text-sm text-hospital-600">Loading topic images…</p>
          ) : null}

          {mediaState.error ? (
            <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {mediaState.error}
            </p>
          ) : null}

          {!mediaState.loading && !mediaState.error && !mediaItems.length ? (
            <div className="mt-4 rounded-2xl border border-dashed border-hospital-300 bg-hospital-50 p-5 text-sm leading-relaxed text-hospital-700">
              No active media was found for this topic yet. The text lesson is still available.
            </div>
          ) : null}

          <div className="mt-5 grid gap-4">
            {mediaItems.map((item) => (
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

        <div className="flex justify-center pb-2">
          <Link to="/free-qa" className="btn btn-primary w-full sm:w-auto">
            Q/A with chatbot
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}
