from fastapi import FastAPI
from app.routers import health, documents

app = FastAPI(
    title="Fraud Document Analyzer API",
    description="API pour l'analyse automatique de documents Fraud/KYC.",
    version="0.1.0"
)

app.include_router(health.router)
app.include_router(documents.router)


@app.get("/")
def read_root():
    return {
        "message": "Fraud Document Analyzer API is running"
    }
