import rawCourseText from "../../cld_sarcopenia_course_4_language.txt?raw";

export const LEARNING_TOPIC_ORDER = ["cld", "sarcopenia", "diet", "exercise", "safety"];

const LANGUAGE_MARKERS = {
  ENGLISH: "en",
  HINDI: "hi",
  KANNADA: "kn",
  MARATHI: "mr",
};

const TOPIC_DEFINITIONS = [
  {
    id: "cld",
    titles: {
      en: "CLD",
      hi: "सीएलडी",
      kn: "ಸಿಎಲ್‌ಡಿ",
      mr: "सीएलडी",
    },
    sourceTitles: [
      "What the liver is and why it matters",
      "What Chronic Liver Disease (CLD) is",
      "What symptoms a person may notice in CLD",
    ],
  },
  {
    id: "sarcopenia",
    titles: {
      en: "Sarcopenia",
      hi: "सार्कोपीनिया",
      kn: "ಸಾರ್ಕೋಪೀನಿಯಾ",
      mr: "सार्कोपेनिया",
    },
    sourceTitles: [
      "What sarcopenia is",
      "Why muscle loss happens",
    ],
  },
  {
    id: "diet",
    titles: {
      en: "Diet / Protein",
      hi: "आहार / प्रोटीन",
      kn: "ಆಹಾರ / ಪ್ರೋಟೀನ್",
      mr: "आहार / प्रथिने",
    },
    sourceTitles: [
      "Why protein matters",
      "Foods that help",
    ],
  },
  {
    id: "exercise",
    titles: {
      en: "Exercises",
      hi: "व्यायाम",
      kn: "ವ್ಯಾಯಾಮ",
      mr: "व्यायाम",
    },
    sourceTitles: [
      "Safe exercise",
    ],
  },
  {
    id: "safety",
    titles: {
      en: "Safety / Warning Signs",
      hi: "सुरक्षा / चेतावनी संकेत",
      kn: "ಸುರಕ್ಷತೆ / ಎಚ್ಚರಿಕೆ ಲಕ್ಷಣಗಳು",
      mr: "सुरक्षा / इशारा चिन्हे",
    },
    sourceTitles: [
      "What to do when feeling weak or dizzy",
      "Safety and warning signs",
      "Simple closing reminder for every lesson",
    ],
  },
];

const WEAK_TOPIC_TO_LEARNING_TOPIC = {
  cld: "cld",
  sarcopenia: "sarcopenia",
  diet: "diet",
  exercise: "exercise",
  safety: "safety",
};

function normalizeHeading(value = "") {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function cleanText(value = "") {
  return value
    .replace(/\r/g, "")
    .trim();
}

function splitParagraphs(value = "") {
  return cleanText(value)
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function createIntro(paragraphs = []) {
  return paragraphs[0] || "";
}

function parseCourseText(text) {
  const sectionLookup = new Map();
  const sections = text
    .split(/^-{20,}$/m)
    .map((section) => section.trim())
    .filter(Boolean);

  sections.forEach((section) => {
    const titleMatch = section.match(/^(\d+)\)\s+(.+)$/m);
    if (!titleMatch) return;

    const order = Number(titleMatch[1]);
    const sourceTitle = titleMatch[2].trim();
    const contentByLanguage = {};
    const afterTitle = section.slice(section.indexOf(titleMatch[0]) + titleMatch[0].length).trim();
    const languageRegex =
      /^(ENGLISH|HINDI|KANNADA|MARATHI):\s*([\s\S]*?)(?=^(?:ENGLISH|HINDI|KANNADA|MARATHI):|\s*$)/gm;
    let match;

    while ((match = languageRegex.exec(afterTitle))) {
      contentByLanguage[LANGUAGE_MARKERS[match[1]]] = cleanText(match[2]);
    }

    sectionLookup.set(normalizeHeading(sourceTitle), {
      id: normalizeHeading(sourceTitle).replace(/\s+/g, "-"),
      order,
      sourceTitle,
      contentByLanguage,
    });
  });

  return sectionLookup;
}

const parsedSections = parseCourseText(rawCourseText);

function getTopicSections(topicDefinition, language = "en") {
  return topicDefinition.sourceTitles
    .map((sourceTitle) => parsedSections.get(normalizeHeading(sourceTitle)))
    .filter(Boolean)
    .map((section) => {
      const content = section.contentByLanguage[language] || section.contentByLanguage.en || "";
      const paragraphs = splitParagraphs(content);
      return {
        id: section.id,
        order: section.order,
        title: section.sourceTitle,
        paragraphs,
        content,
      };
    });
}

export function getLearningTopics(language = "en") {
  return TOPIC_DEFINITIONS.map((topicDefinition) => {
    const sections = getTopicSections(topicDefinition, language);
    const firstSection = sections[0];
    const introParagraphs = firstSection?.paragraphs || [];
    const remainingSections =
      sections.length > 1
        ? [
            {
              ...firstSection,
              paragraphs: introParagraphs.slice(1),
            },
            ...sections.slice(1),
          ].filter((section) => section.paragraphs.length)
        : [];

    return {
      id: topicDefinition.id,
      title: topicDefinition.titles[language] || topicDefinition.titles.en,
      intro: createIntro(introParagraphs),
      sections: remainingSections,
      allSections: sections,
    };
  });
}

export function getLearningTopicById(topicId, language = "en") {
  return getLearningTopics(language).find((topic) => topic.id === topicId) || null;
}

export function getLearningTopicIndex(topicId) {
  return LEARNING_TOPIC_ORDER.indexOf(topicId);
}

export function getRecommendedLearningTopicId(weakTopicSummary) {
  const rankedTopics = weakTopicSummary?.rankedWeakTopics || [];
  const firstMatch = rankedTopics
    .map((item) => WEAK_TOPIC_TO_LEARNING_TOPIC[item.topic])
    .find(Boolean);

  return firstMatch || LEARNING_TOPIC_ORDER[0];
}
