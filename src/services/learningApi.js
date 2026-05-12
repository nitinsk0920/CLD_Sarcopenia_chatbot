import { apiFetch } from "./apiClient";

export function fetchLearningTopicMedia(topicId) {
  return apiFetch(`/learning/topics/${topicId}`, {
    fallbackMessage: "Could not load learning media.",
  });
}
