from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass

from services.language_utils import normalize_language_code


DEFAULT_MAX_INPUT_CHARS = 2000

MESSAGES = {
    "en": {
        "empty": "Please enter a question about CLD, sarcopenia, nutrition, exercise, or patient education.",
        "too_long": "Please shorten your question and try again.",
        "injection": "I can help with patient education about CLD, sarcopenia, nutrition, exercise, and safety. I can’t change my safety instructions.",
        "scope": "I can help with patient education about CLD, sarcopenia, nutrition, exercise, and related safety topics. Please ask a question in one of these areas.",
        "clinician": "This is a patient-specific medical question. Please discuss it with your doctor or nurse, who can review your individual situation.",
        "medication_safety": "I can’t recommend medicines, doses, or changes to your treatment. Please check with your doctor or pharmacist before starting, stopping, or changing any medicine.",
        "urgent": "Your message matches a symptom phrase configured for urgent escalation. Please contact your hospital care team now or follow your hospital's approved emergency process.",
        "no_evidence": "The available educational material does not provide enough information to answer reliably. Please ask your doctor or nurse.",
        "food_no_evidence": "The educational material does not provide specific information about this food. Please ask your doctor or dietitian whether it is suitable for your individual needs.",
        "exercise_no_evidence": "The educational material cannot determine whether exercise is safe for you personally. Please ask your doctor or nurse before starting or changing an exercise routine.",
        "symptom_no_evidence": "I cannot determine the personal cause of this symptom from chat. The available educational material does not provide enough information; please discuss it with your doctor or nurse.",
        "conflict": "The available education materials contain conflicting information on this point. Please ask your doctor or nurse to verify it.",
        "unsafe_output": "I can provide general education, but I can’t diagnose or recommend individual treatment. Please discuss this question with your doctor or nurse.",
        "service_unavailable": "I couldn't prepare a complete answer just now. Please try again shortly.",
    },
    "hi": {
        "empty": "कृपया CLD, सार्कोपीनिया, पोषण, व्यायाम या रोगी शिक्षा से जुड़ा प्रश्न लिखें।",
        "too_long": "कृपया अपना प्रश्न छोटा करके फिर से भेजें।",
        "injection": "मैं CLD, सार्कोपीनिया, पोषण, व्यायाम और सुरक्षा के बारे में रोगी शिक्षा दे सकता हूँ। मैं अपने सुरक्षा निर्देश नहीं बदल सकता।",
        "scope": "मैं CLD, सार्कोपीनिया, पोषण, व्यायाम और संबंधित सुरक्षा विषयों पर रोगी शिक्षा दे सकता हूँ। कृपया इन्हीं विषयों में प्रश्न पूछें।",
        "clinician": "यह आपके लिए विशेष चिकित्सा प्रश्न है। अपनी स्थिति की समीक्षा के लिए कृपया डॉक्टर या नर्स से बात करें।",
        "medication_safety": "मैं दवा, उसकी खुराक या उपचार में बदलाव की सलाह नहीं दे सकता। कोई दवा शुरू, बंद या बदलने से पहले कृपया डॉक्टर या फार्मासिस्ट से पूछें।",
        "urgent": "आपके संदेश में अस्पताल द्वारा तत्काल ध्यान के लिए निर्धारित लक्षण-वाक्यांश है। कृपया अभी अपनी अस्पताल देखभाल टीम से संपर्क करें या अस्पताल की स्वीकृत आपातकालीन प्रक्रिया अपनाएँ।",
        "no_evidence": "उपलब्ध शैक्षिक सामग्री में विश्वसनीय उत्तर देने के लिए पर्याप्त जानकारी नहीं है। कृपया डॉक्टर या नर्स से पूछें।",
        "food_no_evidence": "शैक्षिक सामग्री में इस खाद्य पदार्थ के बारे में विशेष जानकारी नहीं है। कृपया अपनी व्यक्तिगत जरूरतों के अनुसार इसकी उपयुक्तता डॉक्टर या आहार विशेषज्ञ से पूछें।",
        "exercise_no_evidence": "शैक्षिक सामग्री यह तय नहीं कर सकती कि व्यायाम आपके लिए व्यक्तिगत रूप से सुरक्षित है या नहीं। व्यायाम शुरू करने या बदलने से पहले डॉक्टर या नर्स से पूछें।",
        "symptom_no_evidence": "मैं चैट से इस लक्षण का व्यक्तिगत कारण निर्धारित नहीं कर सकता। उपलब्ध शैक्षिक सामग्री में पर्याप्त जानकारी नहीं है; कृपया डॉक्टर या नर्स से चर्चा करें।",
        "conflict": "उपलब्ध शैक्षिक सामग्री में इस विषय पर विरोधाभासी जानकारी है। कृपया डॉक्टर या नर्स से इसकी पुष्टि करें।",
        "unsafe_output": "मैं सामान्य जानकारी दे सकता हूँ, लेकिन निदान या व्यक्तिगत उपचार की सलाह नहीं दे सकता। कृपया डॉक्टर या नर्स से चर्चा करें।",
        "service_unavailable": "अभी पूरा उत्तर तैयार नहीं हो पाया। कृपया थोड़ी देर बाद फिर से पूछें।",
    },
    "kn": {
        "empty": "ದಯವಿಟ್ಟು CLD, ಸಾರ್ಕೋಪೀನಿಯಾ, ಪೋಷಣೆ, ವ್ಯಾಯಾಮ ಅಥವಾ ರೋಗಿ ಶಿಕ್ಷಣದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
        "too_long": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಚಿಕ್ಕದಾಗಿ ಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "injection": "CLD, ಸಾರ್ಕೋಪೀನಿಯಾ, ಪೋಷಣೆ, ವ್ಯಾಯಾಮ ಮತ್ತು ಸುರಕ್ಷತೆ ಕುರಿತು ರೋಗಿ ಶಿಕ್ಷಣದಲ್ಲಿ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ನನ್ನ ಸುರಕ್ಷತಾ ಸೂಚನೆಗಳನ್ನು ಬದಲಾಯಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "scope": "CLD, ಸಾರ್ಕೋಪೀನಿಯಾ, ಪೋಷಣೆ, ವ್ಯಾಯಾಮ ಮತ್ತು ಸಂಬಂಧಿತ ಸುರಕ್ಷತೆ ಕುರಿತು ಶಿಕ್ಷಣ ನೀಡಬಹುದು. ದಯವಿಟ್ಟು ಇವುಗಳಲ್ಲಿ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
        "clinician": "ಇದು ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ವೈದ್ಯಕೀಯ ಪ್ರಶ್ನೆಯಾಗಿದೆ. ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ದಯವಿಟ್ಟು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಜೊತೆ ಮಾತನಾಡಿ.",
        "medication_safety": "ಯಾವುದೇ ಔಷಧಿ ಅಥವಾ ಅದರ ಪ್ರಮಾಣವನ್ನು ಶಿಫಾರಸು ಮಾಡಲು ಅಥವಾ ಚಿಕಿತ್ಸೆಯಲ್ಲಿ ಬದಲಾವಣೆ ಹೇಳಲು ಸಾಧ್ಯವಿಲ್ಲ. ಔಷಧಿ ಆರಂಭಿಸುವ, ನಿಲ್ಲಿಸುವ ಅಥವಾ ಬದಲಿಸುವ ಮೊದಲು ವೈದ್ಯರು ಅಥವಾ ಔಷಧ ತಜ್ಞರನ್ನು ಕೇಳಿ.",
        "urgent": "ನಿಮ್ಮ ಸಂದೇಶದಲ್ಲಿ ಆಸ್ಪತ್ರೆ ತುರ್ತು ಗಮನಕ್ಕಾಗಿ ಸಂರಚಿಸಿದ ಲಕ್ಷಣದ ಪದಗುಚ್ಛವಿದೆ. ದಯವಿಟ್ಟು ಈಗಲೇ ನಿಮ್ಮ ಆರೈಕೆ ತಂಡವನ್ನು ಸಂಪರ್ಕಿಸಿ ಅಥವಾ ಆಸ್ಪತ್ರೆಯ ಅನುಮೋದಿತ ತುರ್ತು ಕ್ರಮ ಅನುಸರಿಸಿ.",
        "no_evidence": "ಲಭ್ಯವಿರುವ ಶಿಕ್ಷಣ ಮಾಹಿತಿಯಲ್ಲಿ ವಿಶ್ವಾಸಾರ್ಹ ಉತ್ತರ ನೀಡಲು ಸಾಕಷ್ಟು ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಅವರನ್ನು ಕೇಳಿ.",
        "food_no_evidence": "ಈ ಆಹಾರದ ಬಗ್ಗೆ ಶಿಕ್ಷಣ ಮಾಹಿತಿಯಲ್ಲಿ ನಿರ್ದಿಷ್ಟ ಮಾಹಿತಿ ಇಲ್ಲ. ಇದು ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಅಗತ್ಯಗಳಿಗೆ ಸೂಕ್ತವೇ ಎಂದು ವೈದ್ಯರು ಅಥವಾ ಆಹಾರ ತಜ್ಞರನ್ನು ಕೇಳಿ.",
        "exercise_no_evidence": "ವ್ಯಾಯಾಮ ನಿಮಗೆ ವೈಯಕ್ತಿಕವಾಗಿ ಸುರಕ್ಷಿತವೇ ಎಂದು ಶಿಕ್ಷಣ ಮಾಹಿತಿಯಿಂದ ನಿರ್ಧರಿಸಲಾಗುವುದಿಲ್ಲ. ವ್ಯಾಯಾಮ ಆರಂಭಿಸುವ ಅಥವಾ ಬದಲಾಯಿಸುವ ಮೊದಲು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಅವರನ್ನು ಕೇಳಿ.",
        "symptom_no_evidence": "ಚಾಟ್ ಮೂಲಕ ಈ ಲಕ್ಷಣದ ವೈಯಕ್ತಿಕ ಕಾರಣವನ್ನು ನಿರ್ಧರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ. ಲಭ್ಯವಿರುವ ಶಿಕ್ಷಣ ಮಾಹಿತಿಯಲ್ಲಿ ಸಾಕಷ್ಟು ವಿವರಗಳಿಲ್ಲ; ದಯವಿಟ್ಟು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಜೊತೆ ಚರ್ಚಿಸಿ.",
        "conflict": "ಲಭ್ಯವಿರುವ ಶಿಕ್ಷಣ ಮಾಹಿತಿಯಲ್ಲಿ ಈ ವಿಷಯದ ಬಗ್ಗೆ ವಿರೋಧಾಭಾಸವಿದೆ. ದಯವಿಟ್ಟು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಮೂಲಕ ದೃಢಪಡಿಸಿಕೊಳ್ಳಿ.",
        "unsafe_output": "ಸಾಮಾನ್ಯ ಶಿಕ್ಷಣ ನೀಡಬಹುದು, ಆದರೆ ರೋಗನಿರ್ಣಯ ಅಥವಾ ವೈಯಕ್ತಿಕ ಚಿಕಿತ್ಸಾ ಸಲಹೆ ನೀಡಲು ಸಾಧ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್ ಜೊತೆ ಚರ್ಚಿಸಿ.",
        "service_unavailable": "ಈಗ ಸಂಪೂರ್ಣ ಉತ್ತರವನ್ನು ಸಿದ್ಧಪಡಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    },
    "mr": {
        "empty": "कृपया CLD, सार्कोपेनिया, पोषण, व्यायाम किंवा रुग्ण शिक्षणाबद्दल प्रश्न विचारा.",
        "too_long": "कृपया प्रश्न लहान करून पुन्हा प्रयत्न करा.",
        "injection": "मी CLD, सार्कोपेनिया, पोषण, व्यायाम आणि सुरक्षिततेबद्दल रुग्ण शिक्षण देऊ शकतो. मी माझ्या सुरक्षा सूचना बदलू शकत नाही.",
        "scope": "मी CLD, सार्कोपेनिया, पोषण, व्यायाम आणि संबंधित सुरक्षिततेबद्दल माहिती देऊ शकतो. कृपया यापैकी एखाद्या विषयावर विचारा.",
        "clinician": "हा तुमच्यासाठी वैयक्तिक वैद्यकीय प्रश्न आहे. तुमच्या परिस्थितीचे मूल्यांकन करण्यासाठी कृपया डॉक्टर किंवा नर्सशी बोला.",
        "medication_safety": "मी औषध, त्याचा डोस किंवा उपचारातील बदल सुचवू शकत नाही. कोणतेही औषध सुरू, बंद किंवा बदलण्यापूर्वी कृपया डॉक्टर किंवा फार्मासिस्टचा सल्ला घ्या.",
        "urgent": "तुमच्या संदेशात रुग्णालयाने तातडीच्या लक्ष्यासाठी निश्चित केलेला लक्षण-वाक्यांश आहे. कृपया आत्ताच उपचार पथकाशी संपर्क साधा किंवा रुग्णालयाची मंजूर आपत्कालीन प्रक्रिया पाळा.",
        "no_evidence": "उपलब्ध शैक्षणिक माहितीत विश्वासार्ह उत्तर देण्यासाठी पुरेशी माहिती नाही. कृपया डॉक्टर किंवा नर्सना विचारा.",
        "food_no_evidence": "या खाद्यपदार्थाबद्दल शैक्षणिक माहितीत विशिष्ट माहिती नाही. तो तुमच्या वैयक्तिक गरजांसाठी योग्य आहे का, हे डॉक्टर किंवा आहारतज्ज्ञांना विचारा.",
        "exercise_no_evidence": "व्यायाम तुमच्यासाठी वैयक्तिकरीत्या सुरक्षित आहे का, हे शैक्षणिक माहितीवरून ठरवता येत नाही. व्यायाम सुरू करण्यापूर्वी किंवा बदलण्यापूर्वी डॉक्टर किंवा नर्सना विचारा.",
        "symptom_no_evidence": "चॅटवरून या लक्षणाचे वैयक्तिक कारण ठरवता येत नाही. उपलब्ध शैक्षणिक माहितीत पुरेशी माहिती नाही; कृपया डॉक्टर किंवा नर्सशी चर्चा करा.",
        "conflict": "उपलब्ध शैक्षणिक माहितीत या मुद्द्यावर विसंगती आहे. कृपया डॉक्टर किंवा नर्सकडून याची खात्री करून घ्या.",
        "unsafe_output": "मी सामान्य माहिती देऊ शकतो, पण निदान किंवा वैयक्तिक उपचारांचा सल्ला देऊ शकत नाही. कृपया डॉक्टर किंवा नर्सशी चर्चा करा.",
        "service_unavailable": "आत्ता पूर्ण उत्तर तयार करता आले नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
    },
}

TOPIC_TERMS = {
    "cld": ("cld", "liver", "hepatic", "cirrhosis", "लिवर", "लिव्हर", "यकृत", "यकೃತ್ತ", "ಯಕೃತ್ತು", "ಯಕೃತ್ತಿನ", "ಯಕೃತ್ತಿನ ಕಾಯಿಲೆ", "ಲಿವರ್", "yakrutta", "yakruttina", "yakrut"),
    "sarcopenia": ("sarcopenia", "ಸಾರ್ಕೋಪೀನಿಯಾ", "muscle", "weakness", "weak", "tired", "fatigue", "कमजोरी", "थकान", "मांसपेश", "स्नायू", "थकवा", "ಸ್ನಾಯು", "ದೌರ್ಬಲ್ಯ", "ದಣಿವು", "ಅಶಕ್ತತೆ", "अशक्तपणा", "ಶಕ್ತಿ", "snayu", "manspeshi"),
    "nutrition": ("diet", "nutrition", "protein", "food", "meal", "eat", "egg", "eggs", "dal", "lentil", "lentils", "pulse", "pulses", "paneer", "yogurt", "milk", "fish", "chicken", "tofu", "अंडा", "अंडे", "दाल", "पनीर", "खाना", "खाद्य", "आहार", "पोषण", "प्रोटीन", "प्रथिने", "डाळ", "अंडी", "खाद्यपदार्थ", "ಪೋಷಣೆ", "ಆಹಾರ", "ಪ್ರೋಟೀನ್", "ಮೊಟ್ಟೆ", "ಬೇಳೆ", "ಹಾಲು", "ಪನೀರ್", "ahara", "poshana"),
    "exercise": ("exercise", "walking", "walk", "movement", "activity", "व्यायाम", "चालणे", "ವ್ಯಾಯಾಮ", "ಚಲನೆ", "ನಡೆಯುವುದು", "चालणे", "nadeyuvudu", "vyayama"),
    "safety": ("safety", "safe", "warning", "dizzy", "dizziness", "सुरक्षा", "चक्कर", "सुरक्षित", "ಎಚ್ಚರಿಕೆ", "ತಲೆಸುತ್ತು", "सुरक्षितता", "धोका", "इशारा", "ಎಚ್ಚರ", "ಚक्कर", "मार्गदर्शन", "सल्ला", "dizziness", "safety"),
    "patient_education": ("patient education", "health education", "रोगी शिक्षा", "ಆರೋಗ್ಯ ಶಿಕ್ಷಣ", "रुग्ण शिक्षण"),
}

INJECTION_PATTERNS = (
    r"ignore (all )?(previous|prior|above|system|developer) instructions",
    r"disregard (all )?(previous|prior|above|system) instructions",
    r"(reveal|show|print|repeat|泄露).{0,30}(system prompt|hidden prompt|instructions)",
    r"(override|bypass|disable|forget).{0,30}(safety|guardrails|instructions|rules)",
    r"act as (a |an )?(different|unrestricted|jailbroken)",
    r"developer mode|jailbreak|prompt injection",
    r"forget (all )?(your )?(rules|instructions|restrictions)|from now on.{0,50}(ignore|bypass|override)",
    r"पिछले निर्देशों को अनदेखा|पिछले निर्देश.*भूल|सुरक्षा निर्देश.*बदल|सभी.*नियम भूल|नियमों को भूल|निर्देशों को भूल|निर्देश.*भूल|प्रतिबंधों को हट",
    r"ಹಿಂದಿನ ಸೂಚನೆಗಳನ್ನು ನಿರ್ಲಕ್ಷಿಸಿ|ಹಿಂದಿನ ಸೂಚನೆ.*ಮರೆತು|ಸೂಚನೆ.*ಮರೆತು|ಸುರಕ್ಷತಾ ಸೂಚನೆ.*ಬದಲ|ಎಲ್ಲ ನಿಯಮಗಳನ್ನು ಮರೆತು|ನಿಯಮಗಳನ್ನು ಮರೆತು|ನಿರ್ಬಂಧಗಳನ್ನು ತೆಗೆ",
    r"मागील सूचनांकडे दुर्लक्ष|मागील सूचना.*विसर|सुरक्षा सूचना.*बदल|सर्व नियम विसर|नियम विसर|सूचना विसर|निर्बंध काढ",
)

GENERAL_EDUCATION_PATTERNS = (
    r"^(can i eat|may i eat)\b.*\b(egg|eggs|dal|lentils?|pulses?|paneer|yogurt|milk|fish|chicken|tofu)\??$",
    r"^(which foods? (contain|have|help)|what foods? help|why is protein important|what is a healthy diet for muscle strength)\b.*\??$",
    r"^(is exercise safe for me|can i safely exercise|which exercises? help|what exercises? help|why is walking important|how can i improve muscle strength)\b.*\??$",
    r"^what should i do (when|if) i feel (weak|dizzy) during exercise\??$",
    r"^what diet should i eat\??$",
    r"^why am i (feeling )?(weak|tired|fatigued)\??$",
    r"^why do i feel (weak|tired|fatigued)\??$",
    r"^why am i losing muscle\??$",
    r"^can cld affect my muscles\??$",
    r"^क्या मैं .* (अंडा|अंडे|दाल|पनीर|खाना) खा सकता.*$",
    r"^(क्या मेरे लिए व्यायाम सुरक्षित है|क्या व्यायाम मेरे लिए सुरक्षित है|मुझे कमजोरी क्यों महसूस हो रही है|मुझे थकान क्यों महसूस हो रही है|मेरी मांसपेशियां क्यों कम हो रही हैं|क्या cld मेरी मांसपेशियों को प्रभावित कर सकता है)\??$",
    r"^(व्यायाम के दौरान कमजोरी|व्यायाम के दौरान चक्कर) महसूस होने पर मुझे क्या करना चाहिए\??$",
    r"^(मी .* (अंडी|डाळ|पनीर|दूध) खाऊ शकतो.*|व्यायाम माझ्यासाठी सुरक्षित आहे का|मला (अशक्तपणा|थकवा) का जाणवतो|माझे स्नायू का कमी होत आहेत|व्यायाम करताना (अशक्तपणा|चक्कर) आल्यास काय करावे|स्नायूंची ताकद|स्नायू टिकवण्यासाठी|प्रथिने|आहार|व्यायाम|चालणे|अशक्तपणा|थकवा|स्नायू कमी)\b.*\??$",
    r"^(ನಾನು .* (ಮೊಟ್ಟೆ|ಬೇಳೆ|ಹಾಲು|ಪನೀರ್) ತಿನ್ನಬಹುದೇ|ವ್ಯಾಯಾಮ ನನಗೆ ಸುರಕ್ಷಿತವೇ|ನನಗೆ ಏಕೆ (ದೌರ್ಬಲ್ಯ|ದಣಿವು) ಅನಿಸುತ್ತದೆ|ನನ್ನ ಸ್ನಾಯುಗಳು ಏಕೆ ಕಡಿಮೆಯಾಗುತ್ತಿವೆ|cld ನನ್ನ ಸ್ನಾಯುಗಳ ಮೇಲೆ ಪರಿಣಾಮ ಬೀರಬಹುದೇ)\??$",
    r"^(ವ್ಯಾಯಾಮ ಮಾಡುವಾಗ (ದೌರ್ಬಲ್ಯ|ತಲೆಸುತ್ತು) ಬಂದರೆ ನಾನು ಏನು ಮಾಡಬೇಕು|ಯಾವ ಆಹಾರ.*ಸ್ನಾಯು|ಯಾವ ವ್ಯಾಯಾಮ.*ಶಕ್ತಿ|ನಡೆಯುವುದು.*ಏಕೆ)\??$",
    r"^(कौन से खाद्य पदार्थ|कौन से व्यायाम|चलना क्यों|मांसपेशियों की ताकत|प्रोटीन क्यों|स्वस्थ आहार).*\??$",
    r"^(कोणते खाद्यपदार्थ|कोणते व्यायाम|चालणे का|स्नायूंची ताकद|प्रथिने का|स्नायू टिकवण्यासाठी).*\??$",
    r"^(ಸ್ನಾಯುಗಳನ್ನು ಕಾಪಾಡಲು|ಯಾವ ಆಹಾರ|ಯಾವ ವ್ಯಾಯಾಮ|ನಡೆಯುವುದು ಏಕೆ|ಸ್ನಾಯು ಶಕ್ತಿಯನ್ನು|ಪ್ರೋಟೀನ್ ಏಕೆ).*\??$",
)

GENERAL_EDUCATION_EXCLUSIONS = (
    r"\b(do i have|diagnos(e|is) me|what is wrong with me)\b",
    r"(क्या मुझे .* बीमारी|मुझे कौन सी बीमारी|ನನಗೆ .* ಕಾಯಿಲೆ ಇದೆಯೇ|ಮला .* आजार आहे का)",
)

MEDICATION_PATTERNS = (
    r"\b(medicines?|medications?|drugs?|tablets?|capsules?|prescriptions?|dosage|doses?|mg|pills?)\b",
    r"\b(start|stop|change|increase|decrease|skip|take|use|continue)\b.{0,45}\b(medicines?|medications?|drugs?|tablets?|dose|dosage|pills?)\b",
    r"(दवा|दवाइयाँ|दवाइयां|दवाई|गोलियां|गोली|खुराक|औषध|औषधे|औषधि|मात्रा|ಔಷಧ|ಔಷಧಿ|ಔಷಧಗಳು|ಮಾತ್ರೆ|ಡೋಸ್)",
    r"\b(can i|could i|should i|may i|is it safe to)\b.{0,40}\b(take|use|try|start)\b",
)

PATIENT_SPECIFIC_PATTERNS = (
    r"\b(do i have|am i having|does this mean i have|diagnose me|what is wrong with me)\b",
    r"\b(what should i do|should i take|should i stop|can i safely)\b",
    r"(क्या मुझे .* बीमारी|मुझे कौन सी बीमारी|मुझे क्या करना चाहिए|क्या मैं .* ले सकता)",
    r"(ನನಗೆ .* ಕಾಯಿಲೆ ಇದೆಯೇ|ನಾನು ಏನು ಮಾಡಬೇಕು|ನಾನು .* ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ)",
    r"(मला .* आजार आहे का|मी काय करावे|मी .* घेऊ का)",
    r"\b(my|i have|i am experiencing)\b.{0,55}\b(pain|swelling|dizziness|dizzy|fatigue|weakness|nausea|vomiting|symptom)\b.{0,45}\b(why|what does|is this|mean|should|diagnos)\b",
    r"\b(why am i|what causes my|why do i feel)\b.{0,45}\b(weak|weakness|pain|swelling|dizzy|dizziness|fatigue|nausea|symptom)\b",
    r"\b(should i|can i)\b.{0,45}\b(exercise|walk|lift|train)\b.{0,35}\b(pain|swelling|dizzy|dizziness|fatigue|weak|symptom)\b",
    r"\b(i have|i am having|i'm having|i feel|i'm feeling)\b.{0,45}\b(pain|swelling|dizzy|dizziness|fatigue|weakness|nausea|vomiting|yellow eyes|yellow skin|abdominal pain|symptom)\b",
    r"\b(what should i eat|what can i eat|make|create|give me)\b.{0,35}\b(diet plan|meal plan|weight loss plan|nutrition plan)\b",
    r"\b(give me|recommend|make|create)\b.{0,35}\b(intense|strenuous|heavy|high[- ]intensity)\b.{0,25}\b(workout|exercise|training|lifting)\b",
    r"\b(i have|my)\b.{0,35}\b(cld|liver disease|sarcopenia)\b.{0,50}\b(diet|eat|exercise|workout|training)\b.{0,30}\b(should|recommend|plan|safe|do)\b",
    r"(मुझे .* (दर्द|सूजन|चक्कर|कमजोरी) .* (क्यों|क्या मतलब|क्या करूँ)|मेरे .* लक्षण .* क्या)",
    r"(ನನಗೆ .* (ನೋವು|ಊತ|ತಲೆಸುತ್ತು|ದೌರ್ಬಲ್ಯ) .* (ಏಕೆ|ಅರ್ಥ|ಏನು ಮಾಡಲಿ))",
    r"(मला .* (वेदना|सूज|चक्कर|अशक्तपणा) .* (का|अर्थ|काय करावे))",
)

PATIENT_PROFILE_PATTERNS = (
    r"\b(what (are|is|did) (my|i)\b.{0,45}\b(profile|details|habits|diet|exercise|age|gender|information|marital status|family|residence|religion|occupation|education|cld|sarcopenia|comorbidit\w*|treatment|hospitali[sz]ation|counselling|counseling|health education|socioeconomic)|what do you know about me|what did i tell you about me|show my profile|my recorded (profile|details|habits|information)|do i have any (recorded )?comorbidit\w*|have i (received|had) (nutritional )?counsel(l)?ing|have i previously received (cld|sarcopenia|health) education)\b",
    r"(मेरी जानकारी|मेरी प्रोफाइल|मेरी आदतें|मैंने आपको क्या बताया|मेरे बारे में आपने क्या दर्ज किया|मेरी उम्र क्या|मेरा आहार क्या|मेरी वैवाहिक स्थिति|मेरी शिक्षा|मेरा व्यवसाय|मेरी बीमारी की अवधि|मेरी बीमारी का चरण|मेरी दवाओं? का विवरण|मेरी पोषण सलाह|मेरी पिछली शिक्षा|मेरे सह.?रोग)",
    r"(ನನ್ನ ಮಾಹಿತಿ|ನನ್ನ ಪ್ರೊಫೈಲ್|ನನ್ನ ಅಭ್ಯಾಸಗಳು|ನಾನು ನಿಮಗೆ ಏನು ಹೇಳಿದೆ|ನನ್ನ ಬಗ್ಗೆ ಏನು ದಾಖಲಿಸಿದ್ದೀರಿ|ನನ್ನ ವಯಸ್ಸು ಏನು|ನನ್ನ ಆಹಾರ ಏನು|ನನ್ನ ವೈವಾಹಿಕ ಸ್ಥಿತಿ|ನನ್ನ ಶಿಕ್ಷಣ|ನನ್ನ ಉದ್ಯೋಗ|ನನ್ನ ಕಾಯಿಲೆಯ ಅವಧಿ|ನನ್ನ ಕಾಯಿಲೆಯ ಹಂತ|ನನ್ನ ಪೌಷ್ಟಿಕ ಸಲಹೆ|ನನ್ನ ಹಿಂದಿನ ಶಿಕ್ಷಣ|ನನ್ನ ಸಹ.?ರೋಗ)",
    r"(माझी माहिती|माझे प्रोफाइल|माझ्या सवयी|मी तुम्हाला काय सांगितले|माझ्याबद्दल काय नोंदवले|माझे वय काय|माझा आहार काय|माझी वैवाहिक स्थिती|माझे शिक्षण|माझा व्यवसाय|माझ्या आजाराचा कालावधी|माझ्या आजाराची अवस्था|माझे पोषण समुपदेशन|माझे पूर्वीचे शिक्षण|माझे सह.?विकार)",
)

LIFESTYLE_CHANGE_PATTERNS = (
    r"\b(improve|change|stop|reduce|quit|manage|work on)\b.{0,45}\b(my )?(habits|lifestyle|smoking|tobacco|alcohol|diet|exercise)\b|\bhow (can|do) i (improve|change|stop|reduce|quit)\b",
    r"(आदतें? (कैसे|कैसे बदल|कैसे छोड़|सुधार)|शराब.*(छोड़|कम)|धूम्रपान.*(छोड़|कम)|जीवनशैली.*सुधार)",
    r"(ಅಭ್ಯಾಸ.*(ಸುಧಾರ|ಬದಲಾ|ನಿಲ್ಲಿ|ಕಡಿಮೆ)|ಮದ್ಯ.*(ನಿಲ್ಲಿ|ಕಡಿಮೆ)|ಧೂಮಪಾನ.*(ನಿಲ್ಲಿ|ಕಡಿಮೆ)|ಜೀವನಶೈಲಿ.*ಸುಧಾರ)",
    r"(सवयी.*(सुधार|बदल|सोड|कमी)|दारू.*(सोड|कमी)|धूम्रपान.*(सोड|कमी)|जीवनशैली.*सुधार)",
)

DIAGNOSIS_TREATMENT_PATTERNS = (
    r"\b(diagnos(e|is)|treat me|prescribe|what disease do i have)\b",
    r"(मुझे .* बीमारी है|मेरा निदान|मेरा इलाज बत|ನನಗೆ .* ಕಾಯಿಲೆ|ನನ್ನ ರೋಗನಿರ್ಣಯ|मला .* आजार|माझे निदान)",
)

UNSAFE_EXERCISE_TERMS = (
    "heavy lifting", "strenuous exercise", "high intensity", "intense workout", "push through pain",
    "जोरदार व्यायाम", "भारी व्यायाम", "तीव्र व्यायाम", "ಅತಿಯಾದ ವ್ಯಾಯಾಮ", "ಭಾರ ಎತ್ತುವುದು",
)

UNSAFE_OUTPUT_PATTERNS = (
    r"\b(you have|you definitely have|this confirms)\b.{0,60}\b(disease|cirrhosis|diagnosis|liver failure)\b",
    r"\b(take|start|stop|increase|decrease|double|halve)\b.{0,40}\b(mg|dose|dosage|medicine|medication|tablet)\b",
    r"\b(you should|you must)\b.{0,45}\b(stop|skip|change|increase|decrease)\b.{0,30}\b(medicine|medication|dose)\b",
    r"\b(push through|ignore)\b.{0,30}\b(pain|dizziness|dizzy|weakness)\b",
    r"(आपको (निश्चित रूप से|है)|आपको .* रोग है|यह (सिरोसिस|लिवर फेलियर) की पुष्टि करता है)",
    r"(ನಿಮಗೆ .* ಕಾಯಿಲೆ ಇದೆ|ಇದು .* ರೋಗವನ್ನು ದೃಢಪಡಿಸುತ್ತದೆ|ಔಷಧ.*(ಪ್ರಾರಂಭಿಸಿ|ನಿಲ್ಲಿಸಿ|ಹೆಚ್ಚಿಸಿ|ಕಡಿಮೆ ಮಾಡಿ))",
    r"(तुम्हाला .* आजार आहे|हे .* रोग निश्चित करते|औषध.*(सुरू करा|थांबवा|वाढवा|कमी करा))",
)


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    response: str = ""
    reason: str = ""


@dataclass(frozen=True)
class RetrievalAssessment:
    status: str
    evidence: tuple[str, ...] = ()
    reason: str = ""


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "this", "to", "what", "when",
    "where", "which", "why", "with", "you", "your", "है", "हैं", "का", "की", "के", "में", "और", "क्या",
    "ಒಂದು", "ಮತ್ತು", "ಇದು", "ಗೆ", "ના", "आहे", "आणि", "काय",
}


def _strip_diacritics_and_marks(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").casefold())
    return "".join(char for char in normalized if unicodedata.category(char)[0] != "M")


NORMALIZED_STOP_WORDS = {_strip_diacritics_and_marks(word) for word in STOP_WORDS}

TOPIC_EVIDENCE_TERMS = {
    "cld": ("cld", "liver", "hepatic", "यकृत", "ಲಿವರ್", "ಯಕೃತ್ತು", "ಯಕೃತ್ತಿನ"),
    "sarcopenia": ("sarcopenia", "muscle", "मांसपेश", "स्नायू", "ಸ್ನಾಯು", "ಸಾರ್ಕೋಪೀನಿಯಾ"),
    "nutrition": ("nutrition", "diet", "protein", "food", "meal", "पोषण", "आहार", "प्रोटीन", "ಆಹಾರ", "ಪೋಷಣೆ"),
    "exercise": ("exercise", "movement", "walking", "workout", "व्यायाम", "ಚಲನೆ", "ನಡೆಯುವುದು"),
    "safety": ("safety", "warning", "safe", "सुरक्षा", "ಎಚ್ಚರಿಕೆ", "सुरक्षितता", "अशक्तपणा", "चक्कर", "तत्काळ"),
}

LOCAL_CONCEPT_ALIASES = {
    "liver": {"लिवर", "यकृत", "यकृताच्या", "यकृताचे", "यकृताचा", "ಯಕೃತ್ತು", "ಯಕೃತ್ತಿನ", "ಲಿವರ್"},
    "disease": {"बीमारी", "बिमारी", "रोग", "ಕಾಯಿಲೆ", "ಕಾಯಿಲೆಯ", "ರೋಗ", "आजार", "आजाराचे"},
    "damage": {"damage", "damages", "damaged", "damaging", "नुकसान", "क्षति", "ಹಾನಿ", "ಹಾನಿಯನ್ನು"},
    "time": {"समय", "कालांतराने", "ಕಾಲ", "वेಳ"},
    "muscle": {"मांसपेशी", "मांसपेशियों", "ಸ್ನಾಯು", "ಸ्नಾಯುಗಳು", "स्नायू", "स्नायूं"},
    "weakness": {"कमजोरी", "ದೌರ್ಬಲ್ಯ", "ಅಶಕ್ತತೆ", "अशक्तपणा"},
    "protein": {"प्रोटीन", "ಪ್ರೋಟೀನ್", "प्रथिने"},
    "diet": {"आहार", "आहाराचा", "आहारात", "ಆಹಾರ", "ಆಹಾರದಲ್ಲಿ"},
    "food": {"भोजन", "खाद्य", "आहार", "ಆಹಾರ", "ಅನ್ನ", "अन्न"},
    "pulse": {"दाल", "दालें", "डाळ", "डाळी", "ಬೇಳೆ", "lentil", "lentils", "pulse", "pulses", "dal"},
    "dairy": {"दूध", "दही", "दुग्ध", "दुग्धजन्य", "दुधातून", "ಹಾಲು", "ಮೊಸರು", "milk", "dairy", "yogurt", "paneer", "पनीर"},
    "egg": {"अंडे", "अंडों", "ಮೊಟ್ಟೆ", "eggs", "egg"},
    "fish": {"मछली", "ಮೀನು", "fish"},
    "chicken": {"चिकन", "ಕೋಳಿ", "chicken"},
    "tofu": {"टोफू", "tofu"},
    "dizziness": {"चक्कर", "ತಲೆಸುತ್ತು", "dizzy", "dizziness"},
    "stop": {"ನಿಲ್ಲಿಸಿ", "ನಿಲ್ಲಿಸಬೇಕು", "थांबवा", "थांबवावे", "stop"},
    "guidance": {"मार्गदर्शन", "सल्ला", "ಮಾರ್ಗದರ್ಶನ", "ಸಲಹೆ", "guidance"},
    "doctor": {"डॉक्टर", "डॉक्टरांशी", "डॉक्टरांना", "वैद्यರು", "ವೈದ್ಯರು", "ವೈದ್ಯರಿಗೆ", "doctor"},
    "nurse": {"नर्स", "नर्सशी", "ನರ್ಸ್", "ನರ್ಸ್‌ಗೆ", "सಿಸ್ಟರ್", "nurse"},
    "worsen": {"वाढल्यास", "बिघडल्यास", "ಹೆಚ್ಚಾದರೆ", "worsens", "worsening"},
    "symptom": {"लक्षणे", "लक्षणांमध्ये", "ಲಕ್ಷಣಗಳು", "symptoms"},
    "exercise": {"व्यायाम", "व्यायामाचा", "व್ಯಾಯಾಮ", "ವ್ಯಾಯಾಮ"},
    "safe": {"सुरक्षित", "ಸುರಕ್ಷಿತ", "सुरक्षित"},
    "balanced": {"संतुलित", "ಸಮತೋಲಿತ", "संतुलित"},
    "support": {"सहायक", "मदद", "ಸಹಾಯ", "मदत"},
    "long": {"लंबे", "दीर्घकालीन", "ದೀರ್ಘಕಾಲದ", "दीर्घकालीन"},
}

LOCAL_CONCEPT_ALIASES["nurse"].update({"\u0928\u0930\u094d\u0938\u0915\u0921\u0942\u0928", "\u0928\u0930\u094d\u0938\u0928\u093e"})
LOCAL_CONCEPT_ALIASES["medical"] = {"medical", "\u0935\u0948\u0926\u094d\u092f\u0915\u0940\u092f"}
LOCAL_CONCEPT_ALIASES["time"].update({"\u0c95\u0cbe\u0cb2\u0c95\u0ccd\u0cb0\u0cae\u0cc7\u0ca3"})
LOCAL_CONCEPT_ALIASES["worsen"].update({"\u0935\u093e\u0922\u0924\u093e"})

POSITIVE_CLAIM_TERMS = {_strip_diacritics_and_marks(term) for term in {"improve", "improves", "improved", "improving", "protect", "protects", "better", "सुधार", "सुधरता", "ಸುಧಾರ", "ಉತ್ತಮ", "सुधारते"}}
NEGATIVE_CLAIM_TERMS = {_strip_diacritics_and_marks(term) for term in {"damage", "damages", "damaged", "harm", "harms", "harmful", "worsen", "worsens", "worse", "नुकसान", "हानि", "बिगाड़", "ಹಾನಿ", "ಕೆಟ್ಟ", "हानी"}}
OPPOSITE_CLAIM_TERMS = {_strip_diacritics_and_marks(term) for term in {"harmless", "safe", "सुरक्षित", "ಸುರಕ್ಷಿತ"}}
NEGATION_TERMS = {_strip_diacritics_and_marks(term) for term in {"not", "never", "no", "cannot", "doesn't", "isn't", "नहीं", "ಅಲ್ಲ", "ಇಲ್ಲ", "नाही"}}


def _message(language: str, key: str) -> str:
    code = normalize_language_code(language)
    return MESSAGES.get(code, MESSAGES["en"])[key]


def generation_unavailable_response(language: str) -> str:
    return _message(language, "service_unavailable")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().casefold())


def _devanagari_language_hint(text: str) -> str | None:
    words = set(re.findall(r"[\u0900-\u097f]+", text))
    if words & {"आहे", "आहेत", "माझे", "मला", "होते", "करावे"}:
        return "mr"
    if words & {"है", "हैं", "मुझे", "कैसे", "क्यों"}:
        return "hi"
    return None


def configured_max_input_chars() -> int:
    try:
        return max(1, int(os.getenv("CHAT_MAX_INPUT_CHARS", str(DEFAULT_MAX_INPUT_CHARS))))
    except ValueError:
        return DEFAULT_MAX_INPUT_CHARS


def configured_red_flag_phrases() -> tuple[str, ...]:
    """Only phrases explicitly supplied by the hospital/clinical team are active."""
    return tuple(
        phrase.strip().casefold()
        for phrase in os.getenv("CLINICIAN_APPROVED_RED_FLAGS", "").split("|")
        if phrase.strip()
    )


def classify_topics(text: str) -> set[str]:
    normalized = _normalize(text)
    return {
        topic
        for topic, terms in TOPIC_TERMS.items()
        if any(term.casefold() in normalized for term in terms)
    }


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def classify_intent(text: str, *, context_text: str = "") -> str:
    """Classify the requested action without treating profile data as clinical evidence."""
    normalized = _normalize(text)
    context = _normalize(context_text)
    topics = classify_topics(normalized)
    if _matches_any(normalized, MEDICATION_PATTERNS) or (
        context and re.search(r"\b(stop|change|increase|decrease|skip|take|continue)\b", normalized)
        and _matches_any(context, MEDICATION_PATTERNS)
    ):
        return "medication_safety"
    if re.search(r"\b(recorded|documented)\b.{0,35}\bcomorbidit\w*\b", normalized):
        return "patient_profile"
    if (
        _matches_any(normalized, DIAGNOSIS_TREATMENT_PATTERNS)
        or re.search(PATIENT_SPECIFIC_PATTERNS[0], normalized, re.IGNORECASE)
        or re.search(PATIENT_SPECIFIC_PATTERNS[7], normalized, re.IGNORECASE)
    ):
        return "diagnosis_treatment"
    is_profile = _matches_any(normalized, PATIENT_PROFILE_PATTERNS)
    is_lifestyle = _matches_any(normalized, LIFESTYLE_CHANGE_PATTERNS)
    if is_profile and is_lifestyle:
        return "profile_lifestyle"
    if is_lifestyle:
        return "lifestyle_changes"
    if is_profile:
        return "patient_profile"
    if topics & {"exercise"}:
        return "exercise"
    if topics & {"nutrition"}:
        return "nutrition"
    if topics & {"safety"} or re.search(r"\b(symptom|warning|feel|feeling|weakness|weak|fatigue|tired)\b|कमजोरी|थकान|दೌರ್ಬಲ್ಯ|ಅಶಕ್ತತೆ|थकवा|अशक्तपणा", normalized):
        return "symptoms_warning_signs"
    if topics:
        return "general_health"
    if context and re.search(r"\b(they|them|it|those|these|that|this)\b|उन्हें|इनको|ಅವು|ಅದನ್ನು|त्यांना|ते", normalized):
        return classify_intent(context)
    return "unrelated"


def _is_general_education_question(text: str, topics: set[str]) -> bool:
    """Allow a small set of education-shaped questions without clearing clinical decisions."""
    normalized = _normalize(text)
    normalized = re.sub(
        r"\s+(please\s+)?(answer|reply|respond|explain|write)\s+(in|using)\s+(english|hindi|kannada|marathi)[.!?]*$",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\s+(हिंदी में (बताएं|जवाब|समझाएं)|ಕನ್ನಡದಲ್ಲಿ (ಹೇಳಿ|ಉತ್ತರಿಸಿ|ವಿವರಿಸಿ)|मराठीत (सांगा|उत्तर|समजावून))[.!?]*$",
        "",
        normalized,
    )
    if not topics or any(re.search(pattern, normalized, re.IGNORECASE) for pattern in GENERAL_EDUCATION_EXCLUSIONS):
        return False
    return any(re.fullmatch(pattern, normalized, re.IGNORECASE) for pattern in GENERAL_EDUCATION_PATTERNS)


def insufficient_evidence_response(question: str, language: str) -> str:
    """Return a topic-specific, non-diagnostic response when RAG has no usable evidence."""
    normalized = _normalize(question)
    topics = classify_topics(normalized)
    food_words = (
        "eat", "food", "egg", "dal", "lentil", "paneer", "milk", "खाना", "अंडे", "दाल",
        "ಆಹಾರ", "ಮೊಟ್ಟೆ", "ಬೇಳೆ", "ತಿನ್ನ", "अन्न", "अंडी", "डाळ", "खाऊ",
    )
    if ("nutrition" in topics and any(word in normalized for word in food_words)):
        return _message(language, "food_no_evidence")
    if "exercise" in topics and any(word in normalized for word in ("safe", "सुरक्षित", "ಸುರಕ್ಷಿತ", "सुरक्षितता")):
        return _message(language, "exercise_no_evidence")
    symptom_words = ("weak", "weakness", "tired", "fatigue", "कमजोरी", "थकान", "ಅಶಕ್ತ", "ದೌರ್ಬಲ್ಯ", "थकवा", "अशक्तपणा")
    if any(word in normalized for word in symptom_words):
        return _message(language, "symptom_no_evidence")
    return _message(language, "no_evidence")


def inspect_input(
    text: str,
    language: str,
    *,
    max_chars: int | None = None,
    approved_red_flags: tuple[str, ...] | None = None,
    context_text: str = "",
) -> GuardrailDecision:
    normalized = _normalize(text)
    context = _normalize(context_text)
    if not normalized:
        return GuardrailDecision(False, _message(language, "empty"), "empty_input")
    if len(text) > (max_chars or configured_max_input_chars()):
        return GuardrailDecision(False, _message(language, "too_long"), "input_too_long")

    red_flags = configured_red_flag_phrases() if approved_red_flags is None else approved_red_flags
    if any(phrase.casefold() in normalized for phrase in red_flags):
        return GuardrailDecision(False, _message(language, "urgent"), "clinician_red_flag")
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        return GuardrailDecision(False, _message(language, "injection"), "prompt_injection")

    topics = classify_topics(normalized)
    intent = classify_intent(text, context_text=context_text)
    if intent == "medication_safety":
        return GuardrailDecision(False, _message(language, "medication_safety"), "medication_question")
    if intent == "diagnosis_treatment" or _matches_any(normalized, DIAGNOSIS_TREATMENT_PATTERNS):
        return GuardrailDecision(False, _message(language, "clinician"), "diagnosis_or_treatment_request")
    individual_plan_patterns = (
        r"\b(what should i eat|what can i eat|make|create|give me)\b.{0,35}\b(diet plan|meal plan|weight loss plan|nutrition plan)\b",
        r"\b(give me|recommend|make|create)\b.{0,35}\b(intense|strenuous|heavy|high[- ]intensity)\b.{0,25}\b(workout|exercise|training|lifting)\b",
    )
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in individual_plan_patterns):
        return GuardrailDecision(False, _message(language, "clinician"), "patient_specific_clinical_question")
    if intent == "patient_profile":
        return GuardrailDecision(True, reason="patient_profile")
    if intent == "profile_lifestyle":
        return GuardrailDecision(True, reason="profile_lifestyle")
    if intent == "lifestyle_changes" and (
        topics or re.search(r"habit|lifestyle|alcohol|smok|tobacco|आदत|शराब|धूम|ಅಭ್ಯಾಸ|ಮದ್ಯ|ಧೂಮಪಾನ|सवय|दारू", normalized)
    ):
        return GuardrailDecision(True, reason="lifestyle_changes")
    if not topics and not (context and classify_topics(context)):
        return GuardrailDecision(False, _message(language, "scope"), "out_of_scope")
    return GuardrailDecision(True)


def validate_medical_safety_output(text: str, language: str) -> GuardrailDecision:
    """Apply only high-impact medical safety checks, not lexical evidence scoring."""
    answer = text.strip() if isinstance(text, str) else ""
    if not answer:
        return GuardrailDecision(False, _message(language, "no_evidence"), "empty_output")
    for pattern in UNSAFE_OUTPUT_PATTERNS:
        if re.search(pattern, answer, re.IGNORECASE):
            if re.search(UNSAFE_OUTPUT_PATTERNS[1], answer, re.IGNORECASE) or re.search(
                UNSAFE_OUTPUT_PATTERNS[2], answer, re.IGNORECASE
            ):
                return GuardrailDecision(False, _message(language, "medication_safety"), "unsafe_medication_output")
            return GuardrailDecision(False, _message(language, "unsafe_output"), "unsafe_diagnostic_or_treatment_output")
    return GuardrailDecision(True, answer)


def _tokens(text: str) -> set[str]:
    normalized = _strip_diacritics_and_marks(text)
    return {
        token for token in re.findall(r"[^\W_]+", normalized, re.UNICODE)
        if len(token) > 1 and token not in NORMALIZED_STOP_WORDS
    }


def _canonical_tokens(text: str) -> set[str]:
    tokens = _tokens(text)
    aliases = {
        token: canonical
        for canonical, variants in LOCAL_CONCEPT_ALIASES.items()
        for alias in variants
        for token in _tokens(alias)
    }
    return {aliases.get(token, token) for token in tokens}


def _topic_content_match(text: str, topics: set[str]) -> bool:
    normalized = _normalize(text)
    return any(
        term in normalized
        for topic in topics
        for term in TOPIC_EVIDENCE_TERMS.get(topic, ())
    )


def _question_relevant(text: str, question: str, topics: set[str]) -> bool:
    evidence_tokens = _canonical_tokens(text)
    query_tokens = _canonical_tokens(question)
    shared = evidence_tokens & query_tokens
    if shared:
        return True
    return _topic_content_match(text, topics)


def _claim_reverses_evidence(claim: str, source: str) -> bool:
    claim_tokens = _canonical_tokens(claim)
    source_tokens = _canonical_tokens(source)
    claim_positive = any(term in token for term in POSITIVE_CLAIM_TERMS for token in claim_tokens)
    claim_negative = any(term in token for term in NEGATIVE_CLAIM_TERMS for token in claim_tokens)
    source_positive = any(term in token for term in POSITIVE_CLAIM_TERMS for token in source_tokens)
    source_negative = any(term in token for term in NEGATIVE_CLAIM_TERMS for token in source_tokens)
    claim_opposite = any(term in token for term in OPPOSITE_CLAIM_TERMS for token in claim_tokens)
    source_opposite = any(term in token for term in OPPOSITE_CLAIM_TERMS for token in source_tokens)
    if (claim_positive and source_negative) or (claim_negative and source_positive):
        return True
    if (claim_opposite and source_negative) or (claim_negative and source_opposite):
        return True
    shared = claim_tokens & source_tokens
    claim_negated = bool(claim_tokens & NEGATION_TERMS)
    source_negated = bool(source_tokens & NEGATION_TERMS)
    return len(shared) >= 2 and claim_negated != source_negated


def _is_nonfactual_safety_text(sentence: str) -> bool:
    patterns = (
        r"\b(this (information|response|answer) is (for )?(education|educational purposes) only|not (a )?(diagnosis|medical advice))\b",
        r"\b(please )?(talk|speak|consult|ask|discuss).{0,45}\b(doctor|nurse|clinician|dietitian)\b",
        r"(यह जानकारी|यह उत्तर).{0,35}(केवल|सिर्फ).{0,20}(शिक्षा|जानकारी)|डॉक्टर या नर्स से (बात|पूछ|चर्चा)",
        r"ಈ ಮಾಹಿತಿ.{0,35}(ಕೇವಲ|ಮಾತ್ರ).{0,20}(ಕಲಿಕೆ|ಶಿಕ್ಷಣ)|ವೈದ್ಯರು ಅಥವಾ ನರ್ಸ್.{0,30}(ಮಾತನಾಡಿ|ಕೇಳಿ|ಚರ್ಚಿಸಿ)",
        r"(ही माहिती|हे उत्तर).{0,35}(केवळ|फक्त).{0,20}(शिक्षण|माहिती)|डॉक्टर किंवा नर्सशी.{0,30}(बोला|विचारा|चर्चा)",
    )
    return any(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)


def _retrieval_documents(retrieval: dict) -> list[dict]:
    documents = []
    faq = retrieval.get("faq_first_match") or {}
    if isinstance(faq, dict):
        faq_text = " ".join(str(faq.get(key) or "") for key in ("question", "answer"))
        if faq_text.strip():
            documents.append({"topic": faq.get("topic", ""), "content": faq_text, "faq": True})
    for chunk in retrieval.get("retrieved_chunks") or []:
        if isinstance(chunk, dict):
            documents.append({**chunk, "faq": False})
    return documents


def _numeric_values(text: str) -> set[str]:
    values = set()
    normalized = "".join(str(unicodedata.digit(char)) if char.isdigit() else char for char in text)
    pattern = r"(?<!\w)(\d+(?:\.\d+)?)\s*(%|kilograms?|kg|milligrams?|mg|grams?|g|kcal|calories?|minutes?|hours?|days?|ग्राम|ಗ್ರಾಂ|ग्रॅम)?\b"
    for match in re.finditer(pattern, normalized, re.IGNORECASE):
        amount = float(match.group(1))
        unit = (match.group(2) or "").casefold()
        if unit in {"kg", "kilogram", "kilograms"}:
            unit, amount = "g", amount * 1000
        elif unit in {"mg", "milligram", "milligrams"}:
            unit, amount = "g", amount / 1000
        elif unit in {"gram", "grams"}:
            unit = "g"
        elif unit in {"kilocalorie", "kilocalories"}:
            unit = "kcal"
        elif unit in {"minute", "minutes"}:
            unit = "min"
        elif unit in {"hour", "hours"}:
            unit = "h"
        elif unit in {"day", "days"}:
            unit = "d"
        elif unit in {"ग्राम", "ಗ್ರಾಂ", "ग्रॅम"}:
            unit = "g"
        amount_text = f"{amount:.6f}".rstrip("0").rstrip(".")
        values.add(f"{unit}:{amount_text}" if unit else f"number:{amount_text}")
    return values


def _opposes(left: str, right: str) -> bool:
    opposites = ((r"\bsafe\b", r"\bunsafe\b"), (r"\bincrease\b", r"\bdecrease\b"),
                 (r"\brecommend\w*\b", r"\bavoid\w*\b"), (r"\bsupport\w*\b", r"\bharm\w*\b"),
                 )
    return any((re.search(a, left) and re.search(b, right)) or (re.search(b, left) and re.search(a, right)) for a, b in opposites)


def _has_conflict(documents: list[dict]) -> bool:
    generic = {"should", "patients", "patient", "people", "person", "exercise", "exercises", "activity", "sudden", "starting", "good", "point"}
    sentences: list[tuple[str, str]] = []
    for document in documents:
        content = str(document.get("content") or "")
        topic = str(document.get("topic") or "").casefold()
        sentences.extend((topic, sentence.strip()) for sentence in re.split(r"(?<=[.!?।])\s+", content) if sentence.strip())
    for index, (topic_a, sentence_a) in enumerate(sentences):
        tokens_a = _tokens(sentence_a)
        predicate_a = {token.rstrip("s") for token in tokens_a} & {
            "support", "help", "harm", "prevent", "cause", "recommend", "avoid", "increase", "decrease", "reduce", "improve", "worsen"
        }
        for topic_b, sentence_b in sentences[index + 1:]:
            if topic_a and topic_b and topic_a != topic_b:
                continue
            tokens_b = _tokens(sentence_b)
            predicate_b = {token.rstrip("s") for token in tokens_b} & {
                "support", "help", "harm", "prevent", "cause", "recommend", "avoid", "increase", "decrease", "reduce", "improve", "worsen"
            }
            shared = tokens_a & tokens_b
            anchors = shared - generic
            if len(anchors) < 2:
                continue
            numbers_a, numbers_b = _numeric_values(sentence_a), _numeric_values(sentence_b)
            if numbers_a and numbers_b and numbers_a != numbers_b:
                return True
            if _opposes(sentence_a.casefold(), sentence_b.casefold()) and anchors:
                return True
            negative_a = bool(re.search(r"\b(not|never|avoid|unsafe|cannot|shouldn't|mustn't)\b", sentence_a, re.IGNORECASE))
            negative_b = bool(re.search(r"\b(not|never|avoid|unsafe|cannot|shouldn't|mustn't)\b", sentence_b, re.IGNORECASE))
            if negative_a != negative_b and len(anchors) >= 3 and predicate_a & predicate_b:
                return True
    return False


def assess_retrieval(retrieval: dict, question: str) -> RetrievalAssessment:
    """Select question-relevant, non-empty evidence and fail closed on detected conflicts."""
    if not isinstance(retrieval, dict):
        return RetrievalAssessment("insufficient", (), "invalid_retrieval_result")
    requested = {"diet" if topic == "nutrition" else topic for topic in classify_topics(question)} - {"patient_education"}
    documents = _retrieval_documents(retrieval)
    relevant: list[str] = []
    reasons: list[str] = []
    for document in documents:
        content = str(document.get("content") or "").strip()
        topic = str(document.get("topic") or "").casefold()
        topic = "diet" if topic == "nutrition" else topic
        if not content:
            reasons.append("retrieved_passage_is_empty")
            continue
        if requested and topic not in requested and topic != "faq":
            reasons.append(f"topic_mismatch:{topic or 'missing'}")
            continue
        if document.get("faq"):
            score_ok = bool(retrieval.get("faq_first_match"))
        else:
            try:
                score_ok = float(document.get("semantic_score", 0)) >= 0.35 or float(document.get("overlap_score", 0)) >= 0.12
            except (TypeError, ValueError):
                score_ok = False
        if not score_ok:
            reasons.append("passage_below_existing_relevance_threshold")
            continue
        if _question_relevant(content, question, requested or {topic}):
            relevant.append(content)
        else:
            reasons.append("passage_does_not_match_question_concepts")
    if not relevant:
        return RetrievalAssessment(
            "insufficient", (), reasons[0] if reasons else ("empty_retrieval" if not documents else "no_relevant_evidence")
        )
    relevant_documents = [
        doc for doc in documents
        if str(doc.get("content") or "").strip() in relevant
    ]
    if _has_conflict(relevant_documents):
        return RetrievalAssessment("conflict", tuple(relevant), "retrieved_passages_conflict_on_shared_claim_or_numeric_value")
    if re.search(r"\b(how much|how many|amount|quantity|grams?|mg|milligrams?|calories?)\b|कितना|कितनी|ग्राम|ಎಷ್ಟು|ಗ್ರಾಂ|किती|ग्रॅम", question, re.IGNORECASE):
        if not _numeric_values(" ".join(relevant)):
            return RetrievalAssessment("insufficient", tuple(relevant), "question_requires_numerical_evidence_but_no_number_or_unit_was_retrieved")
    return RetrievalAssessment("supported", tuple(relevant), "relevant_evidence_selected")


def retrieval_has_support(retrieval: dict, question: str) -> bool:
    return assess_retrieval(retrieval, question).status == "supported"


def _answer_is_grounded(answer: str, evidence: tuple[str, ...]) -> bool:
    evidence_text = " ".join(evidence)
    evidence_sentences = [
        part.strip() for part in re.split(r"(?<=[.!?।])\s+", evidence_text) if part.strip()
    ]
    sentences = [part.strip() for part in re.split(r"(?<=[.!?।])\s+", answer) if part.strip()]
    factual_sentence_count = 0
    for sentence in sentences:
        if _is_nonfactual_safety_text(sentence):
            continue
        factual_sentence_count += 1
        claim_tokens = _canonical_tokens(sentence)
        if not claim_tokens:
            continue
        grounded_in_one_sentence = False
        for evidence_sentence in evidence_sentences:
            reference_phrase = re.search(
                r"\b(according to|source:|reference|citation|study by|guidelines from)\b",
                sentence,
                re.IGNORECASE,
            )
            if reference_phrase and reference_phrase.group(0).casefold() not in evidence_sentence.casefold():
                continue
            if _claim_reverses_evidence(sentence, evidence_sentence):
                continue
            evidence_tokens = _canonical_tokens(evidence_sentence)
            shared_claim_tokens = claim_tokens & evidence_tokens
            overlap = len(shared_claim_tokens) / len(claim_tokens)
            if len(shared_claim_tokens) < 2 or overlap < 0.4:
                continue
            if not _numeric_values(sentence).issubset(_numeric_values(evidence_sentence)):
                continue
            grounded_in_one_sentence = True
            break
        if not grounded_in_one_sentence:
            return False
    return factual_sentence_count > 0


def validate_output(
    text: str,
    language: str,
    *,
    has_retrieval_support: bool,
    retrieved_evidence: tuple[str, ...] = (),
    retrieval_conflict: bool = False,
) -> GuardrailDecision:
    answer = text.strip() if isinstance(text, str) else ""
    if retrieval_conflict:
        return GuardrailDecision(False, _message(language, "conflict"), "retrieval_conflict")
    if not answer:
        return GuardrailDecision(False, _message(language, "no_evidence"), "empty_output")
    if not has_retrieval_support:
        return GuardrailDecision(False, _message(language, "no_evidence"), "no_retrieval_support")
    if not retrieved_evidence or not _answer_is_grounded(answer, retrieved_evidence):
        return GuardrailDecision(False, _message(language, "no_evidence"), "unsupported_claim")
    if any(re.search(pattern, answer, re.IGNORECASE) for pattern in UNSAFE_OUTPUT_PATTERNS):
        return GuardrailDecision(False, _message(language, "unsafe_output"), "unsafe_output")
    expected_language = normalize_language_code(language)
    detected_language = _devanagari_language_hint(answer)
    has_devanagari = any("\u0900" <= char <= "\u097f" for char in answer)
    has_kannada = any("\u0c80" <= char <= "\u0cff" for char in answer)
    if (
        (expected_language == "en" and (has_devanagari or has_kannada))
        or (expected_language in {"hi", "mr"} and (not has_devanagari or detected_language not in {None, expected_language}))
        or (expected_language == "kn" and not has_kannada)
    ):
        return GuardrailDecision(False, _message(language, "unsafe_output"), "incorrect_language")
    return GuardrailDecision(True, answer)
