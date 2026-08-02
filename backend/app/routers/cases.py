import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.models.case import ReviewCase
from app.services.decision_service import evaluate_case
from app.services.document_service import (
    analyze_document,
    analysis_to_record_dict,
    save_uploaded_document,
)
from app.services.banking_extraction_service import extract_banking_information
from app.services.document_classifier_service import BANKING_DOC_TYPES

router = APIRouter(prefix="/api/cases", tags=["Cases"])

VALID_DOC_TYPES = {
    "identity_card", "passport", "residence_permit",
    "residence_card", "rib", "bank_statement",
}


class CreateCaseRequest(BaseModel):
    user_id: str
    requested_doc_type: str


@router.post("/")
def create_case(body: CreateCaseRequest, db: Session = Depends(get_db)):
    if body.requested_doc_type not in VALID_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de document invalide. Valeurs acceptées : {', '.join(sorted(VALID_DOC_TYPES))}",
        )

    case_id = str(uuid4())
    case = ReviewCase(
        id=case_id,
        user_id=body.user_id,
        requested_doc_type=body.requested_doc_type,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(case)
    db.commit()

    return {
        "message": "Dossier créé avec succès",
        "case_id": case_id,
        "user_id": body.user_id,
        "requested_doc_type": body.requested_doc_type,
        "status": "pending",
    }


@router.post("/{case_id}/submit-document")
async def submit_document(
    case_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    case = db.query(ReviewCase).filter(ReviewCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    if case.status != "pending":
        raise HTTPException(status_code=400, detail="Ce dossier a déjà été traité.")

    document = await save_uploaded_document(file)
    analysis = analyze_document(document["path"], original_filename=document["original_filename"])

    # Extraction complémentaire pour les documents bancaires
    if analysis["detected_document_type"] in BANKING_DOC_TYPES:
        banking = extract_banking_information(analysis["extracted_text"], analysis["detected_document_type"])
        analysis.update(banking)

    # Décision workflow
    decision_result = evaluate_case(case.requested_doc_type, analysis)

    # Persistance analyse
    analysis_id = str(uuid4())
    record_data = analysis_to_record_dict(analysis_id, analysis)
    record = AnalysisRecord(**record_data, upload_time=datetime.utcnow())
    db.add(record)

    # Mise à jour dossier
    case.analysis_id = analysis_id
    case.status = decision_result["decision"]
    case.decision = decision_result["decision"]
    case.resolved_at = datetime.utcnow()
    case.email_subject = decision_result.get("email_subject", "")
    case.email_body = decision_result.get("email_body", "")
    case.email_sent = False

    db.commit()

    return {
        "case_id": case_id,
        "user_id": case.user_id,
        "requested_doc_type": case.requested_doc_type,
        "analysis_id": analysis_id,
        "document": document,
        "analysis": analysis,
        "decision": decision_result,
    }


@router.get("/")
def list_cases(user_id: str | None = None, status: str | None = None,
               skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(ReviewCase)
    if user_id:
        q = q.filter(ReviewCase.user_id == user_id)
    if status:
        q = q.filter(ReviewCase.status == status)

    total = q.count()
    cases = q.order_by(ReviewCase.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [_case_to_dict(c) for c in cases],
    }


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(ReviewCase).filter(ReviewCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    return _case_to_dict(case, include_email=True)


def _case_to_dict(case: ReviewCase, include_email: bool = False) -> dict:
    d = {
        "id": case.id,
        "user_id": case.user_id,
        "requested_doc_type": case.requested_doc_type,
        "status": case.status,
        "decision": case.decision,
        "analysis_id": case.analysis_id,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "email_sent": case.email_sent,
    }
    if include_email:
        d["email_subject"] = case.email_subject
        d["email_body"] = case.email_body
    return d
