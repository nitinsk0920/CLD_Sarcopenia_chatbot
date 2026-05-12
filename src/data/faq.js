export const faqItems = [
  {
    question: "Why am I feeling weak?",
    answer:
      "CLD and sarcopenia can reduce muscle strength. Small frequent meals, enough protein, and safe exercise can help. Please also inform your nurse or doctor.",
    keywords: ["weak", "tired", "strength"],
  },
  {
    question: "Can I eat eggs or dal?",
    answer:
      "In many cases, eggs and dal are good protein sources. Your exact diet should follow your nurse or doctor advice for your condition.",
    keywords: ["egg", "eggs", "dal", "protein", "food", "diet"],
  },
  {
    question: "Is exercise safe for me?",
    answer:
      "Usually light to moderate exercise is helpful when done safely. Stop if dizzy or unwell and discuss with your nurse before changing activity level.",
    keywords: ["exercise", "walk", "walking", "activity"],
  },
  {
    question: "Can sarcopenia be reversed?",
    answer:
      "Many patients improve with nutrition, activity, and regular follow-up. Progress differs by person, so keep working with your care team.",
    keywords: ["reversed", "reverse", "recover", "improve", "sarcopenia"],
  },
  {
    question: "Can I change my medicines based on chatbot advice?",
    answer:
      "No. This demo chatbot is only for education. Never change medicines without consulting your doctor.",
    keywords: ["medicine", "medicines", "tablet", "dose", "change"],
  },
];

export function getAnswerForQuestion(text) {
  const lowerText = text.toLowerCase().trim();
  if (!lowerText) {
    return "Please type your question. You can ask about weakness, diet, protein, exercise, or safety.";
  }

  const match = faqItems.find((item) =>
    item.keywords.some((word) => lowerText.includes(word))
  );

  return (
    match?.answer ||
    "I can help with basic education on CLD, sarcopenia, diet, exercise, and safety. For personal medical decisions, please consult your nurse or doctor."
  );
}
