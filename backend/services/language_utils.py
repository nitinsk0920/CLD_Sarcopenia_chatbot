from __future__ import annotations

import re


SUPPORTED_LANGUAGE_CODES = ("en", "hi", "kn", "mr")
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "mr": "Marathi",
}
LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "hindi": "hi",
    "hi": "hi",
    "marathi": "mr",
    "mr": "mr",
    "kannada": "kn",
    "kn": "kn",
}


def normalize_language_code(value: str | None, fallback: str = "en") -> str:
    if not value:
        return fallback
    normalized = str(value).strip().lower()
    return LANGUAGE_ALIASES.get(normalized, fallback)


def language_name(code: str | None) -> str:
    return LANGUAGE_NAMES.get(normalize_language_code(code), "English")


def detect_language_from_text(text: str) -> str | None:
    sample = (text or "").strip()
    if not sample:
        return None

    kannada_tokens = re.findall(r"[\u0C80-\u0CFF]+", sample)
    latin_tokens = re.findall(r"[a-zA-Z]+", sample)
    if len(kannada_tokens) >= 2 and len(kannada_tokens) * 2 >= len(latin_tokens):
        return "kn"

    if re.search(r"[\u0900-\u097F]", sample):
        marathi_tokens = {
            "आहे",
            "आहेत",
            "मला",
            "माझे",
            "माझा",
            "माझी",
            "माझ्या",
            "काय",
            "होते",
            "जाणवते",
            "जाणवतो",
            "जाणवतात",
            "अशक्तपणा",
            "थकवा",
            "स्नायू",
            "कशी",
            "कसे",
        }
        hindi_tokens = {
            "है",
            "हैं",
            "क्या",
            "मुझे",
            "मेरा",
            "मेरी",
            "मेरे",
            "कैसे",
            "क्यों",
            "महसूस",
            "होती",
            "होता",
            "करना",
            "खाना",
            "सकता",
            "सकती",
            "बताएं",
            "बताइए",
        }
        token_set = set(re.findall(r"[\u0900-\u097F]+", sample))
        marathi_score = len(token_set & marathi_tokens)
        hindi_score = len(token_set & hindi_tokens)
        if marathi_score > hindi_score and marathi_score > 0:
            return "mr"
        if hindi_score > marathi_score and hindi_score > 0:
            return "hi"

    return None


def resolve_response_language(
    text: str,
    selected_language: str | None = None,
    patient_language: str | None = None,
    transcribed_language: str | None = None,
) -> str:
    requested_language = _explicit_response_language_request(text)
    if requested_language:
        return requested_language

    text_detected = detect_language_from_text(text)
    if text_detected:
        return text_detected

    # Transcription metadata describes this turn; it is not a language
    # preference that can override a current-message decision.
    transcribed = (
        normalize_language_code(transcribed_language, fallback="")
        if transcribed_language
        else ""
    )
    if transcribed in {"hi", "kn", "mr"}:
        return transcribed

    selected = normalize_language_code(selected_language, fallback="") if selected_language else ""
    if selected:
        return selected

    preferred = normalize_language_code(patient_language, fallback="") if patient_language else ""
    if preferred:
        return preferred

    return "en"


def _explicit_response_language_request(text: str) -> str | None:
    normalized = (text or "").casefold()
    patterns = (
        (
            "hi",
            r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+hindi\b"
            r"|\b(?:hindi|हिंदी)\s+(?:me|mein|में)\s+(?:answer|reply|jawab|जवाब|उत्तर|बताओ|बताएं|समझाओ|समझाएं)"
            r"|हिंदी\s+में\s+(?:बताएं|बताइए|जवाब(?:\s+दें)?|उत्तर(?:\s+दें)?|समझाएं|समझाइए)",
        ),
        (
            "kn",
            r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+kannada\b"
            r"|\bkannada\s+(?:dalli|alli)\s+(?:answer|reply|heli|uttarisi|vivarisi)"
            r"|ಕನ್ನಡದಲ್ಲಿ\s*(?:ಹೇಳಿ|ಉತ್ತರಿಸಿ|ವಿವರಿಸಿ|ಉತ್ತರ\s*ಕೊಡಿ)",
        ),
        (
            "mr",
            r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+marathi\b"
            r"|\bmarathi\s+(?:madhe|madhye)\s+(?:answer|reply|sanga|uttar|samjava)"
            r"|मराठी(?:मध्ये|त)\s*(?:सांगा|उत्तर(?:\s+द्या)?|समजावून\s+सांगा)",
        ),
        (
            "en",
            r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+english\b"
            r"|\benglish\s+(?:madhe|madhye|me|mein)\s+(?:answer|reply|sanga|uttar)"
            r"|इंग्रजी(?:त|मध्ये)\s*(?:सांगा|उत्तर(?:\s+द्या)?)"
            r"|ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ\s*(?:ಹೇಳಿ|ಉತ್ತರಿಸಿ|ವಿವರಿಸಿ)",
        ),
    )
    return next((code for code, pattern in patterns if re.search(pattern, normalized)), None)
