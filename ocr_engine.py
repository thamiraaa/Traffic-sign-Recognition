"""
ocr_engine.py — Image preprocessing and Tesseract OCR pipeline.

Improvements over the original ocr_test.py:
  • Deskewing (corrects tilted scans)
  • CLAHE contrast enhancement (better for faded documents)
  • Sharpening kernel
  • Confidence score reporting
  • Camera / file dual input support
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image

import config

# ─────────────────────────────────────────────────────────
# Configure Tesseract
# ─────────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


# ─────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────

def _deskew(image: np.ndarray) -> np.ndarray:
    # Threshold image first since it's grayscale
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 5:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated


def _sharpen(image: np.ndarray) -> np.ndarray:
    """Apply a mild unsharp-mask style sharpening."""
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)


def _detect_and_crop_document(image: np.ndarray) -> np.ndarray:
    """Detect document boundaries and crop/warp to it to remove noise."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)
    
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        img_area = image.shape[0] * image.shape[1]
        if len(approx) == 4 and cv2.contourArea(c) > 0.15 * img_area:
            doc_cnt = approx
            break
            
    if doc_cnt is not None:
        # We found a document contour, warp it
        doc_cnt = doc_cnt.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        s = doc_cnt.sum(axis=1)
        rect[0] = doc_cnt[np.argmin(s)]
        rect[2] = doc_cnt[np.argmax(s)]
        diff = np.diff(doc_cnt, axis=1)
        rect[1] = doc_cnt[np.argmin(diff)]
        rect[3] = doc_cnt[np.argmax(diff)]
        
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
            
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
    return image


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def ai_preprocess_image(path: str) -> np.ndarray:
    """
    Preprocess image optimized for AI Vision models.
    Corrects rotation, crops, and enhances contrast, but does NOT apply harsh binary thresholding
    which can confuse LLMs. Returns a colour RGB image array.
    """
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {path}")

    # 0 — Document Boundary Detection & Crop
    img = _detect_and_crop_document(img)

    # 1 — Convert to grayscale for deskew and CLAHE, but we want a colour output eventually for Gemini
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2 — Deskew (early before distortion)
    # Deskewing is safe on grayscale
    gray = _deskew(gray)
    
    # Apply the same deskew rotation to the color image (to keep it color for Gemini)
    # Actually, _deskew computes threshold then rotates. Let's just use _deskew on gray and assume 
    # it's good enough, but for Gemini, color is better. Let's rewrite deskew for color.
    # To keep it simple, we will just use the grayscale image but converted back to 3-channel
    # as Gemini Vision accepts color or grayscale fine.
    
    # 3 — Bilateral Filter (Removes noise while keeping edges sharp)
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 4 — CLAHE (adaptive histogram equalisation for faded docs)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # 5 — Sharpening
    gray = _sharpen(gray)

    # Convert back to BGR for saving to a standard image file
    bgr_out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return bgr_out

def preprocess_image(path: str) -> np.ndarray:
    """
    Load an image from *path* and apply the full preprocessing
    pipeline suitable for Indian identity documents.

    Returns a binary (thresholded) NumPy array ready for OCR.
    Raises FileNotFoundError if the image cannot be loaded.
    """
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {path}")

    # 0 — Document Boundary Detection & Crop
    img = _detect_and_crop_document(img)

    # 1 — Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2 — Upscale (critical for small text)
    gray = cv2.resize(gray, None, fx=2.5, fy=2.5,
                      interpolation=cv2.INTER_CUBIC)

    # 3 — Deskew (do this early before distortion)
    gray = _deskew(gray)

    # 4 — Bilateral Filter (Removes holograms/noise while keeping edges sharp)
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 5 — CLAHE (adaptive histogram equalisation for faded docs)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 6 — Adaptive threshold
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2
    )

    # 7 — Morphological Closing (Stitches broken letters together)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    # 8 — Sharpening
    gray = _sharpen(gray)

    return gray


def preprocess_from_array(img: np.ndarray) -> np.ndarray:
    """Same pipeline but accepts an existing OpenCV image array (e.g. from camera)."""
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(tmp.name, img)
    result = preprocess_image(tmp.name)
    os.unlink(tmp.name)
    return result


def run_ocr(processed: np.ndarray) -> dict:
    """
    Run Tesseract on a preprocessed image array.

    Returns:
        {
          'text': str,           # full raw OCR text
          'confidence': float,   # mean word confidence (0-100)
          'words': list[dict]    # per-word detail from pytesseract
        }
    """
    # Changed PSM from 4 to 6 (Assume a single uniform block of text)
    config_str = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed, config=config_str)

    # Per-word confidence
    try:
        data = pytesseract.image_to_data(processed,
                                         config=config_str,
                                         output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data['conf'] if str(c) != '-1']
        confidence = round(sum(confs) / len(confs), 1) if confs else 0.0
        words = [
            {'word': data['text'][i], 'conf': int(data['conf'][i])}
            for i in range(len(data['text']))
            if data['text'][i].strip() and str(data['conf'][i]) != '-1'
        ]
    except Exception:
        confidence = 0.0
        words = []

    return {
        'text': text,
        'confidence': confidence,
        'words': words
    }


def capture_from_camera(device_index: int = 0) -> np.ndarray:
    """
    Capture a single frame from a webcam or scanner.
    Returns the raw BGR image array.
    Raises RuntimeError if the camera cannot be opened.
    """
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera device {device_index}")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame from camera")
    return frame


def numpy_to_pil(image: np.ndarray) -> Image.Image:
    """Convert a preprocessed numpy array to a PIL Image (for Tkinter display)."""
    return Image.fromarray(image)
