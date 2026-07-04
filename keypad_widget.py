"""
keypad_widget.py — Reusable on-screen keypad components using CustomTkinter.

Provides:
  • NumericKeypad  — digit-only input (for amounts, account numbers, etc.)
  • AlphaKeypad   — QWERTY layout (for names, branches, etc.)
  • KeypadPopup   — full-screen modal overlay triggered by tapping an entry field
"""

import customtkinter as ctk
import tkinter as tk


# ═══════════════════════════════════════════════════════════
# Base Keypad
# ═══════════════════════════════════════════════════════════

class BaseKeypad(ctk.CTkFrame):
    """Base class for on-screen keypads."""

    def __init__(self, parent, target_var, on_confirm=None,
                 done_label="✔ Done", clear_label="Clear", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.target_var  = target_var
        self.on_confirm  = on_confirm
        self.done_label  = done_label
        self.clear_label = clear_label
        self._build_keys()

    def _build_keys(self):
        pass

    def _on_key(self, char):
        current = self.target_var.get()
        if char == "⌫":
            self.target_var.set(current[:-1])
        elif char == "__SPACE__":
            self.target_var.set(current + " ")
        elif char == "__CLEAR__":
            self.target_var.set("")
        elif char == "__DONE__":
            if self.on_confirm:
                self.on_confirm(self.target_var.get())
        else:
            self.target_var.set(current + char)


# ═══════════════════════════════════════════════════════════
# Numeric Keypad
# ═══════════════════════════════════════════════════════════

class NumericKeypad(BaseKeypad):
    """Large-button numeric keypad for touchscreen."""

    BTN_H = 62  # Taller buttons for finger-friendly use

    def _build_keys(self):
        rows = [
            ["7", "8", "9"],
            ["4", "5", "6"],
            ["1", "2", "3"],
            ["__CLEAR__", "0", "⌫"],
            ["__DONE__"],
        ]

        for r, row in enumerate(rows):
            self.grid_rowconfigure(r, weight=1)
            is_full = len(row) == 1
            for c, char in enumerate(row):
                self.grid_columnconfigure(c, weight=1)

                if char == "__DONE__":
                    display = self.done_label
                    fg, hover, tc = "#0E9F6E", "#047857", "#FFFFFF"
                elif char == "__CLEAR__":
                    display = self.clear_label
                    fg, hover, tc = "#E02424", "#C01C1C", "#FFFFFF"
                elif char == "⌫":
                    display, fg, hover, tc = "⌫", "#E3A008", "#B17A05", "#1B2A3F"
                else:
                    display = char
                    fg, hover, tc = "#1A56DB", "#1648C0", "#FFFFFF"

                btn = ctk.CTkButton(
                    self, text=display,
                    font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                    fg_color=fg, hover_color=hover, text_color=tc,
                    height=self.BTN_H, corner_radius=8,
                    command=lambda k=char: self._on_key(k),
                )
                if is_full:
                    btn.grid(row=r, column=0, columnspan=3,
                             padx=5, pady=4, sticky="nsew")
                else:
                    btn.grid(row=r, column=c, padx=5, pady=4, sticky="nsew")


# ═══════════════════════════════════════════════════════════
# Alpha (QWERTY) Keypad
# ═══════════════════════════════════════════════════════════

class AlphaKeypad(BaseKeypad):
    """QWERTY on-screen keyboard for text input."""

    BTN_H = 48

    def _build_keys(self):
        rows = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "⌫"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
            ["Z", "X", "C", "V", "B", "N", "M"],
            ["__CLEAR__", "__SPACE__", "__DONE__"],
        ]

        self.grid_columnconfigure(0, weight=1)

        for r, row in enumerate(rows):
            self.grid_rowconfigure(r, weight=1)
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.grid(row=r, column=0, sticky="nsew", pady=2, padx=2)

            for c, char in enumerate(row):
                row_frame.grid_columnconfigure(c, weight=1)

                if char == "__DONE__":
                    display = self.done_label
                    fg, hover, tc = "#0E9F6E", "#047857", "#FFFFFF"
                elif char == "__CLEAR__":
                    display = self.clear_label
                    fg, hover, tc = "#E02424", "#C01C1C", "#FFFFFF"
                elif char == "__SPACE__":
                    display = "Space"
                    fg, hover, tc = "#374151", "#1F2937", "#FFFFFF"
                elif char == "⌫":
                    display, fg, hover, tc = "⌫", "#E3A008", "#B17A05", "#1B2A3F"
                else:
                    display = char
                    fg, hover, tc = "#1B2A3F", "#2D4460", "#E0E9F4"

                btn = ctk.CTkButton(
                    row_frame, text=display,
                    font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                    fg_color=fg, hover_color=hover, text_color=tc,
                    height=self.BTN_H, corner_radius=6,
                    border_width=1, border_color="#8DA9C4",
                    command=lambda k=char: self._on_key(k),
                )
                btn.grid(row=0, column=c, padx=2, sticky="nsew")


# ═══════════════════════════════════════════════════════════
# Keypad Popup (Modal overlay for kiosk touch input)
# ═══════════════════════════════════════════════════════════

class KeypadPopup(ctk.CTkToplevel):
    """
    Full-screen modal keypad popup.

    Opens when a user taps an entry field on a touchscreen kiosk.
    Supports both numeric and alpha (QWERTY) modes.

    Usage:
        KeypadPopup(parent, mode="numeric",
                    field_label="Account Number",
                    initial_value=current_var.get(),
                    lang="en",
                    on_confirm=lambda val: current_var.set(val))
    """

    def __init__(self, parent, mode: str, field_label: str,
                 initial_value: str, lang: str, on_confirm):
        super().__init__(parent)

        from translations import t

        self.on_confirm_cb = on_confirm
        self._value_var    = tk.StringVar(value=initial_value)

        self.title("")
        self.resizable(False, False)
        self.grab_set()          # modal
        self.attributes("-topmost", True)
        self.configure(fg_color="#0E3A8C")

        # ── Size: covers bottom 55% of the screen ──────────
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        popup_h  = int(screen_h * 0.58)
        popup_w  = min(screen_w, 900)
        x_pos    = (screen_w - popup_w) // 2
        y_pos    = screen_h - popup_h
        self.geometry(f"{popup_w}x{popup_h}+{x_pos}+{y_pos}")

        # ── Header ─────────────────────────────────────────
        done_label  = t("keypad_done", lang)
        clear_label = t("keypad_clear", lang)
        title_key   = "keypad_title_numeric" if mode == "numeric" else "keypad_title_alpha"

        hdr = ctk.CTkFrame(self, fg_color="#1A56DB", corner_radius=0)
        hdr.pack(fill="x", ipady=6)

        ctk.CTkLabel(
            hdr,
            text=f"  {field_label}",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            hdr, text="✕",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="transparent", hover_color="#E02424",
            text_color="#FFFFFF", width=44, height=36,
            command=self.destroy,
        ).pack(side="right", padx=6)

        # ── Current value display ───────────────────────────
        disp_frame = ctk.CTkFrame(self, fg_color="#EBF3FF", corner_radius=0)
        disp_frame.pack(fill="x", ipady=4)

        self._display = ctk.CTkLabel(
            disp_frame, textvariable=self._value_var,
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#111928",
            anchor="w",
        )
        self._display.pack(fill="x", padx=16, pady=4)

        # ── Keypad ─────────────────────────────────────────
        pad_frame = ctk.CTkFrame(self, fg_color="transparent")
        pad_frame.pack(fill="both", expand=True, padx=16, pady=10)

        if mode == "numeric":
            kp = NumericKeypad(
                pad_frame, self._value_var,
                on_confirm=self._on_done,
                done_label=done_label, clear_label=clear_label,
            )
        else:
            kp = AlphaKeypad(
                pad_frame, self._value_var,
                on_confirm=self._on_done,
                done_label=done_label, clear_label=clear_label,
            )
        kp.pack(fill="both", expand=True)

    def _on_done(self, value: str):
        if self.on_confirm_cb:
            self.on_confirm_cb(value)
        self.destroy()


# ═══════════════════════════════════════════════════════════
# Helper: open keypad popup on entry click
# ═══════════════════════════════════════════════════════════

def attach_keypad(entry_widget: ctk.CTkEntry, var: tk.StringVar,
                  field_label: str, lang: str,
                  mode: str = "alpha"):
    """
    Bind a touch-friendly popup keypad to an entry widget.

    Call this once after creating each CTkEntry on the missing-info
    or denomination screen, e.g.:

        attach_keypad(entry, var, "Account Number", lang, mode="numeric")
    """
    def _open(_event=None):
        KeypadPopup(
            entry_widget.winfo_toplevel(),
            mode=mode,
            field_label=field_label,
            initial_value=var.get(),
            lang=lang,
            on_confirm=lambda val: var.set(val),
        )

    entry_widget.bind("<Button-1>", _open)
    entry_widget.configure(state="readonly")   # prevent physical keyboard pop-up
