"""
security.py — Secure Data Deletion Module

Protects customer privacy by:
  1. Overwriting temporary scan files with random bytes before deletion.
  2. Clearing all in-memory OCR/extracted data from the app state.

Called at every session end (Home button, Start Over, or app close).
"""

import os
import gc


def secure_delete(file_path: str) -> bool:
    """
    Overwrite *file_path* with zeros then delete it.

    Returns True on success, False if the file didn't exist or failed.
    """
    if not file_path or not os.path.isfile(file_path):
        return False
    try:
        size = os.path.getsize(file_path)
        with open(file_path, "r+b") as f:
            # Overwrite with null bytes
            f.write(b"\x00" * size)
            f.flush()
            os.fsync(f.fileno())
        os.remove(file_path)
        print(f"[Security] Securely deleted: {os.path.basename(file_path)}")
        return True
    except Exception as exc:
        print(f"[Security] Could not delete {file_path}: {exc}")
        try:
            os.remove(file_path)          # at least delete even if overwrite failed
        except Exception:
            pass
        return False


def cleanup_session(temp_files: list):
    """
    Securely delete all files in *temp_files* list and run GC.

    Args:
        temp_files : list of absolute file path strings to destroy.
    """
    deleted = 0
    for path in temp_files:
        if secure_delete(path):
            deleted += 1

    # Force garbage collection to clear any lingering data
    gc.collect()
    print(f"[Security] Session cleanup done. {deleted}/{len(temp_files)} files removed.")


def clear_app_state(app):
    """
    Reset all sensitive fields in the KioskApp state object.
    Clears OCR data and temp file list.
    Does not delete files here; that's done by cleanup_session().
    """
    try:
        if hasattr(app, 'ocr_result'):
            app.ocr_result.clear()
        if hasattr(app, 'scanned_docs'):
            app.scanned_docs.clear()
        # Clear receipt info
        app.last_pdf_path = ""
        app.last_txn_id   = ""
    except Exception as exc:
        print(f"[Security] State clear error: {exc}")


def verify_coin() -> bool:
    """
    Verify that a ₹5 coin has been inserted into the hardware slot.

    In SOFTWARE SIMULATION mode (kiosk demo / development):
        Always returns True immediately.

    In HARDWARE mode (real deployment):
        Hook this function to your coin validator serial port / GPIO pin.
        Example for GPIO: import RPi.GPIO as GPIO; return GPIO.input(COIN_PIN)
        Example for serial: read a pulse from the coin acceptor module.

    Returns:
        True  — coin accepted, allow the user to proceed.
        False — no valid coin detected (show retry message).
    """
    # ── SOFTWARE SIMULATION (default) ──────────────────
    return True

    # ── HARDWARE HOOK (uncomment for real kiosk) ───────
    # try:
    #     import serial, time
    #     with serial.Serial("COM3", 9600, timeout=2) as ser:
    #         ser.write(b"CHECK\n")
    #         response = ser.readline().decode().strip()
    #         return response == "COIN_OK"
    # except Exception as exc:
    #     print(f"[Coin] Hardware error: {exc}")
    #     return False

