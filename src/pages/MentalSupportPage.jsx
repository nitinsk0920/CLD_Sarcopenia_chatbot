import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import { useLanguage } from "../i18n/LanguageContext";

export default function MentalSupportPage({ onRestart }) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const supportMessages = t("mentalSupport.messages");
  const [selected, setSelected] = useState(supportMessages[0] || "");

  useEffect(() => {
    if (!supportMessages.includes(selected)) {
      setSelected(supportMessages[0] || "");
    }
  }, [selected, supportMessages]);

  function handleRestart() {
    onRestart?.();
    navigate("/");
  }

  return (
    <AppLayout
      title={t("mentalSupport.title")}
      subtitle={t("mentalSupport.subtitle")}
      backTo="/result"
    >
      <div className="stack">
        <section className="question-card">
          <p className="question-title">{t("mentalSupport.messageForYou")}</p>
          <p>{selected}</p>
        </section>

        <div className="chip-row">
          {supportMessages.map((msg) => (
            <button key={msg} type="button" className="btn btn-secondary" onClick={() => setSelected(msg)}>
              {t("mentalSupport.showSupport")}
            </button>
          ))}
        </div>

        <label className="field">
          <span>{t("mentalSupport.feeling")}</span>
          <textarea rows={3} placeholder={t("mentalSupport.feelingPlaceholder")} />
        </label>

        <button type="button" className="btn btn-primary btn-block" onClick={handleRestart}>
          {t("mentalSupport.restart")}
        </button>
      </div>
    </AppLayout>
  );
}
