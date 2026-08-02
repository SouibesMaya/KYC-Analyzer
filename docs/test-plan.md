# Plan de tests — KYC Analyzer / Fraud Document Analyzer

## 1. Objectif

Ce document décrit la stratégie de test mise en place pour valider le
comportement de l'API backend (FastAPI) du projet KYC Analyzer : tests
unitaires et d'intégration sur les endpoints exposés, et tests de sécurité
ciblés sur la gestion des erreurs et la validation des entrées.

L'objectif n'est pas de couvrir exhaustivement chaque branche logique des
services d'OCR/MRZ/classification (dépendants de Tesseract et de la qualité
des images fournies, donc difficiles à tester unitairement de façon stable),
mais de garantir que :

- les endpoints critiques répondent avec les codes HTTP attendus ;
- les erreurs utilisateur (fichier manquant, champ invalide, ressource
  introuvable) sont gérées proprement et ne remontent jamais d'exception
  brute côté client ;
- les réponses JSON contiennent les clés attendues par le frontend.

## 2. Périmètre et outillage

- **Framework** : `pytest`
- **Client de test** : `fastapi.testclient.TestClient` (basé sur `httpx`)
- **Isolation des données** : les tests utilisent une base SQLite **en
  mémoire**, injectée via `app.dependency_overrides` sur la dépendance
  `get_db` (voir `backend/tests/conftest.py`). `backend/kyc_analyzer.db`
  (données réelles) n'est ni lu ni modifié pendant l'exécution des tests.
- **Emplacement** : `backend/tests/`

## 3. Tests unitaires et d'intégration

| Fichier | Portée |
|---|---|
| `test_health.py` | `GET /` et `GET /health/` répondent 200. |
| `test_documents.py` | Existence du routeur documents, upload sans fichier (422 contrôlé), liste des analyses (JSON `total`/`items`), analyse inconnue (404). |
| `test_cases.py` | Création de dossier valide, champs manquants (422), type de document invalide (400), liste des dossiers (JSON), dossier inconnu (404), soumission de document sur dossier inconnu (404). |
| `test_analytics.py` | `GET /api/analytics/kpis` répond 200 et contient les clés KPI utilisées par le tableau de bord frontend (`total_documents`, `total_cases`, `emails_sent`, `compliance_rate`, `avg_risk_score`, `mrz_rate`, `expired_count`, `by_type`, `by_status`, `by_decision`, `daily_counts`), avec et sans filtre de date. |

Ces tests couvrent le cycle fonctionnel principal décrit dans
`docs/architecture.md` (création de dossier → soumission → décision) au
niveau du contrat HTTP, sans dépendre du résultat réel de l'OCR (les
endpoints qui déclenchent l'analyse complète d'un document nécessitent un
vrai fichier image/PDF et Tesseract installé ; ils sont donc exercés via des
cas d'erreur contrôlés — dossier/analyse inconnus — plutôt que via une
analyse de bout en bout, ce qui rendrait la suite fragile et dépendante de
l'environnement).

## 4. Tests de sécurité

Fichier : `test_security.py`

- Upload d'un fichier `.exe` et d'un fichier `.txt` → rejeté avec `400`
  (validation de l'extension dans `app/services/document_service.py`,
  `ALLOWED_EXTENSIONS = {.pdf, .jpg, .jpeg, .png}`).
- Appel d'une route inexistante → `404`.
- Vérification qu'aucune réponse d'erreur (404, 422) ne contient de
  traceback Python brut, ce qui garantit que les exceptions sont bien
  interceptées via `HTTPException` / la validation Pydantic plutôt que
  remontées telles quelles au client.

Ces tests ne remplacent pas un audit de sécurité complet (pentest, SAST/DAST)
mais couvrent les points de contrôle applicatifs les plus directement
vérifiables par des tests automatisés.

## 5. Comment lancer les tests

```powershell
cd backend
python -m venv .venv          # si pas déjà fait
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

Ou, en une ligne, pour un rapport détaillé :

```powershell
pytest -v
```

## 6. Synthèse des résultats attendus

Sur l'état actuel du code, l'ensemble de la suite (21 tests) passe :

```
21 passed, 5 warnings in ~0.7s
```

Les avertissements (`warnings`) proviennent de dépréciations dans les
dépendances (`@app.on_event("startup")`, `datetime.utcnow()`) et non d'un
défaut fonctionnel ; ils sont documentés comme limite connue (section 7).

## 7. Limites des tests

- **Pas de test de bout en bout de l'OCR/MRZ réel** : les services
  `ocr_service.py`, `mrz_service.py`, `identity_extraction_service.py`
  dépendent de l'installation locale de Tesseract et de la qualité de
  l'image fournie ; ils ne sont pas mockés ici. Une analyse complète
  (upload → OCR → classification → décision) a été validée manuellement à
  travers l'usage réel de l'application (cf. `backend/kyc_analyzer.db` /
  `database/dump.sql`), mais pas via une suite automatisée déterministe.
- **Pas de test de charge / performance.**
- **Pas de test frontend automatisé** : `frontend/index.html` (Alpine.js)
  est vérifié manuellement dans un navigateur, pas via un framework de test
  UI (Playwright, Cypress…).
- **Couverture de sécurité limitée à l'applicatif** : pas de scan de
  dépendances (SCA), pas de test d'intrusion réseau, pas de test
  d'authentification (l'API n'implémente pas encore d'authentification —
  voir `docs/rgpd-security.md`, section limites V1).
- Les tests s'exécutent sur une base en mémoire recréée à chaque session de
  test : ils ne valident pas de scénarios de migration de schéma.
