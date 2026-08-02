-- ============================================================================
-- KYC Analyzer / Fraud Document Analyzer — Schéma de base de données
-- ============================================================================
-- SGBD cible      : SQLite 3 (fichier backend/kyc_analyzer.db)
-- Source de vérité : backend/app/models/analysis.py et backend/app/models/case.py
--                    (SQLAlchemy ORM — ce fichier documente la structure réelle
--                    générée par Base.metadata.create_all(), il ne remplace pas
--                    les modèles Python).
-- Ce fichier ne contient AUCUNE donnée (pas d'INSERT). Voir dump.sql pour un
-- export anonymisé et seed.sql pour l'amorçage d'un environnement de dev.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Table : analyses
-- Rôle  : une ligne = une analyse automatique d'un document uploadé (OCR, MRZ,
--         classification, flou, score de risque). Alimentée par
--         POST /api/documents/upload-and-analyze et
--         POST /api/cases/{case_id}/submit-document.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyses (
    id                      VARCHAR PRIMARY KEY,      -- UUID généré à l'analyse
    original_filename       VARCHAR NOT NULL,         -- nom du fichier tel qu'envoyé par le client
    upload_time             DATETIME,                 -- horodatage de l'analyse (UTC)

    -- Classification
    detected_document_type  VARCHAR,                  -- identity_card | passport | residence_permit
                                                        -- | residence_card | rib | bank_statement | unknown

    -- Identité (OCR structuré ou MRZ)
    last_name               VARCHAR,
    first_name              VARCHAR,
    date_of_birth           VARCHAR,                  -- format ISO (YYYY-MM-DD)
    sex                     VARCHAR,                  -- 'M' | 'F' (lecture MRZ uniquement)

    -- Nationalité / pays émetteur
    nationality              VARCHAR,                 -- code pays ISO 3166-1 alpha-3 (ex : FRA)
    nationality_label         VARCHAR,                -- libellé FR (ex : Française)
    country_code              VARCHAR,                -- code pays émetteur du document (MRZ)
    country_label             VARCHAR,

    document_number          VARCHAR,                 -- numéro de document détecté (OCR/MRZ)

    -- Validité
    expiration_date           VARCHAR,                -- format ISO (YYYY-MM-DD)
    is_expired                BOOLEAN,

    -- Qualité image
    blur_score                 FLOAT,                 -- variance du Laplacien (plus haut = plus net)
    is_blurry                  BOOLEAN,                -- score < seuil (100)

    -- Scoring & décision
    global_risk_score           INTEGER,               -- 0-100, cumul des alertes pondérées
    status                        VARCHAR,             -- low_risk | manual_review | high_risk
    recommendation                VARCHAR,             -- texte court à destination du reviewer

    synthesis_text                 TEXT,               -- synthèse texte générée pour le reviewer
    ocr_enabled                     BOOLEAN,           -- OCR exécuté avec succès
    mrz_parsed                       BOOLEAN,          -- zone MRZ détectée et lue
    extracted_text                   TEXT,             -- texte brut OCR complet (peut contenir des PII)
    alerts                            TEXT             -- liste JSON des alertes de risque détectées
);

-- Aucun index déclaré sur "analyses" côté modèle SQLAlchemy à ce jour.

-- ----------------------------------------------------------------------------
-- Table : review_cases
-- Rôle  : un dossier de review ouvert pour un utilisateur (user_id) auquel un
--         type de document a été demandé. Le dossier est résolu quand le
--         document est soumis et analysé (POST /api/cases/{case_id}/submit-document),
--         ce qui déclenche le moteur de décision (app/services/decision_service.py)
--         et, le cas échéant, la génération d'un email client.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_cases (
    id                    VARCHAR PRIMARY KEY,         -- UUID généré à la création du dossier
    user_id               VARCHAR NOT NULL,            -- identifiant utilisateur (métier, pas de FK)
    requested_doc_type    VARCHAR NOT NULL,            -- type de document demandé au client

    status                VARCHAR DEFAULT 'pending',   -- pending | compliant | wrong_document
                                                         -- | expired | low_quality | manual_review
    decision              VARCHAR,                     -- miroir de status une fois le dossier résolu

    created_at            DATETIME,
    resolved_at            DATETIME,                    -- rempli à la soumission du document

    analysis_id            VARCHAR,                     -- FK vers analyses.id (analyse liée au dossier)

    -- Email client généré par le moteur de décision (non envoyé automatiquement,
    -- l'envoi est simulé côté frontend)
    email_subject           VARCHAR,
    email_body               TEXT,
    email_sent                BOOLEAN DEFAULT 0,

    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Seul index réellement déclaré dans le modèle SQLAlchemy
-- (Column(..., index=True) sur ReviewCase.user_id) :
CREATE INDEX IF NOT EXISTS ix_review_cases_user_id ON review_cases(user_id);
