from pathlib import Path
from uuid import uuid4

import cv2
from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def save_uploaded_document(file: UploadFile) -> dict:
    """
    Vérifie et sauvegarde un document uploadé.
    Formats acceptés : PDF, JPG, JPEG, PNG.
    """

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format non autorisé. Formats acceptés : PDF, JPG, JPEG, PNG."
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille maximale : {MAX_FILE_SIZE_MB} MB."
        )

    saved_filename = f"{uuid4()}{file_extension}"
    saved_path = UPLOAD_DIR / saved_filename

    with open(saved_path, "wb") as buffer:
        buffer.write(file_content)

    return {
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "content_type": file.content_type,
        "size_bytes": len(file_content),
        "path": str(saved_path)
    }


def detect_blur_score(document_path: str) -> dict:
    """
    Détecte si une image est floue à partir de la variance du Laplacien.
    Plus le score est bas, plus l'image est probablement floue.

    Pour l'instant, les PDF ne sont pas encore convertis en image.
    """

    file_extension = Path(document_path).suffix.lower()

    if file_extension == ".pdf":
        return {
            "blur_score": None,
            "is_blurry": None,
            "threshold": None,
            "message": "Analyse du flou non disponible pour les PDF dans cette V1."
        }

    image = cv2.imread(document_path)

    if image is None:
        return {
            "blur_score": None,
            "is_blurry": None,
            "threshold": None,
            "message": "Impossible de lire l'image."
        }

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray_image, cv2.CV_64F).var()

    threshold = 100
    is_blurry = bool(blur_score < threshold)
    return {
        "blur_score": round(float(blur_score), 2),
        "is_blurry": is_blurry,
        "threshold": threshold,
        "message": "Document flou détecté." if is_blurry else "Document suffisamment lisible."
    }


def analyze_document_mock(document_path: str) -> dict:
    """
    Première analyse du document.
    Pour l'instant : analyse simulée + vrai contrôle de flou sur les images.
    """

    blur_result = detect_blur_score(document_path)

    alerts = [
        "Analyse partiellement simulée",
        "OCR non encore activé",
        "Type de document non confirmé"
    ]

    global_risk_score = 35

    if blur_result["is_blurry"] is True:
        alerts.append("Document potentiellement flou")
        global_risk_score += 25

    if blur_result["is_blurry"] is None:
        alerts.append(blur_result["message"])

    if global_risk_score <= 30:
        status = "low_risk"
        recommendation = "Document probablement conforme"
    elif global_risk_score <= 60:
        status = "manual_review"
        recommendation = "Vérification humaine recommandée"
    else:
        status = "high_risk"
        recommendation = "Rejet ou escalade recommandé"

    return {
        "document_path": document_path,
        "detected_document_type": "unknown",
        "is_expired": None,
        "blur_score": blur_result["blur_score"],
        "is_blurry": blur_result["is_blurry"],
        "blur_threshold": blur_result["threshold"],
        "readability_score": None,
        "fraud_suspicion_score": 20,
        "global_risk_score": global_risk_score,
        "status": status,
        "recommendation": recommendation,
        "alerts": alerts
    }