const speechLanguageMap = {
  en: "en-IN",
  hi: "hi-IN",
  kn: "kn-IN",
  mr: "mr-IN",
};

function getSpeechLanguage(language = "en") {
  return speechLanguageMap[language] || "en-IN";
}

function findMatchingVoice(voices = [], language = "en") {
  const target = getSpeechLanguage(language).toLowerCase();
  const base = target.split("-")[0];

  return (
    voices.find((voice) => voice.lang?.toLowerCase() === target) ||
    voices.find((voice) => voice.lang?.toLowerCase().startsWith(`${base}-`)) ||
    voices.find((voice) => voice.lang?.toLowerCase() === base) ||
    null
  );
}

export function speakText(text, language = "en", callbacks = {}) {
  if (!("speechSynthesis" in window)) {
    return false;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const voice = findMatchingVoice(voices, language);

  utterance.lang = getSpeechLanguage(language);
  utterance.rate = 0.92;
  utterance.pitch = 1;

  if (voice) {
    utterance.voice = voice;
  }

  if (callbacks.onend) {
    utterance.onend = callbacks.onend;
  }

  if (callbacks.onerror) {
    utterance.onerror = callbacks.onerror;
  }

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
  return true;
}

export function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
