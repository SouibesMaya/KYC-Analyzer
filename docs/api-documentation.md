# Documentation API — KYC Analyzer / Fraud Document Analyzer

## 1. Description générale

L'API est construite avec **FastAPI** (`backend/main.py`). Elle expose des
endpoints REST/JSON permettant de :

- créer et suivre des **dossiers de review** (`review_cases`) associant un
  utilisateur à un type de document demandé ;
- uploader et **analyser automatiquement** un document (OCR, lecture de la
  zone MRZ, classification du type de document, détection de flou, scoring
  de risque) ;
- consulter l'**historique** des analyses effectuées ;
- consulter des **indicateurs agrégés (KPI)** pour un tableau de bord.

Toutes les réponses sont au format JSON. Le frontend (`frontend/index.html`)
consomme cette API directement depuis le navigateur (`http://localhost:8000`
par défaut, CORS ouvert en développement — voir `docs/rgpd-security.md`).

La documentation interactive **Swagger** générée automatiquement par
FastAPI est disponible, une fois le serveur lancé, sur :

```
http://127.0.0.1:8000/docs
```

(et la spécification OpenAPI brute sur `http://127.0.0.1:8000/openapi.json`).

## 2. Routeurs

| Routeur | Fichier | Préfixe | Rôle |
|---|---|---|---|
| Health | `app/routers/health.py` | `/health` | Vérification de disponibilité du service |
| Documents | `app/routers/documents.py` | `/api/documents` | Upload et analyse directe d'un document, historique des analyses |
| Cases | `app/routers/cases.py` | `/api/cases` | Cycle de vie complet d'un dossier de review (création → soumission → décision) |
| Analytics | `app/routers/analytics.py` | `/api/analytics` | Indicateurs agrégés pour le tableau de bord |

Tous les routeurs sont enregistrés dans `backend/main.py` via
`app.include_router(...)`.

## 3. Endpoint racine

### `GET /`

Vérifie que l'API répond.

Réponse :
```json
{ "message": "KYC Document Analyzer API — v2.0.0" }
```

## 4. Health

### `GET /health/`

Réponse :
```json
{ "status": "ok", "message": "API is running" }
```

## 5. Documents (`/api/documents`)

### `GET /api/documents/test`
Vérifie que le routeur documents est bien monté. Réponse : `{ "message": "Documents router is working" }`.

### `POST /api/documents/upload`
Upload simple d'un document (sans déclencher l'analyse). Corps :
`multipart/form-data` avec un champ `file`.

Réponse (200) :
```json
{
  "message": "Document uploadé avec succès",
  "document": {
    "original_filename": "cni.png",
    "saved_filename": "5d1e...-....png",
    "content_type": "image/png",
    "size_bytes": 184213,
    "path": "uploads/5d1e...-....png"
  }
}
```

Erreurs : `400` si l'extension n'est pas dans `pdf, jpg, jpeg, png` ou si le
fichier dépasse 10 Mo ; `422` si aucun fichier n'est envoyé.

### `POST /api/documents/upload-and-analyze`
Upload puis analyse complète du document (OCR, MRZ, classification, flou,
scoring). Corps : `multipart/form-data`, champ `file`.

Réponse (200) :
```json
{
  "message": "Document uploadé et analysé avec succès",
  "analysis_id": "247c3a68-eec5-4b67-97a7-b9b3dd583db5",
  "document": { "...": "voir /upload" },
  "analysis": {
    "detected_document_type": "identity_card",
    "last_name": "DUPONT",
    "first_name": "MARIE",
    "date_of_birth": "1998-07-13",
    "expiration_date": "2030-02-11",
    "is_expired": false,
    "blur_score": 783.94,
    "is_blurry": false,
    "global_risk_score": 15,
    "status": "low_risk",
    "recommendation": "Document probablement conforme",
    "synthesis_text": "SYNTHESE  CARTE NATIONALE D'IDENTITE\n...",
    "alerts": ["Date d'expiration non détectée"]
  }
}
```

### `GET /api/documents/analyses?skip=0&limit=50`
Historique paginé des analyses (utilisé par l'onglet "Historique" du
frontend).

Réponse (200) :
```json
{
  "total": 15,
  "items": [
    {
      "id": "...", "original_filename": "...", "upload_time": "2026-06-30T17:29:05",
      "detected_document_type": "identity_card", "last_name": "...", "first_name": "...",
      "date_of_birth": "...", "nationality_label": "...", "expiration_date": "...",
      "is_expired": false, "global_risk_score": 15, "status": "low_risk", "mrz_parsed": false
    }
  ]
}
```

### `GET /api/documents/analyses/{analysis_id}`
Détail complet d'une analyse (tous les champs de `analyses`, y compris
`extracted_text` et `alerts`). `404` si l'identifiant est inconnu.

### `DELETE /api/documents/analyses/{analysis_id}`
Supprime une analyse. `404` si l'identifiant est inconnu.

## 6. Cases (`/api/cases`)

### `POST /api/cases/` — créer un dossier

Payload :
```json
{ "user_id": "USR-12345", "requested_doc_type": "identity_card" }
```

`requested_doc_type` doit être l'une des valeurs suivantes :
`identity_card`, `passport`, `residence_permit`, `residence_card`, `rib`,
`bank_statement`. Sinon : `400 Bad Request`.

Réponse (200) :
```json
{
  "message": "Dossier créé avec succès",
  "case_id": "307c19c4-b2dd-42b2-aacc-240ea99f5e95",
  "user_id": "USR-12345",
  "requested_doc_type": "identity_card",
  "status": "pending"
}
```

### `POST /api/cases/{case_id}/submit-document` — soumettre le document reçu

Corps : `multipart/form-data`, champ `file`. Déclenche l'analyse complète,
puis le moteur de décision (`app/services/decision_service.py`) qui compare
le document reçu au document demandé.

Erreurs : `404` si le dossier n'existe pas, `400` si le dossier a déjà été
traité (`status != "pending"`).

Réponse (200) :
```json
{
  "case_id": "...",
  "user_id": "USR-12345",
  "requested_doc_type": "identity_card",
  "analysis_id": "...",
  "document": { "...": "..." },
  "analysis": { "...": "..." },
  "decision": {
    "decision": "expired",
    "requested_doc_type": "identity_card",
    "received_doc_type": "identity_card",
    "requested_doc_label": "Carte Nationale d'Identité",
    "received_doc_label": "Carte Nationale d'Identité",
    "requires_action": true,
    "requires_email": true,
    "requires_manual_review": false,
    "email_subject": "[Betclic] Document expiré – action requise",
    "email_body": "Bonjour,\n\nLe document que vous nous avez transmis..."
  }
}
```

`decision.decision` peut valoir : `compliant`, `wrong_document`, `expired`,
`low_quality`, `manual_review`.

### `GET /api/cases/?user_id=&status=&skip=0&limit=50`
Liste paginée et filtrable des dossiers.

Réponse (200) :
```json
{ "total": 7, "items": [ { "id": "...", "user_id": "...", "requested_doc_type": "...", "status": "expired", "decision": "expired", "analysis_id": "...", "created_at": "...", "resolved_at": "...", "email_sent": false } ] }
```

### `GET /api/cases/{case_id}`
Détail d'un dossier (inclut `email_subject` et `email_body`). `404` si
inconnu.

## 7. Analytics (`/api/analytics`)

### `GET /api/analytics/kpis?days=&from_date=&to_date=`

Indicateurs agrégés utilisés par le tableau de bord. `days` (ex : `30`) ou
`from_date`/`to_date` (format `YYYY-MM-DD`) permettent de filtrer la
période ; sans paramètre, l'ensemble des données est agrégé.

Réponse (200) :
```json
{
  "total_documents": 15,
  "total_cases": 7,
  "emails_sent": 4,
  "compliance_rate": 0.0,
  "avg_risk_score": 22.3,
  "mrz_rate": 0.0,
  "expired_count": 4,
  "by_type": { "identity_card": 11, "residence_permit": 4 },
  "by_status": { "low_risk": 11, "manual_review": 4 },
  "by_decision": { "expired": 4, "wrong_document": 2, "pending": 1 },
  "daily_counts": [ { "date": "2026-06-30", "count": 15 } ]
}
```

Note : `emails_sent` compte les dossiers dont la décision nécessite un email
client (`wrong_document`, `expired`, `low_quality`) — l'envoi réel n'étant
que simulé côté frontend, ce compteur reflète les décisions générées, pas des
emails effectivement transmis (voir `docs/rgpd-security.md`).

## 8. Codes d'erreur communs

| Code | Signification |
|---|---|
| `400` | Requête invalide (extension de fichier non autorisée, fichier trop volumineux, type de document invalide, dossier déjà traité) |
| `404` | Ressource introuvable (dossier ou analyse inexistants, route inconnue) |
| `422` | Erreur de validation FastAPI/Pydantic (champ requis manquant, mauvais type) |

Les messages d'erreur (`detail`) sont rédigés en français et destinés à être
affichés tels quels côté frontend (cf. `showToast(e.message, 'error')` dans
`frontend/index.html`).
