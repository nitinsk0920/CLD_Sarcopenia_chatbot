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

    if re.search(r"[\u0C80-\u0CFF]", sample):
        return "kn"

    if re.search(r"[\u0900-\u097F]", sample):
        marathi_tokens = {
            "आहे",
            "आहेत",
            "माझे",
            "मला",
            "काय",
            "होते",
            "करावे",
            "सुरक्षित",
            "व्यायाम",
            "आहार",
        }
        hindi_tokens = {
            "है",
            "हैं",
            "क्या",
            "मुझे",
            "कैसे",
            "क्यों",
            "व्यायाम",
            "सुरक्षित",
            "आहार",
        }
        token_set = set(re.findall(r"[\u0900-\u097F]+", sample))
        if token_set & marathi_tokens:
            return "mr"
        if token_set & hindi_tokens:
            return "hi"

    return None


def resolve_response_language(
    text: str,
    selected_language: str | None = None,
    patient_language: str | None = None,
    transcribed_language: str | None = None,
) -> str:
    detected = normalize_language_code(transcribed_language, fallback="") if transcribed_language else ""
    if detected:
        return detected

    requested_language = _explicit_response_language_request(text)
    if requested_language:
        return requested_language

    text_detected = detect_language_from_text(text)
    if text_detected:
        return text_detected

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
        ("hi", r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+hindi\b|हिंदी में (?:बताएं|जवाब|समझाएं)"),
        ("kn", r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+kannada\b|ಕನ್ನಡದಲ್ಲಿ (?:ಹೇಳಿ|ಉತ್ತರಿಸಿ|ವಿವರಿಸಿ)"),
        ("mr", r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+marathi\b|मराठीत (?:सांगा|उत्तर|समजावून)"),
        ("en", r"\b(?:answer|reply|respond|explain|write)\s+(?:in|using)\s+english\b|इंग्रजीत (?:सांगा|उत्तर)"),
    )
    return next((code for code, pattern in patterns if re.search(pattern, normalized)), None)
