"""
ai_helper.py — Gemini AI post-processing and Vision OCR extraction.

Sends raw image or OCR text to the Gemini API with a structured prompt
asking it to extract and correct the relevant fields, then
returns a clean dict.
"""

import json
import re
import warnings
import config


def _extract_json_from_response(text: str) -> dict:
    """Try to parse JSON from the AI response (handles markdown code fences)."""
    clean = re.sub(r'```(?:json)?', '', text).strip().strip('`')
    return json.loads(clean)


# Models to try in order (best available that works on this API key)
_VISION_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-1.5-flash",
]


def _call_gemini(prompt: str) -> str:
    """Call the Gemini API and return the text response."""
    import google.generativeai as genai
    warnings.simplefilter('ignore', FutureWarning)
    genai.configure(api_key=config.GEMINI_API_KEY)
    for model_name in _VISION_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    raise RuntimeError("All Gemini models exhausted")


def enhance_with_vision(image_path: str, doc_type: str) -> dict:
    """
    Process the image directly using Gemini Vision.
    Sends the original colour image (not preprocessed/grayscale) for best accuracy.
    Tries multiple Gemini models in order until one succeeds.
    """
    import warnings
    import google.generativeai as genai
    from PIL import Image
    import json
    import re

    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    warnings.simplefilter('ignore', FutureWarning)
    genai.configure(api_key=config.GEMINI_API_KEY)

    # Always send the original color image — Gemini Vision works best on it
    img = Image.open(image_path)
    # Resize if very large to stay within token limits but keep quality
    MAX_DIM = 2048
    if max(img.width, img.height) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)

    if doc_type == "aadhaar":
        prompt = (
            "You are a precise OCR system for Indian Aadhaar cards.\n"
            "STRICT RULES:\n"
            "- Extract ONLY information physically visible in this image.\n"
            "- Do NOT guess, invent, or fill in any missing details.\n"
            "- If a field is not visible or illegible, set it to exactly: Not found\n"
            "- Aadhaar number is 12 digits, format: XXXX XXXX XXXX\n"
            "- Gender is exactly one of: Male / Female / Transgender\n\n"
            "Return ONLY this JSON (no extra text, no markdown):\n"
            '{"name":"","father_name":"","dob":"","gender":"","aadhaar_number":"","address":""}'
        )
    elif doc_type == "passbook":
        prompt = (
            "You are a precise OCR system for Indian Bank Passbooks.\n"
            "STRICT RULES:\n"
            "- Extract ONLY information physically visible in this image.\n"
            "- Do NOT guess, invent, or fill in any missing details.\n"
            "- If a field is not visible or illegible, set it to exactly: Not found\n"
            "- IFSC code is exactly 11 characters (4 letters + 0 + 6 alphanumeric).\n\n"
            "Return ONLY this JSON (no extra text, no markdown):\n"
            '{"bank_name":"","branch":"","ifsc":"","account_no":"","name":"","cif":"","mobile":""}'
        )
    elif doc_type == "pan":
        prompt = (
            "You are a precise OCR system for Indian PAN cards.\n"
            "STRICT RULES:\n"
            "- Extract ONLY information physically visible in this image.\n"
            "- Do NOT guess, invent, or fill in any missing details.\n"
            "- If a field is not visible or illegible, set it to exactly: Not found\n"
            "- PAN number is exactly 10 characters: 5 uppercase letters, 4 digits, 1 uppercase letter.\n\n"
            "Return ONLY this JSON (no extra text, no markdown):\n"
            '{"name":"","father_name":"","dob":"","pan_number":""}'
        )
    else:
        raise ValueError(f"Unknown doc_type: {doc_type}")

    last_exc = None
    for model_name in _VISION_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, img])
            raw = response.text

            # Robust JSON extraction — handles markdown fences and stray text
            # Try to find the first { ... } block
            json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if json_match:
                clean = json_match.group(0)
            else:
                clean = re.sub(r'```(?:json)?', '', raw).strip().strip('`')

            ai_data = json.loads(clean)

            # Normalize: empty strings / null / "none" / "n/a" → "Not found"
            for k in list(ai_data.keys()):
                v = ai_data[k]
                if not v or str(v).strip().lower() in ("", "none", "n/a", "na", "null", "not available"):
                    ai_data[k] = "Not found"

            ai_data["ai_enhanced"] = True
            ai_data["doc_type"] = doc_type
            ai_data["_confidence"] = 100.0
            ai_data["_raw_text"] = f"Extracted via Gemini Vision ({model_name})"
            return ai_data

        except Exception as exc:
            last_exc = exc
            print(f"[ai_helper] {model_name} failed: {exc}")
            continue

    raise RuntimeError(f"All Gemini Vision models failed. Last error: {last_exc}")


def enhance_with_ai(ocr_text: str, doc_type: str, regex_data: dict) -> dict:
    """
    Fallback for when Vision isn't used.
    Post-process regex-extracted data using the Gemini AI on text.
    """
    import google.generativeai as genai
    import warnings
    import json
    import re
    if not config.GEMINI_API_KEY:
        return regex_data

    try:
        warnings.simplefilter('ignore', FutureWarning)
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        strict_rules = (
            "CRITICAL RULES:\n"
            "1. The application must never replace, guess, invent, or modify any customer information.\n"
            "2. Extract ONLY what is present in the OCR text.\n"
            "3. If a field is missing, strictly return 'Not found'.\n"
        )
        
        if doc_type == "aadhaar":
            prompt = f"{strict_rules}Extract and correct from OCR text: {ocr_text}\nReturn JSON with keys: name, father_name, dob, gender, aadhaar_number, address."
        elif doc_type == "passbook":
            prompt = f"{strict_rules}Extract and correct from OCR text: {ocr_text}\nReturn JSON with keys: bank_name, branch, ifsc, account_no, name, cif, mobile."
        elif doc_type == "pan":
            prompt = f"{strict_rules}Extract and correct from OCR text: {ocr_text}\nReturn JSON with keys: name, dob, pan_number."
        else:
            return regex_data

        response = model.generate_content(prompt)
        clean = re.sub(r'```(?:json)?', '', response.text).strip().strip('`')
        ai_data = json.loads(clean)

        merged = dict(regex_data)
        for key, ai_val in ai_data.items():
            if ai_val and ai_val.lower() != "not found":
                if merged.get(key, "Not found") == "Not found" or key in merged:
                    merged[key] = ai_val

        merged["ai_enhanced"] = True
        return merged

    except Exception as exc:
        regex_data["ai_error"] = str(exc)
        return regex_data


# ─────────────────────────────────────────────────────────
# Number-to-Words Converter (Indian English)
# ─────────────────────────────────────────────────────────

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
    "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
]
_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty",
    "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digits(n: int) -> str:
    if n < 20:
        return _ONES[n]
    t, o = divmod(n, 10)
    return (_TENS[t] + " " + _ONES[o]).strip()


def _three_digits(n: int) -> str:
    h, rem = divmod(n, 100)
    parts = []
    if h:
        parts.append(_ONES[h] + " Hundred")
    if rem:
        parts.append(_two_digits(rem))
    return " ".join(parts)


def number_to_words_rupees(amount) -> str:
    """
    Convert a numeric amount to Indian English words.
    
    Examples:
        2000  → "Two Thousand Rupees Only"
        150000 → "One Lakh Fifty Thousand Rupees Only"
        1234567 → "Twelve Lakh Thirty Four Thousand Five Hundred Sixty Seven Rupees Only"
    """
    try:
        n = int(str(amount).replace(",", "").replace("₹", "").strip())
    except (ValueError, TypeError):
        return str(amount)

    if n == 0:
        return "Zero Rupees Only"

    parts = []

    # Crores (1,00,00,000+)
    if n >= 10000000:
        crores = n // 10000000
        parts.append(_two_digits(crores) + " Crore")
        n %= 10000000

    # Lakhs (1,00,000+)
    if n >= 100000:
        lakhs = n // 100000
        parts.append(_two_digits(lakhs) + " Lakh")
        n %= 100000

    # Thousands (1,000+)
    if n >= 1000:
        thousands = n // 1000
        parts.append(_two_digits(thousands) + " Thousand")
        n %= 1000

    # Hundreds + remainder
    if n > 0:
        parts.append(_three_digits(n))

    return " ".join(parts) + " Rupees Only"
