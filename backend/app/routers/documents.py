import json
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.services.document_service import (
    analyze_document,
    analysis_to_record_dict,
    save_uploaded_document,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("/test")
def test_router():
    return {"message": "Documents router is working"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    document = await save_uploaded_document(file)
    return {"message": "Document uploadé avec succès", "document": document}


@router.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...), db: Session = Depends(get_db)):
    document = await save_uploaded_document(file)
    analysis = analyze_document(document["path"], original_filename=document["original_filename"])

    analysis_id = str(uuid4())
    record_data = analysis_to_record_dict(analysis_id, analysis)

    record = AnalysisRecord(**record_data, upload_time=datetime.utcnow())
    db.add(record)
    db.commit()

    return {
        "message": "Document uploadé et analysé avec succès",
        "analysis_id": analysis_id,
        "document": document,
        "analysis": analysis,
    }


@router.get("/analyses")
def list_analyses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    records = (
        db.query(AnalysisRecord)
        .order_by(AnalysisRecord.upload_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(AnalysisRecord).count()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "original_filename": r.original_filename,
            "upload_time": r.upload_time.isoformat() if r.upload_time else None,
            "detected_document_type": r.detected_document_type,
            "last_name": r.last_name,
            "first_name": r.first_name,
            "date_of_birth": r.date_of_birth,
            "nationality_label": r.nationality_label,
            "expiration_date": r.expiration_date,
            "is_expired": r.is_expired,
            "global_risk_score": r.global_risk_score,
            "status": r.status,
            "mrz_parsed": r.mrz_parsed,
        })

    return {"total": total, "items": items}


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")

    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "upload_time": record.upload_time.isoformat() if record.upload_time else None,
        "detected_document_type": record.detected_document_type,
        "last_name": record.last_name,
        "first_name": record.first_name,
        "date_of_birth": record.date_of_birth,
        "sex": record.sex,
        "nationality": record.nationality,
        "nationality_label": record.nationality_label,
        "country_code": record.country_code,
        "country_label": record.country_label,
        "document_number": record.document_number,
        "expiration_date": record.expiration_date,
        "is_expired": record.is_expired,
        "blur_score": record.blur_score,
        "is_blurry": record.is_blurry,
        "global_risk_score": record.global_risk_score,
        "status": record.status,
        "recommendation": record.recommendation,
        "synthesis_text": record.synthesis_text,
        "ocr_enabled": record.ocr_enabled,
        "mrz_parsed": record.mrz_parsed,
        "extracted_text": record.extracted_text,
        "alerts": json.loads(record.alerts) if record.alerts else [],
    }


@router.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")
    db.delete(record)
    db.commit()
    return {"message": "Analyse supprimée."}
