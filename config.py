"""
config.py — Central configuration for the Bank Kiosk system.
Edit the paths and API key here before running the application.
"""

import os

# ─────────────────────────────────────────────────────────
# Tesseract OCR
# ─────────────────────────────────────────────────────────
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ─────────────────────────────────────────────────────────
# Gemini AI (optional – leave empty string to disable)
# Set via environment variable for security, or paste key here.
# ─────────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyBmIMlkeshkXh2oUgmp07SrzC1M-J833Uo"

# ─────────────────────────────────────────────────────────
# Default Test Image Paths (used when no image is chosen)
# ─────────────────────────────────────────────────────────
DEFAULT_AADHAAR_PATH  = r"C:\Users\Thamira\OneDrive\Desktop\bank hardware\hh aadhar.jpeg"
DEFAULT_PASSBOOK_PATH = r"C:\Users\Thamira\OneDrive\Desktop\bank hardware\bank passbook.jpeg"
DEFAULT_PAN_PATH      = r"C:\Users\Thamira\OneDrive\Desktop\thamira pancard.jpeg"

# ─────────────────────────────────────────────────────────
# PDF Output
# ─────────────────────────────────────────────────────────
PDF_OUTPUT_DIR = r"C:\Users\Thamira\OneDrive\Desktop"
PDF_FILENAME   = "bank_form_filled.pdf"

# ─────────────────────────────────────────────────────────
# SQLite Database
# ─────────────────────────────────────────────────────────
DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "kiosk_transactions.db"
)

# ─────────────────────────────────────────────────────────
# UI / Kiosk Settings
# ─────────────────────────────────────────────────────────
APP_TITLE      = "Auto Bank Form Filling System"
WINDOW_WIDTH   = 1100
WINDOW_HEIGHT  = 800
FULLSCREEN     = False          # Set True for real kiosk deployment

# ── Professional Corporate Banking palette ─────────────
COLOR_BG           = "#FFFFFF"     # Pure clean white
COLOR_SURFACE      = "#F2F6FC"     # Subtle cool-white surface
COLOR_PRIMARY      = "#1A56DB"     # Deep professional blue (SBI/HDFC style)
COLOR_SECONDARY    = "#0E3A8C"     # Dark corporate navy
COLOR_SUCCESS      = "#0E9F6E"     # Professional green
COLOR_WARNING      = "#E3A008"     # Warm amber
COLOR_ERROR        = "#E02424"     # Alert red
COLOR_TEXT         = "#111928"     # Near-black for crisp readability
COLOR_SUBTEXT      = "#6B7280"     # Professional gray subtext
COLOR_GLASS        = "#EBF3FF"     # Light blue-white card background
COLOR_GLASS_BORDER = "#C3DDFF"     # Subtle blue card border

FONT_FAMILY     = "Segoe UI"

# ─────────────────────────────────────────────────────────
# Multi-Language Support
# ─────────────────────────────────────────────────────────
LANGUAGES = {
    "en": {"name": "English",   "native": "English",    "flag": "🇬🇧"},
    "ta": {"name": "Tamil",     "native": "தமிழ்",       "flag": "🇮🇳"},
    "hi": {"name": "Hindi",     "native": "हिंदी",        "flag": "🇮🇳"},
    "te": {"name": "Telugu",    "native": "తెలుగు",       "flag": "🇮🇳"},
    "kn": {"name": "Kannada",   "native": "ಕನ್ನಡ",        "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "native": "മലയാളം",       "flag": "🇮🇳"},
}

# ─────────────────────────────────────────────────────────
# Document Type Registry
# Each doc entry: label, icon, ocr_capable (True=extract data, False=verify by upload)
# ─────────────────────────────────────────────────────────
DOC_REGISTRY = {
    "aadhaar": {
        "label":       "Aadhaar Card",
        "icon":        "🪪",
        "ocr_capable": True,
        "prompt_key":  "doc_prompt_aadhaar",
    },
    "pan": {
        "label":       "PAN Card",
        "icon":        "📄",
        "ocr_capable": True,
        "prompt_key":  "doc_prompt_pan",
    },
    "passbook": {
        "label":       "Bank Passbook",
        "icon":        "📘",
        "ocr_capable": True,
        "prompt_key":  "doc_prompt_passbook",
    },
    "photo": {
        "label":       "Passport Photo",
        "icon":        "📷",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_photo",
    },
    "address_proof": {
        "label":       "Address Proof",
        "icon":        "🏠",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_address_proof",
    },
    "voter_id": {
        "label":       "Voter ID / Passport / DL",
        "icon":        "🗳️",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_voter_id",
    },
    "beneficiary": {
        "label":       "Beneficiary Details",
        "icon":        "🏦",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_beneficiary",
    },
    "cheque": {
        "label":       "Cheque",
        "icon":        "📝",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_cheque",
    },
    "debit_card": {
        "label":       "Debit Card",
        "icon":        "💳",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_debit_card",
    },
    "nominee_id": {
        "label":       "Nominee ID Proof",
        "icon":        "👨‍👩‍👧",
        "ocr_capable": False,
        "prompt_key":  "doc_prompt_nominee_id",
    },
}

# ─────────────────────────────────────────────────────────
# Banking Service Types
# docs: list of DOC_REGISTRY keys required (in order)
# mandatory: subset that MUST be scanned (rest are optional)
# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────
# Banking Service Types
# ─────────────────────────────────────────────────────────
# "docs": list of required document types.
# "requires": list of fields needed for this service.
# If a field is in "requires", the kiosk will ask for it if missing.
# Note: "amount" triggers the DenominationScreen for cash_deposit/withdrawal.
FORM_TYPES = {
    "cash_withdrawal": {
        "category":  "cash",
        "label":     "Cash Withdrawal Slip",
        "icon":      "💸",
        "image":     "assets/signboards/sb_cash_withdrawal.png",
        "desc":      "Withdraw cash from account",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "amount"],
    },
    "cash_deposit": {
        "category":  "cash",
        "label":     "Cash Deposit Slip",
        "icon":      "💵",
        "image":     "assets/signboards/sb_cash_deposit.png",
        "desc":      "Deposit cash into account",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "amount"],
    },
    "neft_transfer": {
        "category":  "non-cash",
        "label":     "NEFT Form",
        "icon":      "🏦",
        "image":     "assets/signboards/sb_neft_transfer.png",
        "desc":      "National Electronic Funds Transfer",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "branch", "ifsc", "amount", "beneficiary_name", "beneficiary_acc", "beneficiary_ifsc"],
    },
    "rtgs_transfer": {
        "category":  "non-cash",
        "label":     "RTGS Form",
        "icon":      "⚡",
        "image":     "assets/signboards/sb_rtgs_transfer.png",
        "desc":      "Real Time Gross Settlement",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "branch", "ifsc", "amount", "beneficiary_name", "beneficiary_acc", "beneficiary_ifsc"],
    },
    "demand_draft": {
        "category":  "non-cash",
        "label":     "Demand Draft Application",
        "icon":      "📝",
        "image":     "assets/signboards/sb_demand_draft.png",
        "desc":      "Apply for a Demand Draft",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "branch", "amount", "beneficiary_name", "payable_at"],
    },
    "account_opening": {
        "category":  "non-cash",
        "label":     "Account Opening Form",
        "icon":      "👤",
        "image":     "assets/signboards/sb_account_opening.png",
        "desc":      "Open a new bank account",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "dob", "address", "aadhaar_number", "pan_number", "mobile"],
    },
    "atm_card": {
        "category":  "non-cash",
        "label":     "ATM Card Application",
        "icon":      "💳",
        "image":     "assets/signboards/sb_atm_card.png",
        "desc":      "Apply for a new ATM/Debit card",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "address", "mobile"],
    },
    "mobile_update": {
        "category":  "non-cash",
        "label":     "Mobile Number Update Form",
        "icon":      "📱",
        "image":     "assets/signboards/sb_mobile_update.png",
        "desc":      "Update registered mobile number",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "mobile", "aadhaar_number"],
    },
    "address_change": {
        "category":  "non-cash",
        "label":     "Address Change Form",
        "icon":      "🏠",
        "image":     "assets/signboards/sb_address_change.png",
        "desc":      "Update residential address",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "address"],
    },
    "nomination_form": {
        "category":  "non-cash",
        "label":     "Nomination Form",
        "icon":      "👨‍👩‍👧",
        "image":     "assets/signboards/sb_nomination_form.png",
        "desc":      "Add or update nominee details",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "nominee_name", "nominee_relation", "nominee_dob"],
    },
    "fixed_deposit": {
        "category":  "cash",
        "label":     "Fixed Deposit Opening Form",
        "icon":      "🏦",
        "image":     "assets/signboards/sb_fixed_deposit.png",
        "desc":      "Open a Fixed Deposit (FD)",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "branch", "ifsc", "amount", "tenure"],
    },
    "recurring_deposit": {
        "category":  "cash",
        "label":     "Recurring Deposit Opening Form",
        "icon":      "📅",
        "image":     "assets/signboards/sb_recurring_deposit.png",
        "desc":      "Open a Recurring Deposit (RD)",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "branch", "ifsc", "amount", "tenure"],
    },
    "cheque_deposit": {
        "category":  "cash",
        "label":     "Cheque Deposit Slip",
        "icon":      "📝",
        "image":     "assets/signboards/sb_cheque_deposit.png",
        "desc":      "Deposit a cheque into account",
        "docs":      ["aadhaar", "passbook", "cheque"],
        "mandatory": ["aadhaar", "passbook", "cheque"],
        "requires":  ["name", "account_no", "branch"],
    },
    "check_balance": {
        "category":  "cash",
        "label":     "Check Balance",
        "icon":      "💰",
        "image":     "assets/signboards/sb_check_balance.png",
        "desc":      "Check account balance",
        "docs":      ["passbook"],
        "mandatory": ["passbook"],
        "requires":  ["name", "account_no"],
    },
    "kyc_update": {
        "category":  "non-cash",
        "label":     "KYC Update Form",
        "icon":      "🔄",
        "image":     "assets/signboards/sb_kyc_update.png",
        "desc":      "Update KYC documents",
        "docs":      ["aadhaar", "pan", "passbook"],
        "mandatory": ["aadhaar", "pan", "passbook"],
        "requires":  ["name", "account_no", "aadhaar_number", "pan_number", "mobile", "address"],
    },
    "cheque_book": {
        "category":  "non-cash",
        "label":     "Cheque Book Request",
        "icon":      "📒",
        "image":     "assets/signboards/sb_cheque_book.png",
        "desc":      "Request a new cheque book",
        "docs":      ["aadhaar", "passbook"],
        "mandatory": ["aadhaar", "passbook"],
        "requires":  ["name", "account_no", "branch"],
    },
    "passbook_update": {
        "category":  "non-cash",
        "label":     "Passbook Update Request",
        "icon":      "📘",
        "image":     "assets/signboards/sb_passbook_update.png",
        "desc":      "Request passbook update / reprint",
        "docs":      ["aadhaar", "passbook"],
        "mandatory": ["aadhaar", "passbook"],
        "requires":  ["name", "account_no", "branch"],
    },
}

