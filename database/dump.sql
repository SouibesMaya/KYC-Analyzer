-- ============================================================================
-- KYC Analyzer / Fraud Document Analyzer — Export de base (dump)
-- ============================================================================
-- Généré à partir de : backend/kyc_analyzer.db (SQLite, état du 2026-08-02)
-- Contenu            : structure réelle (DROP + CREATE) + données réellement
--                      présentes en base au moment de l'export.
--
-- ANONYMISATION — les données ci-dessous sont réelles (15 analyses de
-- documents effectivement uploadés en test, 7 dossiers de review) mais les
-- champs qui constituent des données à caractère personnel identifiantes ont
-- été remplacés par des valeurs neutres avant export, car ce fichier est
-- destiné à être versionné dans un dépôt Git pour un rendu de mémoire :
--   - last_name, first_name              -> NULL ou 'REDACTED'
--   - date_of_birth                      -> '1990-01-01' (si une date existait)
--   - document_number                    -> 'REDACTED0' (si un numéro existait)
--   - original_filename                  -> 'document_sample_N.<ext>'
--   - extracted_text, synthesis_text     -> '[REDACTED_OCR_TEXT]'
--   - review_cases.email_body            -> '[REDACTED_EMAIL_BODY]'
-- Tous les autres champs (scores, statuts, types de document, dates
-- d'expiration, nationalité, décisions, horodatages) sont inchangés : ce sont
-- des métadonnées d'analyse, pas des identifiants directs.
-- Voir docs/rgpd-security.md pour la justification complète de cette approche.
-- ============================================================================

PRAGMA foreign_keys = OFF;

-- Ordre de suppression : review_cases avant analyses (FK review_cases.analysis_id -> analyses.id)
DROP TABLE IF EXISTS review_cases;
DROP TABLE IF EXISTS analyses;

-- ----------------------------------------------------------------------------
-- Structure (identique à schema.sql)
-- ----------------------------------------------------------------------------
CREATE TABLE analyses (
    id                      VARCHAR PRIMARY KEY,
    original_filename       VARCHAR NOT NULL,
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
    blur_score               FLOAT,
    is_blurry                BOOLEAN,
    global_risk_score         INTEGER,
    status                     VARCHAR,
    recommendation             VARCHAR,
    synthesis_text              TEXT,
    ocr_enabled                 BOOLEAN,
    mrz_parsed                   BOOLEAN,
    extracted_text                TEXT,
    alerts                         TEXT
);

CREATE TABLE review_cases (
    id                    VARCHAR PRIMARY KEY,
    user_id               VARCHAR NOT NULL,
    requested_doc_type    VARCHAR NOT NULL,
    status                VARCHAR DEFAULT 'pending',
    decision              VARCHAR,
    created_at            DATETIME,
    resolved_at            DATETIME,
    analysis_id            VARCHAR,
    email_subject           VARCHAR,
    email_body               TEXT,
    email_sent                BOOLEAN DEFAULT 0,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

CREATE INDEX ix_review_cases_user_id ON review_cases(user_id);

-- ----------------------------------------------------------------------------
-- Données — table analyses (15 lignes, anonymisées, ordre chronologique)
-- ----------------------------------------------------------------------------
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('4afb3da6-7c95-4d3d-8149-75da631e868c', 'document_sample_1.png', '2026-06-30 17:18:29.899122', 'identity_card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 783.94, 0, 25, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('8e564216-1321-474b-bb01-81fa59a2dd70', 'document_sample_2.png', '2026-06-30 17:18:35.963215', 'identity_card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 783.94, 0, 25, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('247c3a68-eec5-4b67-97a7-b9b3dd583db5', 'document_sample_3.png', '2026-06-30 17:29:05.640904', 'identity_card', NULL, 'REDACTED', '1990-01-01', NULL, NULL, NULL, NULL, NULL, 'REDACTED0', NULL, NULL, 783.94, 0, 15, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('ea485bcd-e726-45e5-ac95-68ffc722fe3f', 'document_sample_4.png', '2026-06-30 17:30:26.784621', 'identity_card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'REDACTED0', NULL, NULL, 1514.63, 0, 25, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('e3c3f8bc-788f-4a4d-8095-735dcd696f5e', 'document_sample_5.png', '2026-06-30 17:34:40.631173', 'identity_card', NULL, 'REDACTED', NULL, NULL, 'FRA', NULL, 'FRA', NULL, 'REDACTED0', NULL, NULL, 1514.63, 0, 15, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('d6432a80-d6c9-40d4-bcf2-2f5154715192', 'document_sample_6.png', '2026-06-30 17:50:23.477625', 'identity_card', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'REDACTED0', NULL, NULL, 783.94, 0, 25, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('e258eda6-5ed0-4023-a599-abd872ac6633', 'document_sample_7.png', '2026-06-30 17:51:31.150620', 'identity_card', NULL, 'REDACTED', NULL, NULL, 'FRA', NULL, 'FRA', NULL, 'REDACTED0', NULL, NULL, 1514.63, 0, 15, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Date d''expiration non détectée"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('108a34d2-a6ec-486d-9858-8f52b900d4f9', 'document_sample_8.png', '2026-06-30 17:53:40.056142', 'identity_card', NULL, NULL, '1990-01-01', NULL, 'DZA', NULL, 'DZA', NULL, 'REDACTED0', '2025-11-01', 1, 960.53, 0, 50, 'manual_review', 'Vérification humaine recommandée', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Document expiré"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('51856342-11d6-406f-912e-695f02047db0', 'document_sample_9.png', '2026-06-30 17:54:24.979462', 'identity_card', NULL, NULL, '1990-01-01', NULL, 'DZA', NULL, 'DZA', NULL, 'REDACTED0', '2025-11-01', 1, 960.53, 0, 50, 'manual_review', 'Vérification humaine recommandée', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Document expiré"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('534ae1fa-a934-491f-af27-2c89e7c957c9', 'document_sample_10.png', '2026-06-30 17:57:53.472382', 'identity_card', NULL, NULL, '1990-01-01', NULL, 'DZA', NULL, 'DZA', NULL, 'REDACTED0', '2025-11-01', 1, 960.53, 0, 50, 'manual_review', 'Vérification humaine recommandée', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Document expiré"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('e43fcf42-6f5c-4264-a15c-dffabdaa9639', 'document_sample_11.png', '2026-06-30 18:01:23.472418', 'identity_card', NULL, NULL, '1990-01-01', NULL, 'DZA', NULL, 'DZA', NULL, 'REDACTED0', '2025-11-01', 1, 960.53, 0, 50, 'manual_review', 'Vérification humaine recommandée', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '["Nom ou prénom non détecté", "Document expiré"]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('f0fe76dc-1800-49b9-9808-7d7258763ff9', 'document_sample_12.png', '2026-06-30 18:13:54.408782', 'residence_permit', NULL, NULL, '1990-01-01', NULL, 'DZA', 'Algérienne', 'DZA', 'Algérienne', 'REDACTED0', '2025-11-01', 1, 960.53, 0, 0, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '[]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('15b14fec-7c15-4da8-8caf-3ee49ab671c5', 'document_sample_13.png', '2026-06-30 18:14:59.648496', 'residence_permit', NULL, NULL, '1990-01-01', NULL, 'DZA', 'Algérienne', 'DZA', 'Algérienne', 'REDACTED0', '2025-11-01', 1, 960.53, 0, 0, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '[]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('2d003b38-91de-4cea-a40c-340c3f7e066e', 'document_sample_14.png', '2026-06-30 18:28:37.009337', 'residence_permit', NULL, NULL, '1990-01-01', NULL, 'DZA', 'Algérienne', 'DZA', 'Algérienne', 'REDACTED0', '2025-11-01', 1, 960.53, 0, 0, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '[]');
INSERT INTO analyses (id, original_filename, upload_time, detected_document_type, last_name, first_name, date_of_birth, sex, nationality, nationality_label, country_code, country_label, document_number, expiration_date, is_expired, blur_score, is_blurry, global_risk_score, status, recommendation, synthesis_text, ocr_enabled, mrz_parsed, extracted_text, alerts) VALUES ('b79bd04f-3c83-4939-a89b-5a3d5a65ab6e', 'document_sample_15.png', '2026-06-30 20:46:45.603006', 'residence_permit', NULL, NULL, '1990-01-01', NULL, 'DZA', 'Algérienne', 'DZA', 'Algérienne', 'REDACTED0', '2025-11-01', 1, 960.53, 0, 0, 'low_risk', 'Document probablement conforme', '[REDACTED_OCR_TEXT]', 1, 0, '[REDACTED_OCR_TEXT]', '[]');

-- ----------------------------------------------------------------------------
-- Données — table review_cases (7 lignes, anonymisées, ordre chronologique)
-- user_id : identifiants de test factices (numériques courts), pas des PII.
-- ----------------------------------------------------------------------------
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('307c19c4-b2dd-42b2-aacc-240ea99f5e95', '1234567', 'residence_permit', 'expired', 'expired', '2026-06-30 17:54:14.321456', '2026-06-30 17:54:24.979916', '51856342-11d6-406f-912e-695f02047db0', '[Betclic] Document expiré – action requise', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('dbe885f2-97b2-4b70-9cac-43a4334c8a53', '123456', 'residence_permit', 'expired', 'expired', '2026-06-30 17:57:47.890197', '2026-06-30 17:57:53.472966', '534ae1fa-a934-491f-af27-2c89e7c957c9', '[Betclic] Document expiré – action requise', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('819f6290-c4a1-4d94-987c-539f5de29b61', '12345', 'residence_permit', 'expired', 'expired', '2026-06-30 18:13:44.600011', '2026-06-30 18:13:54.409403', 'f0fe76dc-1800-49b9-9808-7d7258763ff9', '[Betclic] Document expiré – action requise', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('783c84dd-5972-4b77-9463-bcf5b2baf151', '12345', 'rib', 'wrong_document', 'wrong_document', '2026-06-30 18:14:51.426233', '2026-06-30 18:14:59.648877', '15b14fec-7c15-4da8-8caf-3ee49ab671c5', '[Betclic] Document requis : Relevé d''Identité Bancaire (RIB)', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('459da454-676b-4cbd-a496-e535c5b69e57', '12345', 'residence_permit', 'expired', 'expired', '2026-06-30 18:28:27.808291', '2026-06-30 18:28:37.009679', '2d003b38-91de-4cea-a40c-340c3f7e066e', '[Betclic] Document expiré – action requise', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('6951a854-afcd-4ce1-8ebb-03f30ceeb1e2', '123456', 'rib', 'wrong_document', 'wrong_document', '2026-06-30 20:46:33.313029', '2026-06-30 20:46:45.604013', 'b79bd04f-3c83-4939-a89b-5a3d5a65ab6e', '[Betclic] Document requis : Relevé d''Identité Bancaire (RIB)', '[REDACTED_EMAIL_BODY]', 0);
INSERT INTO review_cases (id, user_id, requested_doc_type, status, decision, created_at, resolved_at, analysis_id, email_subject, email_body, email_sent) VALUES ('7f6f31e8-4544-441d-939c-feec212ca62e', '2345', 'residence_permit', 'pending', NULL, '2026-08-02 17:07:36.027296', NULL, NULL, NULL, NULL, 0);

PRAGMA foreign_keys = ON;

-- ============================================================================
-- Requêtes de reporting (KPI dashboard) — à titre de référence / vérification
-- manuelle en base. La logique équivalente est implémentée en Python dans
-- backend/app/routers/analytics.py (GET /api/analytics/kpis).
-- ============================================================================

-- Nombre total d'analyses effectuées
-- SELECT COUNT(*) AS total_analyses FROM analyses;

-- Nombre de documents détectés comme expirés
-- SELECT COUNT(*) AS expired_count FROM analyses WHERE is_expired = 1;

-- Nombre de documents détectés comme flous
-- SELECT COUNT(*) AS blurry_count FROM analyses WHERE is_blurry = 1;

-- Répartition des analyses par type de document détecté
-- SELECT detected_document_type, COUNT(*) AS nb
-- FROM analyses
-- GROUP BY detected_document_type
-- ORDER BY nb DESC;

-- Répartition des analyses par statut de risque
-- SELECT status, COUNT(*) AS nb
-- FROM analyses
-- GROUP BY status
-- ORDER BY nb DESC;

-- Score de risque moyen (global_risk_score)
-- SELECT ROUND(AVG(global_risk_score), 1) AS avg_risk_score FROM analyses;

-- Nombre de dossiers de review par statut
-- SELECT status, COUNT(*) AS nb
-- FROM review_cases
-- GROUP BY status
-- ORDER BY nb DESC;

-- Nombre d'emails générés (décisions nécessitant un email client) : le champ
-- email_sent reste à 0 dans cette base car l'envoi n'est que simulé côté
-- frontend (bouton "Envoyer l'email" sans appel SMTP réel) — cf. app/services/decision_service.py
-- SELECT COUNT(*) AS emails_generated
-- FROM review_cases
-- WHERE decision IN ('wrong_document', 'expired', 'low_quality');

-- SELECT COUNT(*) AS emails_marked_sent FROM review_cases WHERE email_sent = 1;

-- Taux de lecture MRZ (zone MRZ détectée et parsée avec succès)
-- SELECT ROUND(100.0 * SUM(mrz_parsed) / COUNT(*), 1) AS mrz_rate_pct FROM analyses;
