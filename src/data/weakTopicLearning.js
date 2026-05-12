import rawCourseText from "../../cld_sarcopenia_course_4_language.txt?raw";
import { analysisTopicLabels, getPreTestQuestionBank } from "./quizQuestions";

const languageMarkers = {
  ENGLISH: "en",
  HINDI: "hi",
  KANNADA: "kn",
  MARATHI: "mr",
};

const topicSectionMap = {
  cld: [
    "What the liver is and why it matters",
    "What Chronic Liver Disease (CLD) is",
    "What symptoms a person may notice in CLD",
  ],
  sarcopenia: [
    "What sarcopenia is",
    "Why muscle loss happens",
  ],
  diet: [
    "Why protein matters",
    "Foods that help",
  ],
  exercise: [
    "Safe exercise",
  ],
  safety: [
    "What to do when feeling weak or dizzy",
    "Safety and warning signs",
    "Simple closing reminder for every lesson",
  ],
};

function normalizeHeading(value = "") {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function splitIntoSentences(text = "") {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseCourseSections(text) {
  const sections = text
    .split(/^-{20,}$/m)
    .map((section) => section.trim())
    .filter(Boolean);

  const parsed = {};

  sections.forEach((section) => {
    const titleMatch = section.match(/^(\d+)\)\s+(.+)$/m);
    if (!titleMatch) return;

    const title = titleMatch[2].trim();
    const normalizedTitle = normalizeHeading(title);
    const afterTitle = section.slice(section.indexOf(titleMatch[0]) + titleMatch[0].length).trim();
    const languageContent = {};
    const regex =
      /^(ENGLISH|HINDI|KANNADA|MARATHI):\s*([\s\S]*?)(?=^(?:ENGLISH|HINDI|KANNADA|MARATHI):|\s*$)/gm;
    let match;

    while ((match = regex.exec(afterTitle))) {
      languageContent[languageMarkers[match[1]]] = match[2].trim();
    }

    parsed[normalizedTitle] = languageContent;
  });

  return parsed;
}

const parsedCourseSections = parseCourseSections(rawCourseText);

function getTopicSnippet(topic, language = "en") {
  const sectionTitles = topicSectionMap[topic] || [];
  const combinedText = sectionTitles
    .map((title) => {
      const content = parsedCourseSections[normalizeHeading(title)] || {};
      return content[language] || content.en || "";
    })
    .filter(Boolean)
    .join(" ");

  const sentences = splitIntoSentences(combinedText);
  return sentences.slice(0, 2).join(" ");
}

function buildSupportiveExplanation(question, language = "en") {
  const topicSnippet = getTopicSnippet(question.analysisTopic || question.topic, language);
  const questionExplanation =
    language === "en" ? question.explanation || "" : "";

  return [questionExplanation, topicSnippet]
    .filter(Boolean)
    .join(" ")
    .trim();
}

export function extractWrongQuestions(summary, language = "en") {
  const questionBank = getPreTestQuestionBank(language);
  const questionMap = Object.fromEntries(questionBank.map((item) => [item.id, item]));

  return (summary?.wrongAnswers || [])
    .map((item) => {
      const question = questionMap[item.id];
      if (!question) return null;

      return {
        id: item.id,
        topic: item.analysisTopic || item.topic,
        topicTag: item.topicTag,
        question: question.question,
        selectedAnswer:
          typeof item.selectedIndex === "number"
            ? question.options?.[item.selectedIndex] || ""
            : "",
        correctAnswer:
          typeof item.correctIndex === "number"
            ? question.options?.[item.correctIndex] || ""
            : "",
        explanation: buildSupportiveExplanation(question, language),
      };
    })
    .filter(Boolean);
}

export function groupWrongQuestionsByTopic(summary, language = "en") {
  const wrongQuestions = extractWrongQuestions(summary, language);
  const rankedTopics = summary?.rankedWeakTopics || [];

  const groupedMap = wrongQuestions.reduce((accumulator, item) => {
    if (!accumulator[item.topic]) {
      accumulator[item.topic] = [];
    }
    accumulator[item.topic].push(item);
    return accumulator;
  }, {});

  return rankedTopics
    .filter((topicSummary) => groupedMap[topicSummary.topic]?.length)
    .map((topicSummary) => ({
      topic: topicSummary.topic,
      label: analysisTopicLabels[topicSummary.topic] || topicSummary.topic,
      mistakes: topicSummary.mistakes,
      items: groupedMap[topicSummary.topic],
    }));
}
