import { createContext, useContext, useEffect, useMemo, useState } from "react";
import en from "./translations/en";
import kn from "./translations/kn";
import hi from "./translations/hi";
import mr from "./translations/mr";

const LANGUAGE_STORAGE_KEY = "cld-chatbot-language";

const languageMap = {
  en,
  kn,
  hi,
  mr,
};

const aliasMap = {
  english: "en",
  kannada: "kn",
  hindi: "hi",
  marathi: "mr",
  en: "en",
  kn: "kn",
  hi: "hi",
  mr: "mr",
};

const LanguageContext = createContext(null);

function getNestedValue(source, path) {
  return path.split(".").reduce((current, key) => current?.[key], source);
}

function interpolateValue(value, variables = {}) {
  if (Array.isArray(value)) {
    return value.map((item) => interpolateValue(item, variables));
  }

  if (typeof value !== "string") {
    return value;
  }

  return value.replace(/\{(\w+)\}/g, (match, key) => {
    return variables[key] ?? match;
  });
}

export function normalizeLanguageCode(value) {
  if (!value) return "en";
  const normalized = String(value).trim().toLowerCase();
  return aliasMap[normalized] || "en";
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    if (typeof window === "undefined") return "en";
    return normalizeLanguageCode(window.localStorage.getItem(LANGUAGE_STORAGE_KEY));
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  function setLanguage(nextLanguage) {
    setLanguageState(normalizeLanguageCode(nextLanguage));
  }

  function t(path, variables = {}) {
    const currentDictionary = languageMap[language] || en;
    const value =
      getNestedValue(currentDictionary, path) ??
      getNestedValue(en, path) ??
      path;

    return interpolateValue(value, variables);
  }

  function formatList(items = []) {
    if (!items.length) return "";

    try {
      return new Intl.ListFormat(language, {
        style: "long",
        type: "conjunction",
      }).format(items);
    } catch {
      return items.join(", ");
    }
  }

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      formatList,
      availableLanguages: Object.keys(languageMap),
    }),
    [language]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }

  return context;
}
