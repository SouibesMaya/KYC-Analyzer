# RGPD, sécurité et accessibilité — KYC Analyzer / Fraud Document Analyzer

Ce document couvre, pour le rendu de mémoire, les aspects protection des
données personnelles, sécurité applicative et accessibilité du projet dans
son état actuel (V1 / MVP), ainsi que les recommandations pour une mise en
production.

## 1. Données personnelles manipulées

L'application traite, par nature (analyse automatique de documents
d'identité et bancaires pour un service fraude/KYC), des données à caractère
personnel potentiellement sensibles :

- **Identité** : nom, prénom, date de naissance, sexe, nationalité, numéro
  de document (extraits par OCR ou lecture de la zone MRZ — `analyses.last_name`,
  `first_name`, `date_of_birth`, `sex`, `nationality`, `document_number`).
- **Documents bancaires** : IBAN, BIC, titulaire de compte (extraits par
  `app/services/banking_extraction_service.py`, non persistés en base — voir
  section 2).
- **Texte OCR brut** (`analyses.extracted_text`) : peut contenir l'intégralité
  du texte visible sur le document (adresse, filiation, etc.).
- **Fichiers uploadés** (`backend/uploads/`) : copie brute du document
  (image/PDF) tel qu'envoyé par l'utilisateur.
- **Identifiant utilisateur** (`review_cases.user_id`) : identifiant métier
  fourni par l'appelant, pas nécessairement une donnée directement
  identifiante en soi, mais qui devient indirectement identifiante une fois
  reliée à une analyse.

## 2. Minimisation des données

- Les champs extraits en base (`analyses`) sont strictement ceux utilisés par
  le moteur de décision et le tableau de bord KPI (voir `docs/mcd-mld-mpd.md`
  pour le détail des colonnes) : aucune donnée bancaire structurée (IBAN,
  titulaire) n'est ajoutée au modèle `AnalysisRecord` — l'extraction bancaire
  (`banking_extraction_service.py`) reste au niveau de la réponse HTTP d'un
  appel, sans persistance dédiée.
- Le fichier original reste sur disque (`backend/uploads/`) le temps de
  l'analyse, mais n'est jamais dupliqué en base (seul le chemin logique
  transite en mémoire pendant le traitement).
- Aucune donnée n'est envoyée à un service tiers : OCR (Tesseract), lecture
  MRZ et classification de document s'exécutent entièrement en local, sans
  appel API externe.

## 3. Absence de données réelles dans le dépôt Git

- `backend/kyc_analyzer.db` (base SQLite locale contenant les vraies analyses
  effectuées pendant le développement) est **exclu du dépôt** via
  `.gitignore` (`backend/*.db`).
- `backend/uploads/` (documents réellement uploadés — cartes d'identité,
  titres de séjour, RIB scannés en test) est **exclu du dépôt** via
  `.gitignore` (`backend/uploads/*`, seul `.gitkeep` est conservé pour
  préserver la structure du dossier).
- Pour le rendu, la structure de la base est documentée dans
  `database/schema.sql` (aucune donnée) et un jeu de données est fourni dans
  `database/dump.sql`, **anonymisé** : les champs directement identifiants
  (`last_name`, `first_name`, `date_of_birth`, `document_number`,
  `original_filename`, `extracted_text`, `synthesis_text`,
  `review_cases.email_body`) y sont remplacés par des valeurs neutres
  (`REDACTED`, `1990-01-01`, `document_sample_N.ext`, etc.) ; les métadonnées
  d'analyse (scores, statuts, décisions, dates, type de document, nationalité)
  sont conservées telles quelles car elles ne permettent pas, seules,
  d'identifier une personne.
- `database/seed.sql` est volontairement vide : voir le commentaire en tête
  de fichier pour la justification (ne pas rejouer, même anonymisées, des
  données issues de documents réels comme jeu d'amorçage générique).

## 4. Durée de conservation

- **V1 (état actuel)** : aucune purge automatique. Les enregistrements
  (`analyses`, `review_cases`) et les fichiers dans `backend/uploads/`
  persistent indéfiniment sur le poste/serveur local.
- **Recommandation production** : définir une durée de conservation alignée
  sur l'obligation légale applicable au contrôle KYC/lutte anti-fraude (à
  arbitrer avec la conformité Betclic), puis mettre en place une purge
  planifiée (tâche cron / job planifié) sur `analyses`, `review_cases` et
  les fichiers correspondants dans `uploads/`.

## 5. Droits des utilisateurs

- **État actuel** : l'API expose `DELETE /api/documents/analyses/{analysis_id}`,
  qui permet de supprimer une analyse. Il n'existe pas encore d'endpoint
  dédié à l'exercice des droits RGPD (droit d'accès structuré par personne,
  droit à l'effacement déclenché par la personne concernée plutôt que par un
  opérateur interne, droit à la portabilité).
- **Recommandation production** : ajouter un point d'entrée (ou une
  procédure manuelle documentée) permettant, à partir d'un identifiant
  utilisateur (`user_id`) ou d'un numéro de document, de retrouver puis
  supprimer/exporter l'ensemble des enregistrements liés à une personne.

## 6. Bandeau cookies / mentions légales

- Le frontend (`frontend/index.html`) est une application interne
  (outil métier équipe fraude), sans dépôt de cookies de tracking ni
  analytics tiers : `localStorage`/cookies ne sont pas utilisés dans le code
  actuel, et aucun bandeau cookies n'est donc requis en l'état.
- Aucune page "Mentions légales / CGU" n'a été ajoutée : l'application n'est
  pas exposée au grand public, elle est destinée à un usage interne outillé.
  Si une exposition plus large était envisagée, une section dédiée devrait
  être ajoutée au frontend.

## 7. Accès restreint en production

- **État actuel** : aucune authentification ni autorisation n'est
  implémentée sur l'API (`backend/main.py`, aucun middleware d'auth, aucune
  dépendance de sécurité sur les routers). Toute personne ayant accès au
  réseau où tourne le backend peut appeler tous les endpoints, y compris la
  suppression d'analyses.
- C'est un point bloquant pour une mise en production réelle avec des
  données personnelles sensibles.
- **Recommandation production** : ajouter une authentification (SSO
  d'entreprise, JWT, ou a minima une clé d'API) devant les routers
  `documents`, `cases` et `analytics`, et restreindre l'accès réseau au
  périmètre de l'équipe fraude/KYC.

## 8. CORS

- `backend/main.py` configure `allow_origins=["*"]` (toutes origines
  acceptées). C'est acceptable en développement local (frontend statique
  ouvert en `file://` ou servi localement, backend sur `localhost:8000`)
  mais **doit être restreint** en production à la ou aux origines réelles du
  frontend déployé (voir le commentaire ajouté directement dans le code).

## 9. Uploads

- Extensions acceptées : `.pdf`, `.jpg`, `.jpeg`, `.png` uniquement
  (`app/services/document_service.py`, `ALLOWED_EXTENSIONS`), vérifiées
  côté serveur (pas seulement côté frontend).
- Taille maximale : 10 Mo (`MAX_FILE_SIZE_BYTES`), vérifiée côté serveur.
- Les fichiers sont enregistrés sous un nom généré (`uuid4() + extension`),
  jamais sous le nom original fourni par le client : cela évite les
  collisions et les attaques par traversée de chemin (path traversal) via un
  nom de fichier malveillant.
- Le dossier `backend/uploads/` est créé automatiquement s'il n'existe pas
  (`UPLOAD_DIR.mkdir(exist_ok=True)`).
- Ces contrôles sont vérifiés par `backend/tests/test_security.py`
  (rejet des extensions non autorisées).

## 10. Stockage local SQLite (MVP) et migration production

- Le choix de SQLite (fichier `backend/kyc_analyzer.db`) est adapté à un MVP
  / démonstrateur : simplicité, zéro configuration, un seul fichier.
- Limites connues de ce choix : pas de gestion fine des accès concurrents à
  grande échelle, pas de chiffrement au repos natif, sauvegarde manuelle
  (copie de fichier).
- **Migration recommandée pour la production** : bascule vers un SGBD
  managé (PostgreSQL, par exemple), avec chiffrement au repos et
  sauvegardes automatisées. Le code applicatif utilisant SQLAlchemy
  (`backend/app/database.py`), la migration se limite en théorie à changer
  `DATABASE_URL` et à valider la compatibilité des types (`Boolean`,
  `DateTime`, `Text`) — sans réécriture des modèles ni des routers.

## 11. Accessibilité

État vérifié sur `frontend/index.html` :

- `<html lang="fr">` : présent.
- Labels de formulaire : les champs "User ID" et "Document demandé" (création
  de dossier) utilisent désormais des `<label for="...">` associés à un
  `id` sur le champ correspondant (association programmatique, pas
  seulement visuelle).
- Zones de dépôt de fichier (drag & drop) : rendues focusables au clavier
  (`tabindex="0"`, `role="button"`) et activables via Entrée/Espace, avec un
  `aria-label` décrivant l'action et les formats acceptés ; les champs
  `<input type="file">` associés portent également un `aria-label`.
- Onglets de navigation : `aria-current="page"` posé dynamiquement sur
  l'onglet actif.
- Messages d'erreur/succès (toast) : `role="alert"` et `aria-live="assertive"`
  pour être annoncés par les lecteurs d'écran ; les icônes purement
  décoratives (✓, !) sont marquées `aria-hidden="true"`.
- Fenêtre modale de détail de dossier : `role="dialog"`, `aria-modal="true"`,
  fermeture au clavier (Échap), bouton de fermeture doté d'un `aria-label`.
- Contrastes : le thème utilise du texte quasi-noir (`--text: #0f172a`) sur
  fond clair et du blanc sur les cartes KPI sombres ; non vérifié par un
  outil automatisé (voir perspective ci-dessous).
- Responsive : mise en page en grille Tailwind avec points de rupture
  (`lg:grid-cols-4`, etc.), déjà en place et conservée telle quelle.

### Limites et perspectives accessibilité

- La navigation clavier n'a pas été auditée exhaustivement au-delà des
  zones modifiées ci-dessus (ex. : ordre de tabulation complet sur le
  tableau de bord, tableaux de données).
- Aucun audit automatisé (Lighthouse, axe, W3C) n'a été exécuté sur ce
  projet à ce jour ; c'est une perspective d'amélioration recommandée avant
  une mise en production, en complément de la vérification manuelle
  effectuée ici.

## 12. Synthèse — limites de la V1 et recommandations production

| Sujet | État V1 | Recommandation production |
|---|---|---|
| Authentification/autorisation | Absente | SSO / JWT / clé API + restriction réseau |
| CORS | `allow_origins=["*"]` | Restreindre aux origines réelles du frontend |
| Base de données | SQLite fichier local | PostgreSQL managé, chiffrement au repos |
| Conservation des données | Illimitée | Politique de rétention + purge planifiée |
| Droits utilisateurs | Suppression manuelle par endpoint | Procédure/API dédiée droit d'accès/effacement |
| Audit accessibilité | Vérification manuelle ciblée | Audit Lighthouse/axe/W3C complet |
| Anonymisation des exports | Appliquée sur `database/dump.sql` pour le rendu | Politique d'anonymisation formalisée pour tout export futur |
