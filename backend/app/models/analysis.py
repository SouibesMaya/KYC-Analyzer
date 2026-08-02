from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)

    detected_document_type = Column(String)
    last_name = Column(String)
    first_name = Column(String)
    date_of_birth = Column(String)
    sex = Column(String)

    nationality = Column(String)
    nationality_label = Column(String)
    country_code = Column(String)
    country_label = Column(String)
    document_number = Column(String)

    expiration_date = Column(String)
    is_expired = Column(Boolean)

    blur_score = Column(Float)
    is_blurry = Column(Boolean)

    global_risk_score = Column(Integer)
    status = Column(String)
    recommendation = Column(String)

    synthesis_text = Column(Text)
    ocr_enabled = Column(Boolean)
    mrz_parsed = Column(Boolean)
    extracted_text = Column(Text)
    alerts = Column(Text)
