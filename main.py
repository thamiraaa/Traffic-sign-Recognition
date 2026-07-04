"""
main.py — Auto Bank Form Filling System
Fully Multilingual AI-Powered Kiosk based on new comprehensive requirements.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
from datetime import date

import config
import ocr_engine
import extractor
import ai_helper
import form_generator
import tts_engine
import db_logger
import security
from translations import t
from keypad_widget import attach_keypad, KeypadPopup

# Set CustomTkinter appearance to Light mode for professional banking look
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# ═══════════════════════════════════════════════════════════
# KioskApp
# ═══════════════════════════════════════════════════════════

class KioskApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.configure(fg_color=config.COLOR_BG)

        if config.FULLSCREEN:
            self.attributes("-fullscreen", True)

        # ── Kiosk-wide state ─────────────────────────────
        self.language         = tk.StringVar(value="en")
        self.form_type        = tk.StringVar(value="other_services")
        self.doc_type         = tk.StringVar(value="aadhaar")
        self.image_path       = tk.StringVar(value="")

        self.scanned_docs: dict = {}
        self.ocr_result: dict = {}
        self.temp_files: list = []

        self.last_pdf_path = ""
        self.last_txn_id   = ""
        self.current_scan_doc = ""
        self.is_editing_all = False  # Flag for full edit mode

        # ── Container ────────────────────────────────────
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ── Build all screens ────────────────────────────
        self.screens = {}
        for ScreenClass in (
            LanguageScreen,
            CoinScreen,
            ServiceScreen,
            DocumentTrackerScreen,
            ScanScreen,
            DenominationScreen,
            MissingInfoScreen,
            ConfirmationScreen,
            ReceiptScreen,
        ):
            screen = ScreenClass(self.container, self)
            self.screens[ScreenClass.__name__] = screen
            screen.grid(row=0, column=0, sticky="nsew")

        self.show_screen("LanguageScreen")

    def show_screen(self, name: str):
        screen = self.screens[name]
        screen.on_show()
        screen.tkraise()

    def get_lang(self) -> str:
        return self.language.get()

    def reset_session(self):
        """Secure wipe of all session data and return to Language screen."""
        security.cleanup_session(self.temp_files)
        security.clear_app_state(self)
        self.ocr_result    = {}
        self.scanned_docs  = {}
        self.last_pdf_path = ""
        self.last_txn_id   = ""
        self.current_scan_doc = ""
        self.is_editing_all = False
        self.show_screen("LanguageScreen")


# ═══════════════════════════════════════════════════════════
# Base Screen
# ═══════════════════════════════════════════════════════════

class BaseScreen(ctk.CTkFrame):

    def __init__(self, parent, app: KioskApp):
        super().__init__(parent, fg_color=config.COLOR_BG)
        self.app = app
        self._image_cache = {}

    def on_show(self):
        pass

    def load_icon_image(self, path: str, size=(100, 100)):
        cache_key = (path, size)
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
        try:
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
            img = Image.open(full_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            self._image_cache[cache_key] = ctk_img
            return ctk_img
        except Exception as e:
            return None

    def _topbar(self, text, bg=None, fg=None, size=24):
        bg = bg or config.COLOR_SECONDARY
        fg = fg or "#FFFFFF"
        bar = ctk.CTkFrame(self, fg_color=bg, corner_radius=0)
        bar.pack(fill="x", ipady=14)
        lbl = ctk.CTkLabel(bar, text=text,
                           font=ctk.CTkFont(family=config.FONT_FAMILY, size=size, weight="bold"),
                           text_color=fg)
        lbl.pack(pady=(4, 4))
        ctk.CTkFrame(self, fg_color=config.COLOR_PRIMARY, height=3, corner_radius=0).pack(fill="x")
        return lbl

    def _footer_bar(self, back_screen=None):
        # Always rebuild inside the pre-existing _footer_container to prevent overlap
        container = getattr(self, "_footer_container", None)
        if container is None:
            # Fallback: create a persistent container if missing
            self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=79)
            self._footer_container.pack(fill="x", side="bottom")
            container = self._footer_container

        # Clear any previous bar widgets inside the container
        for w in container.winfo_children():
            w.destroy()

        # Divider line
        divider = ctk.CTkFrame(container, fg_color=config.COLOR_PRIMARY, height=2, corner_radius=0)
        divider.pack(fill="x", side="top")

        # Main bar
        bar = ctk.CTkFrame(container, fg_color=config.COLOR_SURFACE, corner_radius=0, height=75)
        bar.pack(fill="x", expand=True)
        bar.pack_propagate(False)

        # "Start Over" button - ALWAYS translated!
        l = self.app.get_lang()
        ctk.CTkButton(
            bar, text=t("btn_start_over", l),
            command=self.app.reset_session,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color=config.COLOR_ERROR, hover_color="#C01C1C", text_color="#FFFFFF",
            width=160, height=42, corner_radius=8
        ).pack(side="right", padx=20, pady=16)

        if back_screen:
            ctk.CTkButton(
                bar, text=t("btn_back", l),
                command=lambda: self.app.show_screen(back_screen),
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
                fg_color=config.COLOR_BG, hover_color=config.COLOR_GLASS,
                text_color=config.COLOR_PRIMARY,
                width=150, height=42, corner_radius=8,
                border_width=2, border_color=config.COLOR_PRIMARY
            ).pack(side="left", padx=20, pady=16)
        return bar

    def speak(self, key: str):
        tts_engine.speak_script(key, self.app.get_lang())


# ═══════════════════════════════════════════════════════════
# Screen 1 — Language Selection
# ═══════════════════════════════════════════════════════════

class LanguageScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._lang_frames = []
        self._build()

    # ════════════════════════════════════════════════════
    # Ticker / Features
    # ════════════════════════════════════════════════════
    _TICKER_KEYS = [
        "intro_ticker_withdrawal", "intro_ticker_deposit",
        "intro_ticker_neft", "intro_ticker_dd",
        "intro_ticker_account", "intro_ticker_atm",
        "intro_ticker_mobile", "intro_ticker_address",
        "intro_ticker_kyc", "intro_ticker_cheque",
    ]

    def _build(self):
        # ════════════════════════════════════════════════
        # Hero Header
        # ════════════════════════════════════════════════
        hero = ctk.CTkFrame(self, fg_color="#0D2B6E", corner_radius=0)
        hero.pack(fill="x", ipady=0)

        # Top accent line
        ctk.CTkFrame(hero, fg_color="#F5A623", height=5, corner_radius=0).pack(fill="x")

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=12)

        # Bank icon + title side by side
        ctk.CTkLabel(inner, text="🏦",
                     font=ctk.CTkFont(size=52)).pack(side="left", padx=(0, 16))

        txt_col = ctk.CTkFrame(inner, fg_color="transparent")
        txt_col.pack(side="left", fill="both")
        
        self._hero_title = ctk.CTkLabel(txt_col,
                     text="",
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=26, weight="bold"),
                     text_color="#FFFFFF")
        self._hero_title.pack(anchor="w")
        
        self._hero_tagline = ctk.CTkLabel(txt_col,
                     text="",
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=13),
                     text_color="#A8C4F0")
        self._hero_tagline.pack(anchor="w", pady=(2, 0))

        # ════════════════════════════════════════════════
        # Scrolling services ticker
        # ════════════════════════════════════════════════
        ticker_bar = ctk.CTkFrame(self, fg_color="#1A4A9E", corner_radius=0, height=36)
        ticker_bar.pack(fill="x")
        ticker_bar.pack_propagate(False)
        
        self._ticker_lbl = ctk.CTkLabel(
            ticker_bar, text="",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            text_color="#FFD700")
        self._ticker_lbl.pack(expand=True)

        # ════════════════════════════════════════════════
        # Feature badges row
        # ════════════════════════════════════════════════
        badge_bar = ctk.CTkFrame(self, fg_color="#EFF6FF", corner_radius=0, height=44)
        badge_bar.pack(fill="x")
        
        self._badge_labels = []
        for _ in range(5):
            b = ctk.CTkFrame(badge_bar, fg_color="#DBEAFE", corner_radius=20)
            b.pack(side="left", padx=10, pady=6)
            lbl = ctk.CTkLabel(b, text="",
                         font=ctk.CTkFont(family=config.FONT_FAMILY, size=12, weight="bold"),
                         text_color="#1E40AF")
            lbl.pack(padx=4, pady=2)
            self._badge_labels.append(lbl)

        # ════════════════════════════════════════════════
        # Language selection area
        # ════════════════════════════════════════════════
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=50, pady=10)

        # Pulsing "Touch to begin" label
        self._touch_lbl = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=19, weight="bold"),
            text_color="#0D2B6E")
        self._touch_lbl.pack(pady=(0, 16))

        # Language grid
        grid = ctk.CTkFrame(content, fg_color="transparent")
        grid.pack()

        langs = list(config.LANGUAGES.items())
        for idx, (code, info) in enumerate(langs):
            row, col = divmod(idx, 3)
            self._lang_button(grid, code, info).grid(row=row, column=col, padx=18, pady=12)

        # ════════════════════════════════════════════════
        # Bottom strip
        # ════════════════════════════════════════════════
        foot = ctk.CTkFrame(self, fg_color="#0D2B6E", corner_radius=0, height=30)
        foot.pack(fill="x", side="bottom")
        self._foot_lbl = ctk.CTkLabel(foot,
                     text="",
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=11),
                     text_color="#A8C4F0")
        self._foot_lbl.pack(expand=True)

    def _lang_button(self, parent, code: str, info: dict):
        frame = ctk.CTkFrame(parent,
                             fg_color="white",
                             border_width=3,
                             border_color="#CBD5E1",
                             corner_radius=18,
                             width=230, height=150,
                             cursor="hand2")
        frame.grid_propagate(False)

        ctk.CTkLabel(frame, text=info["flag"],
                     font=ctk.CTkFont(size=46)).pack(pady=(14, 0))
        ctk.CTkLabel(frame, text=info["native"],
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=22, weight="bold"),
                     text_color="#0D2B6E").pack(pady=(3, 0))
        ctk.CTkLabel(frame, text=info["name"],
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=12),
                     text_color="#64748B").pack()

        def _enter(e, f=frame):
            f.configure(border_color="#0D2B6E", border_width=4, fg_color="#EFF6FF")

        def _leave(e, f=frame):
            f.configure(border_color="#CBD5E1", border_width=3, fg_color="white")

        def _select(c=code, f=frame):
            self.app.language.set(c)
            for child in getattr(self, "_lang_frames", []):
                child.configure(border_color=config.COLOR_SUCCESS if child is f else config.COLOR_GLASS_BORDER,
                                border_width=4 if child is f else 2)
            tts_engine.speak_script("language_selected", c)
            # Navigate to Coin Payment Screen (Step 2)
            self.after(1200, lambda: self.app.show_screen("CoinScreen"))

        for w in [frame] + list(frame.winfo_children()):
            w.bind("<Button-1>", lambda e, fn=_select: fn())

        if not hasattr(self, "_lang_frames"):
            self._lang_frames = []
        self._lang_frames.append(frame)
        return frame

    def on_show(self):
        lang = self.app.get_lang()
        self._hero_title.configure(text=t("intro_system_name", lang))
        self._hero_tagline.configure(text=t("intro_tagline", lang))
        self._touch_lbl.configure(text=t("intro_touch_prompt", lang))
        self._foot_lbl.configure(text=t("intro_footer", lang))
        
        ticker_text = "   •   ".join(t(k, lang) for k in self._TICKER_KEYS)
        self._ticker_lbl.configure(text=ticker_text)
        
        badges = [
            t("intro_badge_secure", lang), t("intro_badge_fast", lang), 
            t("intro_badge_accurate", lang), t("intro_badge_multilang", lang), 
            t("intro_badge_print", lang)
        ]
        for lbl, b_text in zip(self._badge_labels, badges):
            lbl.configure(text=f" {b_text} ")

        for f in getattr(self, "_lang_frames", []):
            f.configure(border_color=config.COLOR_GLASS_BORDER, border_width=2)
        tts_engine.speak_script("welcome", lang)


# ═══════════════════════════════════════════════════════════
# Screen 2 — Coin Payment
# ═══════════════════════════════════════════════════════════

class CoinScreen(BaseScreen):
    """Step 2 — Ask user to insert ₹5 coin before proceeding."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl  = None
        self._instr_lbl  = None
        self._status_lbl = None
        self._sim_btn    = None
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        # ── Coin Icon ──────────────────────────────────────
        coin_card = ctk.CTkFrame(
            content,
            fg_color=config.COLOR_GLASS,
            border_width=3, border_color=config.COLOR_GLASS_BORDER,
            corner_radius=20,
        )
        coin_card.pack(expand=True, pady=30, padx=80)

        ctk.CTkLabel(
            coin_card, text="🪙",
            font=ctk.CTkFont(size=96),
        ).pack(pady=(40, 10))

        self._instr_lbl = ctk.CTkLabel(
            coin_card, text="",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=22, weight="bold"),
            text_color=config.COLOR_PRIMARY,
            wraplength=700,
        )
        self._instr_lbl.pack(pady=(0, 10), padx=40)

        self._status_lbl = ctk.CTkLabel(
            coin_card, text="",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"),
            text_color=config.COLOR_SUCCESS,
        )
        self._status_lbl.pack(pady=(0, 20))

        self._sim_btn = ctk.CTkButton(
            coin_card, text="",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_SECONDARY,
            text_color="#FFFFFF",
            height=60, corner_radius=12,
            command=self._coin_accepted,
        )
        self._sim_btn.pack(pady=(0, 40), padx=60, fill="x")

        # ── Footer ─────────────────────────────────────────
        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("coin_screen_title", lang))
        self._instr_lbl.configure(text=t("coin_instruction_main", lang))
        self._status_lbl.configure(text=t("coin_waiting", lang))
        self._sim_btn.configure(text=t("coin_btn_simulate", lang), state="normal")

        self._footer_bar(back_screen="LanguageScreen")

        tts_engine.speak_script("coin_insert", lang)

    def _coin_accepted(self):
        lang = self.app.get_lang()
        self._sim_btn.configure(state="disabled")
        self._status_lbl.configure(text=t("coin_accepted_msg", lang))
        tts_engine.speak_script("coin_accepted", lang)
        self.after(1800, lambda: self.app.show_screen("ServiceScreen"))


# ═══════════════════════════════════════════════════════════
# Screen 3 — Service Selection
# ═══════════════════════════════════════════════════════════

class ServiceScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl = None
        self._instr_lbl = None
        self._grid = None
        self._footer = None
        self._service_cards = []
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("Select Banking Service")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        self._instr_lbl = ctk.CTkLabel(content, text="",
                                       font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"),
                                       text_color=config.COLOR_PRIMARY)
        self._instr_lbl.pack(pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._grid = ctk.CTkFrame(scroll, fg_color="transparent")
        self._grid.pack()

        # Footer placeholder
        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def _populate_grid(self):
        for w in self._grid.winfo_children():
            w.destroy()
        self._service_cards.clear()

        lang = self.app.get_lang()

        # ── Split by category ──────────────────────────────
        cash_forms    = [(k, v) for k, v in config.FORM_TYPES.items() if v.get("category") == "cash"]
        noncash_forms = [(k, v) for k, v in config.FORM_TYPES.items() if v.get("category") != "cash"]

        def _section_header(text, color):
            hdr = ctk.CTkFrame(self._grid, fg_color=color, corner_radius=10, height=44)
            hdr.pack(fill="x", pady=(18, 6), padx=4)
            ctk.CTkLabel(hdr, text=text,
                         font=ctk.CTkFont(family=config.FONT_FAMILY, size=17, weight="bold"),
                         text_color="#FFFFFF").pack(expand=True, pady=10)

        def _cards_row(items):
            row_frame = ctk.CTkFrame(self._grid, fg_color="transparent")
            row_frame.pack(fill="x", pady=4)
            for key, info in items:
                card = self._service_card(row_frame, key, info, lang)
                card.pack(side="left", padx=15, pady=8)

        # ── Cash section ──────────────────────────────────
        cash_title    = t("category_cash", lang)
        noncash_title = t("category_noncash", lang)

        _section_header(f"💵  {cash_title}", "#1A6B3A")
        _cards_row(cash_forms)

        _section_header(f"🏦  {noncash_title}", "#1B3F72")
        _cards_row(noncash_forms)

    def _service_card(self, parent, key: str, info: dict, lang: str):
        # Translate form label into user language
        form_label_key = f"form_{key}"
        label = t(form_label_key, lang)
        if label == form_label_key:
            label = t(info.get("label", key), lang)

        frame = ctk.CTkFrame(parent, fg_color=config.COLOR_GLASS,
                             border_width=2, border_color=config.COLOR_GLASS_BORDER,
                             corner_radius=15, width=240, height=200, cursor="hand2")
        frame.pack_propagate(False)

        img_path = info.get("image", "")
        if img_path:
            # Resolve relative path from the directory containing main.py
            abs_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), img_path)
        else:
            abs_img_path = ""
        if abs_img_path and os.path.exists(abs_img_path):
            try:
                img = ctk.CTkImage(light_image=Image.open(abs_img_path), size=(80, 60))
                ctk.CTkLabel(frame, text="", image=img).pack(pady=(16, 4))
            except Exception:
                ctk.CTkLabel(frame, text=info.get("icon", ""), font=ctk.CTkFont(size=46)).pack(pady=(16, 4))
        else:
            ctk.CTkLabel(frame, text=info.get("icon", ""), font=ctk.CTkFont(size=46)).pack(pady=(16, 4))

        ctk.CTkLabel(frame, text=label,
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=15, weight="bold"),
                     text_color=config.COLOR_TEXT, wraplength=220).pack(padx=6)

        def _select(k=key, f=frame, lbl=label):
            self.app.form_type.set(k)
            self.app.scanned_docs = {}
            self.app.ocr_result   = {}
            self.app.is_editing_all = False
            for c in self._service_cards:
                c.configure(border_color=config.COLOR_PRIMARY if c is f else config.COLOR_GLASS_BORDER,
                            border_width=4 if c is f else 2)
            tts_engine.speak(lbl, self.app.get_lang())
            self.after(600, lambda: self.app.show_screen("DocumentTrackerScreen"))

        for w in [frame] + list(frame.winfo_children()):
            w.bind("<Button-1>", lambda e, fn=_select: fn())

        self._service_cards.append(frame)
        return frame

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("service_title", lang))
        self._instr_lbl.configure(text=t("service_instruction", lang))
        self._populate_grid()

        self._footer_bar(back_screen="LanguageScreen")
        self.speak("select_service")




# ═══════════════════════════════════════════════════════════
# Screen 3 — Document Tracker
# ═══════════════════════════════════════════════════════════

class DocumentTrackerScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._doc_cards = {}
        self._tick_labels = {}
        self._built_lang = None

    def _build_screen(self):
        lang = self.app.get_lang()
        self._built_lang = lang
        for w in self.winfo_children():
            w.destroy()
        self._doc_cards.clear()
        self._tick_labels.clear()

        ft_key = self.app.form_type.get()
        ft_cfg = config.FORM_TYPES.get(ft_key, {})
        docs   = ft_cfg.get("docs", [])
        mandatory = ft_cfg.get("mandatory", docs)

        self._topbar(f"📄 {t('doc_tracker_title', lang)} - {t(ft_cfg.get('label', ''), lang)}")

        banner = ctk.CTkFrame(self, fg_color="#EFF6FF", border_width=1, border_color=config.COLOR_GLASS_BORDER, corner_radius=0)
        banner.pack(fill="x", ipady=8)
        ctk.CTkLabel(banner, text=t("doc_instruction", lang),
                     font=ctk.CTkFont(family=config.FONT_FAMILY, size=15, weight="bold"),
                     text_color=config.COLOR_PRIMARY).pack()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=15)
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(expand=True)

        for idx, doc_key in enumerate(docs):
            reg = config.DOC_REGISTRY.get(doc_key, {})
            is_mandatory = doc_key in mandatory
            row, col = divmod(idx, 3)
            card, tick = self._doc_card(grid, doc_key, reg, is_mandatory, lang)
            card.grid(row=row, column=col, padx=20, pady=20)
            self._doc_cards[doc_key] = card
            self._tick_labels[doc_key] = tick

        # Bottom Bar
        ctk.CTkFrame(self, fg_color=config.COLOR_PRIMARY, height=2, corner_radius=0).pack(fill="x", side="bottom")
        bottom = ctk.CTkFrame(self, fg_color=config.COLOR_SURFACE, corner_radius=0, height=80)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        ctk.CTkButton(
            bottom, text=t("btn_start_over", lang),
            command=self.app.reset_session,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color=config.COLOR_ERROR, hover_color="#C01C1C", text_color="#FFFFFF",
            width=160, height=44
        ).pack(side="left", padx=20, pady=18)

        ctk.CTkButton(
            bottom, text=t("btn_back", lang),
            command=lambda: self.app.show_screen("ServiceScreen"),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color="transparent", hover_color=config.COLOR_GLASS, text_color=config.COLOR_PRIMARY,
            width=160, height=44, border_width=2, border_color=config.COLOR_PRIMARY
        ).pack(side="left", padx=10, pady=18)

        self._continue_btn = ctk.CTkButton(
            bottom, text=t("btn_continue", lang),
            command=self._on_continue,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"),
            fg_color=config.COLOR_SUCCESS, hover_color="#047857", text_color="#FFFFFF",
            width=220, height=50, corner_radius=10, state="disabled"
        )
        self._continue_btn.pack(side="right", padx=20, pady=15)

    def _doc_card(self, parent, doc_key: str, reg: dict, is_mandatory: bool, lang: str):
        border_color = config.COLOR_PRIMARY if is_mandatory else config.COLOR_GLASS_BORDER
        frame = ctk.CTkFrame(
            parent, fg_color=config.COLOR_GLASS,
            border_width=2, border_color=border_color,
            corner_radius=16, width=220, height=220, cursor="hand2"
        )
        frame.grid_propagate(False)

        if is_mandatory:
            ctk.CTkLabel(
                frame, text=f" {t('doc_required_badge', lang)} ",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=10, weight="bold"),
                fg_color=config.COLOR_PRIMARY, text_color="white", corner_radius=6
            ).place(x=8, y=8)

        img = self.load_icon_image(reg.get("image", ""), size=(80, 55))
        if img:
            ctk.CTkLabel(frame, image=img, text="").pack(pady=(32 if is_mandatory else 22, 4))
        else:
            ctk.CTkLabel(frame, text=reg.get("icon", "\U0001f4c4"), font=ctk.CTkFont(size=44)).pack(pady=(32 if is_mandatory else 22, 4))

        ctk.CTkLabel(
            frame, text=t(reg.get("label", doc_key), lang),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=15, weight="bold"),
            text_color=config.COLOR_TEXT, wraplength=200
        ).pack(padx=8)

        action = t("doc_btn_ocr", lang) if reg.get("ocr_capable", False) else t("doc_btn_upload", lang)
        ctk.CTkLabel(
            frame, text=action,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=11),
            text_color=config.COLOR_SUBTEXT
        ).pack(pady=(2, 0))

        tick = ctk.CTkLabel(frame, text="✔", font=ctk.CTkFont(size=35, weight="bold"),
                             text_color=config.COLOR_SUCCESS, fg_color=("white", "white"))

        def _on_click(k=doc_key):
            self.app.current_scan_doc = k
            self.app.image_path.set("")
            tts_engine.speak_script(reg.get("prompt_key", "doc_prompt_aadhaar"), lang)
            self.app.show_screen("ScanScreen")

        # Bind click on frame AND all child widgets
        for w in [frame] + list(frame.winfo_children()):
            w.bind("<Button-1>", lambda e, fn=_on_click: fn())
            # Make sure child labels don't swallow clicks
            w.configure(cursor="hand2")

        return frame, tick

    def _refresh_ticks(self):
        ft_key = self.app.form_type.get()
        ft_cfg = config.FORM_TYPES.get(ft_key, {})
        mandatory = ft_cfg.get("mandatory", ft_cfg.get("docs", []))
        all_mandatory_done = all(k in self.app.scanned_docs for k in mandatory)

        for doc_key, frame in self._doc_cards.items():
            tick = self._tick_labels.get(doc_key)
            if doc_key in self.app.scanned_docs:
                frame.configure(border_color=config.COLOR_SUCCESS, border_width=3, fg_color="#F0FFF4")
                if tick: tick.place(relx=0.85, rely=0.15, anchor="center")
            else:
                border = config.COLOR_PRIMARY if doc_key in mandatory else config.COLOR_GLASS_BORDER
                frame.configure(border_color=border, border_width=2, fg_color=config.COLOR_GLASS)
                if tick: tick.place_forget()

        if all_mandatory_done:
            self._continue_btn.configure(state="normal")
            tts_engine.speak_script("all_docs_done", self.app.get_lang())
        else:
            self._continue_btn.configure(state="disabled")

    def _on_continue(self):
        ft_key = self.app.form_type.get()
        ft_cfg = config.FORM_TYPES.get(ft_key, {})
        requires = ft_cfg.get("requires", [])
        
        if "amount" in requires:
            self.app.show_screen("DenominationScreen")
        else:
            # Check if any required fields are missing
            missing = False
            for req in requires:
                if req == "amount": continue
                val = self.app.ocr_result.get(req, "")
                if not val or val == "Not found":
                    missing = True
                    break
            
            if missing:
                self.app.is_editing_all = False
                self.app.show_screen("MissingInfoScreen")
            else:
                self.app.show_screen("ConfirmationScreen")

    def on_show(self):
        # Always rebuild so cards are fresh for the current form type and language
        self._build_screen()
        self._refresh_ticks()
        tts_engine.speak_script("scan_documents", self.app.get_lang())


# ═══════════════════════════════════════════════════════════
# Screen 4 — Scan Image
# ═══════════════════════════════════════════════════════════

class ScanScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl = None
        self._current_photo = None  # Strong reference to prevent GC
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("Scan Document")
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=50, pady=30)
        content.grid_columnconfigure(0, weight=5)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(content, fg_color=config.COLOR_SURFACE, border_width=2, border_color=config.COLOR_PRIMARY, corner_radius=10)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self.left_frame.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(self.left_frame, text="", font=ctk.CTkFont(family=config.FONT_FAMILY, size=16),
                                          text_color=config.COLOR_SUBTEXT, fg_color=config.COLOR_BG, corner_radius=8)
        self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._doc_type_label = ctk.CTkLabel(right, text="", font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"),
                                            text_color=config.COLOR_PRIMARY)
        self._doc_type_label.pack(pady=(0, 16))

        btn_font = ctk.CTkFont(family=config.FONT_FAMILY, size=15, weight="bold")
        self.btn_browse = ctk.CTkButton(right, text="📂", command=self._browse_file, font=btn_font, fg_color=config.COLOR_PRIMARY, text_color="#FFFFFF", height=45)
        self.btn_browse.pack(fill="x", pady=8)

        self.btn_default = ctk.CTkButton(right, text="🗂", command=self._use_default, font=btn_font, fg_color=config.COLOR_SECONDARY, text_color="#FFFFFF", height=45)
        self.btn_default.pack(fill="x", pady=8)
        
        self.btn_camera = ctk.CTkButton(right, text="📸", command=self._capture_camera, font=btn_font, fg_color=config.COLOR_SUCCESS, text_color="#FFFFFF", height=45)
        self.btn_camera.pack(fill="x", pady=8)

        self.status_var = tk.StringVar(value="")
        self.status_label = ctk.CTkLabel(right, textvariable=self.status_var, font=ctk.CTkFont(family=config.FONT_FAMILY, size=14), text_color=config.COLOR_WARNING, wraplength=350)
        self.status_label.pack(pady=10)

        self.progress = ctk.CTkProgressBar(right, mode="indeterminate", width=350)
        self.progress.pack(pady=(0, 10))
        self.progress.set(0)

        self.scan_btn = ctk.CTkButton(right, text="🔍", command=self._run_scan, font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"),
                                      fg_color=config.COLOR_PRIMARY, text_color="#FFFFFF", height=55, corner_radius=10)
        self.scan_btn.pack(fill="x", pady=(5, 0))

        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("scan_title", lang))

        # ── Reset image preview for each new document scan ──
        self._current_photo = None
        self.app.image_path.set("")
        if hasattr(self, "preview_label") and self.preview_label.winfo_exists():
            self.preview_label.destroy()
        self.preview_label = ctk.CTkLabel(self.left_frame, text=t("scan_preview_empty", lang),
                                          font=ctk.CTkFont(family=config.FONT_FAMILY, size=16),
                                          text_color=config.COLOR_SUBTEXT, fg_color=config.COLOR_BG, corner_radius=8)
        self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)

        self.btn_browse.configure(text=t("scan_btn_browse", lang))
        self.btn_default.configure(text=t("scan_btn_default", lang))
        self.btn_camera.configure(text=t("scan_btn_camera", lang))

        doc_key = self.app.current_scan_doc
        reg = config.DOC_REGISTRY.get(doc_key, {})
        ocr_cap = reg.get("ocr_capable", True)
        doc_label = t(reg.get("label", doc_key), lang)

        self._doc_type_label.configure(text=f"\U0001f4c4 {doc_label}")
        self.scan_btn.configure(text=t("scan_btn_run_ocr", lang) if ocr_cap else t("scan_btn_verify", lang))

        self._footer_bar(back_screen="DocumentTrackerScreen")

        self.status_var.set("")
        self.progress.stop()
        self.scan_btn.configure(state="normal")
        tts_engine.speak_script("place_doc_on_scanner", lang)

    def _show_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((450, 350))
            # Store on self to prevent garbage collection using robust PhotoImage
            self._current_photo = ImageTk.PhotoImage(img)
            
            if hasattr(self, "preview_label") and self.preview_label.winfo_exists():
                self.preview_label.destroy()
            self.preview_label = ctk.CTkLabel(self.left_frame, text="", fg_color=config.COLOR_BG, corner_radius=8)
            self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)
            self.preview_label.configure(image=self._current_photo)
        except Exception as e:
            print(f"[ScanScreen Error] Failed to show image {path}: {e}")
            self.status_var.set(f"Unable to display image: {e}")

    def _browse_file(self):
        path = filedialog.askopenfilename(
            parent=self.app,
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if path:
            self.app.image_path.set(path)
            lang = self.app.get_lang()
            self.status_var.set(t("scan_status_loaded", lang))
            self._show_image(path)

    def _use_default(self):
        lang = self.app.get_lang()
        dk   = self.app.current_scan_doc
        reg  = config.DOC_REGISTRY.get(dk, {})
        doc_label = t(reg.get("label", dk), lang)
        path = (config.DEFAULT_AADHAAR_PATH  if dk == "aadhaar" else
                config.DEFAULT_PAN_PATH      if dk == "pan"     else
                config.DEFAULT_PASSBOOK_PATH)
        if os.path.exists(path):
            self.app.image_path.set(path)
            self._show_image(path)
            self.status_var.set(t("scan_status_loaded", lang))
        else:
            placeholder = None
            icon_path = reg.get("image")
            if icon_path:
                placeholder = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_path)
            if placeholder and os.path.exists(placeholder):
                self._show_image(placeholder)
            self.app.image_path.set("")
            self.status_var.set(t("scan_status_default_missing", lang).format(doc=doc_label))

    def _capture_camera(self):
        lang = self.app.get_lang()
        self.status_var.set(t("scan_status_scanning", lang))
        self.progress.start()

        def _worker():
            try:
                frame = ocr_engine.capture_from_camera()
                import tempfile, cv2
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                cv2.imwrite(tmp.name, frame)
                
                # Must update UI from the main thread
                self.after(0, lambda: self._on_camera_success(tmp.name, lang))
            except Exception as e:
                print(f"[Camera Error] {e}")
                self.after(0, lambda: self._on_camera_error(lang))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_camera_success(self, filepath, lang):
        self.progress.stop()
        self.app.temp_files.append(filepath)
        self.app.image_path.set(filepath)
        self._show_image(filepath)
        self.status_var.set(t("scan_status_captured", lang))

    def _on_camera_error(self, lang):
        self.progress.stop()
        self.status_var.set(t("scan_status_camera_error", lang))
        tts_engine.speak_script("scan_error_retry", lang)

    def _run_scan(self):
        path = self.app.image_path.get()
        if not path or not os.path.exists(path):
            self.status_var.set("Please select or capture a valid document first.")
            return

        doc_key = self.app.current_scan_doc
        reg = config.DOC_REGISTRY.get(doc_key, {})
        if not reg.get("ocr_capable", True):
            self._scan_done(doc_key)
            return

        self.scan_btn.configure(state="disabled")
        self.progress.start()
        
        lang = self.app.get_lang()
        self.status_var.set(t("scan_started", lang))
        tts_engine.speak_script("scan_started", lang)

        def _worker():
            try:
                # Map doc_key to actual ocr schema type
                dt_map = {"aadhaar": "aadhaar", "pan": "pan", "passbook": "passbook"}
                dt = dt_map.get(doc_key, "aadhaar")

                # Announce "processing" after scan starts
                self.after(0, lambda: tts_engine.speak_script("scan_processing", lang))

                try:
                    # Send the original image directly to Gemini Vision —
                    # colour images give much better OCR than preprocessed grayscale.
                    final = ai_helper.enhance_with_vision(path, dt)

                except Exception as vision_err:
                    print(f"[Vision API fallback] {vision_err}")
                    try:
                        processed = ocr_engine.preprocess_image(path)
                        res = ocr_engine.run_ocr(processed)
                        final = ai_helper.enhance_with_ai(res["text"], dt, extractor.extract(res["text"], dt))
                    except Exception as ocr_err:
                        print(f"[OCR fallback error] {ocr_err}")
                        # Last resort: raw pytesseract directly on the original file
                        try:
                            import pytesseract, config as cfg
                            pytesseract.pytesseract.tesseract_cmd = cfg.TESSERACT_PATH
                            raw_text = pytesseract.image_to_string(path, config="--oem 3 --psm 6")
                            final = extractor.extract(raw_text, dt)
                        except Exception:
                            final = {}  # Complete failure — proceed silently as requested

                # Write all successfully-extracted fields into the shared OCR result
                for k, v in final.items():
                    if v and str(v).strip().lower() not in ("", "not found", "none", "n/a") and not k.startswith("_"):
                        self.app.ocr_result[k] = v

                self.after(0, lambda: self._scan_done(doc_key))
            except Exception as e:
                print(f"[OCR Error] {e}")
                # Even on extreme error, proceed to next step silently
                self.after(0, lambda: self._scan_done(doc_key))

        threading.Thread(target=_worker, daemon=True).start()

    def _scan_done(self, doc_key):
        lang = self.app.get_lang()
        self.progress.stop()
        self.app.scanned_docs[doc_key] = True
        self.status_label.configure(text_color=config.COLOR_SUCCESS)
        self.status_var.set(t("extract_success", lang))
        tts_engine.speak_script("extract_success", lang)
        self.after(4500, lambda: self.app.show_screen("DocumentTrackerScreen"))

    def _scan_low_confidence(self):
        lang = self.app.get_lang()
        self.progress.stop()
        self.scan_btn.configure(state="normal")
        self.status_var.set(t("scan_status_error", lang)) # Re-using error status text but could be more specific
        tts_engine.speak_script("scan_error_retry", lang)
        
    def _scan_err(self):
        lang = self.app.get_lang()
        self.progress.stop()
        self.scan_btn.configure(state="normal")
        self.status_var.set(t("scan_status_error", lang))
        tts_engine.speak_script("scan_error_retry", lang)


# ═══════════════════════════════════════════════════════════
# Screen 5 — Denomination (Cash Deposit/Withdrawal only)
# ═══════════════════════════════════════════════════════════

class DenominationScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl = None
        self._instr_lbl = None
        self._amount_var = None
        self._words_lbl = None
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("Enter Details")
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=30)
        
        self._instr_lbl = ctk.CTkLabel(content, text="", font=ctk.CTkFont(family=config.FONT_FAMILY, size=18, weight="bold"), text_color=config.COLOR_PRIMARY)
        self._instr_lbl.pack(pady=(0, 20))

        grid = ctk.CTkFrame(content, fg_color=config.COLOR_GLASS, corner_radius=15, border_width=2, border_color=config.COLOR_GLASS_BORDER)
        grid.pack(pady=20, padx=20, ipadx=40, ipady=30)

        f = ctk.CTkFrame(grid, fg_color="transparent")
        f.pack(fill="x", pady=10)
        
        self._amt_prefix_lbl = ctk.CTkLabel(f, text="Amount (₹): ", font=ctk.CTkFont(family=config.FONT_FAMILY, size=32, weight="bold"))
        self._amt_prefix_lbl.pack(side="left", padx=20)
        
        self._amount_var = tk.StringVar(value="")
        
        entry = ctk.CTkEntry(f, textvariable=self._amount_var, font=ctk.CTkFont(size=32), width=200, justify="center")
        entry.pack(side="left", padx=10)
        
        # Hook the entry widget to open keypad and trigger TTS
        def on_amt_click(ev):
            lang = self.app.get_lang()
            ft = self.app.form_type.get()
            if "deposit" in ft:
                tts_engine.speak_dynamic("denom_deposit_prompt", lang, "amount")
            else:
                tts_engine.speak_dynamic("denom_withdraw_prompt", lang, "amount")
        
        entry.bind("<Button-1>", on_amt_click, add="+")
        entry.bind("<FocusIn>", on_amt_click, add="+")
        attach_keypad(entry, self._amount_var, "Amount", self.app.get_lang(), mode="numeric")

        # ── Amount in Words display ──────────────────────────
        words_frame = ctk.CTkFrame(grid, fg_color="#F0FFF4", corner_radius=10, border_width=1, border_color=config.COLOR_SUCCESS)
        words_frame.pack(fill="x", padx=20, pady=(10, 5))

        self._words_prefix_lbl = ctk.CTkLabel(
            words_frame, text="Amount in Words:",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            text_color=config.COLOR_SUBTEXT,
        )
        self._words_prefix_lbl.pack(anchor="w", padx=15, pady=(8, 0))

        self._words_lbl = ctk.CTkLabel(
            words_frame, text="—",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=20, weight="bold"),
            text_color=config.COLOR_SUCCESS,
            wraplength=600,
        )
        self._words_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Auto-update words when amount changes
        self._amount_var.trace_add("write", self._update_words)

        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def _update_words(self, *_args):
        raw = self._amount_var.get().strip()
        if raw and raw.isdigit() and int(raw) > 0:
            words = ai_helper.number_to_words_rupees(raw)
            self._words_lbl.configure(text=words)
        else:
            self._words_lbl.configure(text="—")

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("denom_title", lang))
        self._instr_lbl.configure(text=t("denom_instr", lang))
        self._amt_prefix_lbl.configure(text=t("field_amount", lang) + ": ")
        
        bar = self._footer_bar(back_screen="DocumentTrackerScreen")
        ctk.CTkButton(
            bar, text=t("btn_continue", lang),
            command=self._on_continue,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"),
            fg_color=config.COLOR_SUCCESS, hover_color="#047857",
            text_color="#FFFFFF", width=220, height=50, corner_radius=10,
        ).pack(side="right", padx=20, pady=15)
        tts_engine.speak_script("denom_screen_intro", lang)
        
    def _on_continue(self):
        raw = self._amount_var.get().strip()
        self.app.ocr_result["amount"] = raw
        # Convert to English words and store
        if raw and raw.isdigit() and int(raw) > 0:
            self.app.ocr_result["amount_in_words"] = ai_helper.number_to_words_rupees(raw)
            # Speak the amount in the user's language
            lang = self.app.get_lang()
            tts_engine.speak(f"{raw}", lang)
        
        # Check if any required fields are missing
        ft_key = self.app.form_type.get()
        ft_cfg = config.FORM_TYPES.get(ft_key, {})
        requires = ft_cfg.get("requires", [])
        
        missing = False
        for req in requires:
            if req == "amount": continue
            val = self.app.ocr_result.get(req, "")
            if not val or val == "Not found":
                missing = True
                break
        
        if missing:
            self.app.is_editing_all = False
            self.app.show_screen("MissingInfoScreen")
        else:
            self.app.show_screen("ConfirmationScreen")


# ═══════════════════════════════════════════════════════════
# Screen 6 — Missing Info (Smart Data Entry)
# ═══════════════════════════════════════════════════════════

class MissingInfoScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl = None
        self._entries = {}
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("Provide Missing Details")
        
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=40, pady=20)
        
        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("missing_title", lang))
        
        for w in self.content.winfo_children(): w.destroy()
        self._entries.clear()

        ft_cfg = config.FORM_TYPES.get(self.app.form_type.get(), {})
        requires = ft_cfg.get("requires", [])
        
        missing_fields = []
        for req in requires:
            if self.app.is_editing_all:
                missing_fields.append(req)
            elif not self.app.ocr_result.get(req) or self.app.ocr_result.get(req) == "Not found":
                missing_fields.append(req)

        if not missing_fields:
            # Nothing missing, skip to confirmation
            self.after(100, lambda: self.app.show_screen("ConfirmationScreen"))
            return

        ctk.CTkLabel(self.content, text=t("missing_instruction", lang), font=ctk.CTkFont(size=18, weight="bold"), text_color=config.COLOR_WARNING).pack(pady=(0, 20))

        # Numeric fields use digit-only keypad; all others use QWERTY
        NUMERIC_FIELDS = {"amount", "mobile", "account_no", "tenure", "aadhaar_number"}

        for fld in missing_fields:
            row = ctk.CTkFrame(self.content, fg_color="transparent")
            row.pack(fill="x", pady=10)
            lbl = t(f"field_{fld}", lang)
            if lbl == f"field_{fld}": lbl = fld.replace("_", " ").title()

            ctk.CTkLabel(
                row, text=f"{lbl}:",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"),
                width=250, anchor="e",
            ).pack(side="left", padx=20)

            var = tk.StringVar(value=self.app.ocr_result.get(fld, ""))
            self._entries[fld] = var

            mode = "numeric" if fld in NUMERIC_FIELDS else "alpha"
            entry = ctk.CTkEntry(
                row, textvariable=var,
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=16),
                height=48,
            )
            entry.pack(side="left", fill="x", expand=True, padx=(0, 40))
            # Attach popup keypad – tapping the field opens an on-screen keyboard
            attach_keypad(entry, var, lbl, lang, mode=mode)

        bar = self._footer_bar(back_screen="DenominationScreen" if "amount" in requires and self.app.form_type.get() in ["cash_deposit", "cash_withdrawal"] else "DocumentTrackerScreen")
        
        def _rescan():
            self.app.show_screen("DocumentTrackerScreen")
            
        ctk.CTkButton(
            bar, text=f"📷 {t('btn_start_over', lang)} / Rescan",
            command=_rescan,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color="transparent", text_color=config.COLOR_PRIMARY,
            border_width=2, border_color=config.COLOR_PRIMARY,
            width=180, height=44,
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkButton(bar, text=t("btn_continue", lang), command=self._save_and_continue,
                      font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"), fg_color=config.COLOR_SUCCESS, text_color="#FFFFFF", width=220, height=50, corner_radius=10).pack(side="right", padx=20, pady=15)
        tts_engine.speak_script("enter_missing", lang)

    def _save_and_continue(self):
        for k, var in self._entries.items():
            self.app.ocr_result[k] = var.get().strip()
        self.app.show_screen("ConfirmationScreen")


# ═══════════════════════════════════════════════════════════
# Screen 7 — Confirmation (Final Preview)
# ═══════════════════════════════════════════════════════════

class ConfirmationScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._title_lbl = None
        self._build()

    def _build(self):
        self._title_lbl = self._topbar("Final Preview")
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=config.COLOR_GLASS, corner_radius=12, border_width=2, border_color=config.COLOR_GLASS_BORDER)
        self.scroll.pack(fill="both", expand=True, padx=40, pady=20)
        
        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def on_show(self):
        lang = self.app.get_lang()
        self._title_lbl.configure(text=t("confirm_title", lang))

        for w in self.scroll.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.scroll, text=t("confirm_instruction", lang), font=ctk.CTkFont(size=18, weight="bold"), text_color=config.COLOR_WARNING).pack(pady=10)

        ft_cfg = config.FORM_TYPES.get(self.app.form_type.get(), {})
        requires = ft_cfg.get("requires", [])

        # Display scanned images at the top for side-by-side verification
        if self.app.temp_files:
            images_frame = ctk.CTkScrollableFrame(self.scroll, orientation="horizontal", height=200, fg_color="transparent")
            images_frame.pack(fill="x", pady=(0, 10))
            
            from PIL import Image as PILImage
            for img_path in self.app.temp_files:
                if os.path.exists(img_path):
                    try:
                        pil_img = PILImage.open(img_path)
                        # Resize for preview height 180
                        ratio = 180 / pil_img.height
                        new_w = int(pil_img.width * ratio)
                        ctk_img = ctk.CTkImage(light_image=pil_img, size=(new_w, 180))
                        img_lbl = ctk.CTkLabel(images_frame, text="", image=ctk_img)
                        img_lbl.image = ctk_img
                        img_lbl.pack(side="left", padx=10)
                    except Exception as e:
                        print(f"Error loading preview image {img_path}: {e}")

        # Display fields in 2 columns
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", pady=10)

        # 1. Build a list of all relevant keys
        skip_keys = {"doc_type", "ai_enhanced", "_confidence", "_raw_text", "ai_error", "amount_in_words"}
        all_keys = []
        for k in self.app.ocr_result:
            if k not in skip_keys and self.app.ocr_result.get(k) and self.app.ocr_result.get(k) != "Not found":
                all_keys.append(k)
        
        # 2. Add System Date and Form Type if they aren't there
        self.app.ocr_result["system_date"] = str(date.today())
        form_label = config.FORM_TYPES.get(self.app.form_type.get(), {}).get("label", self.app.form_type.get())
        self.app.ocr_result["form_type_lbl"] = form_label
        
        all_keys.append("system_date")
        all_keys.append("form_type_lbl")

        labels_map = {
            "name": "Full Name", "dob": "Date of Birth", "gender": "Gender",
            "aadhaar_number": "Aadhaar Number", "address": "Address",
            "holder_name": "Account Holder", "account_no": "Account Number",
            "ifsc": "IFSC Code", "branch": "Branch", "bank_name": "Bank Name",
            "cif": "Customer ID (CIF)", "mobile": "Mobile Number",
            "pan_number": "PAN Number", "father_name": "Father Name",
            "amount": "Amount (₹)", "cheque_no": "Cheque Number",
            "system_date": "Current System Date", "form_type_lbl": "Selected Banking Service"
        }

        idx = 0
        for fld in all_keys:
            val = self.app.ocr_result.get(fld, "—")
            
            # Try translation first, fallback to labels_map, fallback to titlecase
            lbl = t(f"field_{fld}", lang)
            if lbl == f"field_{fld}":
                lbl = t(fld, lang)
            if lbl == fld:
                lbl = labels_map.get(fld, fld.replace("_", " ").title())
            
            row, col = divmod(idx, 2)
            cell = ctk.CTkFrame(grid, fg_color=config.COLOR_SURFACE, corner_radius=8, border_width=1, border_color=config.COLOR_GLASS_BORDER)
            cell.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
            
            ctk.CTkLabel(cell, text=lbl, font=ctk.CTkFont(size=12), text_color=config.COLOR_SUBTEXT).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(cell, text=str(val), font=ctk.CTkFont(size=16, weight="bold"), text_color=config.COLOR_TEXT, wraplength=400).pack(anchor="w", padx=10, pady=(0,5))
            
            # Show amount in words if applicable
            if fld == "amount" and "amount_in_words" in self.app.ocr_result:
                words = self.app.ocr_result["amount_in_words"]
                ctk.CTkLabel(
                    cell, text=words, font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=config.COLOR_SUCCESS, wraplength=400
                ).pack(anchor="w", padx=10, pady=(0,5))

            idx += 1
        
        grid.grid_columnconfigure((0,1), weight=1)

        # ── Signature Reminder Banner ────────────────────────
        sign_banner = ctk.CTkFrame(
            self.scroll,
            fg_color="#FFF3CD",
            border_color="#E3A008",
            border_width=3,
            corner_radius=12,
        )
        sign_banner.pack(fill="x", padx=10, pady=(20, 10))

        ctk.CTkLabel(
            sign_banner,
            text=t("sign_reminder_banner", lang),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"),
            text_color="#7D4E00",
            wraplength=700,
            justify="center",
        ).pack(padx=20, pady=18)

        bar = self._footer_bar()
        tts_engine.speak_script("review_details", lang)

        def _edit():
            self.app.is_editing_all = True
            self.app.show_screen("MissingInfoScreen")

        # ── Left: Edit button ───────────────────────────────
        ctk.CTkButton(
            bar, text=f"✏ {t('btn_back', lang)} / Edit",
            command=_edit,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color="transparent", text_color=config.COLOR_PRIMARY,
            border_width=2, border_color=config.COLOR_PRIMARY,
            width=160, height=44,
        ).pack(side="left", padx=20, pady=16)

        # ── Centre: Voice Review button (optional, for elderly/visually impaired) ──
        def _voice_review():
            tts_engine.speak_review(self.app.ocr_result, lang)

        ctk.CTkButton(
            bar, text=t("btn_voice_review", lang),
            command=_voice_review,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14, weight="bold"),
            fg_color=config.COLOR_WARNING, hover_color="#B17A05",
            text_color="#1B2A3F",
            width=220, height=44, corner_radius=8,
        ).pack(side="left", padx=8, pady=16)

        # ── Right: Confirm button ───────────────────────────
        ctk.CTkButton(
            bar, text=t("btn_confirm", lang),
            command=self._submit,
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=16, weight="bold"),
            fg_color=config.COLOR_SUCCESS, hover_color="#047857",
            text_color="#FFFFFF",
            width=260, height=55, corner_radius=10,
        ).pack(side="right", padx=20, pady=10)

        tts_engine.speak_script("form_complete", lang)
        amount_val = self.app.ocr_result.get("amount", "")
        if amount_val and amount_val.isdigit() and int(amount_val) > 0:
            tts_engine.speak(amount_val, lang)
        # Speak signature reminder AFTER form_complete
        self.after(2500, lambda: tts_engine.speak_script("sign_reminder", lang))

    def _submit(self):
        ft = self.app.form_type.get()
        data = self.app.ocr_result
        lang = self.app.get_lang()
        try:
            self.app.last_pdf_path = form_generator.generate_form_by_type(
                data, ft, 
                os.path.join(config.PDF_OUTPUT_DIR, f"form_{ft}_{date.today().strftime('%Y%m%d')}.pdf"),
                lang=lang
            )
            import random, string
            self.app.last_txn_id = "TXN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.app.show_screen("ReceiptScreen")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ═══════════════════════════════════════════════════════════
# Screen 8 — Receipt
# ═══════════════════════════════════════════════════════════

class ReceiptScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._top = self._topbar("")
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=60, pady=40)
        
        self.card = ctk.CTkFrame(content, fg_color=config.COLOR_GLASS, border_width=2, border_color=config.COLOR_GLASS_BORDER, corner_radius=20)
        self.card.pack(expand=True, fill="both")
        
        self._instr = ctk.CTkLabel(self.card, text="", font=ctk.CTkFont(size=20, weight="bold"), text_color=config.COLOR_SUCCESS)
        self._instr.pack(pady=40)

        self._txn_lbl = ctk.CTkLabel(self.card, text="", font=ctk.CTkFont(size=24, weight="bold"), text_color=config.COLOR_PRIMARY)
        self._txn_lbl.pack(pady=10)

        self.btn_print = ctk.CTkButton(self.card, text="", command=self._print_pdf, font=ctk.CTkFont(size=18, weight="bold"), height=50)
        self.btn_print.pack(pady=20)

        self._footer_container = ctk.CTkFrame(self, fg_color="transparent", height=77)
        self._footer_container.pack(fill="x", side="bottom")

    def on_show(self):
        lang = self.app.get_lang()
        self._top.configure(text=t("receipt_title", lang))
        self._instr.configure(text=t("receipt_instr", lang))
        self.btn_print.configure(text=t("receipt_btn_print", lang))
        self._txn_lbl.configure(text=f"TXN: {self.app.last_txn_id}")
        
        self._footer_bar()
        
        tts_engine.speak_script("application_complete", lang)

        # Automatically open the PDF so the user can see it
        if hasattr(self.app, 'last_pdf_path') and self.app.last_pdf_path and os.path.exists(self.app.last_pdf_path):
            try:
                os.startfile(self.app.last_pdf_path)
            except Exception as e:
                print(f"[PDF Open Error] {e}")

    def _print_pdf(self):
        lang = self.app.get_lang()
        self.btn_print.configure(state="disabled")
        self._instr.configure(text=t("print_started", lang))
        tts_engine.speak_script("print_started", lang)

        if hasattr(self.app, 'last_pdf_path') and self.app.last_pdf_path and os.path.exists(self.app.last_pdf_path):
            try:
                os.startfile(self.app.last_pdf_path, "print")
            except Exception as e:
                print(f"[PDF Print Error] {e}")

        # After 3 seconds, announce process completed
        self.after(3500, lambda: self._complete_process(lang))

    def _complete_process(self, lang):
        self._instr.configure(text=t("printing_success", lang))
        tts_engine.speak_script("printing_success", lang)
        # Give it 5 seconds to speak, then reset
        self.after(5000, self.app.reset_session)

if __name__ == "__main__":
    app = KioskApp()
    app.mainloop()
    tts_engine.stop()
