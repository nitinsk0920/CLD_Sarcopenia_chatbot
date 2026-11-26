from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from chatbot_graph import HealthcareEducationChatbot
from services.language_utils import resolve_response_language


@pytest.mark.parametrize(
    ("question", "selected", "transcribed", "expected"),
    [
        ("What is CLD?", "hi", "", "hi"),
        ("मुझे कमजोरी क्यों महसूस हो रही है?", "en", "", "hi"),
        ("मला थकवा का जाणवतो?", "kn", "", "mr"),
        ("ವ್ಯಾಯಾಮ ನನಗೆ ಸುರಕ್ಷಿತವೇ?", "mr", "", "kn"),
        ("CLD means? Answer in Hindi", "kn", "kn", "hi"),
        ("What is sarcopenia? Answer in English", "hi", "mr", "en"),
        ("What is sarcopenia? ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.", "en", "en", "kn"),
        ("मुझे कमजोरी क्यों महसूस होती है? मराठीमध्ये उत्तर द्या.", "en", "hi", "mr"),
        ("What is CLD? Hindi mein jawab do", "kn", "kn", "hi"),
        ("ಸಾರ್ಕೋಪೀನಿಯಾ ಎಂದರೇನು? Answer in English.", "kn", "kn", "en"),
        ("What is CLD?", "hi", "en", "hi"),
        ("CLD means?", "", "", "en"),
    ],
)
def test_response_language_priority_for_each_message(question, selected, transcribed, expected):
    assert resolve_response_language(
        question,
        selected_language=selected,
        transcribed_language=transcribed,
    ) == expected


class _Rag:
    def search(self, *, question, **_kwargs):
        return {
            "retrieved_chunks": [{
                "topic": "cld",
                "semantic_score": 0.9,
                "overlap_score": 0.5,
                "content": "Chronic liver disease is a long-term condition that can damage the liver.",
            }]
        }


class _Gemini:
    def __init__(self):
        self.calls = []

    def generate_answer(self, *, prompt, language_code, **_kwargs):
        self.calls.append((language_code, prompt))
        return {
            "en": "Chronic liver disease is a long-term condition that can damage the liver.",
            "hi": "यकृत का दीर्घकालिक रोग समय के साथ नुकसान कर सकता है।",
            "kn": "ಯಕೃತ್ತಿನ ದೀರ್ಘಕಾಲದ ಕಾಯಿಲೆ ಕಾಲಕ್ರಮೇಣ ಹಾನಿ ಮಾಡಬಹುದು.",
            "mr": "यकृताचा दीर्घकालीन आजार कालांतराने नुकसान करू शकतो.",
        }[language_code]


def _chatbot():
    gemini = _Gemini()
    return HealthcareEducationChatbot(
        rag_service=_Rag(),
        gemini_service=gemini,
        checkpointer=InMemorySaver(),
    ), gemini


def test_same_session_language_sequence_is_resolved_independently_per_turn():
    chatbot, gemini = _chatbot()
    turns = [
        ("मला थकवा का जाणवतो?", "en", "mr"),
        ("मुझे कमजोरी क्यों महसूस हो रही है?", "mr", "hi"),
        ("ವ್ಯಾಯಾಮ ನನಗೆ ಸುರಕ್ಷಿತವೇ?", "mr", "kn"),
        ("What is CLD?", "en", "en"),
    ]

    results = [
        chatbot.chat(
            session_id="language-sequence",
            user_question=question,
            selected_language=selected,
        )
        for question, selected, _expected in turns
    ]

    expected = [language for _question, _selected, language in turns]
    assert [result["response_language"] for result in results] == expected
    assert [language for language, _prompt in gemini.calls] == expected
    for (language, prompt) in gemini.calls:
        assert f"Write the complete answer in { {'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada', 'mr': 'Marathi'}[language] } ({language})" in prompt
        assert "never copy their response language" in prompt


def test_concurrent_sessions_keep_their_selected_language_isolated():
    chatbot, gemini = _chatbot()
    requests = [
        ("patient-hindi", "hi"),
        ("patient-kannada", "kn"),
        ("patient-marathi", "mr"),
        ("patient-english", "en"),
    ]

    def ask(item):
        session_id, selected = item
        result = chatbot.chat(
            session_id=session_id,
            user_question="What is CLD?",
            selected_language=selected,
        )
        return session_id, selected, result["response_language"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(ask, requests))

    assert {(selected, resolved) for _session, selected, resolved in results} == {
        ("hi", "hi"), ("kn", "kn"), ("mr", "mr"), ("en", "en")
    }
    assert sorted(language for language, _prompt in gemini.calls) == ["en", "hi", "kn", "mr"]
