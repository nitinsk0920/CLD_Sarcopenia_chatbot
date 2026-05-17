const DEFAULT_SUPABASE_URL = "https://gynjgfoxpdqzwbpvckwf.supabase.co";
const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || DEFAULT_SUPABASE_URL).replace(/\/$/, "");
const LEARNING_AUDIO_BASE_URL =
  import.meta.env.VITE_LEARNING_AUDIO_BASE_URL ||
  `${SUPABASE_URL}/storage/v1/object/public/learning-audio`;

const LANGUAGE_AUDIO_CONFIG = {
  en: { folder: "ENGLISH" },
  hi: { folder: "HINDI" },
  kn: { folder: "KANNADA" },
  mr: { folder: "MARATHI" },
};

export const learningAudioMap = {
  en: {
    1: "1 EN.ogg",
    2: "2 EN.ogg",
    3: "3 EN.ogg",
    4: "4 EN.ogg",
    5: "5 EN.ogg",
    6: "6 EN.ogg",
    7: "7 EN.ogg",
    8: "8 EN.ogg",
    9: "9 EN.ogg",
    10: "10 EN.ogg",
    11: "11 EN.mp3",
  },
  hi: {
    1: "1 HIN.mpeg",
    2: "2 hin.mpeg",
    3: "3 hin.mp3",
    4: "4 hin.mp3",
    5: "5 hin.mp3",
    6: "6 hin.mp3",
    7: "7 hin.mp3",
    8: "8 hin.mp3",
    9: "9 hin.mp3",
    10: "10 hin.mp3",
    11: "11 hin.mp3",
  },
  kn: {
    1: "1 kan.mp3",
    2: "2 kan.mp3",
    3: "3 kan.mp3",
    4: "4 kan.mp3",
    5: "5 kan.mp3",
    6: "6 kan.mp3",
    7: "7 kan.mp3",
    8: "8 kan.mp3",
    9: "9 kan.mp3",
    10: "10 kan.mp3",
    11: "11 kan.mp3",
  },
  mr: {
    1: "1 MA.mp3",
    2: "2 MA.mp3",
    3: "3 MA.mp3",
    4: "4 MA.mp3",
    5: "5 MA.mp3",
    6: "6 MA.mp3",
    7: "7 MA.mp3",
    8: "8 MA.mp3",
    9: "9 MA.mp3",
    10: "10 MA.mp3",
    11: "11 ma.mp3",
  },
};

function buildPublicAudioUrl(folder, fileName) {
  return `${LEARNING_AUDIO_BASE_URL}/${folder}/${encodeURIComponent(fileName)}`;
}

export function getLearningAudioUrls(languageCode = "en", sectionNumber) {
  const config = LANGUAGE_AUDIO_CONFIG[languageCode] || LANGUAGE_AUDIO_CONFIG.en;
  const primaryFileName = learningAudioMap[languageCode]?.[sectionNumber];

  if (!primaryFileName) {
    return [];
  }

  return [buildPublicAudioUrl(config.folder, primaryFileName)];
}
