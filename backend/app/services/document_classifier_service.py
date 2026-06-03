def detect_document_type(extracted_text: str) -> dict:
    """
    Détecte le type de document à partir du texte OCR.
    V1 simple basée sur des mots-clés.
    """

    text = extracted_text.lower()

    identity_keywords = [
        "carte nationale",
        "identite",
        "identité",
        "date de naissance",
        "date d'expiration",
        "republique francaise",
        "république française"
    ]

    passport_keywords = [
        "passport",
        "passeport",
        "surname",
        "given names",
        "nationality",
        "date of expiry"
    ]

    rib_keywords = [
        "iban",
        "bic",
        "releve d'identite bancaire",
        "relevé d'identité bancaire",
        "titulaire du compte",
        "domiciliation"
    ]

    identity_score = sum(1 for keyword in identity_keywords if keyword in text)
    passport_score = sum(1 for keyword in passport_keywords if keyword in text)
    rib_score = sum(1 for keyword in rib_keywords if keyword in text)

    scores = {
        "identity_card": identity_score,
        "passport": passport_score,
        "rib": rib_score
    }

    detected_type = max(scores, key=scores.get)
    confidence_score = scores[detected_type]

    if confidence_score == 0:
        detected_type = "unknown"

    return {
        "detected_document_type": detected_type,
        "document_type_confidence": confidence_score,
        "document_type_scores": scores
    }