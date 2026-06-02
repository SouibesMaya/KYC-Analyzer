from pathlib import Path


def extract_text_from_image(image_path: str) -> dict:
    """
    OCR simulé pour la V1.
    Cette fonction sera remplacée par un vrai moteur OCR comme Tesseract ou une API OCR.
    """

    path = Path(image_path)

    if not path.exists():
        return {
            "ocr_enabled": False,
            "extracted_text": "",
            "message": f"Fichier introuvable : {image_path}"
        }

    simulated_text = """
    REPUBLIQUE FRANCAISE
    CARTE NATIONALE D'IDENTITE
    Nom: SOUIBES
    Prenom: Mohamed
    Date de naissance: 01/01/1998
    Date d'expiration: 16/02/2031
    """

    return {
        "ocr_enabled": True,
        "extracted_text": simulated_text.strip(),
        "message": "OCR simulé exécuté avec succès"
    }