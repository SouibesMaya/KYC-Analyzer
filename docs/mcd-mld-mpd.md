# Modélisation de la base de données — MCD / MLD / MPD

Ce document décrit la base de données **réellement implémentée** par les
modèles SQLAlchemy (`backend/app/models/analysis.py`,
`backend/app/models/case.py`) et confirmée par l'inspection du fichier
`backend/kyc_analyzer.db`. Il ne propose pas de modèle théorique alternatif :
l'objectif est de documenter l'existant, pas de le redessiner.

## 1. Modèle Conceptuel de Données (MCD) simplifié

Deux entités métier, reliées par une relation 1–0..1 (un dossier est résolu
par au plus une analyse ; une analyse peut exister indépendamment d'un
dossier, via l'analyse rapide `POST /api/documents/upload-and-analyze`).

```
┌───────────────────────┐              ┌───────────────────────┐
│      DOSSIER          │              │       ANALYSE         │
│  (review_cases)        │  0,1 ── 1,1  │      (analyses)        │
├───────────────────────┤   résolu par  ├───────────────────────┤
│ user_id                │─────────────▶│ document_type          │
│ requested_doc_type      │              │ identité (nom, dob...) │
│ status / décision       │              │ validité (expiration)  │
│ email                   │              │ qualité (flou)         │
└───────────────────────┘              │ score de risque         │
                                          └───────────────────────┘
```

- Un **Dossier** (`review_cases`) est ouvert pour un `user_id` avec un type
  de document attendu (`requested_doc_type`). Il est créé en statut
  `pending`, sans analyse associée.
- Une **Analyse** (`analyses`) est produite pour chaque document uploadé,
  que ce soit dans le cadre d'un dossier ou en "analyse rapide" isolée
  (aucun dossier associé dans ce second cas).
- Quand un document est soumis pour un dossier, l'analyse produite est
  reliée au dossier (`review_cases.analysis_id`), et le dossier passe à un
  statut final (`compliant`, `wrong_document`, `expired`, `low_quality`,
  `manual_review`).

## 2. Modèle Logique de Données (MLD)

```
ANALYSES (
  id                      VARCHAR  PK,
  original_filename       VARCHAR  NOT NULL,
  upload_time             DATETIME,
  detected_document_type  VARCHAR,
  last_name               VARCHAR,
  first_name              VARCHAR,
  date_of_birth           VARCHAR,
  sex                     VARCHAR,
  nationality             VARCHAR,
  nationality_label       VARCHAR,
  country_code            VARCHAR,
  country_label           VARCHAR,
  document_number         VARCHAR,
  expiration_date         VARCHAR,
  is_expired              BOOLEAN,
  blur_score              FLOAT,
  is_blurry               BOOLEAN,
  global_risk_score       INTEGER,
  status                  VARCHAR,
  recommendation          VARCHAR,
  synthesis_text          TEXT,
  ocr_enabled             BOOLEAN,
  mrz_parsed              BOOLEAN,
  extracted_text          TEXT,
  alerts                  TEXT   -- JSON sérialisé en texte, voir section 5
)

REVIEW_CASES (
  id                    VARCHAR  PK,
  user_id               VARCHAR  NOT NULL,
  requested_doc_type    VARCHAR  NOT NULL,
  status                VARCHAR,
  decision              VARCHAR,
  created_at            DATETIME,
  resolved_at           DATETIME,
  analysis_id           VARCHAR  FK -> ANALYSES.id,
  email_subject         VARCHAR,
  email_body            TEXT,
  email_sent            BOOLEAN
)
```

Cardinalité : `REVIEW_CASES (0,N) —— (0,1) ANALYSES`
(une analyse est référencée par au plus un dossier ; un dossier référence au
plus une analyse — en pratique exactement une fois résolu).

## 3. Modèle Physique de Données (MPD)

Généré tel quel par `Base.metadata.create_all()` (SQLAlchemy) sur SQLite —
voir `database/schema.sql` pour le script SQL exécutable et commenté.

- **Clés primaires** : `id VARCHAR` (UUID généré côté application, pas
  d'auto-incrément SQLite).
- **Clé étrangère** : `review_cases.analysis_id → analyses.id`.
- **Index réel** : `ix_review_cases_user_id` sur `review_cases.user_id`
  (déclaré via `Column(..., index=True)` dans `app/models/case.py`) — c'est
  le seul index explicite du schéma actuel, aucun index n'est déclaré sur
  `analyses`.
- **Contraintes NOT NULL** : `analyses.original_filename`,
  `review_cases.user_id`, `review_cases.requested_doc_type`.
- Pas de contrainte `UNIQUE` autre que la clé primaire, pas de contrainte
  `CHECK` sur les valeurs de `status`/`decision` (les valeurs valides sont
  garanties uniquement côté application — voir `VALID_DOC_TYPES` dans
  `app/routers/cases.py` et les constantes `DECISION_*` dans
  `app/services/decision_service.py`).

## 4. Rôle des champs principaux

| Champ | Table | Rôle |
|---|---|---|
| `global_risk_score` | analyses | Score 0–100 cumulé à partir des alertes détectées (type inconnu, flou, OCR absent, nom/expiration non détectés, document expiré) — voir `document_service.py::analyze_document`. |
| `status` | analyses | Verdict de risque de l'analyse seule (`low_risk` / `manual_review` / `high_risk`), indépendant du type de document demandé. |
| `mrz_parsed` | analyses | Indique si la zone MRZ (bande normée en bas des CNI/passeports) a pu être lue — une lecture MRZ réussie est plus fiable qu'une extraction OCR libre. |
| `status` / `decision` | review_cases | Résultat du **moteur de décision** (`decision_service.py`), qui compare le document reçu au document demandé — distinct du `status` de l'analyse : un document peut être `low_risk` en tant qu'analyse, mais donner lieu à la décision `wrong_document` si ce n'est pas le bon type de document. |
| `analysis_id` | review_cases | Lien vers l'analyse qui a résolu le dossier ; `NULL` tant que le dossier est `pending`. |
| `email_sent` | review_cases | Toujours à `0`/`false` dans les données actuelles : l'envoi d'email est **simulé** côté frontend (bouton "Envoyer l'email"), aucun SMTP réel n'est déclenché côté backend. |

## 5. Limites actuelles du modèle

- **`alerts` stocké en texte JSON** (`analyses.alerts`) plutôt que dans une
  table dédiée : une analyse peut cumuler plusieurs alertes
  (`"Document potentiellement flou"`, `"Date d'expiration non détectée"`,
  etc.), mais elles sont sérialisées en une seule colonne texte
  (`json.dumps(...)` / `json.loads(...)` dans `document_service.py` et
  `app/routers/documents.py`). Cela rend impossible, en l'état, une requête
  SQL directe du type "compter le nombre d'analyses ayant l'alerte X" sans
  parser le JSON applicativement.
- **`document_type_scores`** (scores de classification par type de
  document, calculés par `document_classifier_service.py`) n'est **pas
  persisté du tout** : seul le type retenu (`detected_document_type`) et sa
  confiance (`document_type_confidence`) transitent en mémoire dans la
  réponse HTTP, sans trace en base pour analyse a posteriori des cas
  ambigus.
- **Pas de contrainte d'intégrité applicative en base** sur les valeurs de
  `status`/`decision`/`requested_doc_type` (validées uniquement côté code
  Python) : une insertion SQL directe pourrait introduire une valeur hors
  énumération.
- **Pas d'horodatage de modification** (`updated_at`) sur `analyses` — seule
  `upload_time` existe, il n'y a pas de suivi si un enregistrement était
  amené à être corrigé.

## 6. Amélioration possible : table dédiée aux alertes

Si le besoin d'interroger finement les alertes en SQL apparaissait (par
exemple pour un KPI "documents flous ET expirés"), une évolution possible
serait d'extraire `analyses.alerts` vers une table associée :

```sql
CREATE TABLE analysis_alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id  VARCHAR NOT NULL REFERENCES analyses(id),
    code         VARCHAR NOT NULL,   -- ex: 'BLURRY', 'EXPIRED', 'UNKNOWN_TYPE'
    message      VARCHAR NOT NULL    -- texte affiché au reviewer
);
```

Ceci est une piste documentée pour une itération future, **pas** un
changement appliqué dans ce rendu (conformément à la consigne de ne pas
modifier l'architecture existante sans nécessité) : le format actuel
(colonne `alerts` en JSON texte) reste pleinement fonctionnel pour les
besoins actuels du dashboard (`docs/api-documentation.md`, section
Analytics), qui n'agrège que des compteurs simples ne nécessitant pas de
descendre au niveau de chaque alerte individuelle.
