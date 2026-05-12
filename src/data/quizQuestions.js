export const analysisTopicLabels = {
  cld: "CLD basics",
  sarcopenia: "sarcopenia basics",
  diet: "diet and protein",
  exercise: "exercise",
  safety: "safety",
};

export const quizTopicTags = {
  cld: "CLD",
  sarcopenia: "sarcopenia",
  diet: "diet",
  exercise: "exercise",
  safety: "safety",
  scenario: "scenario",
};

const baseQuestionDefinitions = [
  { id: 1, topic: "cld", topicTag: "CLD", analysisTopic: "cld", question: "Chronic liver disease means:", options: ["Short-term liver infection", "Long-term liver damage that progresses over time", "Liver cancer only", "Temporary liver swelling"], correctIndex: 1, explanation: "Chronic liver disease means long-term liver damage that keeps progressing over time." },
  { id: 2, topic: "sarcopenia", topicTag: "sarcopenia", analysisTopic: "sarcopenia", question: "Sarcopenia refers to:", options: ["Weight gain", "Loss of muscle mass and strength", "Bone weakness", "Increase in body fat"], correctIndex: 1, explanation: "Sarcopenia means loss of muscle mass and muscle strength." },
  { id: 3, topic: "cld", topicTag: "CLD", analysisTopic: "cld", question: "Patients with liver disease may develop sarcopenia because:", options: ["Liver affects digestion and protein metabolism", "They drink excess water", "They sleep more", "They take medicines"], correctIndex: 0, explanation: "Liver disease can affect digestion and protein metabolism, which may lead to muscle loss." },
  { id: 4, topic: "sarcopenia", topicTag: "sarcopenia", analysisTopic: "sarcopenia", question: "A common symptom of sarcopenia is:", options: ["Severe headache", "Muscle weakness and tiredness", "Chest pain", "Skin rash"], correctIndex: 1, explanation: "Muscle weakness and tiredness are common signs of sarcopenia." },
  { id: 5, topic: "sarcopenia", topicTag: "sarcopenia", analysisTopic: "sarcopenia", question: "Sarcopenia in CLD patients:", options: ["Has no health impact", "Can increase risk of falls and complications", "Occurs only in elderly", "Is always permanent"], correctIndex: 1, explanation: "Sarcopenia can increase the risk of falls and other complications in CLD patients." },
  { id: 6, topic: "sarcopenia", topicTag: "sarcopenia", analysisTopic: "sarcopenia", question: "Early identification of sarcopenia helps in:", options: ["Avoiding hospital visits", "Improving strength and quality of life", "Stopping all medications", "Avoiding food intake"], correctIndex: 1, explanation: "Finding sarcopenia early can help improve strength and quality of life." },
  { id: 7, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "Protein is important for CLD patients with sarcopenia because it:", options: ["Increases fat", "Builds and maintains muscles", "Causes liver damage", "Increases swelling"], correctIndex: 1, explanation: "Protein helps build and maintain muscles." },
  { id: 8, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "Which food is a good protein source?", options: ["White rice only", "Dal and eggs", "Sugar", "Tea"], correctIndex: 1, explanation: "Dal and eggs are good protein sources." },
  { id: 9, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "If a patient eats very little protein, it may lead to:", options: ["Muscle improvement", "Further muscle loss", "Better digestion", "Increased energy"], correctIndex: 1, explanation: "Too little protein may lead to further muscle loss." },
  { id: 10, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "Small frequent meals are advised because they:", options: ["Reduce muscle breakdown", "Increase hunger", "Cause nausea", "Delay digestion"], correctIndex: 0, explanation: "Small frequent meals can help reduce muscle breakdown." },
  { id: 11, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "A bedtime snack is recommended to:", options: ["Prevent muscle loss overnight", "Increase blood sugar only", "Reduce appetite", "Cause sleep problems"], correctIndex: 0, explanation: "A bedtime snack can help prevent muscle loss during the night." },
  { id: 12, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "Which of the following is safer for a CLD patient?", options: ["Skipping meals", "Balanced diet with adequate protein", "Fasting daily", "Only liquid diet"], correctIndex: 1, explanation: "A balanced diet with enough protein is safer for a CLD patient." },
  { id: 13, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "If a patient asks the AI tool, “Can I eat dal every day?”, the correct response is:", options: ["Dal is harmful", "Dal is a good protein source when taken as advised", "Dal should be avoided always", "Only fruits should be eaten"], correctIndex: 1, explanation: "Dal can be a good protein source when taken as advised." },
  { id: 14, topic: "diet", topicTag: "diet", analysisTopic: "diet", question: "Salt restriction is important mainly to prevent:", options: ["Muscle growth", "Fluid accumulation (ascites)", "Weight gain", "Liver healing"], correctIndex: 1, explanation: "Salt restriction is mainly used to help prevent fluid accumulation such as ascites." },
  { id: 15, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "Exercise for patients with sarcopenia should be:", options: ["Avoided completely", "Light to moderate and regular", "Very heavy daily", "Only bed rest"], correctIndex: 1, explanation: "Exercise should be light to moderate and done regularly." },
  { id: 16, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "Resistance exercises help by:", options: ["Increasing fat", "Improving muscle strength", "Causing injury", "Increasing swelling"], correctIndex: 1, explanation: "Resistance exercises help improve muscle strength." },
  { id: 17, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "Walking is useful because it:", options: ["Has no benefit", "Improves endurance and muscle function", "Causes breathlessness", "Increases liver damage"], correctIndex: 1, explanation: "Walking can improve endurance and muscle function." },
  { id: 18, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "Sudden heavy exercise may:", options: ["Be safe for all", "Increase risk of injury", "Improve liver function instantly", "Reduce weakness"], correctIndex: 1, explanation: "Sudden heavy exercise may increase the risk of injury." },
  { id: 19, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "Rest and activity balance is important to:", options: ["Avoid muscle use", "Prevent fatigue and muscle loss", "Increase weakness", "Avoid sleep"], correctIndex: 1, explanation: "A balance of rest and activity helps prevent fatigue and muscle loss." },
  { id: 20, topic: "exercise", topicTag: "exercise", analysisTopic: "exercise", question: "If a patient feels dizzy during exercise, they should:", options: ["Continue exercising", "Stop and inform the nurse/doctor", "Ignore it", "Increase speed"], correctIndex: 1, explanation: "If dizziness happens during exercise, the patient should stop and inform the nurse or doctor." },
  { id: 21, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "AI educational tools are mainly used to:", options: ["Replace doctors", "Support patient education and understanding", "Prescribe medicines", "Diagnose disease"], correctIndex: 1, explanation: "AI educational tools are used to support patient education and understanding." },
  { id: 22, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "Nurse involvement in AI education helps to:", options: ["Reduce learning", "Ensure safety and clarity", "Avoid patient interaction", "Delay care"], correctIndex: 1, explanation: "Nurse involvement helps ensure safety and clarity." },
  { id: 23, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "If the AI gives information you do not understand, you should:", options: ["Ignore it", "Ask the nurse for clarification", "Stop using the tool", "Guess the meaning"], correctIndex: 1, explanation: "If the patient does not understand the AI answer, they should ask the nurse for clarification." },
  { id: 24, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "AI tools should NOT be used for:", options: ["Health education", "Diet guidance", "Changing medicines without consultation", "Answering general questions"], correctIndex: 2, explanation: "AI tools should not be used for changing medicines without consultation." },
  { id: 25, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "Asking questions during learning helps patients to:", options: ["Become confused", "Understand and remember better", "Waste time", "Increase fear"], correctIndex: 1, explanation: "Asking questions helps patients understand and remember better." },
  { id: 26, topic: "safety", topicTag: "safety", analysisTopic: "safety", question: "Following diet and exercise advice can:", options: ["Worsen sarcopenia", "Improve strength and daily functioning", "Increase hospital stay", "Stop liver disease completely"], correctIndex: 1, explanation: "Following diet and exercise advice can improve strength and daily functioning." },
  { id: 27, topic: "scenario", topicTag: "scenario", analysisTopic: "diet", question: "A patient asks, “I feel weak even after eating.” The correct action is:", options: ["Stop eating", "Ask AI/nurse about protein intake and exercise", "Skip meals", "Rest only"], correctIndex: 1, explanation: "If a patient feels weak even after eating, they should ask the AI or nurse about protein intake and exercise." },
  { id: 28, topic: "scenario", topicTag: "scenario", analysisTopic: "exercise", question: "If a patient is unsure about exercise safety, they should:", options: ["Avoid all activity", "Ask the nurse-guided AI tool for advice", "Copy others", "Start heavy exercise"], correctIndex: 1, explanation: "If the patient is unsure about exercise safety, they should ask the nurse-guided AI tool for advice." },
  { id: 29, topic: "scenario", topicTag: "scenario", analysisTopic: "exercise", question: "A CLD patient wants to improve muscle strength. The best combination is:", options: ["Medicines only", "Protein intake + exercise + education", "Rest only", "Fasting"], correctIndex: 1, explanation: "The best combination is protein intake, exercise, and education together." },
  { id: 30, topic: "scenario", topicTag: "scenario", analysisTopic: "safety", question: "Interactive learning improves outcomes because it:", options: ["Limits questions", "Allows personalized understanding and engagement", "Replaces nurses", "Provides fixed information only"], correctIndex: 1, explanation: "Interactive learning improves outcomes because it allows personalized understanding and engagement." },
];

const localizedText = {
  hi: {
    1: { question: "क्रॉनिक लिवर डिजीज का मतलब है:", options: ["कम समय का लिवर संक्रमण", "लंबे समय तक बढ़ने वाली लिवर की क्षति", "केवल लिवर कैंसर", "अस्थायी लिवर सूजन"] },
    2: { question: "सारकोपीनिया का मतलब है:", options: ["वजन बढ़ना", "मांसपेशियों की मात्रा और शक्ति कम होना", "हड्डियों की कमजोरी", "शरीर में चर्बी बढ़ना"] },
    3: { question: "लिवर रोग वाले मरीजों में सारकोपीनिया हो सकता है क्योंकि:", options: ["लिवर पाचन और प्रोटीन मेटाबॉलिज्म को प्रभावित करता है", "वे बहुत अधिक पानी पीते हैं", "वे अधिक सोते हैं", "वे दवाएँ लेते हैं"] },
    4: { question: "सारकोपीनिया का एक सामान्य लक्षण है:", options: ["तेज सिरदर्द", "मांसपेशियों की कमजोरी और थकान", "छाती में दर्द", "त्वचा पर दाने"] },
    5: { question: "CLD मरीजों में सारकोपीनिया:", options: ["स्वास्थ्य पर कोई असर नहीं करता", "गिरने और जटिलताओं का खतरा बढ़ा सकता है", "केवल बुजुर्गों में होता है", "हमेशा स्थायी होता है"] },
    6: { question: "सारकोपीनिया की जल्दी पहचान से मदद मिलती है:", options: ["अस्पताल जाने से बचने में", "ताकत और जीवन की गुणवत्ता सुधारने में", "सभी दवाएँ बंद करने में", "भोजन से बचने में"] },
    7: { question: "CLD और सारकोपीनिया वाले मरीजों के लिए प्रोटीन ज़रूरी है क्योंकि यह:", options: ["चर्बी बढ़ाता है", "मांसपेशियाँ बनाता और संभालता है", "लिवर को नुकसान पहुँचाता है", "सूजन बढ़ाता है"] },
    8: { question: "इनमें से कौन सा भोजन अच्छा प्रोटीन स्रोत है?", options: ["केवल सफेद चावल", "दाल और अंडे", "चीनी", "चाय"] },
    9: { question: "यदि मरीज बहुत कम प्रोटीन खाता है, तो इससे हो सकता है:", options: ["मांसपेशियाँ सुधरें", "मांसपेशियाँ और कम हों", "पाचन बेहतर हो", "ऊर्जा बढ़े"] },
    10: { question: "बार-बार थोड़ी मात्रा में भोजन करने की सलाह इसलिए दी जाती है क्योंकि इससे:", options: ["मांसपेशियों का टूटना कम होता है", "भूख बढ़ती है", "मतली होती है", "पाचन देर से होता है"] },
    11: { question: "सोने से पहले हल्का नाश्ता लेने की सलाह इसलिए दी जाती है ताकि:", options: ["रात में मांसपेशियों की कमी रोकी जा सके", "सिर्फ शुगर बढ़े", "भूख कम हो", "नींद की समस्या हो"] },
    12: { question: "CLD मरीज के लिए इनमें से क्या अधिक सुरक्षित है?", options: ["भोजन छोड़ना", "पर्याप्त प्रोटीन वाला संतुलित आहार", "रोज़ उपवास करना", "केवल तरल आहार"] },
    13: { question: "यदि मरीज AI से पूछे, “क्या मैं रोज़ दाल खा सकता हूँ?”, तो सही उत्तर है:", options: ["दाल हानिकारक है", "दाल सही सलाह के अनुसार अच्छा प्रोटीन स्रोत है", "दाल हमेशा नहीं खानी चाहिए", "केवल फल खाने चाहिए"] },
    14: { question: "नमक कम करना मुख्य रूप से किससे बचाने के लिए ज़रूरी है?", options: ["मांसपेशियों की वृद्धि", "शरीर में पानी भरना (ऐसाइटिस)", "वजन बढ़ना", "लिवर ठीक होना"] },
    15: { question: "सारकोपीनिया वाले मरीजों के लिए व्यायाम कैसा होना चाहिए?", options: ["पूरी तरह बंद", "हल्का से मध्यम और नियमित", "बहुत भारी रोज़", "केवल बिस्तर पर आराम"] },
    16: { question: "रेसिस्टेंस एक्सरसाइज से मदद मिलती है क्योंकि यह:", options: ["चर्बी बढ़ाती है", "मांसपेशियों की ताकत बढ़ाती है", "चोट पहुँचाती है", "सूजन बढ़ाती है"] },
    17: { question: "चलना फायदेमंद है क्योंकि यह:", options: ["कोई फायदा नहीं देता", "सहनशक्ति और मांसपेशी कार्य बेहतर करता है", "साँस फूलाता है", "लिवर को और नुकसान पहुँचाता है"] },
    18: { question: "अचानक भारी व्यायाम करने से:", options: ["सबके लिए सुरक्षित रहता है", "चोट का खतरा बढ़ सकता है", "लिवर तुरंत ठीक होता है", "कमजोरी कम होती है"] },
    19: { question: "आराम और गतिविधि के बीच संतुलन ज़रूरी है ताकि:", options: ["मांसपेशियों का उपयोग न हो", "थकान और मांसपेशियों की कमी रोकी जा सके", "कमजोरी बढ़े", "नींद से बचा जा सके"] },
    20: { question: "यदि व्यायाम करते समय चक्कर आए, तो मरीज को क्या करना चाहिए?", options: ["व्यायाम जारी रखना", "रुककर नर्स/डॉक्टर को बताना", "इसे अनदेखा करना", "गति बढ़ाना"] },
    21: { question: "AI शैक्षिक उपकरणों का मुख्य उपयोग है:", options: ["डॉक्टरों की जगह लेना", "मरीज को शिक्षा और समझ में मदद देना", "दवाएँ लिखना", "रोग का निदान करना"] },
    22: { question: "AI शिक्षा में नर्स की भागीदारी से मदद मिलती है:", options: ["सीखना कम होता है", "सुरक्षा और स्पष्टता सुनिश्चित होती है", "मरीज से बात कम होती है", "देखभाल में देरी होती है"] },
    23: { question: "यदि AI ऐसी जानकारी दे जिसे आप समझ न पाएं, तो आपको:", options: ["अनदेखा करना चाहिए", "नर्स से समझाना चाहिए", "उपकरण का उपयोग बंद करना चाहिए", "अंदाज़ा लगाना चाहिए"] },
    24: { question: "AI उपकरणों का उपयोग किसके लिए नहीं होना चाहिए?", options: ["स्वास्थ्य शिक्षा", "आहार संबंधी मार्गदर्शन", "बिना सलाह दवा बदलना", "सामान्य प्रश्नों के उत्तर देना"] },
    25: { question: "सीखते समय प्रश्न पूछने से मरीज को मदद मिलती है:", options: ["उलझन बढ़ती है", "समझने और याद रखने में", "समय बर्बाद होता है", "डर बढ़ता है"] },
    26: { question: "आहार और व्यायाम की सलाह मानने से:", options: ["सारकोपीनिया बढ़ेगा", "ताकत और रोज़मर्रा के काम बेहतर हो सकते हैं", "अस्पताल में भर्ती बढ़ेगी", "लिवर रोग पूरी तरह रुक जाएगा"] },
    27: { question: "मरीज पूछता है, “खाने के बाद भी मुझे कमजोरी लगती है।” सही कदम है:", options: ["खाना बंद कर दें", "AI/नर्स से प्रोटीन और व्यायाम के बारे में पूछें", "भोजन छोड़ दें", "केवल आराम करें"] },
    28: { question: "यदि मरीज को व्यायाम की सुरक्षा को लेकर संदेह हो, तो उसे:", options: ["सारी गतिविधि बंद कर देनी चाहिए", "नर्स-गाइडेड AI से सलाह लेनी चाहिए", "दूसरों की नकल करनी चाहिए", "भारी व्यायाम शुरू कर देना चाहिए"] },
    29: { question: "CLD मरीज मांसपेशियों की ताकत बढ़ाना चाहता है। सबसे अच्छा संयोजन है:", options: ["केवल दवाएँ", "प्रोटीन + व्यायाम + शिक्षा", "केवल आराम", "उपवास"] },
    30: { question: "इंटरएक्टिव लर्निंग से बेहतर परिणाम इसलिए मिलते हैं क्योंकि यह:", options: ["प्रश्न कम करती है", "व्यक्तिगत समझ और सहभागिता देती है", "नर्सों की जगह लेती है", "केवल तय जानकारी देती है"] },
  },
  kn: {
    1: { question: "ಕ್ರಾನಿಕ್ ಲಿವರ್ ಡಿಸೀಸ್ ಎಂದರೆ:", options: ["ಕಡಿಮೆ ಅವಧಿಯ ಲಿವರ್ ಸೋಂಕು", "ಕಾಲಕ್ರಮೇಣ ಮುಂದುವರಿಯುವ ದೀರ್ಘಕಾಲದ ಲಿವರ್ ಹಾನಿ", "ಮಾತ್ರ ಲಿವರ್ ಕ್ಯಾನ್ಸರ್", "ತಾತ್ಕಾಲಿಕ ಲಿವರ್ ಊತ"] },
    2: { question: "ಸಾರ್ಕೋಪೀನಿಯಾ ಎಂದರೆ:", options: ["ತೂಕ ಹೆಚ್ಚಾಗುವುದು", "ಸ್ನಾಯುಗಳ ಪ್ರಮಾಣ ಮತ್ತು ಶಕ್ತಿ ಕಡಿಮೆಯಾಗುವುದು", "ಎಲುಬಿನ ದುರ್ಬಲತೆ", "ದೇಹದಲ್ಲಿ ಕೊಬ್ಬು ಹೆಚ್ಚಾಗುವುದು"] },
    3: { question: "ಲಿವರ್ ರೋಗ ಇರುವ ರೋಗಿಗಳಿಗೆ ಸಾರ್ಕೋಪೀನಿಯಾ ಉಂಟಾಗಬಹುದು ಏಕೆಂದರೆ:", options: ["ಲಿವರ್ ಜೀರ್ಣಕ್ರಿಯೆ ಮತ್ತು ಪ್ರೋಟೀನ್ ವಿನಿಮಯವನ್ನು ಪ್ರಭಾವಿಸುತ್ತದೆ", "ಅವರು ತುಂಬಾ ಹೆಚ್ಚು ನೀರು ಕುಡಿಯುತ್ತಾರೆ", "ಅವರು ಹೆಚ್ಚು ನಿದ್ರೆ ಮಾಡುತ್ತಾರೆ", "ಅವರು ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ"] },
    4: { question: "ಸಾರ್ಕೋಪೀನಿಯಾದ ಸಾಮಾನ್ಯ ಲಕ್ಷಣ ಯಾವುದು?", options: ["ತೀವ್ರ ತಲೆನೋವು", "ಸ್ನಾಯುಗಳ ದುರ್ಬಲತೆ ಮತ್ತು ದಣಿವು", "ಛಾತಿ ನೋವು", "ಚರ್ಮದ ಮಚ್ಚೆ"] },
    5: { question: "CLD ರೋಗಿಗಳಲ್ಲಿ ಸಾರ್ಕೋಪೀನಿಯಾ:", options: ["ಆರೋಗ್ಯದ ಮೇಲೆ ಯಾವ ಪ್ರಭಾವವೂ ಬೀರುವುದಿಲ್ಲ", "ಬೀಳುವಿಕೆ ಮತ್ತು ಸಮಸ್ಯೆಗಳ ಅಪಾಯವನ್ನು ಹೆಚ್ಚಿಸುತ್ತದೆ", "ಮಾತ್ರ ವಯೋವೃದ್ಧರಲ್ಲಿ ಉಂಟಾಗುತ್ತದೆ", "ಯಾವಾಗಲೂ ಶಾಶ್ವತವಾಗಿರುತ್ತದೆ"] },
    6: { question: "ಸಾರ್ಕೋಪೀನಿಯಾದ ಆರಂಭಿಕ ಗುರುತು ಹಿಡಿಯುವುದರಿಂದ ಸಹಾಯವಾಗುವುದು:", options: ["ಆಸ್ಪತ್ರೆ ಭೇಟಿಗಳನ್ನು ತಪ್ಪಿಸುವುದು", "ಶಕ್ತಿ ಮತ್ತು ಜೀವನಮಟ್ಟ ಸುಧಾರಿಸುವುದು", "ಎಲ್ಲಾ ಔಷಧಿಗಳನ್ನು ನಿಲ್ಲಿಸುವುದು", "ಆಹಾರ ಸೇವನೆ ತಪ್ಪಿಸುವುದು"] },
    7: { question: "CLD ಮತ್ತು ಸಾರ್ಕೋಪೀನಿಯಾ ಇರುವ ರೋಗಿಗಳಿಗೆ ಪ್ರೋಟೀನ್ ಮುಖ್ಯ ಏಕೆಂದರೆ ಅದು:", options: ["ಕೊಬ್ಬನ್ನು ಹೆಚ್ಚಿಸುತ್ತದೆ", "ಸ್ನಾಯುಗಳನ್ನು ನಿರ್ಮಿಸಿ ಉಳಿಸುತ್ತದೆ", "ಲಿವರ್‌ಗೆ ಹಾನಿ ಉಂಟುಮಾಡುತ್ತದೆ", "ಊತ ಹೆಚ್ಚಿಸುತ್ತದೆ"] },
    8: { question: "ಈ ಕೆಳಗಿನ ಯಾವುದು ಒಳ್ಳೆಯ ಪ್ರೋಟೀನ್ ಮೂಲ?", options: ["ಮಾತ್ರ ಬಿಳಿ ಅಕ್ಕಿ", "ಬೇಳೆ ಮತ್ತು ಮೊಟ್ಟೆ", "ಸಕ್ಕರೆ", "ಚಹಾ"] },
    9: { question: "ರೋಗಿ ತುಂಬಾ ಕಡಿಮೆ ಪ್ರೋಟೀನ್ ತಿಂದರೆ, ಅದರಿಂದ ಏನು ಆಗಬಹುದು?", options: ["ಸ್ನಾಯುಗಳು ಸುಧಾರಿಸುತ್ತವೆ", "ಸ್ನಾಯುಗಳು ಇನ್ನಷ್ಟು ಕಡಿಮೆಯಾಗುತ್ತವೆ", "ಜೀರ್ಣಕ್ರಿಯೆ ಉತ್ತಮವಾಗುತ್ತದೆ", "ಶಕ್ತಿ ಹೆಚ್ಚಾಗುತ್ತದೆ"] },
    10: { question: "ಸಣ್ಣ ಪ್ರಮಾಣದಲ್ಲಿ ಆಗಾಗ್ಗೆ ಆಹಾರ ತಿನ್ನುವಂತೆ ಏಕೆ ಹೇಳಲಾಗುತ್ತದೆ?", options: ["ಸ್ನಾಯುಗಳ ಕುಸಿತವನ್ನು ಕಡಿಮೆ ಮಾಡುತ್ತದೆ", "ಹಸಿವು ಹೆಚ್ಚಿಸುತ್ತದೆ", "ಅಸಹನೆ ಉಂಟುಮಾಡುತ್ತದೆ", "ಜೀರ್ಣಕ್ರಿಯೆ ವಿಳಂಬವಾಗುತ್ತದೆ"] },
    11: { question: "ಮಲಗುವ ಮುನ್ನ ತಿಂಡಿ ತೆಗೆದುಕೊಳ್ಳುವಂತೆ ಹೇಳುವುದರಿಂದ ಉದ್ದೇಶ ಏನು?", options: ["ರಾತ್ರಿಯಲ್ಲಿ ಸ್ನಾಯು ನಷ್ಟ ತಪ್ಪಿಸಲು", "ಮಾತ್ರ ರಕ್ತದಲ್ಲಿನ ಸಕ್ಕರೆ ಹೆಚ್ಚಿಸಲು", "ಹಸಿವು ಕಡಿಮೆ ಮಾಡಲು", "ನಿದ್ರಾ ಸಮಸ್ಯೆ ಉಂಟುಮಾಡಲು"] },
    12: { question: "CLD ರೋಗಿಗೆ ಈ ಕೆಳಗಿನ ಯಾವುದು ಹೆಚ್ಚು ಸುರಕ್ಷಿತ?", options: ["ಆಹಾರ ಬಿಟ್ಟುಕೊಳ್ಳುವುದು", "ಸಾಕಷ್ಟು ಪ್ರೋಟೀನ್ ಇರುವ ಸಮತೋಲನ ಆಹಾರ", "ಪ್ರತಿದಿನ ಉಪವಾಸ", "ಮಾತ್ರ ದ್ರವ ಆಹಾರ"] },
    13: { question: "ರೋಗಿ AI ಸಾಧನವನ್ನು ಕೇಳಿದರೆ, “ನಾನು ಪ್ರತಿದಿನ ಬೇಳೆ ತಿನ್ನಬಹುದೇ?”, ಸರಿಯಾದ ಉತ್ತರ ಯಾವುದು?", options: ["ಬೇಳೆ ಹಾನಿಕಾರಕ", "ಸರಿಯಾದ ಸಲಹೆಯಂತೆ ಬೇಳೆ ಒಳ್ಳೆಯ ಪ್ರೋಟೀನ್ ಮೂಲ", "ಬೇಳೆಯನ್ನು ಯಾವಾಗಲೂ ತಪ್ಪಿಸಬೇಕು", "ಮಾತ್ರ ಹಣ್ಣು ತಿನ್ನಬೇಕು"] },
    14: { question: "ಉಪ್ಪನ್ನು ಕಡಿಮೆ ಮಾಡುವುದು ಮುಖ್ಯವಾಗಿ ಯಾವುದನ್ನು ತಪ್ಪಿಸಲು?", options: ["ಸ್ನಾಯು ಬೆಳವಣಿಗೆ", "ದೇಹದಲ್ಲಿ ದ್ರವ ಸಂಗ್ರಹ (ಅಸೈಟಿಸ್)", "ತೂಕ ಹೆಚ್ಚಾಗುವುದು", "ಲಿವರ್ ಗುಣಮುಖವಾಗುವುದು"] },
    15: { question: "ಸಾರ್ಕೋಪೀನಿಯಾ ಇರುವ ರೋಗಿಗಳಿಗಾಗಿ ವ್ಯಾಯಾಮ ಹೇಗಿರಬೇಕು?", options: ["ಪೂರ್ಣವಾಗಿ ತಪ್ಪಿಸಬೇಕು", "ಲಘು ಅಥವಾ ಮಧ್ಯಮ ಮತ್ತು ನಿಯಮಿತ", "ತುಂಬಾ ಭಾರಿ ಪ್ರತಿದಿನ", "ಮಾತ್ರ ಹಾಸಿಗೆ ವಿಶ್ರಾಂತಿ"] },
    16: { question: "ರೆಸಿಸ್ಟನ್ಸ್ ವ್ಯಾಯಾಮ ಸಹಾಯ ಮಾಡುವುದೇನು?", options: ["ಕೊಬ್ಬು ಹೆಚ್ಚಿಸುತ್ತದೆ", "ಸ್ನಾಯುಗಳ ಶಕ್ತಿ ಹೆಚ್ಚಿಸುತ್ತದೆ", "ಗಾಯ ಉಂಟುಮಾಡುತ್ತದೆ", "ಊತ ಹೆಚ್ಚಿಸುತ್ತದೆ"] },
    17: { question: "ನಡೆಯುವುದು ಉಪಯುಕ್ತ ಏಕೆಂದರೆ ಅದು:", options: ["ಯಾವ ಪ್ರಯೋಜನವೂ ಇಲ್ಲ", "ಸಹನಶಕ್ತಿ ಮತ್ತು ಸ್ನಾಯು ಕಾರ್ಯ ಸುಧಾರಿಸುತ್ತದೆ", "ಉಸಿರಾಟದ ತೊಂದರೆ ಉಂಟುಮಾಡುತ್ತದೆ", "ಲಿವರ್‌ಗೆ ಇನ್ನಷ್ಟು ಹಾನಿ ಉಂಟುಮಾಡುತ್ತದೆ"] },
    18: { question: "ಅಕಸ್ಮಾತ್ ಭಾರೀ ವ್ಯಾಯಾಮ ಮಾಡುವುದರಿಂದ ಏನು ಆಗಬಹುದು?", options: ["ಎಲ್ಲರಿಗೂ ಸುರಕ್ಷಿತ", "ಗಾಯದ ಅಪಾಯ ಹೆಚ್ಚಾಗಬಹುದು", "ಲಿವರ್ ತಕ್ಷಣ ಸುಧಾರಿಸುತ್ತದೆ", "ದುರ್ಬಲತೆ ಕಡಿಮೆಯಾಗುತ್ತದೆ"] },
    19: { question: "ವಿಶ್ರಾಂತಿ ಮತ್ತು ಚಟುವಟಿಕೆಯ ನಡುವೆ ಸಮತೋಲನ ಏಕೆ ಮುಖ್ಯ?", options: ["ಸ್ನಾಯು ಬಳಕೆಯನ್ನು ತಪ್ಪಿಸಲು", "ದಣಿವು ಮತ್ತು ಸ್ನಾಯು ನಷ್ಟ ತಪ್ಪಿಸಲು", "ದುರ್ಬಲತೆ ಹೆಚ್ಚಿಸಲು", "ನಿದ್ರೆ ತಪ್ಪಿಸಲು"] },
    20: { question: "ವ್ಯಾಯಾಮ ಮಾಡುವಾಗ ರೋಗಿಗೆ ತಲೆಸುತ್ತು ಬಂದರೆ ಅವರು ಏನು ಮಾಡಬೇಕು?", options: ["ವ್ಯಾಯಾಮ ಮುಂದುವರಿಸಬೇಕು", "ನಿಲ್ಲಿಸಿ ನರ್ಸ್/ಡಾಕ್ಟರ್‌ಗೆ ತಿಳಿಸಬೇಕು", "ಅವಗಣಿಸಬೇಕು", "ವೇಗ ಹೆಚ್ಚಿಸಬೇಕು"] },
    21: { question: "AI ಶೈಕ್ಷಣಿಕ ಸಾಧನಗಳನ್ನು ಮುಖ್ಯವಾಗಿ ಬಳಸುವುದು:", options: ["ವೈದ್ಯರ ಬದಲು", "ರೋಗಿ ಶಿಕ್ಷಣ ಮತ್ತು ಅರಿವಿಗೆ ಸಹಾಯ ಮಾಡಲು", "ಔಷಧಿ ನೀಡಲು", "ರೋಗ ಪತ್ತೆಹಚ್ಚಲು"] },
    22: { question: "AI ಶಿಕ್ಷಣದಲ್ಲಿ ನರ್ಸ್ ಭಾಗವಹಿಸುವುದರಿಂದ ಏನು ಪ್ರಯೋಜನ?", options: ["ಕಲಿಕೆ ಕಡಿಮೆಯಾಗುತ್ತದೆ", "ಭದ್ರತೆ ಮತ್ತು ಸ್ಪಷ್ಟತೆ ಖಚಿತವಾಗುತ್ತದೆ", "ರೋಗಿಯೊಂದಿಗೆ ಸಂವಹನ ಕಡಿಮೆಯಾಗುತ್ತದೆ", "ಪರಿಚರ್ಯೆಗೆ ವಿಳಂಬವಾಗುತ್ತದೆ"] },
    23: { question: "AI ನೀಡಿದ ಮಾಹಿತಿ ಅರ್ಥವಾಗದಿದ್ದರೆ ನೀವು ಏನು ಮಾಡಬೇಕು?", options: ["ಅದನ್ನು ಕಡೆಗಣಿಸಬೇಕು", "ನರ್ಸ್‌ನಿಂದ ವಿವರ ಕೇಳಬೇಕು", "ಸಾಧನ ಬಳಕೆ ನಿಲ್ಲಿಸಬೇಕು", "ಅಂದಾಜು ಮಾಡಬೇಕು"] },
    24: { question: "AI ಸಾಧನಗಳನ್ನು ಯಾವ ಕೆಲಸಕ್ಕೆ ಬಳಸಬಾರದು?", options: ["ಆರೋಗ್ಯ ಶಿಕ್ಷಣ", "ಆಹಾರ ಮಾರ್ಗದರ್ಶನ", "ಸಲಹೆಯಿಲ್ಲದೆ ಔಷಧಿ ಬದಲಿಸುವುದು", "ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸುವುದು"] },
    25: { question: "ಕಲಿಕೆಯ ಸಮಯದಲ್ಲಿ ಪ್ರಶ್ನೆ ಕೇಳುವುದರಿಂದ ರೋಗಿಗೆ ಏನು ಸಹಾಯವಾಗುತ್ತದೆ?", options: ["ಗೊಂದಲ ಹೆಚ್ಚುತ್ತದೆ", "ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಮತ್ತು ನೆನಪಿಡಲು ಸಹಾಯವಾಗುತ್ತದೆ", "ಸಮಯ ವ್ಯರ್ಥವಾಗುತ್ತದೆ", "ಭಯ ಹೆಚ್ಚುತ್ತದೆ"] },
    26: { question: "ಆಹಾರ ಮತ್ತು ವ್ಯಾಯಾಮದ ಸಲಹೆ ಅನುಸರಿಸುವುದರಿಂದ:", options: ["ಸಾರ್ಕೋಪೀನಿಯಾ ಹೆಚ್ಚಾಗುತ್ತದೆ", "ಶಕ್ತಿ ಮತ್ತು ದಿನನಿತ್ಯದ ಕಾರ್ಯಕ್ಷಮತೆ ಸುಧಾರಿಸಬಹುದು", "ಆಸ್ಪತ್ರೆ ಉಳಿಯುವ ದಿನಗಳು ಹೆಚ್ಚಾಗುತ್ತವೆ", "ಲಿವರ್ ರೋಗ ಸಂಪೂರ್ಣವಾಗಿ ನಿಲ್ಲುತ್ತದೆ"] },
    27: { question: "ರೋಗಿ ಕೇಳುತ್ತಾನೆ, “ತಿನ್ನಿದ ಮೇಲೂ ನನಗೆ ದುರ್ಬಲತೆ ಇದೆ.” ಸರಿಯಾದ ಕ್ರಮವೇನು?", options: ["ತಿನ್ನುವುದನ್ನು ನಿಲ್ಲಿಸಬೇಕು", "AI/ನರ್ಸ್‌ರನ್ನು ಪ್ರೋಟೀನ್ ಮತ್ತು ವ್ಯಾಯಾಮ ಬಗ್ಗೆ ಕೇಳಬೇಕು", "ಆಹಾರ ಬಿಟ್ಟುಬಿಡಬೇಕು", "ಮಾತ್ರ ವಿಶ್ರಾಂತಿ ಮಾಡಬೇಕು"] },
    28: { question: "ರೋಗಿಗೆ ವ್ಯಾಯಾಮ ಸುರಕ್ಷಿತವೇ ಎಂಬ ಅನುಮಾನ ಇದ್ದರೆ ಅವರು ಏನು ಮಾಡಬೇಕು?", options: ["ಎಲ್ಲಾ ಚಟುವಟಿಕೆಗಳನ್ನು ನಿಲ್ಲಿಸಬೇಕು", "ನರ್ಸ್ ಮಾರ್ಗದರ್ಶನ ಇರುವ AI ಯಿಂದ ಸಲಹೆ ಕೇಳಬೇಕು", "ಇತರರನ್ನು ಅನುಸರಿಸಬೇಕು", "ಭಾರೀ ವ್ಯಾಯಾಮ ಪ್ರಾರಂಭಿಸಬೇಕು"] },
    29: { question: "CLD ರೋಗಿ ಸ್ನಾಯುಗಳ ಶಕ್ತಿ ಹೆಚ್ಚಿಸಿಕೊಳ್ಳಲು ಬಯಸಿದರೆ ಅತ್ಯುತ್ತಮ ಸಂಯೋಜನೆ ಯಾವುದು?", options: ["ಮಾತ್ರ ಔಷಧಿ", "ಪ್ರೋಟೀನ್ + ವ್ಯಾಯಾಮ + ಶಿಕ್ಷಣ", "ಮಾತ್ರ ವಿಶ್ರಾಂತಿ", "ಉಪವಾಸ"] },
    30: { question: "ಇಂಟರಾಕ್ಟಿವ್ ಕಲಿಕೆಯಿಂದ ಉತ್ತಮ ಫಲಿತಾಂಶ ಸಿಗುವುದು ಏಕೆಂದರೆ ಅದು:", options: ["ಪ್ರಶ್ನೆಗಳನ್ನು ಕಡಿಮೆ ಮಾಡುತ್ತದೆ", "ವೈಯಕ್ತಿಕ ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವಿಕೆ ಮತ್ತು ಭಾಗವಹಿಸುವಿಕೆ ನೀಡುತ್ತದೆ", "ನರ್ಸ್‌ಗಳ ಬದಲು ಕೆಲಸ ಮಾಡುತ್ತದೆ", "ಮಾತ್ರ ನಿಗದಿತ ಮಾಹಿತಿ ನೀಡುತ್ತದೆ"] },
  },
  mr: {
    1: { question: "क्रॉनिक लिव्हर डिजीज म्हणजे:", options: ["अल्पकालीन लिव्हर इन्फेक्शन", "काळानुसार वाढत जाणारे दीर्घकालीन लिव्हर नुकसान", "फक्त लिव्हर कॅन्सर", "तात्पुरती लिव्हर सूज"] },
    2: { question: "सार्कोपेनिया म्हणजे:", options: ["वजन वाढणे", "स्नायूंचे प्रमाण आणि ताकद कमी होणे", "हाडांची कमजोरी", "शरीरातील चरबी वाढणे"] },
    3: { question: "लिव्हर रोग असलेल्या रुग्णांना सार्कोपेनिया होऊ शकतो कारण:", options: ["लिव्हर पचन आणि प्रथिनांच्या चयापचयावर परिणाम करतो", "ते खूप जास्त पाणी पितात", "ते जास्त झोपतात", "ते औषधे घेतात"] },
    4: { question: "सार्कोपेनियाचे एक सामान्य लक्षण आहे:", options: ["तीव्र डोकेदुखी", "स्नायूंची कमजोरी आणि थकवा", "छातीत वेदना", "त्वचेवर पुरळ"] },
    5: { question: "CLD रुग्णांमध्ये सार्कोपेनिया:", options: ["आरोग्यावर काही परिणाम करत नाही", "पडणे आणि गुंतागुंत यांचा धोका वाढवू शकतो", "फक्त वृद्धांमध्ये होतो", "नेहमी कायमचा असतो"] },
    6: { question: "सार्कोपेनियाची लवकर ओळख झाल्यास मदत होते:", options: ["रुग्णालय भेट टाळण्यास", "ताकद आणि जीवनमान सुधारण्यास", "सर्व औषधे बंद करण्यास", "अन्न टाळण्यास"] },
    7: { question: "CLD आणि सार्कोपेनिया असलेल्या रुग्णांसाठी प्रथिने महत्त्वाची आहेत कारण ती:", options: ["चरबी वाढवतात", "स्नायू बनवतात आणि टिकवतात", "लिव्हरचे नुकसान करतात", "सूज वाढवतात"] },
    8: { question: "खालीलपैकी कोणता पदार्थ चांगला प्रथिनांचा स्रोत आहे?", options: ["फक्त पांढरा भात", "डाळ आणि अंडी", "साखर", "चहा"] },
    9: { question: "रुग्णाने खूप कमी प्रथिने खाल्ली तर यामुळे होऊ शकते:", options: ["स्नायू सुधारतील", "स्नायू आणखी कमी होतील", "पचन सुधारेल", "ऊर्जा वाढेल"] },
    10: { question: "थोड्या-थोड्या वेळाने खाण्याचा सल्ला का दिला जातो?", options: ["स्नायू तुटणे कमी होते", "भूक वाढते", "मळमळ होते", "पचन उशिरा होते"] },
    11: { question: "झोपण्यापूर्वी खाऊ घ्यायचा सल्ला यासाठी दिला जातो की:", options: ["रात्री स्नायू कमी होणे टाळता येते", "फक्त साखर वाढते", "भूक कमी होते", "झोपेची अडचण होते"] },
    12: { question: "CLD रुग्णासाठी खालीलपैकी काय जास्त सुरक्षित आहे?", options: ["जेवण टाळणे", "पुरेशी प्रथिने असलेला संतुलित आहार", "दररोज उपवास", "फक्त द्रव आहार"] },
    13: { question: "रुग्णाने AI साधनाला विचारले, “मी रोज डाळ खाऊ शकतो का?”, तर योग्य उत्तर आहे:", options: ["डाळ हानिकारक आहे", "योग्य सल्ल्यानुसार डाळ चांगला प्रथिनांचा स्रोत आहे", "डाळ नेहमी टाळावी", "फक्त फळे खावीत"] },
    14: { question: "मीठ कमी करण्याचा मुख्य उद्देश काय आहे?", options: ["स्नायू वाढ", "शरीरात पाणी साठणे (असाइटिस) टाळणे", "वजन वाढणे", "लिव्हर बरा होणे"] },
    15: { question: "सार्कोपेनिया असलेल्या रुग्णांसाठी व्यायाम कसा असावा?", options: ["पूर्णपणे टाळावा", "हलका ते मध्यम आणि नियमित", "दररोज खूप जड", "फक्त बेड रेस्ट"] },
    16: { question: "रेसिस्टन्स एक्सरसाइजमुळे काय फायदा होतो?", options: ["चरबी वाढते", "स्नायूंची ताकद वाढते", "इजा होते", "सूज वाढते"] },
    17: { question: "चालणे उपयुक्त आहे कारण ते:", options: ["काहीही फायदा देत नाही", "सहनशक्ती आणि स्नायू कार्य सुधारते", "श्वास लागतो", "लिव्हरला अधिक नुकसान करते"] },
    18: { question: "अचानक जड व्यायाम केल्यास काय होऊ शकते?", options: ["सर्वांसाठी सुरक्षित असते", "इजा होण्याचा धोका वाढतो", "लिव्हर लगेच सुधारतो", "कमजोरी कमी होते"] },
    19: { question: "विश्रांती आणि हालचालीतील समतोल का महत्त्वाचा आहे?", options: ["स्नायूंचा वापर टाळण्यासाठी", "थकवा आणि स्नायू कमी होणे टाळण्यासाठी", "कमजोरी वाढवण्यासाठी", "झोप टाळण्यासाठी"] },
    20: { question: "व्यायाम करताना रुग्णाला चक्कर आली तर त्याने काय करावे?", options: ["व्यायाम सुरू ठेवावा", "थांबून नर्स/डॉक्टरांना सांगावे", "दुर्लक्ष करावे", "वेग वाढवावा"] },
    21: { question: "AI शैक्षणिक साधनांचा मुख्य उपयोग काय आहे?", options: ["डॉक्टरांची जागा घेणे", "रुग्ण शिक्षण आणि समज वाढवणे", "औषधे लिहून देणे", "रोगाचे निदान करणे"] },
    22: { question: "AI शिक्षणात नर्सचा सहभाग का महत्त्वाचा आहे?", options: ["शिकणे कमी होते", "सुरक्षितता आणि स्पष्टता सुनिश्चित होते", "रुग्णाशी संवाद कमी होतो", "उपचारात उशीर होतो"] },
    23: { question: "AI ने दिलेली माहिती समजली नाही तर तुम्ही काय करावे?", options: ["दुर्लक्ष करावे", "नर्सकडून स्पष्टीकरण घ्यावे", "साधन वापरणे थांबवावे", "अंदाज लावावा"] },
    24: { question: "AI साधनांचा उपयोग कशासाठी करू नये?", options: ["आरोग्य शिक्षण", "आहार मार्गदर्शन", "सल्ल्याविना औषधे बदलणे", "सामान्य प्रश्नांची उत्तरे देणे"] },
    25: { question: "शिकताना प्रश्न विचारल्याने रुग्णाला काय मदत होते?", options: ["गोंधळ वाढतो", "समज आणि लक्षात ठेवणे सुधारते", "वेळ वाया जातो", "भीती वाढते"] },
    26: { question: "आहार आणि व्यायामाचा सल्ला पाळल्याने:", options: ["सार्कोपेनिया वाढतो", "ताकद आणि दैनंदिन कार्यक्षमता सुधारू शकते", "रुग्णालयात राहण्याचा काळ वाढतो", "लिव्हर रोग पूर्णपणे थांबतो"] },
    27: { question: "रुग्ण विचारतो, “खाल्ल्यानंतरही मला अशक्त वाटते.” योग्य कृती काय?", options: ["खाणे बंद करावे", "AI/नर्सकडे प्रथिने आणि व्यायामाबद्दल विचारावे", "जेवण टाळावे", "फक्त विश्रांती घ्यावी"] },
    28: { question: "रुग्णाला व्यायाम सुरक्षित आहे का याची खात्री नसल्यास त्याने काय करावे?", options: ["सर्व हालचाली टाळाव्यात", "नर्स-मार्गदर्शित AI कडून सल्ला घ्यावा", "इतरांची नक्कल करावी", "जड व्यायाम सुरू करावा"] },
    29: { question: "CLD रुग्णाला स्नायूंची ताकद वाढवायची असेल तर सर्वोत्तम संयोजन कोणते?", options: ["फक्त औषधे", "प्रथिने + व्यायाम + शिक्षण", "फक्त विश्रांती", "उपवास"] },
    30: { question: "इंटरअॅक्टिव्ह शिक्षणामुळे चांगले परिणाम मिळतात कारण ते:", options: ["प्रश्न कमी करते", "वैयक्तिक समज आणि सहभाग देते", "नर्सची जागा घेते", "फक्त ठरलेली माहिती देते"] },
  },
};

function getLocalizedQuestion(question, language = "en") {
  if (language === "en") return question;
  const localized = localizedText[language]?.[question.id];

  if (!localized) return question;

  return {
    ...question,
    question: localized.question || question.question,
    options: localized.options || question.options,
    explanation: localized.explanation || question.explanation,
  };
}

export function getPreTestQuestionBank(language = "en") {
  return baseQuestionDefinitions.map((question) => getLocalizedQuestion(question, language));
}

export function getPostTestQuestionBank(language = "en") {
  return baseQuestionDefinitions.map((question) => getLocalizedQuestion(question, language));
}

export const preTestQuestionBank = getPreTestQuestionBank("en");
export const postTestQuestionBank = getPostTestQuestionBank("en");
export const TOTAL_QUIZ_QUESTIONS = baseQuestionDefinitions.length;

function shuffleArray(items) {
  const nextItems = [...items];

  for (let index = nextItems.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [nextItems[index], nextItems[swapIndex]] = [nextItems[swapIndex], nextItems[index]];
  }

  return nextItems;
}

export function prepareQuizQuestions(questionBank) {
  return questionBank.map((question) => {
    const shuffledOptions = shuffleArray(
      question.options.map((option, index) => ({
        text: option,
        originalIndex: index,
        isCorrect: index === question.correctIndex,
      }))
    );

    return {
      ...question,
      originalOptions: [...question.options],
      originalCorrectIndex: question.correctIndex,
      options: shuffledOptions.map((option) => option.text),
      shuffledOptions,
      correctIndex: shuffledOptions.findIndex((option) => option.isCorrect),
    };
  });
}

function getAnswerDetails(answer, question) {
  const defaultCorrectIndex =
    typeof question.originalCorrectIndex === "number" ? question.originalCorrectIndex : question.correctIndex;
  const defaultOptions = question.originalOptions || question.options || [];
  const correctText = defaultOptions[defaultCorrectIndex] || "";

  if (typeof answer === "number") {
    return {
      selectedIndex: answer,
      selectedText: question.options?.[answer] || "",
      originalIndex: answer,
      isCorrect: answer === question.correctIndex,
      correctIndex: defaultCorrectIndex,
      correctText,
    };
  }

  if (answer && typeof answer === "object") {
    const selectedIndex =
      typeof answer.selectedIndex === "number" ? answer.selectedIndex : null;
    const selectedText =
      typeof answer.selectedText === "string"
        ? answer.selectedText
        : selectedIndex !== null
          ? question.options?.[selectedIndex] || ""
          : "";
    const originalIndex =
      typeof answer.originalIndex === "number"
        ? answer.originalIndex
        : selectedText
          ? defaultOptions.findIndex((option) => option === selectedText)
          : null;
    const isCorrect =
      typeof answer.isCorrect === "boolean"
        ? answer.isCorrect
        : originalIndex !== null
          ? originalIndex === defaultCorrectIndex
          : selectedText === correctText;

    return {
      selectedIndex,
      selectedText,
      originalIndex,
      isCorrect,
      correctIndex: defaultCorrectIndex,
      correctText,
    };
  }

  return {
    selectedIndex: null,
    selectedText: "",
    originalIndex: null,
    isCorrect: false,
    correctIndex: defaultCorrectIndex,
    correctText,
  };
}

export function calculateScore(answers, questionBank) {
  return questionBank.reduce((score, item) => {
    return getAnswerDetails(answers[item.id], item).isCorrect ? score + 1 : score;
  }, 0);
}

export function getScoreInterpretation(score) {
  const band = getScoreBand(score);

  if (band === "notAvailable") return "Not available";
  if (band === "poor") return "Poor";
  if (band === "average") return "Average";
  return "Good";
}

export function getScoreFeedback(score) {
  const band = getScoreBand(score);

  if (band === "notAvailable") return "Please complete the quiz to see your feedback.";
  if (band === "poor") return "Your score shows you need more support. We will review the main topics step by step.";
  if (band === "average") return "You have average knowledge. A few topics still need more attention.";
  return "You have a good level of knowledge. Keep reviewing the key safety and self-care points.";
}

export function getScoreBand(score) {
  if (score === null || score === undefined) return "notAvailable";
  if (score <= 10) return "poor";
  if (score <= 20) return "average";
  return "good";
}

export function evaluateQuiz(answers, questionBank) {
  const mistakesByTopic = { cld: 0, sarcopenia: 0, diet: 0, exercise: 0, safety: 0 };
  const topicTotals = { cld: 0, sarcopenia: 0, diet: 0, exercise: 0, safety: 0 };
  const correctByTopic = { cld: 0, sarcopenia: 0, diet: 0, exercise: 0, safety: 0 };
  const wrongAnswers = [];

  questionBank.forEach((item) => {
    const picked = answers[item.id];
    const answerDetails = getAnswerDetails(picked, item);
    const isCorrect = answerDetails.isCorrect;
    const analysisTopic = item.analysisTopic || item.topic;

    topicTotals[analysisTopic] += 1;

    if (isCorrect) {
      correctByTopic[analysisTopic] += 1;
      return;
    }

    mistakesByTopic[analysisTopic] += 1;
    wrongAnswers.push({
      id: item.id,
      topic: item.topic,
      topicTag: item.topicTag,
      analysisTopic,
      selectedIndex:
        typeof answerDetails.originalIndex === "number" ? answerDetails.originalIndex : null,
      selectedAnswer: answerDetails.selectedText || "",
      correctIndex: answerDetails.correctIndex,
      correctAnswer: answerDetails.correctText || "",
    });
  });

  const rankedWeakTopics = Object.entries(mistakesByTopic)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([topic, mistakes]) => ({
      topic,
      label: analysisTopicLabels[topic] || topic,
      mistakes,
      totalQuestions: topicTotals[topic],
      correctAnswers: correctByTopic[topic],
    }));

  const score = calculateScore(answers, questionBank);

  return {
    total: questionBank.length,
    score,
    scoreBand: getScoreBand(score),
    scoreInterpretation: getScoreInterpretation(score),
    feedbackMessage: getScoreFeedback(score),
    wrongAnswers,
    mistakesByTopic,
    correctByTopic,
    topicTotals,
    rankedWeakTopics,
    weakTopics: rankedWeakTopics.map((item) => item.topic),
  };
}

export function getReviewItems(summary, language = "en", mode = "pre") {
  const questionBank = mode === "post" ? getPostTestQuestionBank(language) : getPreTestQuestionBank(language);
  const questionMap = Object.fromEntries(questionBank.map((item) => [item.id, item]));

  return (summary?.wrongAnswers || []).map((item) => {
    const question = questionMap[item.id];
    return {
      ...item,
      question: question?.question || "",
      correctAnswer:
        item.correctAnswer ||
        (typeof item.correctIndex === "number" ? question?.options?.[item.correctIndex] || "" : ""),
      selectedAnswer:
        item.selectedAnswer ||
        (typeof item.selectedIndex === "number" ? question?.options?.[item.selectedIndex] || "" : ""),
      explanation: language === "en" ? question?.explanation || "" : "",
    };
  });
}
