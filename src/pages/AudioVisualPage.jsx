import AppLayout from "../components/AppLayout";
import { useLanguage } from "../i18n/LanguageContext";
import { speakText } from "../utils/speechSynthesis";

const educationPoints = [
  "Eat balanced meals with enough protein as advised.",
  "Do light to moderate activity regularly.",
  "Do not skip follow-up visits.",
  "Never change medicines without doctor advice.",
];

export default function AudioVisualPage() {
  const { language } = useLanguage();

  function playAudio() {
    const text =
      "CLD and sarcopenia education. Eat enough protein, stay active safely, and follow nurse and doctor advice.";
    if (!speakText(text, language)) {
      alert("Text-to-speech is not supported in this browser.");
    }
  }

  return (
    <AppLayout
      title="Audio / Visual Support"
      subtitle="Simple text and voice support for easy understanding."
      backTo="/free-qa"
      nextTo="/mental-support"
      nextLabel="Mental Support"
    >
      <div className="stack">
        <button type="button" className="btn btn-primary btn-block" onClick={playAudio}>
          Play Audio Explanation
        </button>

        <div className="grid-2">
          {educationPoints.map((point) => (
            <article className="visual-card" key={point}>
              <div className="visual-icon" aria-hidden>
                +
              </div>
              <p>{point}</p>
            </article>
          ))}
        </div>

        <p className="muted">
          Visuals are placeholder cards for this demo. You can later replace them with real clinical
          illustrations.
        </p>
      </div>
    </AppLayout>
  );
}
