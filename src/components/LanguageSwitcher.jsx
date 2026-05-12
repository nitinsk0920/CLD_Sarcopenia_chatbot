import { useLanguage } from "../i18n/LanguageContext";

export default function LanguageSwitcher({ compact = false }) {
  const { language, setLanguage, t, availableLanguages } = useLanguage();

  return (
    <label className={`field ${compact ? "min-w-[160px]" : "min-w-[200px]"}`}>
      <span>{t("app.languageLabel")}</span>
      <select value={language} onChange={(event) => setLanguage(event.target.value)}>
        {availableLanguages.map((code) => (
          <option key={code} value={code}>
            {t(`languages.${code}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
