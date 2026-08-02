# KYC Analyzer / Fraud Document Analyzer

## Objectif

Application web interne destinée à l'équipe Fraude/KYC pour l'analyse
automatique de documents d'identité et bancaires : création de dossiers de
review, upload de documents, analyse automatique (OCR, lecture de la zone
MRZ, classification du type de document, détection de flou, scoring de
risque), décision automatisée (conforme / mauvais document / expiré /
qualité insuffisante / vérification manuelle), génération d'un email client
type, et tableau de bord d'indicateurs (KPI).

Projet réalisé dans le cadre d'un mémoire de Bachelor Data & Business
Intelligence.

## Stack technique

- **Backend** : Python 3.13, FastAPI, SQLAlchemy, Uvicorn
- **OCR / traitement d'image** : Tesseract (via `pytesseract`), OpenCV,
  PyMuPDF (conversion PDF → image)
- **Base de données** : SQLite (fichier local, `backend/kyc_analyzer.db`)
- **Frontend** : HTML statique, Alpine.js, Tailwind CDN (pas d'étape de
  build)
- **Tests** : pytest, `fastapi.testclient` (basé sur httpx)

## Structure du projet

```
KYC-Analyzer/
├── backend/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── requirements.txt
│   ├── kyc_analyzer.db            # Base SQLite locale (non versionnée)
│   ├── uploads/                   # Documents uploadés (non versionnés)
│   ├── app/
│   │   ├── database.py            # Config SQLAlchemy (engine, session, create_tables)
│   │   ├── models/                # Modèles ORM : AnalysisRecord, ReviewCase
│   │   ├── routers/                # Endpoints HTTP : health, documents, cases, analytics
│   │   └── services/                # Logique métier : OCR, MRZ, classification, scoring, décision...
│   └── tests/                       # Suite de tests pytest
├── frontend/
│   └── index.html                   # Interface (Alpine.js + Tailwind), aucune étape de build
├── database/
│   ├── schema.sql                   # Structure réelle (sans données)
│   ├── dump.sql                      # Export anonymisé (structure + données)
│   └── seed.sql                       # Volontairement vide (voir commentaire du fichier)
└── docs/
    ├── api-documentation.md
    ├── architecture.md
    ├── mcd-mld-mpd.md
    ├── rgpd-security.md
    └── test-plan.md
```

## Installation

Prérequis : Python 3.11+ et **Tesseract-OCR** installé sur la machine (le
chemin est configuré en dur pour Windows dans
`backend/app/services/ocr_service.py::TESSERACT_PATH` ; à adapter si besoin
selon l'environnement).

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement du backend

```powershell
cd backend
python -m uvicorn main:app --reload
```

L'API est alors disponible sur :

- **URL locale** : http://127.0.0.1:8000
- **Documentation Swagger interactive** : http://127.0.0.1:8000/docs

Les tables SQLite sont créées automatiquement au démarrage si elles
n'existent pas encore (`create_tables()`, appelé depuis l'événement de
démarrage de `main.py`).

## Ouverture du frontend

Le frontend est un unique fichier statique, sans build ni serveur dédié :
ouvrir directement `frontend/index.html` dans un navigateur (double-clic,
ou glisser-déposer dans la barre d'adresse). Il appelle l'API sur
`http://localhost:8000` (voir `const API` dans `frontend/index.html`) — le
backend doit donc être lancé au préalable.

## Lancement des tests

```powershell
cd backend
pytest
```

Ou pour un rapport détaillé : `pytest -v`. Voir `docs/test-plan.md` pour le
détail de la stratégie de tests (unitaires, intégration, sécurité) et les
résultats attendus. Les tests utilisent une base SQLite en mémoire dédiée
(voir `backend/tests/conftest.py`) : ils ne lisent ni ne modifient
`backend/kyc_analyzer.db`.

## Base de données et fichiers SQL

- La base de données réelle (`backend/kyc_analyzer.db`) est locale et
  **n'est pas versionnée** (voir `.gitignore` et `docs/rgpd-security.md`).
- `database/schema.sql` : structure SQL des tables réelles (`analyses`,
  `review_cases`), commentée, sans données.
- `database/dump.sql` : export SQL rejouable (DROP + CREATE + INSERT) des
  données réellement présentes dans `backend/kyc_analyzer.db` au moment du
  rendu, **anonymisé** (champs identifiants remplacés par des valeurs
  neutres — voir l'en-tête du fichier et `docs/rgpd-security.md`). Contient
  aussi, en commentaires, les requêtes de reporting utilisées comme
  référence pour le tableau de bord KPI.
- `database/seed.sql` : volontairement vide (voir commentaire en tête de
  fichier).
- Pour repartir d'une base vide : supprimer `backend/kyc_analyzer.db` puis
  relancer le backend (les tables sont recréées automatiquement, sans
  données).

## Documentation complémentaire

- [`docs/architecture.md`](docs/architecture.md) — architecture globale,
  pipeline d'analyse, choix techniques.
- [`docs/api-documentation.md`](docs/api-documentation.md) — endpoints,
  payloads et réponses.
- [`docs/mcd-mld-mpd.md`](docs/mcd-mld-mpd.md) — modélisation de la base de
  données (MCD/MLD/MPD).
- [`docs/test-plan.md`](docs/test-plan.md) — stratégie et résultats de
  tests.
- [`docs/rgpd-security.md`](docs/rgpd-security.md) — RGPD, sécurité,
  accessibilité.

## Limites connues (V1 / MVP)

- Aucune authentification/autorisation sur l'API (voir
  `docs/rgpd-security.md`, section 7).
- CORS ouvert (`allow_origins=["*"]`), acceptable en développement local
  uniquement.
- Envoi d'email uniquement **simulé** côté frontend, aucun SMTP réel.
- Pas de migration de schéma outillée (pas d'Alembic) : `create_tables()`
  ne fait que créer les tables manquantes.
- Pas de test automatisé de bout en bout de l'OCR/MRZ réel (dépendant de
  Tesseract et de la qualité d'image fournie).
- Pas d'audit d'accessibilité automatisé (Lighthouse/axe/W3C) à ce jour.

## Précautions RGPD

Ce projet traite, par nature, des données à caractère personnel extraites
de documents d'identité et bancaires. Avant toute manipulation du dépôt :

- **Ne jamais commiter** `backend/kyc_analyzer.db` ni le contenu de
  `backend/uploads/` (déjà exclus via `.gitignore`).
- Le seul jeu de données versionné (`database/dump.sql`) est **anonymisé** :
  ne pas le remplacer par un export brut de la base réelle.
- Voir [`docs/rgpd-security.md`](docs/rgpd-security.md) pour le détail
  complet (minimisation, conservation, droits des utilisateurs, accès en
  production).
