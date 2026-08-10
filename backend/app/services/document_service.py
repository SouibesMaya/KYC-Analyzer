import json
from pathlib import Path
from uuid import uuid4

import cv2
from fastapi import HTTPException, UploadFile

from app.services.ocr_service import extract_text_from_image
from app.services.mrz_service import parse_mrz, COUNTRY_CODES
from app.services.document_classifier_service import detect_document_type
from app.services.identity_extraction_service import extract_identity_information
from app.services.synthesis_service import generate_synthesis

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


async def save_uploaded_document(file: UploadFile) -> dict:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format non autorisé. Formats acceptés : PDF, JPG, JPEG, PNG.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux. Taille max : 10 MB.")

    saved_filename = f"{uuid4()}{ext}"
    saved_path = UPLOAD_DIR / saved_filename
    with open(saved_path, "wb") as f:
        f.write(content)

    return {
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "path": str(saved_path),
    }


def detect_blur_score(image_path: str) -> dict:
    path = Path(image_path)
    if path.suffix.lower() == ".pdf":
        return {"blur_score": None, "is_blurry": None, "threshold": None, "message": "PDF converti en image pour l'analyse."}

    image = cv2.imread(image_path)
    if image is None:
        return {"blur_score": None, "is_blurry": None, "threshold": None, "message": "Impossible de lire l'image."}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    threshold = 100
    is_blurry = score < threshold

    return {
        "blur_score": round(score, 2),
        "is_blurry": is_blurry,
        "threshold": threshold,
        "message": "Document flou détecté." if is_blurry else "Qualité d'image suffisante.",
    }


def analyze_document(document_path: str, original_filename: str = "") -> dict:
    ocr_result = extract_text_from_image(document_path)
    analyzed_path = ocr_result.get("analyzed_path", document_path)

    blur_result = detect_blur_score(analyzed_path)

    extracted_text = ocr_result["extracted_text"]

    mrz_result = parse_mrz(extracted_text) if ocr_result["ocr_enabled"] else {"mrz_parsed": False}

    if mrz_result["mrz_parsed"]:
        identity = {
            "last_name": mrz_result.get("last_name"),
            "first_name": mrz_result.get("first_name"),
            "name_found": bool(mrz_result.get("last_name") or mrz_result.get("first_name")),
            "date_of_birth": mrz_result.get("date_of_birth"),
            "expiration_date": mrz_result.get("expiration_date"),
            "is_expired": mrz_result.get("is_expired"),
            "expiration_found": mrz_result.get("expiration_date") is not None,
        }
        classification = {
            "detected_document_type": mrz_result.get("detected_document_type", "unknown"),
            "document_type_confidence": 10,
            "document_type_scores": {},
        }
    else:
        name_region_text = ocr_result.get("name_region_text", "")
        identity = extract_identity_information(extracted_text, name_region_text) if ocr_result["ocr_enabled"] else {
            "last_name": None, "first_name": None, "name_found": False,
            "date_of_birth": None, "expiration_date": None,
            "is_expired": None, "expiration_found": False,
            "nationality": None, "document_number": None,
        }
        classification = detect_document_type(extracted_text) if ocr_result["ocr_enabled"] else {
            "detected_document_type": "unknown", "document_type_confidence": 0,
            "document_type_scores": {"identity_card": 0, "passport": 0, "rib": 0},
        }

    doc_type = classification["detected_document_type"]
    alerts = []
    risk_score = 0

    if doc_type == "unknown":
        alerts.append("Type de document non reconnu")
        risk_score += 15

    if blur_result["is_blurry"] is True:
        alerts.append("Document potentiellement flou")
        risk_score += 25

    if not ocr_result["ocr_enabled"]:
        alerts.append("OCR non exécuté — texte non lisible")
        risk_score += 20
    elif len(extracted_text) < 20:
        alerts.append("Texte OCR insuffisant ou illisible")
        risk_score += 20

    if doc_type in ("identity_card", "passport"):
        if not identity["name_found"]:
            alerts.append("Nom ou prénom non détecté")
            risk_score += 10
        if not identity["expiration_found"]:
            alerts.append("Date d'expiration non détectée")
            risk_score += 15
        if identity["is_expired"] is True:
            alerts.append("Document expiré")
            risk_score += 40

    if doc_type == "rib":
        alerts.append("Contrôle RIB : vérification manuelle requise")
        risk_score += 5

    if risk_score <= 25:
        status = "low_risk"
        recommendation = "Document probablement conforme"
    elif risk_score <= 55:
        status = "manual_review"
        recommendation = "Vérification humaine recommandée"
    else:
        status = "high_risk"
        recommendation = "Rejet ou escalade recommandé"

    analysis = {
        "document_path": document_path,
        "analyzed_path": analyzed_path,
        "original_filename": original_filename,
        "detected_document_type": doc_type,
        "document_type_confidence": classification["document_type_confidence"],
        "document_type_scores": classification.get("document_type_scores", {}),
        "last_name": identity["last_name"],
        "first_name": identity["first_name"],
        "name_found": identity["name_found"],
        "date_of_birth": identity.get("date_of_birth"),
        "expiration_date": identity["expiration_date"],
        "is_expired": identity["is_expired"],
        "expiration_found": identity["expiration_found"],
        "sex": mrz_result.get("sex") if mrz_result["mrz_parsed"] else None,
        "nationality": mrz_result.get("nationality") if mrz_result["mrz_parsed"] else identity.get("nationality"),
        "nationality_label": mrz_result.get("nationality_label") if mrz_result["mrz_parsed"] else COUNTRY_CODES.get(identity.get("nationality", "")),
        "country_code": mrz_result.get("country_code") if mrz_result["mrz_parsed"] else identity.get("nationality"),
        "country_label": mrz_result.get("country_label") if mrz_result["mrz_parsed"] else COUNTRY_CODES.get(identity.get("nationality", "")),
        "document_number": mrz_result.get("document_number") if mrz_result["mrz_parsed"] else identity.get("document_number"),
        "mrz_parsed": mrz_result["mrz_parsed"],
        "mrz_type": mrz_result.get("mrz_type") if mrz_result["mrz_parsed"] else None,
        "blur_score": blur_result["blur_score"],
        "is_blurry": blur_result["is_blurry"],
        "blur_threshold": blur_result["threshold"],
        "ocr_enabled": ocr_result["ocr_enabled"],
        "ocr_message": ocr_result["message"],
        "extracted_text": extracted_text,
        "global_risk_score": min(risk_score, 100),
        "status": status,
        "recommendation": recommendation,
        "alerts": alerts,
    }

    analysis["synthesis_text"] = generate_synthesis(analysis)

    return analysis


def analysis_to_record_dict(analysis_id: str, analysis: dict) -> dict:
    return {
        "id": analysis_id,
        "original_filename": analysis.get("original_filename", ""),
        "detected_document_type": analysis.get("detected_document_type"),
        "last_name": analysis.get("last_name"),
        "first_name": analysis.get("first_name"),
        "date_of_birth": analysis.get("date_of_birth"),
        "sex": analysis.get("sex"),
        "nationality": analysis.get("nationality"),
        "nationality_label": analysis.get("nationality_label"),
        "country_code": analysis.get("country_code"),
        "country_label": analysis.get("country_label"),
        "document_number": analysis.get("document_number"),
        "expiration_date": analysis.get("expiration_date"),
        "is_expired": analysis.get("is_expired"),
        "blur_score": analysis.get("blur_score"),
        "is_blurry": analysis.get("is_blurry"),
        "global_risk_score": analysis.get("global_risk_score"),
        "status": analysis.get("status"),
        "recommendation": analysis.get("recommendation"),
        "synthesis_text": analysis.get("synthesis_text"),
        "ocr_enabled": analysis.get("ocr_enabled"),
        "mrz_parsed": analysis.get("mrz_parsed"),
        "extracted_text": analysis.get("extracted_text"),
        "alerts": json.dumps(analysis.get("alerts", []), ensure_ascii=False),
    }
