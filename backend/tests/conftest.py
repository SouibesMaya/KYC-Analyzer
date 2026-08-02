"""
Configuration pytest partagée.

Objectif : tester l'API réelle (backend/main.py) sans jamais lire ni écrire
dans backend/kyc_analyzer.db (données réelles, cf. docs/rgpd-security.md).
On remplace la dépendance get_db par une base SQLite en mémoire, propre à
chaque session de tests, via app.dependency_overrides — sans modifier le
code applicatif.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.models.analysis import AnalysisRecord  # noqa: E402,F401
from app.models.case import ReviewCase  # noqa: E402,F401

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def client():
    return TestClient(app)
