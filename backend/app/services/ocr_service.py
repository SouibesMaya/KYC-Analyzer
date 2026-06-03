from pathlib import Path

import pytesseract
from PIL import Image


TESSERACT_PATH = r"C:\Users\m.souibes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_from_image(image_path: str) -> dict:
    """
    Extrait le texte brut d'une image avec Tesseract OCR.
    """

    path = Path(image_path)

    if not path.exists():
        return {
            "ocr_enabled": False,
            "extracted_text": "",
            "message": f"Fichier introuvable : {image_path}"
        }

    try:
        image = Image.open(path)

        extracted_text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        return {
            "ocr_enabled": True,
            "extracted_text": extracted_text.strip(),
            "message": "OCR réel exécuté avec succès"
        }

    except Exception as error:
        return {
            "ocr_enabled": False,
            "extracted_text": "",
            "message": f"Erreur OCR : {str(error)}"
        }