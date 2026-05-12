import { useEffect, useMemo, useRef, useState } from "react";
import AppLayout from "../components/AppLayout";
import ChatbotAnswerCard from "../components/ChatbotAnswerCard";
import { faqItems, getAnswerForQuestion } from "../data/faq";
import { useLanguage } from "../i18n/LanguageContext";
import { ApiError, apiFetch, getApiBaseUrl } from "../services/apiClient";
import { animateChatMessages } from "../utils/uiAnimations";

const API_BASE_URL = getApiBaseUrl();
const CHAT_URL = `${API_BASE_URL}/api/chat`;
const AUDIO_URL = `${API_BASE_URL}/api/chat/audio`;
const TRANSCRIBE_URL = `${API_BASE_URL}/api/chat/transcribe`;

function createInitialAssistantMessage(t) {
  return {
    id: "initial-assistant-message",
    role: "assistant",
    text: t("freeQA.initialAnswer"),
    topics: [],
    answerId: "initial-assistant-message",
    responseLanguage: "en",
  };
}

export default function FreeTextQAPage({
  patient,
  weakTopicSummary,
  sessionId,
  onSessionSummaryChange,
}) {
  const { t, language } = useLanguage();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(() => [createInitialAssistantMessage(t)]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [recordingStatus, setRecordingStatus] = useState("");
  const [playingMessageId, setPlayingMessageId] = useState("");
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const audioElementRef = useRef(null);
  const audioCacheRef = useRef(new Map());
  const chatScrollRef = useRef(null);

  const stableSessionId = useMemo(
    () => sessionId || window.crypto?.randomUUID?.() || `chat-session-${Date.now()}`,
    [sessionId]
  );

  useEffect(() => {
    setMessages((current) => {
      if (current.length !== 1 || current[0].id !== "initial-assistant-message") {
        return current;
      }
      return [createInitialAssistantMessage(t)];
    });
  }, [t]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
    };
  }, []);

  useEffect(() => {
    const container = chatScrollRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [messages, loading, streaming]);

  useEffect(() => {
    animateChatMessages(chatScrollRef.current);
  }, [messages.length, loading]);

  async function streamAssistantMessage(nextMessage) {
    const words = nextMessage.text.split(/\s+/).filter(Boolean);
    const streamId = nextMessage.id;

    setStreaming(true);
    setMessages((current) => [
      ...current,
      {
        ...nextMessage,
        text: "",
      },
    ]);

    let visibleText = "";
    for (let index = 0; index < words.length; index += 1) {
      visibleText = visibleText ? `${visibleText} ${words[index]}` : words[index];
      setMessages((current) =>
        current.map((message) =>
          message.id === streamId ? { ...message, text: visibleText } : message
        )
      );
      // Small progressive render to feel like streaming in chat.
      // This keeps the backend unchanged while improving perceived responsiveness.
      // eslint-disable-next-line no-await-in-loop
      await new Promise((resolve) => window.setTimeout(resolve, 18));
    }

    setStreaming(false);
  }

  async function askQuestion(question, extra = {}) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setErrorText(t("freeQA.emptyPrompt"));
      return;
    }

    setLoading(true);
    setErrorText("");

    const userMessage = {
      id: window.crypto?.randomUUID?.() || `user-${Date.now()}`,
      role: "user",
      text: trimmedQuestion,
    };
    setMessages((current) => [...current, userMessage]);
    setInput("");

    try {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 65000);
      const data = await apiFetch(CHAT_URL, {
        method: "POST",
        signal: controller.signal,
        body: {
          session_id: stableSessionId,
          question: trimmedQuestion,
          selected_language: language,
          transcribed_language: extra.transcribedLanguage || "",
          patient_context: patient,
          weak_topic_summary: weakTopicSummary,
        },
        fallbackMessage: "Could not load a chatbot reply.",
      });
      window.clearTimeout(timeoutId);
      if (data.session_summary && onSessionSummaryChange) {
        onSessionSummaryChange(data.session_summary);
      }
      const assistantMessage = {
        id: data.answer_id || window.crypto?.randomUUID?.() || `assistant-${Date.now()}`,
        answerId: data.answer_id || window.crypto?.randomUUID?.() || `assistant-${Date.now()}`,
        role: "assistant",
        text: data.answer || t("freeQA.emptyResponse"),
        topics: data.selected_topics || [],
        responseLanguage: data.response_language || language,
      };
      setLoading(false);
      await streamAssistantMessage(assistantMessage);
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        setLoading(false);
        return;
      }
      const message =
        error instanceof Error ? error.message : t("freeQA.unknownError");
      setErrorText(
        /failed to fetch|network|connect|abort/i.test(message)
          ? t("freeQA.networkFallback")
          : t("freeQA.errorFallback", { message })
      );
      setLoading(false);
      await streamAssistantMessage({
        id: window.crypto?.randomUUID?.() || `fallback-${Date.now()}`,
        answerId: window.crypto?.randomUUID?.() || `fallback-${Date.now()}`,
        role: "assistant",
        text: getAnswerForQuestion(trimmedQuestion),
        topics: [],
        responseLanguage: language,
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    await askQuestion(input);
  }

  async function handlePlayAudio(message) {
    if (!message?.text) return;

    setErrorText("");
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.currentTime = 0;
    }

    try {
      let audioUrl = audioCacheRef.current.get(message.answerId);
      if (!audioUrl) {
        const data = await apiFetch(AUDIO_URL, {
          method: "POST",
          body: {
            session_id: stableSessionId,
            answer_id: message.answerId,
            text: message.text,
            language: message.responseLanguage || language,
          },
          fallbackMessage: t("freeQA.audioFailed"),
        });
        audioUrl = data.audio_url.startsWith("http")
          ? data.audio_url
          : `${API_BASE_URL}${data.audio_url}`;
        audioCacheRef.current.set(message.answerId, audioUrl);
      }

      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;
      setPlayingMessageId(message.id);
      audio.onended = () => setPlayingMessageId("");
      audio.onerror = () => {
        setPlayingMessageId("");
        setErrorText(t("freeQA.audioFailed"));
      };
      await audio.play();
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        setPlayingMessageId("");
        return;
      }
      const messageText =
        error instanceof Error ? error.message : t("freeQA.audioFailed");
      setPlayingMessageId("");
      setErrorText(messageText);
    }
  }

  async function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setErrorText(t("freeQA.voiceNotSupported"));
      return;
    }

    setErrorText("");
    setRecordingStatus(t("freeQA.recordingStarted"));

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      recordedChunksRef.current = [];
      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setRecording(false);
        setTranscribing(true);
        setRecordingStatus(t("freeQA.transcribing"));

        const audioBlob = new Blob(recordedChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
        }

        try {
          const formData = new FormData();
          formData.append("session_id", stableSessionId);
          formData.append("selected_language", language);
          formData.append("audio_file", audioBlob, "voice-input.webm");

          const data = await apiFetch(TRANSCRIBE_URL, {
            method: "POST",
            body: formData,
            fallbackMessage: t("freeQA.transcriptionFailed"),
          });
          setRecordingStatus(
            t("freeQA.transcribedAs", {
              transcript: data.transcript,
            })
          );
          setInput(data.transcript);
          await askQuestion(data.transcript, {
            transcribedLanguage: data.detected_language,
          });
        } catch (error) {
          if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
            setRecordingStatus("");
            return;
          }
          const message =
            error instanceof Error ? error.message : t("freeQA.transcriptionFailed");
          setErrorText(message);
          setRecordingStatus("");
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
      setRecording(true);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : t("freeQA.voicePermissionFailed");
      setErrorText(message);
      setRecording(false);
      setRecordingStatus("");
    }
  }

  return (
    <AppLayout
      title="ASK CHATBOT ANY QUESTIONS"
      subtitle={t("freeQA.subtitle")}
      backTo="/teaching-chatbot"
      nextTo="/post-test"
      nextLabel={t("freeQA.next")}
    >
      <div className="stack">
        <section className="question-card p-0">
          <div className="flex min-h-[72vh] flex-col">
            <div className="border-b border-hospital-200 px-5 py-4 sm:px-6">
              <div>
                <p className="question-title mb-1">{t("freeQA.chatTitle")}</p>
                <p className="muted">{t("freeQA.chatHelper")}</p>
              </div>
            </div>

            <div
              ref={chatScrollRef}
              className="chat-box h-[44vh] flex-1 rounded-none border-0 bg-hospital-50/50 px-4 py-5 sm:px-6"
            >
              {messages.map((message) =>
                message.role === "assistant" ? (
                  <ChatbotAnswerCard
                    key={message.id}
                    text={message.text}
                    topics={message.topics}
                    onPlayAudio={() => handlePlayAudio(message)}
                    isPlayingAudio={playingMessageId === message.id}
                    showMedia={false}
                  />
                ) : (
                  <article key={message.id} className="bubble bubble-user" data-chat-message>
                    <p className="bubble-text">{message.text}</p>
                  </article>
                )
              )}
              {loading ? (
                <article className="bubble bubble-bot" data-chat-message>
                  <p className="bubble-text">{t("freeQA.thinking")}</p>
                </article>
              ) : null}
            </div>

            <div className="border-t border-hospital-200 bg-white px-4 py-4 sm:px-6">
              <div className="mb-4">
                <p className="mb-2 text-sm font-semibold text-hospital-800">
                  {t("freeQA.quickQuestions")}
                </p>
                <div className="flex flex-wrap gap-2">
                  {faqItems.slice(0, 6).map((item) => (
                    <button
                      key={item.question}
                      type="button"
                      className="rounded-full border border-hospital-300 bg-white px-4 py-2 text-sm font-medium text-hospital-700 transition hover:bg-hospital-50"
                      onClick={() => askQuestion(item.question)}
                      disabled={loading || streaming || transcribing}
                    >
                      {item.question}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAsk} className="stack-sm">
                <label className="field">
                  <span>{t("freeQA.field")}</span>
                  <textarea
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder={t("freeQA.placeholder")}
                    rows={2}
                    disabled={loading || streaming || transcribing}
                  />
                </label>

                <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
                  <button
                    className="btn btn-primary btn-block"
                    type="submit"
                    disabled={loading || streaming || transcribing}
                  >
                    {loading || streaming ? t("freeQA.streaming") : t("freeQA.ask")}
                  </button>
                  <button
                    className="btn btn-secondary gap-2"
                    type="button"
                    onClick={recording ? stopRecording : startRecording}
                    disabled={loading || streaming || transcribing}
                    aria-label={recording ? t("freeQA.stopRecording") : t("freeQA.recordVoice")}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      className="h-5 w-5"
                    >
                      <path d="M12 3a3 3 0 0 1 3 3v6a3 3 0 1 1-6 0V6a3 3 0 0 1 3-3Z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <path d="M12 19v3" />
                      <path d="M8 22h8" />
                    </svg>
                    <span>{recording ? t("freeQA.stopRecording") : t("freeQA.recordVoice")}</span>
                  </button>
                  <div className="rounded-xl border border-hospital-200 bg-hospital-50 px-4 py-3 text-sm text-hospital-700">
                    {transcribing
                      ? t("freeQA.transcribing")
                      : recordingStatus || t("freeQA.voiceHint")}
                  </div>
                </div>
              </form>

              {errorText ? <p className="mt-3 error-text">{errorText}</p> : null}
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
