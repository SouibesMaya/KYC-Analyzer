from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import create_tables
from app.routers import health, documents, cases, analytics

app = FastAPI(
    title="KYC Document Analyzer API",
    description="Analyse automatique de documents d'identité pour l'équipe fraude.",
    version="2.0.0",
)

# CORS : "*" est acceptable pour le développement local (frontend statique
# ouvert en file:// ou via un serveur local, backend sur localhost:8000).
# En production, remplacer par la ou les origines réelles du frontend déployé
# (ex : allow_origins=["https://kyc-analyzer.betclic.com"]).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(cases.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup():
    create_tables()


@app.get("/")
def read_root():
    return {"message": "KYC Document Analyzer API — v2.0.0"}
