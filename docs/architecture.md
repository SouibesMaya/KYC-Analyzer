# Architecture — KYC Analyzer / Fraud Document Analyzer

## 1. Vue d'ensemble

L'application suit une architecture simple à deux composants, sans
couche d'orchestration supplémentaire (pas de message queue, pas de
microservices) — choix cohérent avec le périmètre d'un MVP outillant une
équipe fraude/KYC en interne.

```
┌─────────────────────────┐        HTTP / JSON        ┌───────────────────────────┐
│  Frontend (statique)    │ ─────────────────────────▶ │  Backend FastAPI          │
│  frontend/index.html    │ ◀───────────────────────── │  backend/main.py          │
│  (Alpine.js + Tailwind) │                             │  + routers + services     │
└─────────────────────────┘                             └─────────────┬─────────────┘
                                                                        │ SQLAlchemy ORM
                                                                        ▼
                                                          ┌───────────────────────────┐
                                                          │  SQLite                   │
                                                          │  backend/kyc_analyzer.db  │
                                                          └───────────────────────────┘
```

## 2. Frontend

- Un unique fichier HTML (`frontend/index.html`), sans étape de build.
- **Alpine.js** pour la réactivité (un seul composant racine `app()` gérant
  4 onglets : Tableau de bord, Dossiers, Analyse rapide, Historique) et
  **Tailwind CDN** pour le style.
- Appelle directement l'API backend via `fetch()`, à une URL codée en dur
  (`const API = 'http://localhost:8000'`).
- Aucune authentification, aucun state management externe : tout l'état vit
  dans l'objet Alpine `app()`.

## 3. Backend

- **FastAPI** (`backend/main.py`), point d'entrée unique qui monte les
  routeurs et configure CORS.
- Organisation en couches :
  - `app/routers/` : définition des endpoints HTTP (validation d'entrée,
    codes de statut, sérialisation JSON). Ne contient pas de logique
    métier lourde — délègue aux services.
  - `app/services/` : logique métier pure (OCR, MRZ, classification,
    extraction d'identité/bancaire, scoring, synthèse, décision).
  - `app/models/` : modèles SQLAlchemy (`AnalysisRecord`, `ReviewCase`).
  - `app/database.py` : configuration du moteur SQLAlchemy et de la
    session (`get_db`), création des tables au démarrage.
- Serveur ASGI : **Uvicorn**.

### Services métier (`app/services/`)

| Service | Rôle |
|---|---|
| `document_service.py` | Orchestrateur : validation/sauvegarde de l'upload, détection de flou (OpenCV), appel des autres services, calcul du score de risque global, assemblage de l'objet `analysis`. |
| `ocr_service.py` | Prétraitement d'image (upscale, débruitage, CLAHE, netteté) et OCR via **Tesseract** (`pytesseract`), avec un second passage ciblé sur la zone nom. Convertit les PDF en image via **PyMuPDF**. |
| `mrz_service.py` | Détection et parsing de la zone MRZ (TD1 : cartes d'identité/titres de séjour, TD3 : passeports) — lecture normée, plus fiable que l'OCR libre quand elle est disponible. |
| `identity_extraction_service.py` | Extraction par expressions régulières du nom, prénom, date de naissance, date d'expiration, nationalité, numéro de document depuis le texte OCR libre (fallback quand la MRZ n'est pas lisible). |
| `document_classifier_service.py` | Classification du type de document par score de mots-clés (CNI, passeport, titre de séjour, carte de résident, RIB, relevé bancaire). |
| `banking_extraction_service.py` | Extraction IBAN/BIC/titulaire/banque/période pour les documents bancaires (RIB, relevés). |
| `synthesis_service.py` | Génère la synthèse texte lisible par un reviewer humain (affichée dans le frontend). |
| `decision_service.py` | Moteur de décision du workflow "dossier" : compare le document reçu au document demandé, détermine la décision (`compliant`, `wrong_document`, `expired`, `low_quality`, `manual_review`) et génère l'email client correspondant. |

## 4. Base de données

- **SQLite** en fichier unique (`backend/kyc_analyzer.db`), accédé via
  **SQLAlchemy** (mode synchrone, `sessionmaker`).
- Deux tables (détail complet dans `docs/mcd-mld-mpd.md`) :
  - `analyses` : une ligne par document analysé.
  - `review_cases` : un dossier de review par demande utilisateur, relié à
    l'analyse qui l'a résolu (`review_cases.analysis_id → analyses.id`).
- Les tables sont créées automatiquement au démarrage du serveur
  (`create_tables()` dans `app/database.py`, appelé depuis l'événement
  `startup` de `main.py`), sans outil de migration dédié (pas d'Alembic à ce
  stade — cohérent avec un schéma qui n'a pas encore eu besoin d'évoluer).

## 5. Pipeline d'analyse documentaire

Déclenché par `POST /api/documents/upload-and-analyze` ou
`POST /api/cases/{case_id}/submit-document` (`app/services/document_service.py::analyze_document`) :

1. **OCR** (`ocr_service.py`) : conversion PDF→image si nécessaire,
   prétraitement, extraction de texte (Tesseract, `fra+eng`).
2. **Lecture MRZ** (`mrz_service.py`) : tentative de parsing de la zone
   MRZ dans le texte OCR ; si réussie, elle prime sur l'extraction libre
   (plus fiable, format normé).
3. **Extraction d'identité** (`identity_extraction_service.py`) : si pas de
   MRZ, extraction par regex du nom/prénom/dates/nationalité/numéro.
4. **Classification** (`document_classifier_service.py`) : détermination du
   type de document par score de mots-clés (sauf si déjà déterminé par la
   MRZ).
5. **Détection de flou** (`document_service.py::detect_blur_score`, OpenCV,
   variance du Laplacien).
6. **Scoring de risque** : cumul de points selon les alertes détectées
   (type inconnu, flou, OCR absent/insuffisant, nom/expiration non
   détectés, document expiré...) → `global_risk_score` (0–100) et `status`
   (`low_risk` / `manual_review` / `high_risk`).
7. **Synthèse** (`synthesis_service.py`) : texte de synthèse pour le
   reviewer.
8. **Persistance** : l'analyse est enregistrée dans `analyses`
   (`analysis_to_record_dict` + `db.add`/`db.commit`).

En complément, dans le flux "dossier" (`POST /api/cases/{case_id}/submit-document`) :

9. **Extraction bancaire** (`banking_extraction_service.py`) si le document
   détecté est un RIB ou un relevé bancaire.
10. **Décision** (`decision_service.py::evaluate_case`) : comparaison du
    document reçu au document demandé, détermination de la décision finale
    et génération de l'email client si nécessaire.
11. **Mise à jour du dossier** (`review_cases.status`, `.decision`,
    `.resolved_at`, `.email_subject`, `.email_body`).
12. **Alimentation du dashboard KPI** : `GET /api/analytics/kpis` agrège en
    lecture seule les tables `analyses` et `review_cases` (pas de table de
    KPI matérialisée — calcul à la volée).

## 6. Flux utilisateur de bout en bout

```
1. Création dossier         POST /api/cases/                     (user_id, requested_doc_type)
2. Upload document          POST /api/cases/{id}/submit-document  (multipart file)
3. OCR / MRZ                ocr_service.py, mrz_service.py
4. Classification            document_classifier_service.py
5. Scoring                   document_service.py (global_risk_score, status)
6. Décision                  decision_service.py (compliant | wrong_document | expired | low_quality | manual_review)
7. Stockage                  analyses + review_cases (SQLite)
8. KPI dashboard              GET /api/analytics/kpis  →  frontend "Tableau de bord"
```

## 7. Choix techniques et justification

| Choix | Justification |
|---|---|
| FastAPI | Typage des payloads (Pydantic), documentation Swagger générée automatiquement, performances suffisantes pour un usage interne. |
| SQLite | Zéro configuration, adapté à un MVP mono-instance ; migration vers PostgreSQL documentée comme perspective (`docs/rgpd-security.md`). |
| Tesseract (OCR local) | Pas de dépendance à un service cloud tiers pour traiter des documents d'identité sensibles → cohérent avec la minimisation des données. |
| Frontend statique sans build (Alpine.js + Tailwind CDN) | Pas de chaîne de build à maintenir pour un outil interne à faible trafic ; déploiement = un fichier HTML. |
| Séparation routers/services | Les routers restent fins (validation + code HTTP), la logique métier (scoring, décision, extraction) est testable indépendamment du framework web. |
| Pas d'authentification en V1 | Périmètre MVP interne ; identifié comme limite bloquante avant mise en production réelle (`docs/rgpd-security.md`). |
