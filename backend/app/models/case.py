from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.database import Base


class ReviewCase(Base):
    __tablename__ = "review_cases"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    requested_doc_type = Column(String, nullable=False)
    status = Column(String, default="pending")       # pending | compliant | wrong_document | expired | low_quality | manual_review
    decision = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)

    email_subject = Column(String)
    email_body = Column(Text)
    email_sent = Column(Boolean, default=False)
