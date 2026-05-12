import {
  analysisTopicLabels,
  getPostTestQuestionBank,
  getPreTestQuestionBank,
} from "./quizQuestions";

function buildStrongTopics(summary) {
  return Object.keys(analysisTopicLabels).filter(
    (topic) => (summary?.mistakesByTopic?.[topic] ?? 0) === 0
  );
}

function buildQuizAttemptPayload(quizType, summary, answers, questionBank) {
  return {
    quiz_type: quizType,
    score: summary?.score ?? 0,
    total_questions: summary?.total ?? questionBank.length,
    score_level: summary?.scoreInterpretation || summary?.scoreBand || "Not available",
    weak_topics: summary?.weakTopics || [],
    strong_topics: buildStrongTopics(summary),
    submitted_at: new Date().toISOString(),
    summary: summary || {},
    answers: questionBank.map((question) => {
      const answer = answers?.[question.id];
      const selectedIndex =
        answer && typeof answer === "object"
          ? (typeof answer.originalIndex === "number" ? answer.originalIndex : null)
          : (typeof answer === "number" ? answer : null);
      const correctIndex =
        typeof question.correctIndex === "number" ? question.correctIndex : null;
      const selectedAnswer =
        answer && typeof answer === "object"
          ? (typeof answer.selectedText === "string" ? answer.selectedText : null)
          : (selectedIndex !== null ? question.options?.[selectedIndex] || "" : null);
      const isCorrect =
        answer && typeof answer === "object"
          ? Boolean(answer.isCorrect)
          : selectedIndex === correctIndex;

      return {
        question_id: question.id,
        question_text: question.question,
        topic: question.analysisTopic || question.topic,
        selected_index: selectedIndex,
        selected_answer: selectedAnswer,
        correct_index: correctIndex,
        correct_answer:
          correctIndex !== null ? question.options?.[correctIndex] || "" : null,
        is_correct: isCorrect,
        explanation: question.explanation || "",
      };
    }),
  };
}

export function buildFinalReportPayload({
  sessionId,
  sessionStartedAt,
  patient,
  preTestSummary,
  postTestSummary,
  preTestAnswers,
  postTestAnswers,
  shortChatSummary,
}) {
  const preQuestionBank = getPreTestQuestionBank("en");
  const postQuestionBank = getPostTestQuestionBank("en");

  return {
    session_id: sessionId,
    session_started_at: sessionStartedAt || new Date().toISOString(),
    session_ended_at: new Date().toISOString(),
    patient,
    pre_test: buildQuizAttemptPayload(
      "pre",
      preTestSummary,
      preTestAnswers,
      preQuestionBank
    ),
    post_test: buildQuizAttemptPayload(
      "post",
      postTestSummary,
      postTestAnswers,
      postQuestionBank
    ),
    short_chat_summary: shortChatSummary || "",
    learning_summary: "",
    completion_status: "completed",
    doctor_note: "",
  };
}
