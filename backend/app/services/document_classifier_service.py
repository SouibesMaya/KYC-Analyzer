def detect_document_type(extracted_text: str) -> dict:
    text = extracted_text.lower()

    keyword_map = {
        "identity_card": [
            "carte nationale", "identite nationale", "identity card",
            "carte d'identite", "carte nationale d'identite",
            "republique francaise", "république française",
            "date de naissance", "lieu de naissance",
        ],
        "passport": [
            "passport", "passeport", "travel document",
            "date of expiry", "date d'expiration", "given names",
            "nationality", "surname",
        ],
        "residence_permit": [
            "titre de sejour", "titre de séjour", "permis de residence",
            "permis de résidence", "carte de sejour", "carte de séjour",
            "prefecture", "préfecture", "recepisse", "récépissé",
            "autorisation provisoire de sejour", "mention valable en france",
            "certificat de residence", "certificat de résident",
            "residence algerien", "résident algérien",
            "type of permit", "cat. du titre",
            "personal number", "numero personnel",
            "valable jusqu'au", "valid until",
        ],
        "residence_card": [
            "carte de resident", "carte de résident", "resident permanent",
            "résident permanent", "carte de resident ue", "long term resident",
        ],
        "rib": [
            "releve d'identite bancaire", "relevé d'identité bancaire",
            "rib", "iban", "bic", "titulaire du compte",
            "domiciliation", "etablissement", "guichet",
        ],
        "bank_statement": [
            "releve de compte", "relevé de compte", "releve bancaire",
            "relevé bancaire", "solde", "operations", "opérations",
            "debit", "débit", "credit", "crédit", "transactions",
            "arrete au", "arrêté au", "extrait de compte",
        ],
    }

    scores = {doc_type: 0 for doc_type in keyword_map}
    for doc_type, keywords in keyword_map.items():
        scores[doc_type] = sum(1 for kw in keywords if kw in text)

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Titre de séjour et carte de résident partagent des mots-clés
    # On favorise carte de résident si le score est identique
    if scores["residence_card"] > 0 and scores["residence_permit"] > 0:
        if scores["residence_card"] >= scores["residence_permit"]:
            best_type = "residence_card"
        else:
            best_type = "residence_permit"

    if best_score == 0:
        best_type = "unknown"

    return {
        "detected_document_type": best_type,
        "document_type_confidence": best_score,
        "document_type_scores": scores,
    }


DOCUMENT_TYPE_LABELS = {
    "identity_card": "Carte Nationale d'Identité",
    "passport": "Passeport",
    "residence_permit": "Titre de Séjour",
    "residence_card": "Carte de Résident",
    "rib": "Relevé d'Identité Bancaire (RIB)",
    "bank_statement": "Relevé Bancaire",
    "unknown": "Document inconnu",
}

IDENTITY_DOC_TYPES = {"identity_card", "passport", "residence_permit", "residence_card"}
BANKING_DOC_TYPES = {"rib", "bank_statement"}
