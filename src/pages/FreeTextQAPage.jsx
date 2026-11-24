import { useEffect, useMemo, useRef, useState } from "react";
import AppLayout from "../components/AppLayout";
import ChatbotAnswerCard from "../components/ChatbotAnswerCard";
import { faqItems, getAnswerForQuestion } from "../data/faq";
import { useLanguage } from "../i18n/LanguageContext";
import { ApiError, apiFetch, getApiBaseUrl } from "../services/apiClient";
import { animateChatMessages } from "../utils/uiAnimations";
import { fetchPatientChatHistory } from "../services/reportApi";

const API_BASE_URL = getApiBaseUrl();
const CHAT_URL = `${API_BASE_URL}/api/chat`;
const AUDIO_URL = `${API_BASE_URL}/api/chat/audio`;

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
  onExitFlow,
}) {
  const { t, language } = useLanguage();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(() => [createInitialAssistantMessage(t)]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [playingMessageId, setPlayingMessageId] = useState("");
  const audioElementRef = useRef(null);
  const audioCacheRef = useRef(new Map());
  const chatScrollRef = useRef(null);
  const requestInFlightRef = useRef(false);

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
    let active = true;
    fetchPatientChatHistory(stableSessionId)
      .then((history) => {
        if (!active) return;
        const restored = [createInitialAssistantMessage(t)];
        if (history.session_summary) {
          restored.push({
            id: "restored-session-summary",
            role: "assistant",
            text: `Earlier conversation summary: ${history.session_summary}`,
            topics: [],
            answerId: "restored-session-summary",
            responseLanguage: language,
          });
        }
        (history.messages || []).forEach((entry, index) => {
          if (entry.question) {
            restored.push({
              id: `restored-user-${index}`,
              role: "user",
              text: entry.question,
            });
          }
          if (entry.answer) {
            restored.push({
              id: `restored-assistant-${index}`,
              answerId: `restored-assistant-${index}`,
              role: "assistant",
              text: entry.answer,
              topics: entry.topic && entry.topic !== "general" ? [entry.topic] : [],
              responseLanguage: entry.language || language,
            });
          }
        });
        setMessages(restored);
      })
      .catch(() => {
        // Keep the initial prompt if checkpoint history is unavailable.
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => {
      active = false;
    };
  }, [stableSessionId]);

  useEffect(() => {
    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
      audioCacheRef.current.forEach((url) => {
        if (typeof url === "string" && url.startsWith("blob:")) {
          URL.revokeObjectURL(url);
        }
      });
      audioCacheRef.current.clear();
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

  async function askQuestion(question) {
    if (requestInFlightRef.current) return;
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setErrorText(t("freeQA.emptyPrompt"));
      return;
    }

    requestInFlightRef.current = true;
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
          weak_topic_summary: weakTopicSummary,
        },
        fallbackMessage: "Could not load a chatbot reply.",
      });
      window.clearTimeout(timeoutId);
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
      requestInFlightRef.current = false;
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
        const protectedAudioUrl = data.audio_url.startsWith("http")
          ? data.audio_url
          : `${API_BASE_URL}${data.audio_url}`;
        const audioBlob = await apiFetch(protectedAudioUrl, {
          method: "GET",
          responseType: "blob",
          fallbackMessage: t("freeQA.audioFailed"),
        });
        audioUrl = URL.createObjectURL(audioBlob);
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

  return (
    <AppLayout
      title="ASK CHATBOT ANY QUESTIONS"
      subtitle={t("freeQA.subtitle")}
      backTo="/teaching-chatbot"
      nextTo="/post-test"
      nextLabel={t("freeQA.next")}
      onExitFlow={onExitFlow}
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
                      disabled={historyLoading || loading || streaming}
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
                    disabled={historyLoading || loading || streaming}
                  />
                </label>

                <div className="grid gap-3">
                  <button
                    className="btn btn-primary btn-block"
                    type="submit"
                    disabled={historyLoading || loading || streaming}
                  >
                    {loading || streaming ? t("freeQA.streaming") : t("freeQA.ask")}
                  </button>
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
