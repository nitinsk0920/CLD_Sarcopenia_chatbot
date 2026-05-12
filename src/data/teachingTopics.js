import rawCourseText from "../../cld_sarcopenia_course_4_language.txt?raw";

const defaultCourseOrder = [
  "what-the-liver-is-and-why-it-matters",
  "what-is-cld",
  "cld-symptoms",
  "what-is-sarcopenia",
  "why-muscle-loss-happens",
  "why-protein-matters",
  "foods-that-help",
  "safe-exercise",
  "what-to-do-when-weak-or-dizzy",
  "safety-warning-signs",
  "closing-reminder",
];

const moduleBlueprints = [
  {
    id: "what-the-liver-is-and-why-it-matters",
    sourceTitle: "What the liver is and why it matters",
    topicKey: "cld",
    imageTopic: "cld",
  },
  {
    id: "what-is-cld",
    sourceTitle: "What Chronic Liver Disease (CLD) is",
    topicKey: "cld",
    imageTopic: "cld",
  },
  {
    id: "cld-symptoms",
    sourceTitle: "What symptoms a person may notice in CLD",
    topicKey: "cld",
    imageTopic: "cld",
  },
  {
    id: "what-is-sarcopenia",
    sourceTitle: "What sarcopenia is",
    topicKey: "sarcopenia",
    imageTopic: "sarcopenia",
  },
  {
    id: "why-muscle-loss-happens",
    sourceTitle: "Why muscle loss happens",
    topicKey: "sarcopenia",
    imageTopic: "sarcopenia",
  },
  {
    id: "why-protein-matters",
    sourceTitle: "Why protein matters",
    topicKey: "diet",
    imageTopic: "diet",
  },
  {
    id: "foods-that-help",
    sourceTitle: "Foods that help",
    topicKey: "diet",
    imageTopic: "diet",
  },
  {
    id: "safe-exercise",
    sourceTitle: "Safe exercise",
    topicKey: "exercise",
    imageTopic: "exercise",
  },
  {
    id: "what-to-do-when-weak-or-dizzy",
    sourceTitle: "What to do when feeling weak or dizzy",
    topicKey: "safety",
    imageTopic: "exercise",
  },
  {
    id: "safety-warning-signs",
    sourceTitle: "Safety and warning signs",
    topicKey: "safety",
    imageTopic: "safety",
  },
  {
    id: "closing-reminder",
    sourceTitle: "Simple closing reminder for every lesson",
    topicKey: null,
    imageTopic: "",
  },
];

const localizedTitles = {
  en: {
    "what-the-liver-is-and-why-it-matters": "What the Liver Is and Why It Matters",
    "what-is-cld": "What Chronic Liver Disease (CLD) Is",
    "cld-symptoms": "What Symptoms a Person May Notice in CLD",
    "what-is-sarcopenia": "What Sarcopenia Is",
    "why-muscle-loss-happens": "Why Muscle Loss Happens",
    "why-protein-matters": "Why Protein Matters",
    "foods-that-help": "Foods That Help",
    "safe-exercise": "Safe Exercise",
    "what-to-do-when-weak-or-dizzy": "What to Do When Feeling Weak or Dizzy",
    "safety-warning-signs": "Safety and Warning Signs",
    "closing-reminder": "Simple Closing Reminder",
  },
  hi: {
    "what-the-liver-is-and-why-it-matters": "लीवर क्या है और यह क्यों महत्वपूर्ण है",
    "what-is-cld": "क्रॉनिक लिवर डिजीज (CLD) क्या है",
    "cld-symptoms": "CLD में व्यक्ति कौन से लक्षण महसूस कर सकता है",
    "what-is-sarcopenia": "सारकोपीनिया क्या है",
    "why-muscle-loss-happens": "मांसपेशियों की कमी क्यों होती है",
    "why-protein-matters": "प्रोटीन क्यों ज़रूरी है",
    "foods-that-help": "कौन से खाद्य पदार्थ मदद करते हैं",
    "safe-exercise": "सुरक्षित व्यायाम",
    "what-to-do-when-weak-or-dizzy": "कमजोरी या चक्कर आने पर क्या करें",
    "safety-warning-signs": "सुरक्षा और चेतावनी संकेत",
    "closing-reminder": "हर पाठ के लिए सरल अंतिम याद दिलाना",
  },
  kn: {
    "what-the-liver-is-and-why-it-matters": "ಲಿವರ್ ಏನು ಮತ್ತು ಅದು ಏಕೆ ಮುಖ್ಯ",
    "what-is-cld": "ಕ್ರಾನಿಕ್ ಲಿವರ್ ಡಿಸೀಸ್ (CLD) ಎಂದರೇನು",
    "cld-symptoms": "CLD ಯಲ್ಲಿ ವ್ಯಕ್ತಿಗೆ ಕಾಣಬಹುದಾದ ಲಕ್ಷಣಗಳು",
    "what-is-sarcopenia": "ಸಾರ್ಕೋಪೀನಿಯಾ ಎಂದರೇನು",
    "why-muscle-loss-happens": "ಸ್ನಾಯು ನಷ್ಟ ಏಕೆ ಉಂಟಾಗುತ್ತದೆ",
    "why-protein-matters": "ಪ್ರೋಟೀನ್ ಏಕೆ ಮುಖ್ಯ",
    "foods-that-help": "ಸಹಾಯಕವಾಗುವ ಆಹಾರಗಳು",
    "safe-exercise": "ಸುರಕ್ಷಿತ ವ್ಯಾಯಾಮ",
    "what-to-do-when-weak-or-dizzy": "ದುರ್ಬಲತೆ ಅಥವಾ ತಲೆಸುತ್ತು ಕಂಡರೆ ಏನು ಮಾಡಬೇಕು",
    "safety-warning-signs": "ಸುರಕ್ಷತೆ ಮತ್ತು ಎಚ್ಚರಿಕೆ ಲಕ್ಷಣಗಳು",
    "closing-reminder": "ಪ್ರತಿ ಪಾಠಕ್ಕೂ ಸರಳ ಅಂತಿಮ ನೆನಪು",
  },
  mr: {
    "what-the-liver-is-and-why-it-matters": "लिव्हर काय आहे आणि ते का महत्त्वाचे आहे",
    "what-is-cld": "क्रॉनिक लिव्हर डिजीज (CLD) म्हणजे काय",
    "cld-symptoms": "CLD मध्ये व्यक्तीला कोणती लक्षणे जाणवू शकतात",
    "what-is-sarcopenia": "सार्कोपेनिया म्हणजे काय",
    "why-muscle-loss-happens": "स्नायू कमी का होतात",
    "why-protein-matters": "प्रथिने का महत्त्वाची आहेत",
    "foods-that-help": "मदत करणारे अन्नपदार्थ",
    "safe-exercise": "सुरक्षित व्यायाम",
    "what-to-do-when-weak-or-dizzy": "अशक्तपणा किंवा चक्कर आल्यास काय करावे",
    "safety-warning-signs": "सुरक्षा आणि इशारा देणारी लक्षणे",
    "closing-reminder": "प्रत्येक धड्यासाठी साधी शेवटची आठवण",
  },
};

const fallbackMessages = {
  en: "This topic is not yet available in the selected language. Showing English content for now.",
  hi: "यह विषय अभी चुनी गई भाषा में उपलब्ध नहीं है। फिलहाल अंग्रेज़ी सामग्री दिखाई जा रही है।",
  kn: "ಈ ವಿಷಯವು ಆಯ್ಕೆ ಮಾಡಿದ ಭಾಷೆಯಲ್ಲಿ ಇನ್ನೂ ಲಭ್ಯವಿಲ್ಲ. ಈಗಾಗಲೇ ಇಂಗ್ಲಿಷ್ ವಿಷಯವನ್ನು ತೋರಿಸಲಾಗುತ್ತಿದೆ.",
  mr: "हा विषय सध्या निवडलेल्या भाषेत उपलब्ध नाही. आत्तासाठी इंग्रजी मजकूर दाखवला जात आहे.",
};

const weakTopicPriorityMap = {
  cld: [
    "what-the-liver-is-and-why-it-matters",
    "what-is-cld",
    "cld-symptoms",
  ],
  sarcopenia: [
    "what-is-sarcopenia",
    "why-muscle-loss-happens",
  ],
  diet: [
    "why-protein-matters",
    "foods-that-help",
  ],
  exercise: [
    "safe-exercise",
  ],
  safety: [
    "what-to-do-when-weak-or-dizzy",
    "safety-warning-signs",
    "closing-reminder",
  ],
};

const languageMarkers = {
  ENGLISH: "en",
  HINDI: "hi",
  KANNADA: "kn",
  MARATHI: "mr",
};

function normalizeHeading(value = "") {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function uniqueItems(items) {
  return [...new Set(items)];
}

function splitIntoParagraphs(value = "") {
  return value
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseCourseText(text) {
  const headingToId = Object.fromEntries(
    moduleBlueprints.map((module) => [normalizeHeading(module.sourceTitle), module.id])
  );

  const sections = text
    .split(/^-{20,}$/m)
    .map((section) => section.trim())
    .filter(Boolean);

  const parsed = {};

  sections.forEach((section) => {
    const titleMatch = section.match(/^(\d+)\)\s+(.+)$/m);
    if (!titleMatch) return;

    const title = titleMatch[2].trim();
    const moduleId = headingToId[normalizeHeading(title)];
    if (!moduleId) return;

    const afterTitle = section.slice(section.indexOf(titleMatch[0]) + titleMatch[0].length).trim();
    const languageContent = {};
    const regex = /^(ENGLISH|HINDI|KANNADA|MARATHI):\s*([\s\S]*?)(?=^(?:ENGLISH|HINDI|KANNADA|MARATHI):|\s*$)/gm;
    let match;

    while ((match = regex.exec(afterTitle))) {
      const languageCode = languageMarkers[match[1]];
      languageContent[languageCode] = match[2].trim();
    }

    parsed[moduleId] = languageContent;
  });

  return parsed;
}

const parsedCourseContent = parseCourseText(rawCourseText);

function getModuleContent(moduleId, language) {
  const languageContent = parsedCourseContent[moduleId] || {};
  const content = languageContent[language] || languageContent.en || "";
  const usedFallback = Boolean(!languageContent[language] && languageContent.en);

  return {
    content,
    usedFallback,
  };
}

function buildLocalizedModules(language = "en") {
  return moduleBlueprints.map((module) => {
    const { content, usedFallback } = getModuleContent(module.id, language);

    return {
      ...module,
      title: localizedTitles[language]?.[module.id] || localizedTitles.en[module.id] || module.sourceTitle,
      content,
      contentParagraphs: splitIntoParagraphs(content),
      fallbackNotice: usedFallback ? fallbackMessages[language] || fallbackMessages.en : "",
    };
  });
}

export function getOrderedCourseModules(weakTopicSummary, mode = "full", language = "en") {
  const courseModuleMap = Object.fromEntries(
    buildLocalizedModules(language).map((module) => [module.id, module])
  );

  if (mode === "focused") {
    const weakTopics = weakTopicSummary?.rankedWeakTopics?.map((item) => item.topic) || [];
    const priorityModuleIds = uniqueItems(
      weakTopics.flatMap((topic) => weakTopicPriorityMap[topic] || [])
    );

    const focusedIds = priorityModuleIds.length
      ? defaultCourseOrder.filter((id) => priorityModuleIds.includes(id))
      : defaultCourseOrder.slice(0, 4);

    return focusedIds.map((id) => courseModuleMap[id]).filter(Boolean);
  }

  return defaultCourseOrder.map((id) => courseModuleMap[id]).filter(Boolean);
}

