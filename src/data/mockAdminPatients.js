export const mockAdminPatients = [
  {
    patientId: "PT-1001",
    age: 58,
    language: "English",
    preTestScore: 3,
    postTestScore: 7,
    completionStatus: "Completed",
    weakTopics: ["diet and protein", "exercise"],
    answerSummary: {
      correctPre: 3,
      correctPost: 7,
      wrongPreTopics: ["diet and protein", "exercise", "safety"],
      wrongPostTopics: ["safety"],
    },
    courseCompletionStatus: "Completed full learning flow",
    learningNotes:
      "Patient completed weak-topic learning first and showed strong improvement in diet and exercise understanding.",
  },
  {
    patientId: "PT-1002",
    age: 64,
    language: "Hindi",
    preTestScore: 2,
    postTestScore: 5,
    completionStatus: "Completed",
    weakTopics: ["CLD basics", "sarcopenia basics", "safety"],
    answerSummary: {
      correctPre: 2,
      correctPost: 5,
      wrongPreTopics: ["CLD basics", "sarcopenia basics", "safety", "diet and protein"],
      wrongPostTopics: ["safety", "diet and protein"],
    },
    courseCompletionStatus: "Completed full learning flow",
    learningNotes:
      "Patient required simpler phrasing and repeated CLD explanation. Post-test shows moderate improvement.",
  },
  {
    patientId: "PT-1003",
    age: 49,
    language: "Kannada",
    preTestScore: 5,
    postTestScore: 7,
    completionStatus: "Completed",
    weakTopics: ["safety"],
    answerSummary: {
      correctPre: 5,
      correctPost: 7,
      wrongPreTopics: ["safety", "exercise"],
      wrongPostTopics: ["safety"],
    },
    courseCompletionStatus: "Completed full learning flow",
    learningNotes:
      "Patient had good baseline knowledge. Needed reinforcement around dizziness safety rule.",
  },
  {
    patientId: "PT-1004",
    age: 72,
    language: "English",
    preTestScore: 1,
    postTestScore: 4,
    completionStatus: "In Progress",
    weakTopics: ["exercise", "diet and protein", "CLD basics"],
    answerSummary: {
      correctPre: 1,
      correctPost: 4,
      wrongPreTopics: ["CLD basics", "sarcopenia basics", "diet and protein", "exercise", "safety"],
      wrongPostTopics: ["diet and protein", "exercise", "safety"],
    },
    courseCompletionStatus: "Post-test submitted, optional support pending",
    learningNotes:
      "Older patient; responded better to slower pace and safety-first examples. Needs additional exercise counseling.",
  },
  {
    patientId: "PT-1005",
    age: 55,
    language: "Marathi",
    preTestScore: 4,
    postTestScore: 4,
    completionStatus: "In Progress",
    weakTopics: ["sarcopenia basics", "diet and protein"],
    answerSummary: {
      correctPre: 4,
      correctPost: 4,
      wrongPreTopics: ["sarcopenia basics", "diet and protein", "exercise"],
      wrongPostTopics: ["sarcopenia basics", "diet and protein", "exercise"],
    },
    courseCompletionStatus: "Learning completed, needs retest guidance",
    learningNotes:
      "No score change after first cycle. Recommend revisiting sarcopenia basics and protein meal examples.",
  },
  {
    patientId: "PT-1006",
    age: 61,
    language: "English",
    preTestScore: 6,
    postTestScore: 8,
    completionStatus: "Completed",
    weakTopics: ["exercise"],
    answerSummary: {
      correctPre: 6,
      correctPost: 8,
      wrongPreTopics: ["exercise", "safety"],
      wrongPostTopics: [],
    },
    courseCompletionStatus: "Completed full learning flow",
    learningNotes:
      "Strong final performance. Exercise and safety questions resolved after focused coaching.",
  },
];

export function getImprovement(patient) {
  return patient.postTestScore - patient.preTestScore;
}
