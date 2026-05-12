const topicLabels = {
  cld: "CLD / Liver",
  sarcopenia: "Sarcopenia",
  diet: "Diet / Protein",
  exercise: "Exercise",
  safety: "Safety",
};

const topicKeywords = {
  cld: ["cld", "liver", "hepatic", "cirrhosis", "hepar"],
  sarcopenia: ["sarcopenia", "sarcopenic", "muscle", "weakness"],
  diet: ["diet", "protein", "protien", "food", "meal", "nutrition", "eggs", "dal", "paneer", "legume"],
  exercise: ["exercise", "excercise", "walking", "walk", "activity", "training", "fitness"],
  safety: ["safety", "safe", "dizzy", "dizziness", "warning"],
};

const mediaFiles = {
  ...import.meta.glob("../../chatbot_imgs/**/*.{png,jpg,jpeg,webp,gif,avif,svg}", {
    eager: true,
    import: "default",
  }),
  ...import.meta.glob("../../chat_imgs/**/*.{png,jpg,jpeg,webp,gif,avif,svg}", {
    eager: true,
    import: "default",
  }),
};

const rootMediaFiles = import.meta.glob("../../{chatbot_imgs,chat_imgs}/*.{png,jpg,jpeg,webp,gif,avif,svg}", {
  eager: true,
  import: "default",
});

function detectTopicFromFilename(filename) {
  const lower = filename.toLowerCase();
  if (topicKeywords.diet.some((key) => lower.includes(key))) return "diet";
  if (topicKeywords.exercise.some((key) => lower.includes(key))) return "exercise";
  if (topicKeywords.sarcopenia.some((key) => lower.includes(key))) return "sarcopenia";
  if (topicKeywords.cld.some((key) => lower.includes(key))) return "cld";
  if (topicKeywords.safety.some((key) => lower.includes(key))) return "safety";
  return "";
}

function buildTopicMediaMap() {
  const map = {
    cld: [],
    sarcopenia: [],
    diet: [],
    exercise: [],
    safety: [],
  };

  const merged = { ...mediaFiles, ...rootMediaFiles };
  Object.entries(merged).forEach(([filePath, url]) => {
    const topic = detectTopicFromFilename(filePath);
    if (!topic) return;
    map[topic].push(url);
  });

  return map;
}

const topicMediaMap = buildTopicMediaMap();

export function inferTopicFromText(text = "") {
  const lower = text.toLowerCase();
  const orderedTopics = ["diet", "exercise", "sarcopenia", "cld", "safety"];
  const match = orderedTopics.find((topic) =>
    topicKeywords[topic].some((key) => lower.includes(key))
  );
  return match || "";
}

export function getTopicForMessage(messageTopics = [], messageText = "") {
  const fromMessage = messageTopics.find((topic) => topicLabels[topic]);
  if (fromMessage) return fromMessage;
  return inferTopicFromText(messageText);
}

export function getImageForTopic(topic) {
  if (!topic || !topicMediaMap[topic]?.length) return "";
  return topicMediaMap[topic][0];
}

export function getTopicLabel(topic) {
  return topicLabels[topic] || "";
}

export function getTopicMediaSummary() {
  return Object.fromEntries(
    Object.entries(topicMediaMap).map(([topic, files]) => [topic, files.length])
  );
}
