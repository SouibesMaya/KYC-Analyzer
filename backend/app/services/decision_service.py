"""
Moteur de décision du workflow fraude.
Compare le document reçu au document demandé et produit une décision + email.
"""

from app.services.document_classifier_service import DOCUMENT_TYPE_LABELS, IDENTITY_DOC_TYPES, BANKING_DOC_TYPES


DECISION_COMPLIANT = "compliant"
DECISION_WRONG_DOCUMENT = "wrong_document"
DECISION_EXPIRED = "expired"
DECISION_LOW_QUALITY = "low_quality"
DECISION_MANUAL_REVIEW = "manual_review"


def evaluate_case(requested_doc_type: str, analysis: dict) -> dict:
    """
    Évalue un dossier : compare doc demandé vs doc reçu.
    Retourne : décision, motif, template d'email.
    """
    received_type = analysis.get("detected_document_type", "unknown")
    risk_score = analysis.get("global_risk_score", 0)
    is_expired = analysis.get("is_expired", False)
    ocr_enabled = analysis.get("ocr_enabled", False)
    extracted_text = analysis.get("extracted_text", "")

    # 1. Type de document incorrect
    if received_type != "unknown" and received_type != requested_doc_type:
        # Tolérance : CNI et passeport sont interchangeables pour certains process
        both_identity = received_type in IDENTITY_DOC_TYPES and requested_doc_type in IDENTITY_DOC_TYPES
        if not both_identity:
            return _build_decision(
                decision=DECISION_WRONG_DOCUMENT,
                requested=requested_doc_type,
                received=received_type,
                analysis=analysis,
            )

    # 2. Document expiré
    if is_expired:
        return _build_decision(
            decision=DECISION_EXPIRED,
            requested=requested_doc_type,
            received=received_type,
            analysis=analysis,
        )

    # 3. Document illisible / qualité insuffisante
    if not ocr_enabled or (ocr_enabled and len(extracted_text) < 30):
        return _build_decision(
            decision=DECISION_LOW_QUALITY,
            requested=requested_doc_type,
            received=received_type,
            analysis=analysis,
        )

    # 4. Score de risque élevé → review manuelle
    if risk_score > 55:
        return _build_decision(
            decision=DECISION_MANUAL_REVIEW,
            requested=requested_doc_type,
            received=received_type,
            analysis=analysis,
        )

    # 5. Conforme
    return _build_decision(
        decision=DECISION_COMPLIANT,
        requested=requested_doc_type,
        received=received_type,
        analysis=analysis,
    )


def _build_decision(decision: str, requested: str, received: str, analysis: dict) -> dict:
    requested_label = DOCUMENT_TYPE_LABELS.get(requested, requested)
    received_label = DOCUMENT_TYPE_LABELS.get(received, received)

    email = _generate_email(decision, requested_label, received_label, analysis)

    return {
        "decision": decision,
        "requested_doc_type": requested,
        "received_doc_type": received,
        "requested_doc_label": requested_label,
        "received_doc_label": received_label,
        "requires_action": decision != DECISION_COMPLIANT,
        "requires_email": decision in (DECISION_WRONG_DOCUMENT, DECISION_EXPIRED, DECISION_LOW_QUALITY),
        "requires_manual_review": decision == DECISION_MANUAL_REVIEW,
        "email_subject": email["subject"],
        "email_body": email["body"],
    }


def _generate_email(decision: str, requested_label: str, received_label: str, analysis: dict) -> dict:
    holder = ""
    if analysis.get("first_name") or analysis.get("last_name"):
        holder = f"{analysis.get('first_name', '')} {analysis.get('last_name', '')}".strip()

    salutation = f"Bonjour{' ' + holder if holder else ''},"

    if decision == DECISION_WRONG_DOCUMENT:
        return {
            "subject": f"[Betclic] Document requis : {requested_label}",
            "body": (
                f"{salutation}\n\n"
                f"Nous avons bien reçu votre document, cependant celui-ci ne correspond pas au justificatif demandé.\n\n"
                f"- Document demandé : {requested_label}\n"
                f"- Document reçu    : {received_label}\n\n"
                f"Merci de nous transmettre le document correct afin que nous puissions traiter votre dossier.\n\n"
                f"Cordialement,\nL'équipe Fraude & Conformité – Betclic"
            ),
        }

    if decision == DECISION_EXPIRED:
        expiry = analysis.get("expiration_date", "")
        return {
            "subject": "[Betclic] Document expiré – action requise",
            "body": (
                f"{salutation}\n\n"
                f"Le document que vous nous avez transmis ({received_label}) est arrivé à expiration"
                f"{' le ' + expiry if expiry else ''}.\n\n"
                f"Merci de nous faire parvenir un document en cours de validité.\n\n"
                f"Cordialement,\nL'équipe Fraude & Conformité – Betclic"
            ),
        }

    if decision == DECISION_LOW_QUALITY:
        return {
            "subject": "[Betclic] Document illisible – nouvelle transmission requise",
            "body": (
                f"{salutation}\n\n"
                f"Le document reçu ({received_label}) est de qualité insuffisante pour être traité automatiquement "
                f"(image floue, tronquée ou illisible).\n\n"
                f"Merci de nous transmettre une photo ou un scan de bonne qualité :\n"
                f"- Document bien éclairé, à plat\n"
                f"- Tous les coins visibles\n"
                f"- Résolution suffisante (min. 300 dpi)\n\n"
                f"Cordialement,\nL'équipe Fraude & Conformité – Betclic"
            ),
        }

    # COMPLIANT ou MANUAL_REVIEW : pas d'email client
    return {"subject": "", "body": ""}
