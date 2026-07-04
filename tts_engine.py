"""
tts_engine.py — AI Voice Assistant for Bank Kiosk

Supports 6 Indian languages:
  en (English)   — pyttsx3 offline  ✓
  ta (Tamil)     — gTTS online      ✓
  hi (Hindi)     — gTTS online      ✓
  te (Telugu)    — gTTS online      ✓
  kn (Kannada)   — gTTS online      ✓
  ml (Malayalam) — gTTS online      ✓

Speak calls are always non-blocking (background thread).
Falls back to English pyttsx3 if gTTS / internet fails.
"""

import os
import threading
import tempfile
import queue

# ─────────────────────────────────────────────────────────
# Voice script translations (key phrases in all languages)
# ─────────────────────────────────────────────────────────

VOICE_SCRIPTS = {
    # ── Welcome & Language ──────────────────────────────
    "welcome": {
        "en": "Welcome to the Auto Bank Form Filling System. Please tap to begin.",
        "ta": "தானியங்கி வங்கி படிவ நிரப்பும் அமைப்பிற்கு வரவேற்கிறோம். தொடங்க தட்டவும்.",
        "hi": "ऑटो बैंक फॉर्म भरने प्रणाली में आपका स्वागत है। शुरू करने के लिए टैप करें।",
        "te": "ఆటో బ్యాంక్ ఫారం నింపే వ్యవస్థకు స్వాగతం. ప్రారంభించడానికి నొక్కండి.",
        "kn": "ಆಟೋ ಬ್ಯಾಂಕ್ ಫಾರ್ಮ್ ಭರ್ತಿ ವ್ಯವಸ್ಥೆಗೆ ಸ್ವಾಗತ. ಪ್ರಾರಂಭಿಸಲು ಟ್ಯಾಪ್ ಮಾಡಿ.",
        "ml": "ഓട്ടോ ബാങ്ക് ഫോം ഫില്ലിംഗ് സിസ്റ്റത്തിലേക്ക് സ്വാഗതം. ആരംഭിക്കാൻ ടാപ്പ് ചെയ്യുക.",
    },
    "language_selected": {
        "en": "English selected. Welcome! Please insert the five rupee coin to continue.",
        "ta": "தமிழ் தேர்ந்தெடுக்கப்பட்டது. வரவேற்கிறோம்! தொடர ஐந்து ரூபாய் நாணயத்தை செருகவும்.",
        "hi": "हिंदी चुनी गई। स्वागत है! जारी रखने के लिए पाँच रुपये का सिक्का डालें।",
        "te": "తెలుగు ఎంచుకోబడింది. స్వాగతం! కొనసాగించడానికి ఐదు రూపాయల నాణేన్ని చొప్పించండి.",
        "kn": "ಕನ್ನಡ ಆಯ್ಕೆಯಾಗಿದೆ. ಸ್ವಾಗತ! ಮುಂದುವರಿಯಲು ಐದು ರೂಪಾಯಿ ನಾಣ್ಯ ಹಾಕಿ.",
        "ml": "മലയാളം തിരഞ്ഞെടുത്തു. സ്വാഗതം! തുടരാൻ അഞ്ച് രൂപ നാണയം ഇടുക.",
    },

    # ── Coin Authentication ─────────────────────────────
    "coin_insert": {
        "en": "Please insert the five rupee coin to continue.",
        "ta": "தொடர ஐந்து ரூபாய் நாணயத்தை செருகவும்.",
        "hi": "जारी रखने के लिए कृपया पाँच रुपये का सिक्का डालें।",
        "te": "కొనసాగించడానికి దయచేసి ఐదు రూపాయల నాణేన్ని చొప్పించండి.",
        "kn": "ಮುಂದುವರಿಯಲು ದಯವಿಟ್ಟು ಐದು ರೂಪಾಯಿ ನಾಣ್ಯ ಹಾಕಿ.",
        "ml": "തുടരാൻ ദയവായി അഞ്ച് രൂപ നാണയം ഇടുക.",
    },
    "coin_accepted": {
        "en": "Coin accepted. You may continue.",
        "ta": "நாணயம் ஏற்கப்பட்டது. தொடரலாம்.",
        "hi": "सिक्का स्वीकार किया गया। आप जारी रख सकते हैं।",
        "te": "నాణెం అంగీకరించబడింది. మీరు కొనసాగవచ్చు.",
        "kn": "ನಾಣ್ಯ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ನೀವು ಮುಂದುವರಿಯಬಹುದು.",
        "ml": "നാണയം സ്വീകരിച്ചു. നിങ്ങൾ തുടരാം.",
    },
    "coin_error": {
        "en": "Invalid coin. Please insert a five rupee coin.",
        "ta": "தவறான நாணயம். ஐந்து ரூபாய் நாணயத்தை செருகவும்.",
        "hi": "अमान्य सिक्का। कृपया पाँच रुपये का सिक्का डालें।",
        "te": "చెల్లని నాణెం. ఐదు రూపాయల నాణేన్ని చొప్పించండి.",
        "kn": "ಅಮಾನ್ಯ ನಾಣ್ಯ. ಐದು ರೂಪಾಯಿ ನಾಣ್ಯ ಹಾಕಿ.",
        "ml": "അസാധുവായ നാണയം. അഞ്ച് രൂപ നാണയം ഇടുക.",
    },

    # ── Service & Category Selection ────────────────────
    "select_category": {
        "en": "Please select Cash Services or Non-Cash Services.",
        "ta": "ரொக்க சேவைகள் அல்லது ரொக்கமில்லா சேவைகளை தேர்ந்தெடுக்கவும்.",
        "hi": "कृपया नकद सेवाएँ या गैर-नकद सेवाएँ चुनें।",
        "te": "దయచేసి నగదు సేవలు లేదా నగదు రహిత సేవలను ఎంచుకోండి.",
        "kn": "ನಗದು ಸೇವೆಗಳು ಅಥವಾ ನಗದು ರಹಿತ ಸೇವೆಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಿ.",
        "ml": "ക്യാഷ് സേവനങ്ങൾ അല്ലെങ്കിൽ ക്യാഷ് ഇതര സേവനങ്ങൾ തിരഞ്ഞെടുക്കുക.",
    },
    "select_service": {
        "en": "Please select the banking service you require by touching the picture.",
        "ta": "படத்தை தொட்டு தேவையான வங்கி சேவையை தேர்ந்தெடுக்கவும்.",
        "hi": "चित्र को छूकर आवश्यक बैंकिंग सेवा चुनें।",
        "te": "చిత్రాన్ని తాకడం ద్వారా అవసరమైన బ్యాంకింగ్ సేవను ఎంచుకోండి.",
        "kn": "ಚಿತ್ರ ಮುಟ್ಟಿ ಬೇಕಾದ ಬ್ಯಾಂಕಿಂಗ್ ಸೇವೆ ಆಯ್ಕೆ ಮಾಡಿ.",
        "ml": "ചിത്രം തൊട്ട് ആവശ്യമായ ബാങ്കിംഗ് സേവനം തിരഞ്ഞെടുക്കുക.",
    },

    # ── Document Tracking ───────────────────────────────
    "scan_documents": {
        "en": "Please scan each required document. Touch a document card to begin scanning.",
        "ta": "ஒவ்வொரு ஆவணத்தையும் ஸ்கேன் செய்யவும். ஸ்கேன் செய்ய ஆவண அட்டையை தொடவும்.",
        "hi": "कृपया प्रत्येक आवश्यक दस्तावेज़ स्कैन करें। स्कैन करने के लिए दस्तावेज़ कार्ड छुएं।",
        "te": "దయచేసి ప్రతి అవసరమైన పత్రాన్ని స్కాన్ చేయండి. స్కాన్ చేయడానికి పత్రం కార్డ్ తాకండి.",
        "kn": "ದಯವಿಟ್ಟು ಪ್ರತಿ ಅಗತ್ಯ ದಾಖಲೆ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ. ಸ್ಕ್ಯಾನ್ ಮಾಡಲು ದಾಖಲೆ ಕಾರ್ಡ್ ಮುಟ್ಟಿ.",
        "ml": "ദയവായി ഓരോ ആവശ്യമായ രേഖയും സ്കാൻ ചെയ്യുക. സ്കാൻ ചെയ്യാൻ ഡോക്യുമെന്റ് കാർഡ് തൊടുക.",
    },
    "all_docs_done": {
        "en": "All documents verified. You may proceed to fill the form.",
        "ta": "அனைத்து ஆவணங்களும் சரிபார்க்கப்பட்டன. படிவம் நிரப்ப தொடரலாம்.",
        "hi": "सभी दस्तावेज़ सत्यापित हुए। फॉर्म भरने के लिए आगे बढ़ें।",
        "te": "అన్ని పత్రాలు ధృవీకరించబడ్డాయి. ఫారం నింపడానికి కొనసాగవచ్చు.",
        "kn": "ಎಲ್ಲ ದಾಖಲೆಗಳು ಪರಿಶೀಲಿಸಲಾಗಿದೆ. ಫಾರ್ಮ್ ಭರ್ತಿ ಮಾಡಲು ಮುಂದುವರಿಯಬಹುದು.",
        "ml": "എല്ലാ രേഖകളും പരിശോധിച്ചു. ഫോം പൂരിപ്പിക്കാൻ തുടരാം.",
    },
    "select_document": {
        "en": "Please select your document type and place it on the scanner.",
        "ta": "உங்கள் ஆவண வகையை தேர்ந்தெடுத்து ஸ்கேனரில் வைக்கவும்.",
        "hi": "कृपया अपना दस्तावेज़ प्रकार चुनें और स्कैनर पर रखें।",
        "te": "దయచేసి మీ పత్రం రకాన్ని ఎంచుకుని స్కానర్‌పై ఉంచండి.",
        "kn": "ನಿಮ್ಮ ದಾಖಲೆ ಪ್ರಕಾರ ಆಯ್ಕೆ ಮಾಡಿ ಮತ್ತು ಸ್ಕ್ಯಾನರ್‌ನಲ್ಲಿ ಇರಿಸಿ.",
        "ml": "നിങ്ങളുടെ രേഖ തരം തിരഞ്ഞെടുത്ത് സ്കാനറിൽ വയ്ക്കുക.",
    },

    # ── Per-Document Prompts ────────────────────────────
    "doc_prompt_aadhaar": {
        "en": "Please scan your Aadhaar Card.",
        "ta": "உங்கள் ஆதார் அட்டையை ஸ்கேன் செய்யவும்.",
        "hi": "कृपया अपना आधार कार्ड स्कैन करें।",
        "te": "దయచేసి మీ ఆధార్ కార్డ్ స్కాన్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆಧಾರ್ ಕಾರ್ಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ ആധാർ കാർഡ് സ്കാൻ ചെയ്യുക.",
    },
    "doc_prompt_pan": {
        "en": "Please scan your PAN Card.",
        "ta": "உங்கள் பான் கார்டை ஸ்கேன் செய்யவும்.",
        "hi": "कृपया अपना PAN कार्ड स्कैन करें।",
        "te": "దయచేసి మీ PAN కార్డ్ స్కాన్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ PAN ಕಾರ್ಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ PAN കാർഡ് സ്കാൻ ചെയ്യുക.",
    },
    "doc_prompt_passbook": {
        "en": "Please scan your Bank Passbook.",
        "ta": "உங்கள் வங்கி பாஸ்புக்கை ஸ்கேன் செய்யவும்.",
        "hi": "कृपया अपनी बैंक पासबुक स्कैन करें।",
        "te": "దయచేసి మీ బ్యాంక్ పాస్‌బుక్ స్కాన్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ ബാങ്ക് പാസ്ബുക്ക് സ്കാൻ ചെയ്യുക.",
    },
    "doc_prompt_photo": {
        "en": "Please upload your passport-size photograph.",
        "ta": "உங்கள் பாஸ்போர்ட் அளவு புகைப்படத்தை பதிவேற்றவும்.",
        "hi": "कृपया अपनी पासपोर्ट-साइज़ फोटो अपलोड करें।",
        "te": "దయచేసి మీ పాస్‌పోర్ట్ సైజు ఫోటో అప్‌లోడ్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪಾಸ್‌ಪೋರ್ಟ್ ಗಾತ್ರದ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ പാസ്‌പോർട്ട് ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.",
    },
    "doc_prompt_address_proof": {
        "en": "Please upload your address proof document.",
        "ta": "உங்கள் முகவரி சான்று ஆவணத்தை பதிவேற்றவும்.",
        "hi": "कृपया अपना पता प्रमाण दस्तावेज़ अपलोड करें।",
        "te": "దయచేసి మీ చిరునామా రుజువు పత్రాన్ని అప్‌లోడ్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿಳಾಸ ಸಾಕ್ಷ್ಯ ದಾಖಲೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ വിലാസ തെളിവ് രേഖ അപ്‌ലോഡ് ചെയ്യുക.",
    },
    "doc_prompt_voter_id": {
        "en": "Please upload your Voter ID, Passport, or Driving Licence.",
        "ta": "உங்கள் வாக்காளர் அடையாள அட்டை, பாஸ்போர்ட் அல்லது ஓட்டுநர் உரிமத்தை பதிவேற்றவும்.",
        "hi": "कृपया अपना वोटर आईडी, पासपोर्ट, या ड्राइविंग लाइसेंस अपलोड करें।",
        "te": "దయచేసి మీ వోటర్ ID, పాస్‌పోర్ట్ లేదా డ్రైవింగ్ లైసెన్స్ అప్‌లోడ్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ವೋಟರ್ ಐಡಿ, ಪಾಸ್‌ಪೋರ್ಟ್ ಅಥವಾ ಡ್ರೈವಿಂಗ್ ಲೈಸೆನ್ಸ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ വോട്ടർ ഐഡി, പാസ്‌പോർട്ട് അല്ലെങ്കിൽ ഡ്രൈവിംഗ് ലൈസൻസ് അപ്‌ലോഡ് ചെയ്യുക.",
    },
    "doc_prompt_beneficiary": {
        "en": "Please provide the beneficiary account details.",
        "ta": "பயனாளியின் கணக்கு விவரங்களை வழங்கவும்.",
        "hi": "कृपया लाभार्थी खाता विवरण प्रदान करें।",
        "te": "దయచేసి లబ్ధిదారుని ఖాతా వివరాలు అందించండి.",
        "kn": "ದಯವಿಟ್ಟು ಫಲಾನುಭವಿ ಖಾತೆ ವಿವರ ನೀಡಿ.",
        "ml": "ദയവായി ഗുണഭോക്തൃ അക്കൗണ്ട് വിവരങ്ങൾ നൽകുക.",
    },
    "doc_prompt_cheque": {
        "en": "Please place the cheque on the scanner.",
        "ta": "காசோலையை ஸ்கேனரில் வைக்கவும்.",
        "hi": "कृपया चेक को स्कैनर पर रखें।",
        "te": "దయచేసి చెక్‌ను స్కానర్‌పై ఉంచండి.",
        "kn": "ದಯವಿಟ್ಟು ಚೆಕ್ ಸ್ಕ್ಯಾನರ್‌ನಲ್ಲಿ ಇರಿಸಿ.",
        "ml": "ദയവായി ചെക്ക് സ്കാനറിൽ വയ്ക്കുക.",
    },
    "doc_prompt_debit_card": {
        "en": "Please show your Debit Card.",
        "ta": "உங்கள் டெபிட் கார்டை காட்டவும்.",
        "hi": "कृपया अपना डेबिट कार्ड दिखाएं।",
        "te": "దయచేసి మీ డెబిట్ కార్డ్ చూపించండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಡೆಬಿಟ್ ಕಾರ್ಡ್ ತೋರಿಸಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ ഡെബിറ്റ് കാർഡ് കാണിക്കുക.",
    },
    "doc_prompt_nominee_id": {
        "en": "Please upload the nominee's identity proof.",
        "ta": "நியமிக்கப்பட்டவரின் அடையாள ஆவணத்தை பதிவேற்றவும்.",
        "hi": "कृपया नामांकित व्यक्ति का पहचान प्रमाण अपलोड करें।",
        "te": "దయచేసి నామినీ యొక్క గుర్తింపు రుజువు అప్‌లోడ్ చేయండి.",
        "kn": "ದಯವಿಟ್ಟು ನಾಮಿನಿಯ ಗುರುತಿನ ದಾಖಲೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "ml": "ദയവായി നോമിനിയുടെ ഐഡന്റിറ്റി പ്രൂഫ് അപ്‌ലോഡ് ചെയ്യുക.",
    },

    # ── Scanning ────────────────────────────────────────
    "place_blank_form": {
        "en": "Please place the blank form into the machine.",
        "ta": "வெற்று படிவத்தை இயந்திரத்தில் வைக்கவும்.",
        "hi": "कृपया खाली फॉर्म को मशीन में रखें।",
        "te": "దయచేసి ఖాళీ ఫారాన్ని యంత్రంలో ఉంచండి.",
        "kn": "ದಯವಿಟ್ಟು ಖಾಲಿ ಫಾರ್ಮ್ ಅನ್ನು ಯಂತ್ರದಲ್ಲಿ ಇರಿಸಿ.",
        "ml": "ദയവായി ഒഴിഞ്ഞ ഫോം മെഷീനിൽ വയ്ക്കുക.",
    },
    "scanning": {
        "en": "Scanning your document. Please wait.",
        "ta": "உங்கள் ஆவணம் ஸ்கேன் செய்யப்படுகிறது. காத்திருக்கவும்.",
        "hi": "आपका दस्तावेज़ स्कैन हो रहा है। कृपया प्रतीक्षा करें।",
        "te": "మీ పత్రం స్కాన్ అవుతోంది. దయచేసి వేచి ఉండండి.",
        "kn": "ನಿಮ್ಮ ದಾಖಲೆ ಸ್ಕ್ಯಾನ್ ಆಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಕಾಯಿರಿ.",
        "ml": "നിങ്ങളുടെ രേഖ സ്കാൻ ചെയ്യുന്നു. ദയവായി കാത്തിരിക്കുക.",
    },
    "scan_done": {
        "en": "Document verified successfully. Green tick added.",
        "ta": "ஆவணம் வெற்றிகரமாக சரிபார்க்கப்பட்டது. பச்சை டிக் சேர்க்கப்பட்டது.",
        "hi": "दस्तावेज़ सफलतापूर्वक सत्यापित हुआ। हरी टिक जोड़ी गई।",
        "te": "పత్రం విజయవంతంగా ధృవీకరించబడింది. పచ్చని టిక్ జోడించబడింది.",
        "kn": "ದಾಖಲೆ ಯಶಸ್ವಿಯಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ. ಹಸಿರು ಟಿಕ್ ಸೇರಿಸಲಾಗಿದೆ.",
        "ml": "രേഖ വിജയകരമായി പരിശോധിച്ചു. ഗ്രീൻ ടിക്ക് ചേർത്തു.",
    },

    # ── Review & Confirmation ───────────────────────────
    "enter_missing": {
        "en": "Some information is missing. Please enter the required details.",
        "ta": "சில தகவல்கள் காணவில்லை. தேவையான விவரங்களை உள்ளிடவும்.",
        "hi": "कुछ जानकारी नहीं मिली। कृपया आवश्यक विवरण दर्ज करें।",
        "te": "కొంత సమాచారం లేదు. దయచేసి అవసరమైన వివరాలు నమోదు చేయండి.",
        "kn": "ಕೆಲವು ಮಾಹಿತಿ ಇಲ್ಲ. ಅಗತ್ಯ ವಿವರ ನಮೂದಿಸಿ.",
        "ml": "ചില വിവരങ്ങൾ ഇല്ല. ആവശ്യമായ വിവരങ്ങൾ നൽകുക.",
    },
    "form_complete": {
        "en": "Your form is complete. Please confirm to submit.",
        "ta": "உங்கள் படிவம் முடிந்தது. சமர்ப்பிக்க உறுதிப்படுத்தவும்.",
        "hi": "आपका फॉर्म पूरा हो गया। जमा करने के लिए पुष्टि करें।",
        "te": "మీ ఫారం పూర్తయింది. సమర్పించడానికి నిర్ధారించండి.",
        "kn": "ನಿಮ್ಮ ಫಾರ್ಮ್ ಪೂರ್ಣಗೊಂಡಿದೆ. ಸಲ್ಲಿಸಲು ದೃಢೀಕರಿಸಿ.",
        "ml": "നിങ്ങളുടെ ഫോം പൂർത്തിയായി. സമർപ്പിക്കാൻ സ്ഥിരീകരിക്കുക.",
    },

    "sign_reminder": {
        "en": "Important! After printing, please sign in the signature box at the bottom of the form before submitting it at the bank counter.",
        "ta": "முக்கியம்! அச்சிட்ட பின்பு, படிவத்தின் கீழே உள்ள கையொப்ப பெட்டியில் கையெழுத்திட்டு வங்கி கவுண்டரில் சமர்ப்பிக்கவும்.",
        "hi": "ध्यान दें! प्रिंट करने के बाद, फॉर्म के नीचे दिए गए हस्ताक्षर बॉक्स में हस्ताक्षर करें और फिर बैंक काउंटर पर जमा करें।",
        "te": "ముఖ్యం! ప్రింట్ చేసిన తర్వాత, ఫారం దిగువన ఉన్న సంతకం పెట్టెలో సంతకం చేసి బ్యాంక్ కౌంటర్‌లో సమర్పించండి.",
        "kn": "ಮುಖ್ಯ! ಮುದ್ರಿಸಿದ ನಂತರ, ಫಾರ್ಮ್‌ನ ಕೆಳಭಾಗದಲ್ಲಿರುವ ಸಹಿ ಬಾಕ್ಸ್‌ನಲ್ಲಿ ಸಹಿ ಹಾಕಿ, ನಂತರ ಬ್ಯಾಂಕ್ ಕೌಂಟರ್‌ನಲ್ಲಿ ಸಲ್ಲಿಸಿ.",
        "ml": "പ്രധാനം! പ്രിന്റ് ചെയ്തതിനു ശേഷം, ഫോമിന്റെ താഴെ ഉള്ള ഒപ്പ് ബോക്സിൽ ഒപ്പിട്ട് ബാങ്ക് കൗണ്ടറിൽ സമർപ്പിക്കുക.",
    },



    # ── Completion ──────────────────────────────────────
    "application_complete": {
        "en": "Application completed successfully. Please collect your printed form and submit it at the bank counter. Thank you.",
        "ta": "விண்ணப்பம் வெற்றிகரமாக முடிந்தது. அச்சிட்ட படிவத்தை எடுத்து வங்கி கவுண்டரில் சமர்ப்பிக்கவும். நன்றி.",
        "hi": "आवेदन सफलतापूर्वक पूरा हुआ। अपना प्रिंटेड फॉर्म लेकर बैंक काउंटर पर जमा करें। धन्यवाद।",
        "te": "దరఖాస్తు విజయవంతంగా పూర్తయింది. ముద్రించిన ఫారం తీసుకొని బ్యాంక్ కౌంటర్‌లో సమర్పించండి. ధన్యవాదాలు.",
        "kn": "ಅರ್ಜಿ ಯಶಸ್ವಿಯಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ. ಮುದ್ರಿಸಿದ ಫಾರ್ಮ್ ತೆಗೆದುಕೊಂಡು ಬ್ಯಾಂಕ್ ಕೌಂಟರ್‌ನಲ್ಲಿ ಸಲ್ಲಿಸಿ. ಧನ್ಯವಾದ.",
        "ml": "അപേക്ഷ വിജയകരമായി പൂർത്തിയായി. പ്രിന്റ് ചെയ്ത ഫോം ശേഖരിച്ച് ബാങ്ക് കൗണ്ടറിൽ സമർപ്പിക്കുക. നന്ദി.",
    },
    "print_done": {
        "en": "Your form has been printed. Please collect it and submit at the counter. Thank you.",
        "ta": "உங்கள் படிவம் அச்சிடப்பட்டது. அதை சேகரித்து கவுண்டரில் சமர்ப்பிக்கவும். நன்றி.",
        "hi": "आपका फॉर्म प्रिंट हो गया। कृपया इसे लेकर काउंटर पर जमा करें। धन्यवाद।",
        "te": "మీ ఫారం ముద్రించబడింది. దానిని తీసుకొని కౌంటర్‌లో సమర్పించండి. ధన్యవాదాలు.",
        "kn": "ನಿಮ್ಮ ಫಾರ್ಮ್ ಮುದ್ರಿಸಲಾಗಿದೆ. ಅದನ್ನು ತೆಗೆದುಕೊಂಡು ಕೌಂಟರ್‌ನಲ್ಲಿ ಸಲ್ಲಿಸಿ. ಧನ್ಯವಾದ.",
        "ml": "നിങ്ങളുടെ ഫോം പ്രിന്റ് ചെയ്തു. അത് ശേഖരിച്ച് കൗണ്ടറിൽ സമർപ്പിക്കുക. നന്ദി.",
    },
    "error": {
        "en": "An error occurred. Please try again or ask for assistance.",
        "ta": "பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும் அல்லது உதவி கேளுங்கள்.",
        "hi": "एक त्रुटि हुई। कृपया पुनः प्रयास करें या सहायता मांगें।",
        "te": "ఒక లోపం సంభవించింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
        "kn": "ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "ml": "ഒരു പിശക് സംഭവിച്ചു. വീണ്ടും ശ്രമിക്കുക.",
    },
    "payment_request": {
        "en": "Please pay via UPI or cash to print your form.",
        "ta": "உங்கள் படிவத்தை அச்சிட UPI அல்லது ரொக்கம் மூலம் செலுத்தவும்.",
        "hi": "अपना फॉर्म प्रिंट करने के लिए कृपया UPI या नकद द्वारा भुगतान करें।",
        "te": "మీ ఫారాన్ని ముద్రించడానికి దయచేసి UPI లేదా నగదు ద్వారా చెల్లించండి.",
        "kn": "ನಿಮ್ಮ ಫಾರ್ಮ್ ಮುದ್ರಿಸಲು ದಯವಿಟ್ಟು ಯುಪಿಐ ಅಥವಾ ನಗದು ಮೂಲಕ ಪಾವತಿಸಿ.",
        "ml": "നിങ്ങളുടെ ഫോം പ്രിന്റ് ചെയ്യാൻ യുപിഐ അല്ലെങ്കിൽ പണമായി അടയ്ക്കുക.",
    },
    # ── Voice Review ────────────────────────────────────
    "review_start": {
        "en": "Please listen carefully to your details.",
        "ta": "உங்கள் விவரங்களை கவனமாகக் கேளுங்கள்.",
        "hi": "कृपया अपने विवरण ध्यान से सुनें।",
        "te": "దయచేసి మీ వివరాలను జాగ్రత్తగా వినండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಗಮನವಾಗಿ ಆಲಿಸಿ.",
        "ml": "ദയവായി നിങ്ങളുടെ വിവരങ്ങൾ ശ്രദ്ധാപൂർവ്വം ശ്രവിക്കുക.",
    },
    "review_end": {
        "en": "Are all details correct? Please confirm or edit.",
        "ta": "அனைத்து விவரங்களும் சரியா? உறுதிப்படுத்தவும் அல்லது திருத்தவும்.",
        "hi": "क्या सभी विवरण सही हैं? कृपया पुष्टि करें या संपादित करें।",
        "te": "అన్ని వివరాలు సరైనవా? దయచేసి నిర్ధారించండి లేదా సవరించండి.",
        "kn": "ಎಲ್ಲ ವಿವರಗಳು ಸರಿಯಾಗಿವೆಯೇ? ದೃಢೀಕರಿಸಿ ಅಥವಾ ಸಂಪಾದಿಸಿ.",
        "ml": "എല്ലാ വിവരങ്ങളും ശരിയാണോ? ദയവായി സ്ഥിരീകരിക്കുക അല്ലെങ്കിൽ തിരുത്തുക.",
    },

    # ── Scan Error ─────────────────────────────────────
    "scan_error_retry": {
        "en": "Scanning failed. Please place the document again and try.",
        "ta": "ஸ்கேனிங் தோல்வியடைந்தது. ஆவணத்தை மீண்டும் வைத்து முயற்சிக்கவும்.",
        "hi": "स्कैनिंग विफल। कृपया दस्तावेज़ फिर से रखें और प्रयास करें।",
        "te": "స్కానింగ్ విఫలమైంది. దయచేసి పత్రాన్ని మళ్ళీ ఉంచి ప్రయత్నించండి.",
        "kn": "ಸ್ಕ್ಯಾನಿಂಗ್ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ದಾಖಲೆಯನ್ನು ಮತ್ತೆ ಇರಿಸಿ ಪ್ರಯತ್ನಿಸಿ.",
        "ml": "സ്കാനിംഗ് പരാജയപ്പെട്ടു. ദയവായി രേഖ വീണ്ടും വച്ച് ശ്രമിക്കുക.",
    },

    # ── Coin Screen ────────────────────────────────────
    "coin_insert": {
        "en": "Please insert the five rupee coin to continue.",
        "ta": "தொடர ஐந்து ரூபாய் நாணயத்தை செருகவும்.",
        "hi": "जारी रखने के लिए कृपया पाँच रुपये का सिक्का डालें।",
        "te": "కొనసాగించడానికి దయచేసి ఐదు రూపాయల నాణేన్ని చొప్పించండి.",
        "kn": "ಮುಂದುವರಿಯಲು ದಯವಿಟ್ಟು ಐದು ರೂಪಾಯಿ ನಾಣ್ಯ ಹಾಕಿ.",
        "ml": "തുടരാൻ ദയവായി അഞ്ച് രൂപ നാണയം ഇടുക.",
    },
    "coin_accepted": {
        "en": "Payment received successfully. You may now select a service.",
        "ta": "பணம் வெற்றிகரமாக ஏற்கப்பட்டது. இப்போது சேவையைத் தேர்ந்தெடுக்கலாம்.",
        "hi": "भुगतान सफलतापूर्वक प्राप्त हुआ। अब आप एक सेवा चुन सकते हैं।",
        "te": "చెల్లింపు విజయవంతంగా స్వీకరించబడింది. ఇప్పుడు సేవను ఎంచుకోవచ్చు.",
        "kn": "ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಈಗ ಸೇವೆ ಆಯ್ಕೆ ಮಾಡಬಹುದು.",
        "ml": "പേയ്‌മെന്റ് വിജയകരമായി ലഭിച്ചു. ഇപ്പോൾ ഒരു സേവനം തിരഞ്ഞെടുക്കാം.",
    },
    "coin_error": {
        "en": "Invalid coin. Please insert a five rupee coin.",
        "ta": "தவறான நாணயம். ஐந்து ரூபாய் நாணயத்தை செருகவும்.",
        "hi": "अमान्य सिक्का। कृपया पाँच रुपये का सिक्का डालें।",
        "te": "చెల్లని నాణెం. ఐదు రూపాయల నాణేన్ని చొప్పించండి.",
        "kn": "ಅಮಾನ್ಯ ನಾಣ್ಯ. ಐದು ರೂಪಾಯಿ ನಾಣ್ಯ ಹಾಕಿ.",
        "ml": "അസാധുവായ നാണയം. അഞ്ച് രൂപ നാണയം ഇടുക.",
    },

    # ── Denomination Screen ────────────────────────────
    "denom_screen_intro": {
        "en": "Please tap a box to enter how many notes you have.",
        "ta": "உங்களிடம் எத்தனை ரூபாய் நோட்டுகள் உள்ளன என்பதை உள்ளிட பெட்டியைத் தட்டவும்.",
        "hi": "कृपया अपने पास मौजूद नोटों की संख्या दर्ज करने के लिए बॉक्स पर टैप करें।",
        "te": "దయచేసి మీ వద్ద ఎన్ని నోట్లు ఉన్నాయో నమోదు చేయడానికి బాక్స్‌ను నొక్కండి.",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬಳಿ ಇರುವ ನೋಟುಗಳ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಲು ಬಾಕ್ಸ್ ಟ್ಯಾಪ್ ಮಾಡಿ.",
        "ml": "നിങ്ങളുടെ കൈവശമുള്ള നോട്ടുകളുടെ എണ്ണം നൽകാൻ ദയവായി ബോക്സിൽ ടാപ്പുചെയ്യുക.",
    },
    "denom_deposit_prompt": {
        "en": "How many notes of {} are you depositing?",
        "ta": "{} ரூபாயில் எத்தனை நோட்டுகளை டெபாசிட் செய்கிறீர்கள்?",
        "hi": "आप {} के कितने नोट जमा कर रहे हैं?",
        "te": "మీరు {} యొక్క ఎన్ని నోట్లను డిపాజిట్ చేస్తున్నారు?",
        "kn": "ನೀವು {} ನ ಎಷ್ಟು ನೋಟುಗಳನ್ನು ಠೇವಣಿ ಮಾಡುತ್ತಿದ್ದೀರಿ?",
        "ml": "നിങ്ങൾ {} ന്റെ എത്ര നോട്ടുകൾ നിക്ഷേപിക്കുന്നു?",
    },
    "denom_withdraw_prompt": {
        "en": "How many notes of {} do you want to withdraw?",
        "ta": "{} ரூபாயில் எத்தனை நோட்டுகளை எடுக்க விரும்புகிறீர்கள்?",
        "hi": "आप {} के कितने नोट निकालना चाहते हैं?",
        "te": "మీరు {} యొక్క ఎన్ని నోట్లను ఉపసంహరించుకోవాలనుకుంటున్నారు?",
        "kn": "ನೀವು {} ನ ಎಷ್ಟು ನೋಟುಗಳನ್ನು ಹಿಂಪಡೆಯಲು ಬಯಸುತ್ತೀರಿ?",
        "ml": "നിങ്ങൾ {} ന്റെ എത്ര നോട്ടുകൾ പിൻവലിക്കാൻ ആഗ്രഹിക്കുന്നു?",
    },
    "scan_started": {
        "en": "Scanning document... Please wait.",
        "ta": "\u0b86\u0bb5\u0ba3\u0bae\u0bcd \u0bb8\u0bcd\u0b95\u0bc7\u0ba9\u0bcd \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1... \u0b95\u0bbe\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "hi": "\u0926\u0938\u094d\u0924\u093e\u0935\u0947\u091c\u093c \u0938\u094d\u0915\u0948\u0928 \u0939\u094b \u0930\u0939\u093e \u0939\u0948... \u0915\u0943\u092a\u092f\u093e \u092a\u094d\u0930\u0924\u0940\u0915\u094d\u0937\u093e \u0915\u0930\u0947\u0902\u0964",
        "te": "\u0c2a\u0c24\u0c4d\u0c30\u0c02 \u0c38\u0c4d\u0c15\u0c3e\u0c28\u0c4d \u0c1a\u0c47\u0c2f\u0c2c\u0c21\u0c41\u0c24\u0c4b\u0c02\u0c26\u0c3f... \u0c26\u0c2f\u0c1a\u0c47\u0c38\u0c3f \u0c35\u0c47\u0c1a\u0c3f \u0c09\u0c02\u0c21\u0c02\u0c21\u0c3f.",
        "kn": "\u0ca6\u0cbe\u0c96\u0cb2\u0cc6\u0caf\u0ca8\u0ccd\u0ca8\u0cc1 \u0cb8\u0ccd\u0c95\u0ccd\u0caf\u0cbe\u0ca8\u0ccd \u0cae\u0cbe\u0ca1\u0cb2\u0cbe\u0c97\u0cc1\u0ca4\u0ccd\u0ca4\u0cbf\u0ca6\u0cc6... \u0ca6\u0caf\u0cb5\u0cbf\u0c9f\u0ccd\u0c9f\u0cc1 \u0ca8\u0cbf\u0cb0\u0cc0\u0c95\u0ccd\u0cb7\u0cbf\u0cb8\u0cbf.",
        "ml": "\u0d30\u0d47\u0d16 \u0d38\u0d4d\u0d15\u0d3e\u0d7b \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d28\u0d4d\u0d28\u0d41... \u0d26\u0d2f\u0d35\u0d3e\u0d2f\u0d3f \u0d15\u0d3e\u0d24\u0d4d\u0d24\u0d3f\u0d30\u0d3f\u0d15\u0d4d\u0d15\u0d41\u0d15.",
    },
    "extract_success": {
        "en": "Document scanned successfully. Customer details have been extracted successfully. Proceeding to the verification page.",
        "ta": "ஆவணம் வெற்றிகரமாக ஸ்கேன் செய்யப்பட்டது. வாடிக்கையாளர் விவரங்கள் வெற்றிகரமாக பெறப்பட்டுள்ளன. சரிபார்ப்பு பக்கத்திற்கு செல்கிறோம்.",
        "hi": "दस्तावेज़ सफलतापूर्वक स्कैन किया गया। ग्राहक विवरण सफलतापूर्वक निकाला गया। सत्यापन पृष्ठ पर जा रहे हैं।",
        "te": "పత్రం విజయవంతంగా స్కాన్ చేయబడింది. కస్టమర్ వివరాలు విజయవంతంగా సంగ్రహించబడ్డాయి. ధృవీకరణ పేజీకి వెళుతున్నాము.",
        "kn": "ದಾಖಲೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸ್ಕ್ಯಾನ್ ಮಾಡಲಾಗಿದೆ. ಗ್ರಾಹಕ ವಿವರಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಪಡೆಯಲಾಗಿದೆ. ಪರಿಶೀಲನೆ ಪುಟಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ.",
        "ml": "രേഖ വിജയകരമായി സ്കാൻ ചെയ്തു. ഉപഭോക്തൃ വിവരങ്ങൾ വിജയകരമായി വേർതിരിച്ചെടുത്തു. പരിശോധനാ പേജിലേക്ക് പോകുന്നു.",
    },
    "printing_success": {
        "en": "Your bank form has been successfully generated and printed. Thank you for using our Smart Banking Kiosk.",
        "ta": "உங்கள் படிவம் வெற்றிகரமாக உருவாக்கப்பட்டு அச்சிடப்பட்டுள்ளது. நன்றி.",
        "hi": "आपका बैंक फॉर्म सफलतापूर्वक जनरेट और प्रिंट कर दिया गया है। हमारे स्मार्ट बैंकिंग कियॉस्क का उपयोग करने के लिए धन्यवाद।",
        "te": "మీ బ్యాంక్ ఫారం విజయవంతంగా సృష్టించబడింది మరియు ముద్రించబడింది. ధన్యవాదాలు.",
        "kn": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಫಾರ್ಮ್ ಅನ್ನು ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ ಮತ್ತು ಮುದ್ರಿಸಲಾಗಿದೆ. ಧನ್ಯವಾದಗಳು.",
        "ml": "നിങ്ങളുടെ ബാങ്ക് ഫോം വിജയകരമായി സൃഷ്ടിച്ചു അച്ചടിച്ചു. നന്ദി.",
    },
    "print_started": {
        "en": "Printing has started... Please collect your form.",
        "ta": "\u0b85\u0b9a\u0bcd\u0b9a\u0bbf\u0b9f\u0bc1\u0ba4\u0bb2\u0bcd \u0ba4\u0bca\u0b9f\u0b99\u0bcd\u0b95\u0bbf\u0bb5\u0bbf\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1... \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0baa\u0b9f\u0bbf\u0bb5\u0ba4\u0bcd\u0ba4\u0bc8 \u0baa\u0bc6\u0bb1\u0bcd\u0bb1\u0bc1\u0b95\u0bcd\u0b95\u0bca\u0bb3\u0bcd\u0bb3\u0bb5\u0bc1\u0bae\u0bcd.",
        "hi": "\u092a\u094d\u0930\u093f\u0902\u091f\u093f\u0902\u0917 \u0936\u0941\u0930\u0942 \u0939\u094b \u0917\u0908 \u0939\u0948... \u0915\u0943\u092a\u092f\u093e \u0905\u092a\u0928\u093e \u092b\u093c\u0949\u0930\u094d\u092e \u0932\u0947\u0902\u0964",
        "te": "\u0c2a\u0c4d\u0c30\u0c3f\u0c02\u0c1f\u0c3f\u0c02\u0c17\u0c4d \u0c2a\u0c4d\u0c30\u0c3e\u0c30\u0c02\u0c2d\u0c2e\u0c48\u0c02\u0c26\u0c3f... \u0c26\u0c2f\u0c1a\u0c47\u0c38\u0c3f \u0c2e\u0c40 \u0c2b\u0c3e\u0c30\u0c2e\u0c4d \u0c38\u0c47\u0c15\u0c30\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.",
        "kn": "\u0cae\u0cc1\u0ca6\u0ccd\u0cb0\u0ca3 \u0caa\u0ccd\u0cb0\u0cbe\u0cb0\u0c82\u0cad\u0cb5\u0cbe\u0c97\u0cbf\u0ca6\u0cc6... \u0ca6\u0caf\u0cb5\u0cbf\u0c9f\u0ccd\u0c9f\u0cc1 \u0ca8\u0cbf\u0cae\u0ccd\u0cae \u0cab\u0cbe\u0cb0\u0ccd\u0cae\u0ccd \u0c85\u0ca8\u0ccd\u0ca8\u0cc1 \u0cb8\u0c82\u0c97\u0ccd\u0cb0\u0cb9\u0cbf\u0cb8\u0cbf.",
        "ml": "\u0d2a\u0d4d\u0d30\u0d3f\u0d7b\u0d31\u0d4d\u0d31\u0d3f\u0d02\u0d17\u0d4d \u0d06\u0d30\u0d02\u0d2d\u0d3f\u0d1a\u0d4d\u0d1a\u0d41... \u0d26\u0d2f\u0d35\u0d3e\u0d2f\u0d3f \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d41\u0d1f\u0d46 \u0d2b\u0d4b\u0d02 \u0d36\u0d47\u0d16\u0d30\u0d3f\u0d15\u0d4d\u0d15\u0d41\u0d15.",
    },
    "process_completed": {
        "en": "Process completed successfully. Thank you for using Auto Bank.",
        "ta": "\u0b9a\u0bc6\u0baf\u0bb2\u0bcd\u0bae\u0bc1\u0bb1\u0bc8 \u0bb5\u0bc6\u0bb1\u0bcd\u0bb1\u0bbf\u0b95\u0bb0\u0bae\u0bbe\u0b95 \u0bae\u0bc1\u0b9f\u0bbf\u0ba8\u0bcd\u0ba4\u0ba4\u0bc1. \u0ba8\u0ba9\u0bcd\u0bb1\u0bbf.",
        "hi": "\u092a\u094d\u0930\u0915\u094d\u0930\u093f\u092f\u093e \u0938\u092b\u0932\u0924\u093e\u092a\u0942\u0930\u094d\u0935\u0915 \u092a\u0942\u0930\u0940 \u0939\u0941\u0908\u0964 \u0927\u0928\u094d\u092f\u0935\u093e\u0926\u0964",
        "te": "\u0c2a\u0c4d\u0c30\u0c15\u0c4d\u0c30\u0c3f\u0c2f \u0c35\u0c3f\u0c1c\u0c2f\u0c35\u0c02\u0c24\u0c02\u0c17\u0c3e \u0c2a\u0c42\u0c30\u0c4d\u0c24\u0c2f\u0c3f\u0c02\u0c26\u0c3f. \u0c27\u0c28\u0c4d\u0c2f\u0c35\u0c3e\u0c26\u0c3e\u0c32\u0c41.",
        "kn": "\u0caa\u0ccd\u0cb0\u0c95\u0ccd\u0cb0\u0cbf\u0caf\u0cc6 \u0caf\u0cb6\u0cb8\u0ccd\u0cb5\u0cbf\u0caf\u0cbe\u0c97\u0cbf \u0caa\u0cc2\u0cb0\u0ccd\u0ca3\u0c97\u0cca\u0c82\u0ca1\u0cbf\u0ca6\u0cc6. \u0ca7\u0ca8\u0ccd\u0caf\u0cb5\u0cbe\u0ca6\u0c97\u0cb3\u0cc1.",
        "ml": "\u0d2a\u0d4d\u0d30\u0d15\u0d4d\u0d30\u0d3f\u0d2f \u0d35\u0d3f\u0d1c\u0d2f\u0d15\u0d30\u0d2e\u0d3e\u0d2f\u0d3f \u0d2a\u0d42\u0d7c\u0d24\u0d4d\u0d24\u0d3f\u0d2f\u0d3e\u0d2f\u0d3f. \u0d28\u0d28\u0d4d\u0d26\u0d3f.",
    },
    "place_doc_on_scanner": {"en": "Please place your document on the scanner.", "ta": "தயவுசெய்து உங்கள் ஆவணத்தை ஸ்கேனரில் வைக்கவும்.", "hi": "कृपया अपना दस्तावेज़ स्कैनर पर रखें।", "te": "దయచేసి మీ పత్రాన్ని స్కానర్‌పై ఉంచండి.", "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ದಾಖಲೆಯನ್ನು ಸ್ಕ್ಯಾನರ್‌ನಲ್ಲಿ ಇರಿಸಿ.", "ml": "ദയവായി നിങ്ങളുടെ രേഖ സ്കാനറിൽ വയ്ക്കുക."},
    "review_details": {"en": "Please review your details.", "ta": "தயவுசெய்து உங்கள் விவரங்களை சரிபார்க்கவும்.", "hi": "कृपया अपने विवरण की समीक्षा करें।", "te": "దయచేసి మీ వివరాలను సమీక్షించండి.", "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.", "ml": "ദയവായി നിങ്ങളുടെ വിവരങ്ങൾ പരിശോധിക്കുക."},
    "scan_processing": {"en": "Please wait while your document is being processed.", "ta": "உங்கள் ஆவணம் செயலாக்கப்படுகிறது. காத்திருக்கவும்.", "hi": "कृपया प्रतीक्षा करें, आपका दस्तावेज़ संसाधित किया जा रहा है।", "te": "దయచేసి వేచి ఉండండి, మీ పత్రం ప్రాసెస్ చేయబడుతోంది.", "kn": "ದಯವಿಟ್ಟು ಕಾಯಿರಿ, ನಿಮ್ಮ ದಾಖಲೆ ಸಂಸ್ಕರಿಸಲಾಗುತ್ತಿದೆ.", "ml": "ദയവായി കാത്തിരിക്കുക, നിങ്ങളുടെ രേഖ പ്രോസസ്സ് ചെയ്യുന്നു."}
}

# gTTS language codes
_GTTS_LANG_MAP = {
    "en": "en",
    "ta": "ta",
    "hi": "hi",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
}

# Single background speech queue (prevents overlapping audio)
_speech_queue: queue.Queue = queue.Queue()
_tts_thread: threading.Thread = None
_tts_running = False


def _pyttsx3_speak(text: str):
    """Speak text using pyttsx3 (offline, English only)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        print(f"[TTS] pyttsx3 error: {exc}")


def _gtts_speak(text: str, lang_code: str):
    """Speak text using gTTS (online, multi-language)."""
    tmp_path = None
    try:
        from gtts import gTTS
        from playsound import playsound

        gtts_lang = _GTTS_LANG_MAP.get(lang_code, "en")
        tts = gTTS(text=text, lang=gtts_lang, slow=False)

        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()
        tts.save(tmp_path)

        playsound(tmp_path)

    except Exception as exc:
        print(f"[TTS] gTTS error: {exc}")
        # Fall back to pyttsx3 with English
        _pyttsx3_speak(text)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _worker():
    """Background thread that processes the speech queue."""
    global _tts_running
    _tts_running = True
    while _tts_running:
        try:
            item = _speech_queue.get(timeout=0.5)
            if item is None:
                break
            text, lang_code = item
            if lang_code == "en":
                _pyttsx3_speak(text)
            else:
                _gtts_speak(text, lang_code)
            _speech_queue.task_done()
        except queue.Empty:
            continue
    _tts_running = False


def _ensure_worker():
    """Start TTS worker thread if not running."""
    global _tts_thread, _tts_running
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_running = True
        _tts_thread = threading.Thread(target=_worker, daemon=True)
        _tts_thread.start()


def speak(text: str, lang_code: str = "en"):
    """
    Speak *text* in the given language — non-blocking.

    Args:
        text      : The text to speak (already translated).
        lang_code : One of 'en', 'ta', 'hi', 'te', 'kn', 'ml'.
    """
    if not text:
        return
    _ensure_worker()
    # Clear queue to avoid backlog (latest speech wins)
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
        except queue.Empty:
            break
    _speech_queue.put((text, lang_code))


def speak_script(key: str, lang_code: str = "en"):
    """
    Speak a predefined voice script by key.

    Falls back to English if the key/lang combo is not found.
    """
    scripts = VOICE_SCRIPTS.get(key, {})
    text = scripts.get(lang_code) or scripts.get("en", "")
    speak(text, lang_code)


def speak_dynamic(key: str, lang_code: str, *args):
    """
    Speak a template string by replacing {} with args.
    """
    scripts = VOICE_SCRIPTS.get(key, {})
    text = scripts.get(lang_code) or scripts.get("en", "")
    if text:
        try:
            formatted = text.format(*args)
            speak(formatted, lang_code)
        except Exception:
            speak(text, lang_code)


def speak_review(ocr_data: dict, lang_code: str):
    """
    Dynamically generates the voice review string based on extracted data.
    """
    import translations
    scripts_start = VOICE_SCRIPTS.get("review_start", {})
    scripts_end = VOICE_SCRIPTS.get("review_end", {})
    
    start_text = scripts_start.get(lang_code) or scripts_start.get("en", "")
    end_text = scripts_end.get(lang_code) or scripts_end.get("en", "")
    
    review_parts = [start_text]
    
    for key, val in ocr_data.items():
        if val and val != "Not found":
            # Get translated field name
            lbl = translations.t(f"field_{key}", lang_code)
            if lbl == f"field_{key}": lbl = key.replace("_", " ")
            review_parts.append(f"{lbl}: {val}.")
            
    review_parts.append(end_text)
    
    full_text = " ".join(review_parts)
    speak(full_text, lang_code)


def stop():
    """Stop the TTS worker cleanly."""
    global _tts_running
    _tts_running = False
    _speech_queue.put(None)
