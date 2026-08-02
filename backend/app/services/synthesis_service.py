from datetime import date


DOC_TYPE_LABELS = {
    "identity_card": "Carte Nationale d'Identité",
    "passport": "Passeport",
    "rib": "Relevé d'Identité Bancaire",
    "driving_license": "Permis de Conduire",
    "residence_permit": "Titre de Séjour",
    "unknown": "Document inconnu",
}

STATUS_LABELS = {
    "low_risk": "CONFORME",
    "manual_review": "VÉRIFICATION MANUELLE REQUISE",
    "high_risk": "RISQUE ÉLEVÉ",
}

STATUS_RECOMMENDATIONS = {
    "low_risk": "Accepter le document.",
    "manual_review": "Une vérification humaine est recommandée avant validation.",
    "high_risk": "Rejet ou escalade vers un analyste senior recommandé.",
}


def _format_date(iso_date: str | None) -> str | None:
    if not iso_date:
        return None
    try:
        d = date.fromisoformat(iso_date)
        return d.strftime("%d/%m/%Y")
    except Exception:
        return iso_date


def _compute_age(iso_dob: str) -> int | None:
    try:
        dob = date.fromisoformat(iso_dob)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def generate_synthesis(analysis: dict) -> str:
    doc_type = analysis.get("detected_document_type", "unknown")
    doc_label = DOC_TYPE_LABELS.get(doc_type, "Document")
    status = analysis.get("status", "manual_review")

    lines = []
    lines.append(f"SYNTHESE  {doc_label.upper()}")
    lines.append("")

    last_name = analysis.get("last_name")
    first_name = analysis.get("first_name")
    if last_name or first_name:
        full_name = f"{last_name or '?'} {first_name or '?'}".strip()
        lines.append(f"Titulaire     {full_name}")
    else:
        lines.append("Titulaire     Non identifie")

    dob = analysis.get("date_of_birth")
    if dob:
        age = _compute_age(dob)
        age_str = f" ({age} ans)" if age else ""
        lines.append(f"Ne(e) le      {_format_date(dob)}{age_str}")

    nationality_label = analysis.get("nationality_label")
    nationality = analysis.get("nationality")
    country_label = analysis.get("country_label")
    country_code = analysis.get("country_code")
    if nationality_label:
        lines.append(f"Nationalite   {nationality_label}")
    elif nationality:
        lines.append(f"Nationalite   {nationality}")
    elif country_label:
        lines.append(f"Pays emetteur {country_label}")
    elif country_code:
        lines.append(f"Pays emetteur {country_code}")

    doc_number = analysis.get("document_number")
    if doc_number:
        lines.append(f"N document    {doc_number}")

    sex = analysis.get("sex")
    if sex:
        lines.append(f"Genre         {'Masculin' if sex == 'M' else 'Feminin'}")

    lines.append("")

    expiry = analysis.get("expiration_date")
    is_expired = analysis.get("is_expired")
    if expiry:
        if is_expired:
            lines.append(f"EXPIRE        depuis le {_format_date(expiry)}")
        else:
            lines.append(f"Valide        jusqu'au {_format_date(expiry)}")
    elif doc_type in ("identity_card", "passport"):
        lines.append("Expiration    Non detectee")

    blur_score = analysis.get("blur_score")
    is_blurry = analysis.get("is_blurry")
    if blur_score is not None:
        quality = "Insuffisante" if is_blurry else "Bonne"
        lines.append(f"Qualite       {quality} (score {blur_score})")

    if analysis.get("mrz_parsed"):
        lines.append("Zone MRZ      Lue et validee")

    if not analysis.get("ocr_enabled"):
        lines.append("OCR           Non execute")

    alerts = [
        a for a in (analysis.get("alerts") or [])
        if "simule" not in a.lower() and "v1" not in a.lower()
    ]
    if alerts:
        lines.append("")
        lines.append("Alertes")
        for alert in alerts:
            lines.append(f"  {alert}")

    lines.append("")
    score = analysis.get("global_risk_score", 0)
    status_label = STATUS_LABELS.get(status, "INCONNU")
    recommendation = STATUS_RECOMMENDATIONS.get(status, "")
    lines.append(f"Resultat      {status_label}  {score}/100")
    lines.append(f"Action        {recommendation}")

    return "\n".join(lines)
