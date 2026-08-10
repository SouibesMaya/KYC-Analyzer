from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image


TESSERACT_PATH = r"C:\Users\m.souibes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

UPLOAD_DIR = Path("uploads")

_SHARPEN_KERNEL = np.array([
    [-1, -1, -1],
    [-1,  9, -1],
    [-1, -1, -1]
], dtype=np.float32)


def _to_gray_upscaled(image_path: str, min_dim: int = 1500) -> np.ndarray | None:
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) < min_dim:
        scale = min_dim / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def preprocess_image(image_path: str) -> str:
    gray = _to_gray_upscaled(image_path)
    if gray is None:
        return image_path

    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    sharpened = cv2.filter2D(enhanced, -1, _SHARPEN_KERNEL)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    out_path = str(UPLOAD_DIR / (Path(image_path).stem + "_ocr.png"))
    cv2.imwrite(out_path, sharpened)
    return out_path


def ocr_name_region(image_path: str) -> str:
    """
    Second passage OCR ciblé sur le tiers supérieur de l'image (zone nom/prénom).
    Upscale x3 + Otsu + PSM 6 pour maximiser la lecture des polices stylisées.
    """
    img = cv2.imread(image_path)
    if img is None:
        return ""

    h, w = img.shape[:2]
    top = img[0:int(h * 0.38), :]

    # Upscale agressif sur cette petite zone
    scale = 3.0
    top = cv2.resize(top, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=15)

    # Otsu : binarisation globale — plus robuste que CLAHE sur le texte isolé
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Dilatation légère pour relier les lettres fragmentées
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)

    sharpened = cv2.filter2D(dilated, -1, _SHARPEN_KERNEL)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    try:
        text = pytesseract.image_to_string(
            Image.fromarray(sharpened),
            lang="fra+eng",
            config="--psm 6 --oem 3",
        )
        return text.strip()
    except Exception:
        return ""


def pdf_to_image(pdf_path: str) -> str | None:
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        image_path = str(UPLOAD_DIR / (Path(pdf_path).stem + "_page0.png"))
        pix.save(image_path)
        doc.close()
        return image_path
    except Exception:
        return None


def extract_text_from_image(image_path: str) -> dict:
    path = Path(image_path)

    if not path.exists():
        return {
            "ocr_enabled": False,
            "extracted_text": "",
            "analyzed_path": image_path,
            "message": f"Fichier introuvable : {image_path}",
        }

    actual_path = image_path
    if path.suffix.lower() == ".pdf":
        converted = pdf_to_image(image_path)
        if converted:
            actual_path = converted
        else:
            return {
                "ocr_enabled": False,
                "extracted_text": "",
                "analyzed_path": image_path,
                "message": "Conversion PDF en image impossible.",
            }

    try:
        preprocessed_path = preprocess_image(actual_path)
        main_text = pytesseract.image_to_string(
            Image.open(preprocessed_path),
            lang="fra+eng",
            config="--psm 3 --oem 3",
        ).strip()

        # Toujours tenter un passage ciblé sur la zone nom (haut du document)
        name_region_text = ocr_name_region(actual_path)

        # On préfixe le texte de la zone nom pour que l'extraction le trouve en premier
        combined = (name_region_text + "\n\n" + main_text).strip() if name_region_text else main_text

        return {
            "ocr_enabled": True,
            "extracted_text": combined,
            "name_region_text": name_region_text,
            "analyzed_path": actual_path,
            "preprocessed_path": preprocessed_path,
            "message": "OCR exécuté avec succès",
        }
    except Exception as error:
        return {
            "ocr_enabled": False,
            "extracted_text": "",
            "analyzed_path": actual_path,
            "message": f"Erreur OCR : {str(error)}",
        }
