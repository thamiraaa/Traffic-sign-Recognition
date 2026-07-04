"""
form_generator.py — PDF bank form generation using ReportLab.

Generates professional, printable bank forms pre-filled with
extracted data. Supports all form-type specific layouts:
  • SBI Cash Deposit / Withdrawal Slip (SBI-replica layout)
  • Cheque Deposit Slip
  • NEFT Transfer Form
  • RTGS Transfer Form
  • Demand Draft Application
  • Account Opening Form
  • KYC Update Form
  • ATM Card Application
  • Cheque Book Request
  • Mobile Number Update
  • Address Change Form
  • Nomination Form
  • Fixed Deposit (FD) Form
  • Recurring Deposit (RD) Form
  • Passbook Update Request
  • Generic / Other
"""

import os
import random
import string
from datetime import date

from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import config
from translations import t

try:
    pdfmetrics.registerFont(TTFont('Tamil', 'C:\\Windows\\Fonts\\latha.ttf'))
    pdfmetrics.registerFont(TTFont('Hindi', 'C:\\Windows\\Fonts\\mangal.ttf'))
    pdfmetrics.registerFont(TTFont('Telugu', 'C:\\Windows\\Fonts\\gautami.ttf'))
    pdfmetrics.registerFont(TTFont('Kannada', 'C:\\Windows\\Fonts\\tunga.ttf'))
    pdfmetrics.registerFont(TTFont('Malayalam', 'C:\\Windows\\Fonts\\kartika.ttf'))
except Exception as e:
    print(f"Font registration warning: {e}")

def get_font_for_lang(lang):
    font_map = {'ta': 'Tamil', 'hi': 'Hindi', 'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam'}
    font_name = font_map.get(lang, 'Helvetica')
    try:
        pdfmetrics.getFont(font_name)
        return font_name
    except:
        return 'Helvetica'


# ─────────────────────────────────────────────────────────
# Colour definitions
# ─────────────────────────────────────────────────────────
SBI_BLUE    = colors.HexColor("#22409A")   # SBI brand blue
SBI_DARK    = colors.HexColor("#0D1B5E")   # SBI dark header
SBI_LIGHT   = colors.HexColor("#EEF2FF")   # SBI light background
SBI_BORDER  = colors.HexColor("#8FA0C8")   # SBI border grey-blue
NAVY        = colors.HexColor("#0D1B2A")
BLUE        = colors.HexColor("#0077B6")
CYAN        = colors.HexColor("#00B4D8")
WHITE       = colors.white
SILVER      = colors.HexColor("#E0E9F4")
LIGHT       = colors.HexColor("#F4F9FF")
GREEN       = colors.HexColor("#06D6A0")
AMBER       = colors.HexColor("#FFD166")
RED         = colors.HexColor("#E02424")


# ─────────────────────────────────────────────────────────
# Transaction ID generator
# ─────────────────────────────────────────────────────────

def _gen_txn_id() -> str:
    """Generate a unique transaction ID."""
    chars = string.ascii_uppercase + string.digits
    return "TXN" + date.today().strftime("%Y%m%d") + "".join(
        random.choices(chars, k=8)
    )

def amount_to_words(amount) -> str:
    """Converts a number to its Indian Rupee words representation."""
    if not amount or not str(amount).isdigit() or int(amount) == 0:
        return ""
    amount = int(amount)
    
    def convert_below_1000(n):
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", 
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", 
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        word = ""
        if n > 99:
            word += ones[n // 100] + " Hundred "
            n %= 100
        if n > 19:
            word += tens[n // 10] + " "
            word += ones[n % 10]
        else:
            word += ones[n]
        return word.strip()

    parts = []
    
    crores = amount // 10000000
    if crores > 0:
        parts.append(convert_below_1000(crores) + " Crore")
        amount %= 10000000
        
    lakhs = amount // 100000
    if lakhs > 0:
        parts.append(convert_below_1000(lakhs) + " Lakh")
        amount %= 100000
        
    thousands = amount // 1000
    if thousands > 0:
        parts.append(convert_below_1000(thousands) + " Thousand")
        amount %= 1000
        
    if amount > 0:
        parts.append(convert_below_1000(amount))
        
    return " ".join(parts).strip() + " Rupees Only"


# ─────────────────────────────────────────────────────────
# Style definitions
# ─────────────────────────────────────────────────────────

def _styles(lang="en"):
    fn_reg = get_font_for_lang(lang)
    fn_bold = fn_reg if lang != "en" else "Helvetica-Bold"
    
    return {
        "sbi_title": ParagraphStyle(
            "sbi_title",
            fontSize=16, fontName=fn_bold,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=2
        ),
        "sbi_sub": ParagraphStyle(
            "sbi_sub",
            fontSize=8, fontName=fn_reg,
            textColor=colors.HexColor("#C8D4FF"), alignment=TA_CENTER
        ),
        "form_title": ParagraphStyle(
            "form_title",
            fontSize=13, fontName=fn_bold,
            textColor=SBI_BLUE, alignment=TA_CENTER,
            spaceBefore=4, spaceAfter=6
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontSize=9, fontName=fn_bold,
            textColor=WHITE, spaceBefore=2, spaceAfter=2
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontSize=8, fontName=fn_bold,
            textColor=NAVY
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontSize=9, fontName=fn_reg,
            textColor=NAVY
        ),
        "field_value_large": ParagraphStyle(
            "field_value_large",
            fontSize=11, fontName=fn_bold,
            textColor=SBI_DARK
        ),
        "box_label": ParagraphStyle(
            "box_label",
            fontSize=7, fontName=fn_reg,
            textColor=colors.grey
        ),
        "footer": ParagraphStyle(
            "footer",
            fontSize=7, fontName=fn_reg,
            textColor=colors.grey, alignment=TA_CENTER
        ),
        "decl": ParagraphStyle(
            "decl",
            fontSize=8, fontName=fn_reg,
            textColor=colors.HexColor("#4A6E8A"), leading=12
        ),
        "amount_box": ParagraphStyle(
            "amount_box",
            fontSize=20, fontName=fn_bold,
            textColor=SBI_DARK, alignment=TA_CENTER
        ),
        "checkbox_label": ParagraphStyle(
            "checkbox_label",
            fontSize=8, fontName=fn_reg,
            textColor=NAVY
        ),
        "pan_decl": ParagraphStyle(
            "pan_decl",
            fontSize=7.5, fontName=fn_reg,
            textColor=NAVY, leading=11
        ),
        "txn_id": ParagraphStyle(
            "txn_id",
            fontSize=9, fontName=fn_bold,
            textColor=SBI_BLUE, alignment=TA_CENTER
        ),
    }


# ─────────────────────────────────────────────────────────
# Shared layout helpers
# ─────────────────────────────────────────────────────────

def _sbi_header(s: dict, form_label: str, txn_id: str) -> list:
    """SBI-branded header banner."""
    elements = []

    # Main header table — two columns: bank name + txn id
    header_data = [[
        Paragraph("STATE BANK OF INDIA", s["sbi_title"]),
        Paragraph(f"TXN: {txn_id}", s["sbi_sub"]),
    ]]
    ht = Table(header_data, colWidths=[13 * cm, 4 * cm])
    ht.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SBI_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (0, 0),   14),
        ("RIGHTPADDING",  (-1, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(ht)

    # Blue accent strip
    strip = Table([[""]], colWidths=[17 * cm])
    strip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SBI_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(strip)

    # Form label line
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(form_label, s["form_title"]))
    elements.append(HRFlowable(
        width="100%", thickness=1.5, color=SBI_BLUE, spaceAfter=6
    ))
    return elements


def _section_banner(label: str, s: dict) -> Table:
    """Small dark-blue section header bar."""
    t = Table([[Paragraph(label, s["section_header"])]], colWidths=[17 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SBI_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return t


def _field_row(label: str, value: str, s: dict):
    label_p = Paragraph(label, s["field_label"])
    val     = str(value) if value and value != "Not found" else "____________________"
    val_p   = Paragraph(val, s["field_value"])
    return [label_p, val_p]


def _append_extracted_data_section(story: list, data: dict, s: dict):
    """Appends all extra extracted OCR data to the form to ensure zero data loss."""
    skip = {"doc_type", "date", "_raw_text", "_confidence", "ai_enhanced", "ai_error", "system_date", "form_type_lbl", "amount_in_words"}
    labels_map = {
        "name": "Full Name", "dob": "Date of Birth", "gender": "Gender",
        "aadhaar_number": "Aadhaar Number", "address": "Address",
        "holder_name": "Account Holder", "account_no": "Account Number",
        "ifsc": "IFSC Code", "branch": "Branch", "bank_name": "Bank Name",
        "micr": "MICR Code", "mobile": "Mobile Number", "cif": "Customer ID (CIF)",
        "pan_number": "PAN Number", "father_name": "Father Name",
        "amount": "Amount (₹)", "cheque_no": "Cheque Number",
    }
    
    rows = []
    for k, v in data.items():
        if k not in skip and v and v != "Not found":
            label = labels_map.get(k, k.replace("_", " ").title())
            rows.append(_field_row(label, v, s))
            
    if rows:
        story.append(Spacer(1, 10))
        story.append(_section_banner("CUSTOMER KYC / EXTRACTED DATA", s))
        story.append(_fields_table(rows))
        story.append(Spacer(1, 5))



def _fields_table(rows: list, col_widths=None) -> Table:
    """Two-column field table with SBI styling."""
    cw = col_widths or [5 * cm, 12 * cm]
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("BACKGROUND",    (1, 0), (1, -1), WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    return t


def _signature_block(s: dict) -> list:
    """Standard declaration + 3-column signature area."""
    elements = []
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=SBI_BORDER, spaceAfter=6
    ))
    elements.append(Paragraph(
        "I hereby declare that the information provided above is true and correct "
        "to the best of my knowledge. This form has been auto-filled by the AI Bank "
        "Kiosk system and should be verified before submission to the bank.",
        s["decl"]
    ))
    elements.append(Spacer(1, 0.8 * cm))
    sig_rows = [[
        Paragraph("_______________________", s["field_label"]),
        Paragraph("_______________________", s["field_label"]),
        Paragraph("_______________________", s["field_label"]),
    ], [
        Paragraph("Applicant Signature", s["footer"]),
        Paragraph("Date: " + str(date.today()), s["footer"]),
        Paragraph("Bank Official Seal", s["footer"]),
    ]]
    sig_t = Table(sig_rows, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    sig_t.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_t)
    return elements


def _footer_qr(s: dict, data: dict, txn_id: str) -> list:
    """Bottom bar with transaction info."""
    elements = []
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=SILVER))

    ai_note = "✅ AI-Enhanced (Gemini Vision)" if data.get("ai_enhanced") else "📋 OCR Extracted"
    footer_data = [[
        Paragraph(
            f"<b>Transaction ID:</b> {txn_id}<br/>"
            f"<b>Date:</b> {date.today().strftime('%d %B %Y')}<br/>"
            f"<b>Branch:</b> {data.get('branch', 'N/A')}<br/>"
            f"{ai_note}",
            s["footer"]
        ),
        Paragraph(
            "For bank use only\n\n\n____________________\nCashier / Teller",
            s["footer"]
        ),
    ]]
    ft = Table(footer_data, colWidths=[12 * cm, 5 * cm])
    ft.setStyle(TableStyle([
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(ft)
    return elements


# ─────────────────────────────────────────────────────────
# SBI Cash Deposit / Withdrawal Slip — Replica Layout
# ─────────────────────────────────────────────────────────

def _build_sbi_deposit_slip(data: dict, s: dict, form_type: str, txn_id: str, lang: str = "en") -> list:
    """
    SBI-replica Cash Deposit / Withdrawal Slip with:
    - Account details section
    - Denomination table (₹500/₹200/₹100/₹50/₹20/₹10/coins)
    - PAN declaration section
    - Signature + bank use columns
    """
    is_deposit = (form_type == "cash_deposit")
    label = t("CASH DEPOSIT SLIP", lang) if is_deposit else t("CASH WITHDRAWAL SLIP", lang)
    story = _sbi_header(s, label, txn_id)

    name  = data.get("name") or data.get("holder_name") or "____________________"
    acct  = data.get("account_no", "____________________")
    br    = data.get("branch", "____________________")
    mob   = data.get("mobile", "____________________")
    bank  = data.get("bank_name", "State Bank of India")
    ifsc  = data.get("ifsc", "____________________")
    today = date.today().strftime("%d / %m / %Y")
    amount = data.get("amount", "")

    # ── TOP SECTION: Date + Branch ──────────────────────
    story.append(Spacer(1, 3))
    top_data = [[
        Paragraph(t("Branch:", lang), s["field_label"]),
        Paragraph(br, s["field_value_large"]),
        Paragraph(t("Date:", lang), s["field_label"]),
        Paragraph(today, s["field_value_large"]),
    ]]
    top_t = Table(top_data, colWidths=[2 * cm, 7 * cm, 1.8 * cm, 6 * cm])
    top_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, 0), SBI_LIGHT),
        ("BACKGROUND",    (2, 0), (2, 0), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(top_t)
    story.append(Spacer(1, 5))

    # ── ACCOUNT DETAILS ─────────────────────────────────
    story.append(_section_banner(t("ACCOUNT DETAILS", lang), s))
    acct_data = [
        [Paragraph(t("Account Holder Name:", lang), s["field_label"]),
         Paragraph(name, s["field_value_large"]),
         Paragraph(t("Mobile No.:", lang), s["field_label"]),
         Paragraph(mob, s["field_value"])],
        [Paragraph(t("Account Number:", lang), s["field_label"]),
         Paragraph(acct, s["field_value_large"]),
         Paragraph(t("IFSC Code:", lang), s["field_label"]),
         Paragraph(ifsc, s["field_value"])],
        [Paragraph(t("Bank Name:", lang), s["field_label"]),
         Paragraph(bank, s["field_value"]),
         Paragraph(t("Type:", lang), s["field_label"]),
         Paragraph("☑ Savings  ☐ Current  ☐ Other", s["checkbox_label"])],
    ]
    acct_t = Table(acct_data, colWidths=[3.5 * cm, 5.5 * cm, 2.5 * cm, 5.5 * cm])
    acct_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("BACKGROUND",    (2, 0), (2, -1), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(acct_t)
    story.append(Spacer(1, 6))

    # ── CASH DEPOSIT TYPE CHECKBOXES ─────────────────────
    cb_data = [[
        Paragraph(t("Mode of Deposit:", lang), s["field_label"]),
        Paragraph("☑ Cash   ☐ Cheque   ☐ DD", s["checkbox_label"]),
        Paragraph(t("Currency:", lang), s["field_label"]),
        Paragraph("☑ INR (₹)   ☐ Foreign Currency", s["checkbox_label"]),
    ]]
    cb_t = Table(cb_data, colWidths=[3.5 * cm, 5.5 * cm, 2.5 * cm, 5.5 * cm])
    cb_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("BACKGROUND",    (2, 0), (2, -1), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(cb_t)
    story.append(Spacer(1, 6))

    # ── DENOMINATION TABLE + AMOUNT BOX ─────────────────
    story.append(_section_banner(t("CASH DENOMINATION DETAILS", lang), s))
    denom_header = [
        [Paragraph(t("Denomination", lang), s["field_label"]),
         Paragraph(t("No. of Notes", lang), s["field_label"]),
         Paragraph(t("Amount (₹)", lang), s["field_label"])],
    ]
    denom_rows = [
        ["₹ 500", "", ""],
        ["₹ 200", "", ""],
        ["₹ 100", "", ""],
        ["₹ 50",  "", ""],
        ["₹ 20",  "", ""],
        ["₹ 10",  "", ""],
        ["Coins", "", ""],
    ]
    denom_data = denom_header + [
        [Paragraph(r[0], s["field_value"]),
         Paragraph(r[1], s["field_value"]),
         Paragraph(r[2], s["field_value"])]
        for r in denom_rows
    ]
    # Total row
    denom_data.append([
        Paragraph("<b>TOTAL AMOUNT</b>", s["field_label"]),
        Paragraph("", s["field_value"]),
        Paragraph(f"<b>₹ {amount if amount else '____________'}</b>",
                  s["field_label"]),
    ])

    # Amount in words row
    amt_words = amount_to_words(amount) if amount else "_______________________________________"
    denom_data.append([
        Paragraph("<b>Amount in Words</b>", s["field_label"]),
        Paragraph(amt_words, s["field_value"]),
        Paragraph("", s["field_value"]),
    ])

    denom_t = Table(denom_data, colWidths=[4 * cm, 6.5 * cm, 6.5 * cm])
    denom_t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0), SBI_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        # Denomination label column
        ("BACKGROUND",    (0, 1), (0, -3), SBI_LIGHT),
        # Total row
        ("BACKGROUND",    (0, -2), (-1, -2), colors.HexColor("#FFFDE7")),
        # Words row
        ("BACKGROUND",    (0, -1), (-1, -1), SBI_LIGHT),
        # Spanning for words row
        ("SPAN",          (1, -1), (2, -1)),
        # Spanning for total label
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("FONTNAME",      (0, -2), (0, -2), "Helvetica-Bold"),
        ("FONTSIZE",      (2, -2), (2, -2), 11),
        ("TEXTCOLOR",     (2, -2), (2, -2), SBI_DARK),
    ]))
    story.append(denom_t)
    story.append(Spacer(1, 6))

    # ── PAN DECLARATION ─────────────────────────────────
    pan_no   = data.get("pan_number", "________________")
    pan_text = (
        f"PAN / Form 60 Declaration:  PAN: <b>{pan_no}</b>   "
        "☑ I confirm that the PAN provided is correct.   "
        "☐ Form 60 Attached (if PAN not available)"
    )
    story.append(_section_banner("PAN DECLARATION (Mandatory for deposits above ₹50,000)", s))
    pan_t = Table([[Paragraph(pan_text, s["pan_decl"])]], colWidths=[17 * cm])
    pan_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(pan_t)
    story.append(Spacer(1, 6))

    # ── DEPOSITOR NAME + SIGNATURE ───────────────────────
    story.append(_section_banner("DEPOSITOR DETAILS & SIGNATURE", s))
    dep_data = [[
        Paragraph("Depositor Name:", s["field_label"]),
        Paragraph(name, s["field_value_large"]),
        Paragraph("Signature:", s["field_label"]),
        Paragraph("\n\n\n____________________", s["field_value"]),
    ]]
    dep_t = Table(dep_data, colWidths=[3.2 * cm, 6.3 * cm, 2.5 * cm, 5 * cm])
    dep_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("BACKGROUND",    (2, 0), (2, -1), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(dep_t)
    story.append(Spacer(1, 4))

    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Cheque Deposit Slip
# ─────────────────────────────────────────────────────────

def _build_cheque_deposit(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "CHEQUE DEPOSIT SLIP", txn_id)
    name = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("CHEQUE DETAILS", s))
    rows = [
        _field_row("Cheque Number",   data.get("cheque_no", ""), s),
        _field_row("Cheque Date",     data.get("cheque_date", ""), s),
        _field_row("Drawn on Bank",   data.get("bank_name", ""), s),
        _field_row("Amount (₹)",      data.get("amount", ""), s),
        _field_row("Amount in Words", amount_to_words(data.get("amount", "")), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("DEPOSITOR ACCOUNT DETAILS", s))
    rows2 = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
        _field_row("IFSC Code",           data.get("ifsc", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Date",                str(date.today()), s),
    ]
    story.append(_fields_table(rows2))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# NEFT / RTGS Transfer Form
# ─────────────────────────────────────────────────────────

def _build_neft_rtgs_form(data: dict, s: dict, form_type: str, txn_id: str) -> list:
    label = "NEFT TRANSFER APPLICATION FORM" if form_type == "neft_transfer" else "RTGS TRANSFER APPLICATION FORM"
    desc  = "National Electronic Funds Transfer" if form_type == "neft_transfer" else "Real Time Gross Settlement (Min ₹2 Lakhs)"
    story = _sbi_header(s, label, txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(Paragraph(desc, s["decl"]))
    story.append(Spacer(1, 6))

    story.append(_section_banner("REMITTER DETAILS (Your Details)", s))
    rows1 = [
        _field_row("Name",           name, s),
        _field_row("Account Number", data.get("account_no", ""), s),
        _field_row("IFSC Code",      data.get("ifsc", ""), s),
        _field_row("Branch",         data.get("branch", ""), s),
        _field_row("Mobile Number",  data.get("mobile", ""), s),
    ]
    story.append(_fields_table(rows1))
    story.append(Spacer(1, 6))

    story.append(_section_banner("BENEFICIARY DETAILS (Recipient)", s))
    rows2 = [
        _field_row("Beneficiary Name",           "", s),
        _field_row("Beneficiary Account Number", "", s),
        _field_row("Beneficiary Bank Name",      "", s),
        _field_row("Beneficiary IFSC Code",      "", s),
        _field_row("Beneficiary Branch",         "", s),
    ]
    story.append(_fields_table(rows2))
    story.append(Spacer(1, 6))

    story.append(_section_banner("TRANSFER DETAILS", s))
    rows3 = [
        _field_row("Amount (₹)",      data.get("amount", ""), s),
        _field_row("Amount in Words", amount_to_words(data.get("amount", "")), s),
        _field_row("Purpose of Transfer", "", s),
        _field_row("Date",            str(date.today()), s),
    ]
    story.append(_fields_table(rows3))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Demand Draft Application
# ─────────────────────────────────────────────────────────

def _build_demand_draft(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "DEMAND DRAFT APPLICATION FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("APPLICANT DETAILS", s))
    rows1 = [
        _field_row("Applicant Name",    name, s),
        _field_row("Account Number",    data.get("account_no", ""), s),
        _field_row("Mobile Number",     data.get("mobile", ""), s),
        _field_row("Branch",            data.get("branch", ""), s),
        _field_row("PAN Number",        data.get("pan_number", ""), s),
    ]
    story.append(_fields_table(rows1))
    story.append(Spacer(1, 6))

    story.append(_section_banner("DD DETAILS", s))
    rows2 = [
        _field_row("DD Amount (₹)",     data.get("amount", ""), s),
        _field_row("Amount in Words",   amount_to_words(data.get("amount", "")), s),
        _field_row("Payable at City",   "", s),
        _field_row("Payable to (Beneficiary Name)", "", s),
        _field_row("Date",              str(date.today()), s),
    ]
    story.append(_fields_table(rows2))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Account Opening Form
# ─────────────────────────────────────────────────────────

def _build_account_opening(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "SAVINGS ACCOUNT OPENING FORM", txn_id)

    story.append(_section_banner("PERSONAL DETAILS", s))
    rows = [
        _field_row("Full Name",       data.get("name", ""), s),
        _field_row("Date of Birth",   data.get("dob", ""), s),
        _field_row("Gender",          data.get("gender", ""), s),
        _field_row("Father's Name",   data.get("father_name", ""), s),
        _field_row("Mobile Number",   data.get("mobile", ""), s),
        _field_row("Address",         data.get("address", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("IDENTITY DOCUMENTS", s))
    rows2 = [
        _field_row("Aadhaar Number",  data.get("aadhaar_number", ""), s),
        _field_row("PAN Number",      data.get("pan_number", ""), s),
    ]
    story.append(_fields_table(rows2))
    story.append(Spacer(1, 6))

    story.append(_section_banner("ACCOUNT PREFERENCES", s))
    rows3 = [
        _field_row("Account Type",      "Savings Account", s),
        _field_row("Nominee Name",      "", s),
        _field_row("Nominee Relation",  "", s),
        _field_row("Nominee Date of Birth", "", s),
    ]
    story.append(_fields_table(rows3))
    story.append(Spacer(1, 6))

    intro_data = [[Paragraph(
        "☑ I agree to comply with the rules and regulations of the bank.  "
        "☑ I confirm the above details are true and correct.",
        s["checkbox_label"]
    )]]
    intro_t = Table(intro_data, colWidths=[17 * cm])
    intro_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(intro_t)
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# KYC Update Form
# ─────────────────────────────────────────────────────────

def _build_kyc_update(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "KYC UPDATE FORM", txn_id)

    story.append(_section_banner("CUSTOMER DETAILS", s))
    rows = [
        _field_row("Full Name",      data.get("name", ""), s),
        _field_row("Date of Birth",  data.get("dob", ""), s),
        _field_row("Gender",         data.get("gender", ""), s),
        _field_row("Mobile Number",  data.get("mobile", ""), s),
        _field_row("Address",        data.get("address", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("IDENTITY VERIFICATION", s))
    rows2 = [
        _field_row("Aadhaar Number", data.get("aadhaar_number", ""), s),
        _field_row("PAN Number",     data.get("pan_number", ""), s),
        _field_row("Account Number", data.get("account_no", ""), s),
        _field_row("IFSC Code",      data.get("ifsc", ""), s),
    ]
    story.append(_fields_table(rows2))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# ATM Card Application
# ─────────────────────────────────────────────────────────

def _build_atm_card(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "ATM / DEBIT CARD APPLICATION FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("APPLICANT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch Name",         data.get("branch", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Address",             data.get("address", ""), s),
        _field_row("Aadhaar Number",      data.get("aadhaar_number", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("CARD PREFERENCES", s))
    pref_data = [[
        Paragraph("Card Type:", s["field_label"]),
        Paragraph("☑ Classic  ☐ Gold  ☐ Platinum  ☐ International", s["checkbox_label"]),
        Paragraph("Network:", s["field_label"]),
        Paragraph("☑ Visa  ☐ RuPay  ☐ MasterCard", s["checkbox_label"]),
    ]]
    pref_t = Table(pref_data, colWidths=[2.5 * cm, 6.5 * cm, 2 * cm, 6 * cm])
    pref_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("BACKGROUND",    (2, 0), (2, -1), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(pref_t)
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Cheque Book Request
# ─────────────────────────────────────────────────────────

def _build_cheque_book(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "CHEQUE BOOK REQUEST FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("ACCOUNT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Date",                str(date.today()), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("CHEQUE BOOK PREFERENCES", s))
    pref_data = [[
        Paragraph("No. of Leaves:", s["field_label"]),
        Paragraph("☑ 10 Leaves  ☐ 25 Leaves  ☐ 50 Leaves  ☐ 100 Leaves", s["checkbox_label"]),
    ], [
        Paragraph("Delivery:", s["field_label"]),
        Paragraph("☑ Branch Pickup  ☐ Courier to Registered Address", s["checkbox_label"]),
    ]]
    pref_t = Table(pref_data, colWidths=[3 * cm, 14 * cm])
    pref_t.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, SBI_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1), SBI_LIGHT),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(pref_t)
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Mobile Number Update
# ─────────────────────────────────────────────────────────

def _build_mobile_update(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "MOBILE NUMBER UPDATE REQUEST", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("ACCOUNT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
        _field_row("Aadhaar Number",      data.get("aadhaar_number", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("MOBILE NUMBER UPDATE", s))
    mob_data = [
        _field_row("Existing Mobile Number", data.get("mobile", ""), s),
        _field_row("New Mobile Number",       "", s),
        _field_row("Confirm New Mobile No.",  "", s),
        _field_row("Reason for Change",       "", s),
    ]
    story.append(_fields_table(mob_data))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Address Change Form
# ─────────────────────────────────────────────────────────

def _build_address_change(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "ADDRESS CHANGE REQUEST FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("ACCOUNT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Aadhaar Number",      data.get("aadhaar_number", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("ADDRESS DETAILS", s))
    addr_data = [
        _field_row("Current Registered Address", data.get("address", ""), s),
        _field_row("New Address Line 1",          "", s),
        _field_row("New Address Line 2",          "", s),
        _field_row("City",                        "", s),
        _field_row("State",                       "", s),
        _field_row("PIN Code",                    "", s),
        _field_row("Address Proof Submitted",     "☑ Aadhaar  ☐ Utility Bill  ☐ Other", s),
    ]
    story.append(_fields_table(addr_data))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Nomination Form
# ─────────────────────────────────────────────────────────

def _build_nomination_form(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "NOMINATION FORM (Form DA-1)", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("ACCOUNT HOLDER DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("NOMINEE DETAILS", s))
    nom_data = [
        _field_row("Nominee Full Name",         "", s),
        _field_row("Nominee Date of Birth",     "", s),
        _field_row("Relationship with Account Holder", "", s),
        _field_row("Nominee Address",           "", s),
        _field_row("Nominee Mobile Number",     "", s),
        _field_row("Nominee Aadhaar Number",    "", s),
    ]
    story.append(_fields_table(nom_data))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Fixed Deposit (FD) Form
# ─────────────────────────────────────────────────────────

def _build_fd_form(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "FIXED DEPOSIT APPLICATION FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("APPLICANT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("PAN Number",          data.get("pan_number", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("FD DETAILS", s))
    fd_data = [
        _field_row("Principal Amount (₹)",   data.get("amount", ""), s),
        _field_row("Amount in Words",         amount_to_words(data.get("amount", "")), s),
        _field_row("Tenure (Months/Years)",   "", s),
        _field_row("Interest Payout",         "☑ On Maturity  ☐ Monthly  ☐ Quarterly  ☐ Annually", s),
        _field_row("Maturity Instruction",    "☑ Auto-Renew Principal  ☐ Credit to Account", s),
        _field_row("Nominee Name",            "", s),
        _field_row("Date",                    str(date.today()), s),
    ]
    story.append(_fields_table(fd_data))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Recurring Deposit (RD) Form
# ─────────────────────────────────────────────────────────

def _build_rd_form(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "RECURRING DEPOSIT APPLICATION FORM", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("APPLICANT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("PAN Number",          data.get("pan_number", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
    ]
    story.append(_fields_table(rows))
    story.append(Spacer(1, 6))

    story.append(_section_banner("RD DETAILS", s))
    rd_data = [
        _field_row("Monthly Instalment (₹)", data.get("amount", ""), s),
        _field_row("Amount in Words",         amount_to_words(data.get("amount", "")), s),
        _field_row("Tenure (Months)",         "", s),
        _field_row("Total Maturity Amount",   "", s),
        _field_row("Interest Rate",           "As per bank schedule", s),
        _field_row("Auto-Debit from Account", "☑ Yes  ☐ No", s),
        _field_row("Debit Date (of month)",   "", s),
        _field_row("Nominee Name",            "", s),
        _field_row("Date",                    str(date.today()), s),
    ]
    story.append(_fields_table(rd_data))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Passbook Update
# ─────────────────────────────────────────────────────────

def _build_passbook_update(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "PASSBOOK UPDATE REQUEST", txn_id)
    name  = data.get("name") or data.get("holder_name", "—")

    story.append(_section_banner("ACCOUNT DETAILS", s))
    rows = [
        _field_row("Account Holder Name", name, s),
        _field_row("Account Number",      data.get("account_no", ""), s),
        _field_row("Branch",              data.get("branch", ""), s),
        _field_row("Bank Name",           data.get("bank_name", ""), s),
        _field_row("Mobile Number",       data.get("mobile", ""), s),
        _field_row("Date",                str(date.today()), s),
    ]
    story.append(_fields_table(rows))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Generic / Other Form
# ─────────────────────────────────────────────────────────

def _build_generic(data: dict, s: dict, txn_id: str) -> list:
    story = _sbi_header(s, "BANK SERVICE REQUEST FORM", txn_id)
    skip  = {"doc_type", "date", "_raw_text", "_confidence", "ai_enhanced", "ai_error"}
    labels_map = {
        "name": "Full Name", "dob": "Date of Birth", "gender": "Gender",
        "aadhaar_number": "Aadhaar Number", "address": "Address",
        "holder_name": "Account Holder", "account_no": "Account Number",
        "ifsc": "IFSC Code", "branch": "Branch", "bank_name": "Bank Name",
        "micr": "MICR Code", "mobile": "Mobile Number",
        "pan_number": "PAN Number", "father_name": "Father Name",
        "amount": "Amount (₹)", "cheque_no": "Cheque Number",
    }

    story.append(_section_banner("EXTRACTED DATA", s))
    rows = [
        _field_row(labels_map.get(k, k.replace("_", " ").title()), v, s)
        for k, v in data.items()
        if k not in skip
    ]
    if rows:
        story.append(_fields_table(rows))
    _append_extracted_data_section(story, data, s)
    story += _signature_block(s)
    story += _footer_qr(s, data, txn_id)
    return story


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def generate_form_by_type(data: dict, form_type: str,
                          output_path: str = None, lang: str = "en") -> str:
    """
    Generate a filled bank form PDF for the given *form_type*.

    Args:
        data        : dict returned by extractor + ai_helper + user edits
        form_type   : key from config.FORM_TYPES
        output_path : optional full file path for the PDF
        lang        : language code for translating labels (e.g., "ta", "hi")

    Returns:
        The absolute path to the generated PDF.
    """
    if output_path is None:
        output_path = os.path.join(config.PDF_OUTPUT_DIR, config.PDF_FILENAME)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    s = _styles(lang)
    txn_id = _gen_txn_id()

    dispatch = {
        "cash_deposit":     lambda: _build_sbi_deposit_slip(data, s, "cash_deposit", txn_id, lang),
        "cash_withdrawal":  lambda: _build_sbi_deposit_slip(data, s, "cash_withdrawal", txn_id, lang),
        "cheque_deposit":   lambda: _build_cheque_deposit(data, s, txn_id),
        "check_balance":    lambda: _build_generic(data, s, txn_id),
        "neft_transfer":    lambda: _build_neft_rtgs_form(data, s, "neft_transfer", txn_id),
        "rtgs_transfer":    lambda: _build_neft_rtgs_form(data, s, "rtgs_transfer", txn_id),
        "demand_draft":     lambda: _build_demand_draft(data, s, txn_id),
        "account_opening":  lambda: _build_account_opening(data, s, txn_id),
        "kyc_update":       lambda: _build_kyc_update(data, s, txn_id),
        "atm_card":         lambda: _build_atm_card(data, s, txn_id),
        "cheque_book":      lambda: _build_cheque_book(data, s, txn_id),
        "mobile_update":    lambda: _build_mobile_update(data, s, txn_id),
        "address_change":   lambda: _build_address_change(data, s, txn_id),
        "nomination_form":  lambda: _build_nomination_form(data, s, txn_id),
        "fixed_deposit":    lambda: _build_fd_form(data, s, txn_id),
        "recurring_deposit":lambda: _build_rd_form(data, s, txn_id),
        "passbook_update":  lambda: _build_passbook_update(data, s, txn_id),
    }

    builder = dispatch.get(form_type)
    story = builder() if builder else _build_generic(data, s, txn_id)

    doc.build(story)
    return output_path


# ─────────────────────────────────────────────────────────
# Backward-compatible wrapper
# ─────────────────────────────────────────────────────────

def generate_bank_form(data: dict, output_path: str = None) -> str:
    """Backward-compatible API — calls generate_form_by_type with 'other'."""
    return generate_form_by_type(data, "other", output_path)
