from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.models.case import ReviewCase

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

EMAIL_DECISIONS = {"wrong_document", "expired", "low_quality"}


@router.get("/kpis")
def get_kpis(
    days: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    analysis_q = db.query(AnalysisRecord)
    cases_q = db.query(ReviewCase)

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        analysis_q = analysis_q.filter(AnalysisRecord.upload_time >= cutoff)
        cases_q = cases_q.filter(ReviewCase.created_at >= cutoff)

    if from_date:
        try:
            fd = datetime.fromisoformat(from_date)
            analysis_q = analysis_q.filter(AnalysisRecord.upload_time >= fd)
            cases_q = cases_q.filter(ReviewCase.created_at >= fd)
        except ValueError:
            pass

    if to_date:
        try:
            td = datetime.fromisoformat(to_date + "T23:59:59")
            analysis_q = analysis_q.filter(AnalysisRecord.upload_time <= td)
            cases_q = cases_q.filter(ReviewCase.created_at <= td)
        except ValueError:
            pass

    records = analysis_q.order_by(AnalysisRecord.upload_time).all()
    cases = cases_q.all()

    total = len(records)

    by_type: dict = {}
    for r in records:
        t = r.detected_document_type or "unknown"
        by_type[t] = by_type.get(t, 0) + 1

    by_status: dict = {}
    for r in records:
        s = r.status or "unknown"
        by_status[s] = by_status.get(s, 0) + 1

    risk_scores = [r.global_risk_score for r in records if r.global_risk_score is not None]
    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0

    compliance_rate = round(by_status.get("low_risk", 0) / total * 100, 1) if total > 0 else 0

    by_decision: dict = {}
    for c in cases:
        d = c.decision or "pending"
        by_decision[d] = by_decision.get(d, 0) + 1

    emails_sent = sum(1 for c in cases if c.decision in EMAIL_DECISIONS)

    mrz_count = sum(1 for r in records if r.mrz_parsed)
    mrz_rate = round(mrz_count / total * 100, 1) if total > 0 else 0

    expired_count = sum(1 for r in records if r.is_expired)

    daily: dict = {}
    for r in records:
        if r.upload_time:
            day = r.upload_time.strftime("%Y-%m-%d")
            daily[day] = daily.get(day, 0) + 1
    daily_counts = [{"date": d, "count": c} for d, c in sorted(daily.items())]

    return {
        "total_documents": total,
        "total_cases": len(cases),
        "emails_sent": emails_sent,
        "compliance_rate": compliance_rate,
        "avg_risk_score": avg_risk,
        "mrz_rate": mrz_rate,
        "expired_count": expired_count,
        "by_type": by_type,
        "by_status": by_status,
        "by_decision": by_decision,
        "daily_counts": daily_counts,
    }
