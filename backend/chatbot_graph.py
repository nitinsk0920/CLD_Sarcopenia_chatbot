from __future__ import annotations

import re
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from services.gemini_service import GeminiService
from services.language_utils import language_name, resolve_response_language
from services.rag_service import FaissKnowledgeService
from services.session_memory import build_memory_entry, roll_recent_messages


TOPIC_PRIORITY = ["diet", "exercise", "cld", "sarcopenia", "safety"]
TOPIC_LABELS = {
    "cld": "CLD basics",
    "sarcopenia": "sarcopenia basics",
    "diet": "diet and protein",
    "exercise": "exercise",
    "safety": "safety",
}
TOPIC_KEYWORDS = {
    "cld": ["cld", "liver", "chronic liver", "cirrhosis"],
    "sarcopenia": ["sarcopenia", "muscle loss", "muscle weakness", "weak muscles"],
    "diet": ["diet", "protein", "protien", "food", "eggs", "egg", "dal", "meal", "eat"],
    "exercise": ["exercise", "walking", "walk", "activity", "stretching", "strength"],
    "safety": ["dizzy", "dizziness", "unsafe", "warning", "weak", "fatigue"],
}
SERIOUS_SYMPTOM_KEYWORDS = [
    "severe pain",
    "faint",
    "passing out",
    "black stool",
    "vomiting blood",
    "confusion",
    "very dizzy",
    "cannot stand",
    "trouble breathing",
]

HEALTHCARE_SYSTEM_PROMPT = """
You are a calm hospital patient education assistant for Chronic Liver Disease (CLD) and sarcopenia.
Your role is education only.
Explain medical ideas in very simple, patient-friendly language.
Provide complete, patient-friendly responses in clear full sentences. Do not abruptly stop mid-response.
Be warm, brief, clear, and supportive.
Use the same language as the patient whenever possible.
Never diagnose a disease.
Never suggest starting, stopping, or changing medicines.
Never give unsafe or emergency treatment advice.
If the patient mentions serious symptoms, tell them to contact a nurse or doctor urgently.
If needed, include a short disclaimer that this is education only, not diagnosis.
Prefer short paragraphs or 3-5 bullets.
Only use the retrieved CLD, sarcopenia, diet, exercise, and safety knowledge plus safe general medical explanation.
"""


class ChatbotState(TypedDict, total=False):
    session_id: str
    patient_id: str
    user_question: str
    selected_language: str
    transcribed_language: str
    response_language: str
    patient_context: dict[str, Any]
    weak_topic_summary: dict[str, Any]
    session_summary: str
    recent_messages: list[dict[str, Any]]
    current_step: str
    input_analysis: dict[str, Any]
    primary_topic: str
    selected_topics: list[str]
    retrieval_result: dict[str, Any]
    llm_draft: str
    safety_result: dict[str, Any]
    final_response: str
    answer_id: str


def _normalize_text(text: str) -> str:
    lowered = (text or "").strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def _extract_topic_mentions(question: str) -> list[str]:
    question_norm = _normalize_text(question)
    found: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in question_norm for keyword in keywords):
            found.append(topic)
    return found


def _patient_habits(patient_context: dict[str, Any]) -> list[str]:
    raw = patient_context.get("habits") or []
    return [str(item).strip().lower() for item in raw if str(item).strip()]


def _patient_symptoms(patient_context: dict[str, Any]) -> list[str]:
    raw = patient_context.get("symptoms") or []
    return [str(item).strip() for item in raw if str(item).strip()]


def _patient_age(patient_context: dict[str, Any]) -> int | None:
    try:
        value = int(str(patient_context.get("age", "")).strip())
        return value if value > 0 else None
    except Exception:
        return None


def _string_or_default(value: Any, fallback: str = "Not shared") -> str:
    cleaned = str(value).strip()
    return cleaned or fallback


def _format_patient_context(patient_context: dict[str, Any]) -> str:
    habits = ", ".join(_patient_habits(patient_context)) or "none noted"
    symptoms = ", ".join(_patient_symptoms(patient_context)) or "none shared"
    return (
        f"Patient ID: {_string_or_default(patient_context.get('patientId'))}\n"
        f"Age: {_string_or_default(patient_context.get('age'))}\n"
        f"Gender: {_string_or_default(patient_context.get('gender'))}\n"
        f"CLD status: {_string_or_default(patient_context.get('cldStatus'))}\n"
        f"Diet type: {_string_or_default(patient_context.get('dietType'))}\n"
        f"Appetite: {_string_or_default(patient_context.get('appetiteLevel'))}\n"
        f"Protein awareness: {_string_or_default(patient_context.get('proteinAwareness'))}\n"
        f"Exercise habit: {_string_or_default(patient_context.get('exerciseRegular'))}\n"
        f"Exercise type: {_string_or_default(patient_context.get('exerciseType'))}\n"
        f"Exercise frequency: {_string_or_default(patient_context.get('exerciseFrequency'))}\n"
        f"Symptoms: {symptoms}\n"
        f"Habits: {habits}\n"
        f"Language preference: {_string_or_default(patient_context.get('languagePreference'), 'English')}"
    )


def _build_personalization_guidance(patient_context: dict[str, Any]) -> str:
    rules: list[str] = []
    diet_type = _normalize_text(str(patient_context.get("dietType", "")))
    habits = _patient_habits(patient_context)
    symptoms = [item.lower() for item in _patient_symptoms(patient_context)]
    age = _patient_age(patient_context)

    if diet_type == "vegetarian":
        rules.append(
            "When giving protein examples, prefer vegetarian foods like dal, paneer, milk, curd, soy, and legumes."
        )
    elif diet_type in {"non-vegetarian", "non vegetarian"}:
        rules.append(
            "When giving protein examples, you may mention eggs, chicken, fish, milk, curd, and legumes."
        )
    elif diet_type == "mixed":
        rules.append(
            "When giving food examples, include both vegetarian proteins and eggs/chicken/fish if suitable."
        )

    if age is not None and age >= 60:
        rules.append("Recommend only light, safe, gradual exercise and frequent rest breaks.")

    if "alcohol" in habits:
        rules.append("Gently warn that alcohol can worsen liver health and encourage avoiding it.")

    if "smoking" in habits or "tobacco" in habits:
        rules.append("Encourage healthier lifestyle choices without sounding judgmental.")

    if "dizziness" in symptoms or "low energy" in symptoms:
        rules.append("Add an extra short safety note about stopping activity and informing a nurse or doctor if weakness or dizziness increases.")

    if not rules:
        rules.append("Keep the guidance practical, local, culturally familiar, and easy to follow.")

    return "\n".join(f"- {rule}" for rule in rules)


def _format_weak_topics(weak_topic_summary: dict[str, Any]) -> str:
    ranked = weak_topic_summary.get("rankedWeakTopics", []) if weak_topic_summary else []
    if not ranked:
        return "No major weak topics recorded yet."
    parts: list[str] = []
    for item in ranked[:4]:
        topic = item.get("topic", "")
        label = item.get("label") or TOPIC_LABELS.get(topic, topic)
        mistakes = item.get("mistakes", 0)
        parts.append(f"{label} ({mistakes} mistakes)")
    return ", ".join(parts)


def _format_recent_messages(messages: list[dict[str, Any]] | None) -> str:
    recent = messages or []
    if not recent:
        return "No recent questions yet."
    lines: list[str] = []
    for item in recent[-3:]:
        topic = item.get("topic") or "general"
        question = item.get("question") or ""
        answer = item.get("answer") or ""
        lines.append(f"- Topic {topic}: Q={question} | A={answer}")
    return "\n".join(lines)


def _serious_symptom_flag(question: str) -> bool:
    question_norm = _normalize_text(question)
    return any(keyword in question_norm for keyword in SERIOUS_SYMPTOM_KEYWORDS)


class HealthcareEducationChatbot:
    def __init__(self, *, rag_service: FaissKnowledgeService, gemini_service: GeminiService, checkpointer: Any):
        self.rag_service = rag_service
        self.gemini_service = gemini_service
        self.graph = self._build_graph(checkpointer)

    def _build_graph(self, checkpointer: Any):
        graph = StateGraph(ChatbotState)
        graph.add_node("input_analysis", self.input_analysis_node)
        graph.add_node("weak_topic_selection", self.weak_topic_selection_node)
        graph.add_node("retrieval", self.retrieval_node)
        graph.add_node("llm_generation", self.llm_answer_generation_node)
        graph.add_node("safety_check", self.safety_check_node)
        graph.add_node("memory_update", self.memory_update_node)
        graph.add_node("final_formatting", self.final_response_formatting_node)

        graph.add_edge(START, "input_analysis")
        graph.add_edge("input_analysis", "weak_topic_selection")
        graph.add_edge("weak_topic_selection", "retrieval")
        graph.add_edge("retrieval", "llm_generation")
        graph.add_edge("llm_generation", "safety_check")
        graph.add_edge("safety_check", "memory_update")
        graph.add_edge("memory_update", "final_formatting")
        graph.add_edge("final_formatting", END)
        return graph.compile(checkpointer=checkpointer)

    def input_analysis_node(self, state: ChatbotState) -> dict[str, Any]:
        patient_context = state.get("patient_context", {})
        response_language = resolve_response_language(
            state.get("user_question", ""),
            selected_language=state.get("selected_language"),
            patient_language=patient_context.get("languagePreference"),
            transcribed_language=state.get("transcribed_language"),
        )
        topic_mentions = _extract_topic_mentions(state.get("user_question", ""))
        return {
            "response_language": response_language,
            "current_step": "input_analysis",
            "input_analysis": {
                "topic_mentions": topic_mentions,
                "serious_symptom_flag": _serious_symptom_flag(state.get("user_question", "")),
                "is_general_question": len(topic_mentions) == 0,
            },
        }

    def weak_topic_selection_node(self, state: ChatbotState) -> dict[str, Any]:
        analysis = state.get("input_analysis", {})
        mentioned_topics = analysis.get("topic_mentions", [])
        weak_summary = state.get("weak_topic_summary", {})
        ranked = weak_summary.get("rankedWeakTopics", []) if weak_summary else []

        weak_topics = [item.get("topic") for item in ranked if item.get("topic")]
        selected: list[str] = []

        for topic in mentioned_topics:
            if topic in TOPIC_PRIORITY and topic not in selected:
                selected.append(topic)

        if analysis.get("is_general_question", True):
            for basics in ["cld", "sarcopenia"]:
                if basics in weak_topics and basics not in selected:
                    selected.append(basics)

        for topic in weak_topics:
            if topic in TOPIC_PRIORITY and topic not in selected:
                selected.append(topic)

        for topic in TOPIC_PRIORITY:
            if topic not in selected:
                selected.append(topic)

        primary_topic = selected[0] if selected else "cld"
        return {
            "current_step": "weak_topic_selection",
            "selected_topics": selected[:3],
            "primary_topic": primary_topic,
        }

    def retrieval_node(self, state: ChatbotState) -> dict[str, Any]:
        question = state.get("user_question", "").strip() or "Please explain the next topic."
        selected_topics = state.get("selected_topics", [])
        retrieval_result = self.rag_service.search(
            question=question,
            preferred_topics=selected_topics[:2],
            top_k=3,
        )
        return {
            "current_step": "retrieval",
            "retrieval_result": retrieval_result,
        }

    def _build_prompt(self, state: ChatbotState) -> str:
        question = state.get("user_question", "").strip() or "Please explain the next teaching point."
        patient_context = state.get("patient_context", {})
        retrieval_result = state.get("retrieval_result", {})
        faq = retrieval_result.get("faq_first_match")
        chunks = retrieval_result.get("retrieved_chunks", [])
        selected_topics = state.get("selected_topics", [])
        language_code = state.get("response_language", "en")

        retrieved_lines: list[str] = []
        if faq:
            retrieved_lines.append(
                f"FAQ priority match: Q={faq.get('question', '')} | A={faq.get('answer', '')}"
            )
        for item in chunks:
            retrieved_lines.append(
                f"[{item.get('topic', 'general')}] {item.get('content', '')}"
            )

        focus_labels = ", ".join(TOPIC_LABELS.get(topic, topic) for topic in selected_topics) or "general education"
        recent_memory = _format_recent_messages(state.get("recent_messages"))
        session_summary = state.get("session_summary") or "No summary yet."

        return (
            f"Answer language: {language_name(language_code)} ({language_code})\n\n"
            "PATIENT PROFILE\n"
            f"{_format_patient_context(patient_context)}\n\n"
            "PERSONALIZATION RULES\n"
            f"{_build_personalization_guidance(patient_context)}\n\n"
            "WEAK TOPIC SUMMARY\n"
            f"{_format_weak_topics(state.get('weak_topic_summary', {}))}\n"
            f"Current focus topics: {focus_labels}\n\n"
            "SESSION MEMORY SUMMARY\n"
            f"{session_summary}\n\n"
            "RECENT MESSAGES\n"
            f"{recent_memory}\n\n"
            "RETRIEVED KNOWLEDGE\n"
            f"{chr(10).join(retrieved_lines) or 'No retrieved context found.'}\n\n"
            "PATIENT QUESTION\n"
            f"{question}\n\n"
            "INSTRUCTIONS\n"
            "- Start with a direct answer to the patient's question.\n"
            "- Keep the answer brief, complete, and easy to understand.\n"
            "- Use short sentences and patient-friendly wording.\n"
            "- Finish the answer in full sentences and do not end mid-thought.\n"
            "- If the patient asks about diet, mention safe protein guidance relevant to their diet type.\n"
            "- If the patient asks about exercise, keep it safe and gradual, especially for older adults.\n"
            "- If serious symptoms are mentioned, say to contact a nurse or doctor urgently.\n"
            "- Do not add medicine advice.\n"
            "- Avoid greetings unless the patient greeted first.\n"
        )

    def llm_answer_generation_node(self, state: ChatbotState) -> dict[str, Any]:
        prompt = self._build_prompt(state)
        language_code = state.get("response_language", "en")
        answer = self.gemini_service.generate_answer(
            prompt=prompt,
            system_instruction=HEALTHCARE_SYSTEM_PROMPT,
            language_code=language_code,
        )
        return {
            "current_step": "llm_generation",
            "llm_draft": answer,
        }

    def safety_check_node(self, state: ChatbotState) -> dict[str, Any]:
        draft = " ".join((state.get("llm_draft") or "").split())
        question_norm = _normalize_text(state.get("user_question", ""))
        flagged = any(
            pattern in _normalize_text(draft)
            for pattern in [
                "stop your medicine",
                "change your medicine",
                "increase your dose",
                "decrease your dose",
                "you have cirrhosis",
                "i diagnose",
            ]
        )
        needs_disclaimer = flagged or _serious_symptom_flag(question_norm)

        safe_answer = re.sub(
            r"(?i)\b(start|stop|increase|decrease|change)\b[^.]*\.",
            "",
            draft,
        ).strip()
        if needs_disclaimer:
            if _serious_symptom_flag(question_norm):
                safe_answer = (
                    f"{safe_answer}\n\n"
                    "If your symptoms feel severe, sudden, or unsafe, please contact your nurse or doctor urgently."
                ).strip()
            else:
                safe_answer = (
                    f"{safe_answer}\n\n"
                    "This chatbot is for education only. Please ask your nurse or doctor for diagnosis or treatment decisions."
                ).strip()

        return {
            "current_step": "safety_check",
            "safety_result": {
                "flagged": flagged,
                "serious_symptom_flag": _serious_symptom_flag(question_norm),
                "safe_answer": safe_answer or draft,
            },
        }

    def memory_update_node(self, state: ChatbotState) -> dict[str, Any]:
        answer = state.get("safety_result", {}).get("safe_answer", "").strip()
        recent_messages, session_summary = roll_recent_messages(
            previous_messages=state.get("recent_messages"),
            new_entry=build_memory_entry(
                question=state.get("user_question", ""),
                answer=answer,
                language=state.get("response_language", "en"),
                primary_topic=state.get("primary_topic", ""),
            ),
            previous_summary=state.get("session_summary", ""),
        )
        return {
            "current_step": "memory_update",
            "recent_messages": recent_messages,
            "session_summary": session_summary,
        }

    def final_response_formatting_node(self, state: ChatbotState) -> dict[str, Any]:
        answer = state.get("safety_result", {}).get("safe_answer", "") or state.get("llm_draft", "")
        cleaned = " ".join((answer or "").split())
        cleaned = re.sub(r"(?i)^(hello|hi|hey|namaste)[!,.:\-\s]+", "", cleaned).strip()
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        seen: set[str] = set()
        deduped: list[str] = []
        for sentence in sentences:
            normalized = _normalize_text(sentence)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(sentence.strip())
        final_answer = " ".join(deduped).strip()
        return {
            "current_step": "completed",
            "final_response": final_answer,
            "answer_id": str(uuid4()),
        }

    def chat(
        self,
        *,
        session_id: str,
        user_question: str,
        patient_context: dict[str, Any] | None = None,
        weak_topic_summary: dict[str, Any] | None = None,
        selected_language: str | None = None,
        transcribed_language: str | None = None,
    ) -> dict[str, Any]:
        state: ChatbotState = {
            "session_id": session_id,
            "patient_id": str((patient_context or {}).get("patientId", "")).strip(),
            "user_question": user_question or "",
            "selected_language": selected_language or "",
            "transcribed_language": transcribed_language or "",
            "patient_context": patient_context or {},
            "weak_topic_summary": weak_topic_summary or {},
        }
        config = {"configurable": {"thread_id": session_id}}
        result = self.graph.invoke(state, config=config)
        retrieval = result.get("retrieval_result", {})
        return {
            "session_id": session_id,
            "answer_id": result.get("answer_id", str(uuid4())),
            "answer": result.get("final_response", ""),
            "selected_topics": result.get("selected_topics", []),
            "response_language": result.get("response_language", "en"),
            "faq_first_match": retrieval.get("faq_first_match"),
            "retrieved_chunks": retrieval.get("retrieved_chunks", []),
            "safety": result.get("safety_result", {}),
            "session_summary": result.get("session_summary", ""),
        }
