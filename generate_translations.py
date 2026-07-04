import json

# Read the extracted English keys
with open('clean_translations.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Hardcode the new keys for the intro screen
intro_keys = {
    "intro_system_name": {
        "en": "AUTO BANK FORM FILLING SYSTEM",
        "ta": "தானியங்கி வங்கி படிவம் நிரப்பும் அமைப்பு",
        "hi": "ऑटो बैंक फॉर्म भरने की प्रणाली",
        "te": "ఆటో బ్యాంక్ ఫారమ్ నింపే వ్యవస్థ",
        "kn": "ಸ್ವಯಂಚಾಲಿತ ಬ್ಯಾಂಕ್ ಫಾರ್ಮ್ ತುಂಬಿಸುವ ವ್ಯವಸ್ಥೆ",
        "ml": "ഓട്ടോ ബാങ്ക് ഫോം ഫില്ലിംഗ് സിസ്റ്റം",
    },
    "intro_tagline": {
        "en": "AI-Powered Kiosk  •  100% Accurate  •  Multilingual",
        "ta": "AI-ஆல் இயக்கப்படும் கியோஸ்க் • 100% துல்லியம் • பன்மொழி",
        "hi": "AI-संचालित कियोस्क  •  100% सटीक  •  बहुभाषी",
        "te": "AI-ఆధారిత కియోస్క్  •  100% ఖచ్చితమైన  •  బహుభాషా",
        "kn": "AI-ಚಾಲಿತ ಕಿಯೋಸ್ಕ್  •  100% ನಿಖರ  •  ಬಹುಭಾಷಾ",
        "ml": "AI-ഊർജ്ജിത കിയോസ്ക്  •  100% കൃത്യം  •  ബഹുഭാഷ",
    },
    "intro_touch_prompt": {
        "en": "👆  TOUCH YOUR LANGUAGE TO BEGIN  👆",
        "ta": "👆  உங்கள் மொழியைத் தொடவும்  👆",
        "hi": "👆  अपनी भाषा चुनें  👆",
        "te": "👆  మీ భాషను స్పర్శించండి  👆",
        "kn": "👆  ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಸ್ಪರ್ಶಿಸಿ  👆",
        "ml": "👆  നിങ്ങളുടെ ഭാഷ സ്പർശിക്കൂ  👆",
    },
    "intro_badge_secure": {
        "en": "🔒 Secure",
        "ta": "🔒 பாதுகாப்பு",
        "hi": "🔒 सुरक्षित",
        "te": "🔒 సురక్షితం",
        "kn": "🔒 ಸುರಕ್ಷಿತ",
        "ml": "🔒 സുരക്ഷിതം",
    },
    "intro_badge_fast": {
        "en": "⚡ Fast",
        "ta": "⚡ வேகம்",
        "hi": "⚡ तेज़",
        "te": "⚡ వేగంగా",
        "kn": "⚡ ವೇಗ",
        "ml": "⚡ വേഗം",
    },
    "intro_badge_accurate": {
        "en": "✅ Accurate",
        "ta": "✅ துல்லியம்",
        "hi": "✅ सटीक",
        "te": "✅ ఖచ్చితమైన",
        "kn": "✅ ನಿಖರ",
        "ml": "✅ കൃത്യം",
    },
    "intro_badge_multilang": {
        "en": "🌐 Multilingual",
        "ta": "🌐 பன்மொழி",
        "hi": "🌐 बहुभाषी",
        "te": "🌐 బహుభాషా",
        "kn": "🌐 ಬಹುಭಾಷಾ",
        "ml": "🌐 ബഹുഭാഷ",
    },
    "intro_badge_print": {
        "en": "🖨️ Auto-Print",
        "ta": "🖨️ தான-அச்சு",
        "hi": "🖨️ ऑटो-प्रिंट",
        "te": "🖨️ ఆటో-ముద్రణ",
        "kn": "🖨️ ಸ್ವಯಂ-ಮುದ್ರಣ",
        "ml": "🖨️ ഓട്ടോ-പ്രിന്‍റ്",
    },
    "intro_footer": {
        "en": "📄 Aadhaar  •  📄 PAN Card  •  📄 Bank Passbook  •  ✔ Form Auto-Filled & Printed",
        "ta": "📄 ஆதார்  •  📄 பான் கார்டு  •  📄 வங்கி பாஸ்புக்  •  ✔ படிவம் தானாகவே நிரப்பப்படும்",
        "hi": "📄 आधार  •  📄 पैन कार्ड  •  📄 बैंक पासबुक  •  ✔ फॉर्म स्वतः भरा जाएगा",
        "te": "📄 ఆధార్  •  📄 పాన్ కార్డ్  •  📄 బ్యాంక్ పాస్‌బుక్  •  ✔ ఫారమ్ స్వయంగా నిండుతుంది",
        "kn": "📄 ಆಧಾರ್  •  📄 ಪ್ಯಾನ್ ಕಾರ್ಡ್  •  📄 ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್  •  ✔ ಫಾರ್ಮ್ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ತುಂಬಿಸಲ್ಪಡುತ್ತದೆ",
        "ml": "📄 ആധാർ  •  📄 പാൻ കാർഡ്  •  📄 ബാങ്ക് പാസ്ബുക്ക്  •  ✔ ഫോം സ്വതവേ നിറയ്ക്കും",
    },
    "intro_ticker_withdrawal": {
        "en": "💵  Cash Withdrawal",
        "ta": "💵  பணம் எடுக்கல்",
        "hi": "💵  नकद निकासी",
        "te": "💵  నగదు ఉపసంహరణ",
        "kn": "💵  ನಗದು ಹಿಂಪಡೆಯುವಿಕೆ",
        "ml": "💵  പണം പിൻവലിക്കൽ",
    },
    "intro_ticker_deposit": {
        "en": "💰  Cash Deposit",
        "ta": "💰  பணம் செலுத்துதல்",
        "hi": "💰  नकद जमा",
        "te": "💰  నగదు జమ",
        "kn": "💰  ನಗದು ಠೇವಣಿ",
        "ml": "💰  പണം നിക്ഷേപം",
    },
    "intro_ticker_neft": {
        "en": "🔄  NEFT / RTGS Transfer",
        "ta": "🔄  NEFT / RTGS பரிமாற்றம்",
        "hi": "🔄  NEFT / RTGS स्थानांतरण",
        "te": "🔄  NEFT / RTGS బదిలీ",
        "kn": "🔄  NEFT / RTGS ವರ್ಗಾವಣೆ",
        "ml": "🔄  NEFT / RTGS കൈമാറ്റം",
    },
    "intro_ticker_dd": {
        "en": "📋  Demand Draft",
        "ta": "📋  டிமாண்ட் டிராஃப்ட்",
        "hi": "📋  डिमांड ड्राफ्ट",
        "te": "📋  డిమాండ్ డ్రాఫ్ట్",
        "kn": "📋  ಡಿಮಾಂಡ್ ಡ್ರಾಫ್ಟ್",
        "ml": "📋  ഡിമാൻഡ് ഡ്രാഫ്റ്റ്",
    },
    "intro_ticker_account": {
        "en": "🧑‍💼  Account Opening",
        "ta": "🧑‍💼  கணக்கு திறக்கல்",
        "hi": "🧑‍💼  खाता खोलना",
        "te": "🧑‍💼  ఖాతా ప్రారంభం",
        "kn": "🧑‍💼  ಖಾತೆ ತೆರೆಯುವಿಕೆ",
        "ml": "🧑‍💼  അക്കൗണ്ട് തുറക്കൽ",
    },
    "intro_ticker_atm": {
        "en": "💳  ATM Card Request",
        "ta": "💳  ATM கார்டு கோரிக்கை",
        "hi": "💳  ATM कार्ड अनुरोध",
        "te": "💳  ATM కార్డ్ అభ్యర్థన",
        "kn": "💳  ATM ಕಾರ್ಡ್ ವಿನಂತಿ",
        "ml": "💳  ATM കാർഡ് അഭ്യർഥന",
    },
    "intro_ticker_mobile": {
        "en": "📱  Mobile Update",
        "ta": "📱  மொபைல் புதுப்பிப்பு",
        "hi": "📱  मोबाइल अपडेट",
        "te": "📱  మొబైల్ అప్‌డేట్",
        "kn": "📱  ಮೊಬೈಲ್ ಅಪ್‌ಡೇಟ್",
        "ml": "📱  മൊബൈൽ അപ്‌ഡേറ്റ്",
    },
    "intro_ticker_address": {
        "en": "🏠  Address Change",
        "ta": "🏠  முகவரி மாற்றம்",
        "hi": "🏠  पता परिवर्तन",
        "te": "🏠  చిరునామా మార్పు",
        "kn": "🏠  ವಿಳಾಸ ಬದಲಾವಣೆ",
        "ml": "🏠  മേൽവിലാസ മാറ്റം",
    },
    "intro_ticker_kyc": {
        "en": "✔  KYC Update",
        "ta": "✔  KYC புதுப்பிப்பு",
        "hi": "✔  KYC अपडेट",
        "te": "✔  KYC నవీకరణ",
        "kn": "✔  KYC ನವೀಕರಣ",
        "ml": "✔  KYC അപ്‌ഡേറ്റ്",
    },
    "intro_ticker_cheque": {
        "en": "📝  Cheque Book",
        "ta": "📝  காசோலை புத்தகம்",
        "hi": "📝  चेक बुक",
        "te": "📝  చెక్ పుస్తకం",
        "kn": "📝  ಚೆಕ್ ಪುಸ್ತಕ",
        "ml": "📝  ചെക്ക് ബുക്ക്",
    },
    "intro_step1": {
        "en": "Step 1 of 6 — Choose Language",
        "ta": "படி 1 / 6 — மொழி தேர்வு",
        "hi": "चरण 1 / 6 — भाषा चुनें",
        "te": "దశ 1 / 6 — భాష ఎంచుకోండి",
        "kn": "ಹಂತ 1 / 6 — ಭಾಷೆ ಆಯ್ಕೆ ಮಾಡಿ",
        "ml": "ഘട്ടം 1 / 6 — ഭാഷ തിരഞ്ഞെടുക്കൂ",
    },
}

d.update(intro_keys)

out = [
    "# translations.py",
    "# Clean UI translation dictionary for all supported languages.",
    "UI_TEXT = {"
]

for k, langs in d.items():
    out.append(f'    "{k}": {{')
    for lang, val in langs.items():
        # Escape quotes in value
        val = val.replace('"', '\\"')
        out.append(f'        "{lang}": "{val}",')
    out.append("    },")

out.append("}")
out.append("")
out.append("def t(key: str, lang: str = 'en') -> str:")
out.append('    """Helper function to fetch translated UI text."""')
out.append('    if key not in UI_TEXT:')
out.append('        return key  # Fallback to key itself if missing')
out.append('    return UI_TEXT[key].get(lang, UI_TEXT[key].get("en", key))')
out.append("")

with open("translations.py", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Created clean translations.py")
