import re
from datetime import date, datetime


# ─── Date helpers ────────────────────────────────────────────────────────────

def _normalize_ocr_digits(text: str) -> str:
    """Corrige les confusions OCR fréquentes sur les chiffres."""
    return text.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1")


def _extract_dates(text: str) -> list[str]:
    # Accepte aussi les 'O' à la place de '0' (confusion Tesseract)
    t = _normalize_ocr_digits(text)
    patterns = [
        r"\b\d{2}/\d{2}/\d{4}\b",          # 13/07/1990
        r"\b\d{2}-\d{2}-\d{4}\b",           # 13-07-1990
        r"\b\d{4}-\d{2}-\d{2}\b",           # 1990-07-13
        r"\b\d{2}\.\d{2}\.\d{4}\b",         # 13.07.1990
        r"\b\d{2}\s+\d{2}\s+\d{4}\b",       # 13 07 1990 (CNI française)
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, t))
    return found


def _parse_date(value: str) -> date | None:
    value = _normalize_ocr_digits(value)
    value = re.sub(r"\s+", "/", value.strip())  # normalise "13 07 1990" → "13/07/1990"
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _is_plausible_dob(d: date) -> bool:
    return 1920 <= d.year <= 2010


def _is_plausible_expiry(d: date) -> bool:
    return d.year >= 2000


# ─── Name extraction ─────────────────────────────────────────────────────────

def extract_name_fields(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    last_name = None
    first_name = None

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        # CNI française : "NOM /Surname" ou "NOM Surname" (/ parfois lu comme espace)
        if re.match(r"NOM[\s/|\\]*Surname", line, re.IGNORECASE):
            candidate = re.sub(r"\s*SP[EÉ]CIMEN.*", "", next_line, flags=re.IGNORECASE).strip()
            candidate = re.sub(r"\s*SPECIMEN.*", "", candidate, flags=re.IGNORECASE).strip()
            if candidate and not re.search(r"pr[eé]nom|given|sexe|date|lieu|naissance", candidate, re.IGNORECASE):
                last_name = candidate or None
            continue

        # CNI française : "Prénoms / Given names" → ligne suivante = Prénom
        if re.search(r"pr[eé]noms?[\s/|\\]*given\s*names?", line, re.IGNORECASE):
            candidate = next_line
            if candidate and not re.search(r"sexe|nationalit|date|lieu|naissance|usage", candidate, re.IGNORECASE):
                first_name = candidate or None
            continue

        # Format ancien avec deux-points : "NOM : DUPONT"
        if re.search(r"\bnom\b\s*:", line, re.IGNORECASE) and ":" in line:
            last_name = line.split(":", 1)[1].strip() or None

        if re.search(r"\bpr[eé]nom\b\s*:", line, re.IGNORECASE) and ":" in line:
            first_name = line.split(":", 1)[1].strip() or None

        # Passeport : "Surname" label
        if re.match(r"Surname\s*$", line, re.IGNORECASE):
            candidate = next_line
            if candidate and re.match(r"^[A-Z\s\-']+$", candidate):
                last_name = candidate or None

        # Passeport : "Given names" label
        if re.match(r"Given\s*names?\s*$", line, re.IGNORECASE):
            candidate = next_line
            if candidate:
                first_name = candidate or None

    return {
        "last_name": last_name,
        "first_name": first_name,
        "name_found": bool(last_name or first_name),
    }


# ─── Date of birth ───────────────────────────────────────────────────────────

def extract_date_of_birth(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        is_dob_context = bool(re.search(
            r"naissance|birth|geboren|nacimiento|date.de.naiss|date.of.birth",
            line, re.IGNORECASE
        ))

        if is_dob_context:
            # Date sur la même ligne
            dates = _extract_dates(line)
            if dates:
                parsed = _parse_date(dates[0])
                if parsed and _is_plausible_dob(parsed):
                    return parsed.isoformat()
            # Date sur la ligne suivante
            if i + 1 < len(lines):
                dates = _extract_dates(lines[i + 1])
                if dates:
                    parsed = _parse_date(dates[0])
                    if parsed and _is_plausible_dob(parsed):
                        return parsed.isoformat()

    # CNI : ligne "F FRA 13 07 1990" (sexe + nationalité + date naissance)
    for line in lines:
        if re.search(r"\b[FM]\s+[A-Z]{3}\b", line):
            dates = _extract_dates(line)
            for d_str in dates:
                parsed = _parse_date(d_str)
                if parsed and _is_plausible_dob(parsed):
                    return parsed.isoformat()

    return None


# ─── Expiration date ─────────────────────────────────────────────────────────

def extract_expiration_date(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    expiration_date = None
    is_expired = None

    for i, line in enumerate(lines):
        is_expiry_context = bool(re.search(
            r"expir|valid|date.d.expir|expiry|date.of.expir|ablauf",
            line, re.IGNORECASE
        ))

        if is_expiry_context:
            dates = _extract_dates(line)
            if not dates and i + 1 < len(lines):
                dates = _extract_dates(lines[i + 1])
            for d_str in dates:
                parsed = _parse_date(d_str)
                if parsed and _is_plausible_expiry(parsed):
                    expiration_date = parsed
                    is_expired = parsed < date.today()
                    break
            if expiration_date:
                break

    # CNI : "D2H6862M2 11 02 2030" — numéro de doc suivi de la date d'expiration
    if not expiration_date:
        for line in lines:
            if re.search(r"\b[A-Z0-9]{9}\b", line):
                dates = _extract_dates(line)
                for d_str in dates:
                    parsed = _parse_date(d_str)
                    if parsed and parsed.year >= 2020:
                        expiration_date = parsed
                        is_expired = parsed < date.today()
                        break
            if expiration_date:
                break

    return {
        "expiration_date": expiration_date.isoformat() if expiration_date else None,
        "is_expired": is_expired,
        "expiration_found": expiration_date is not None,
    }


# ─── Nationality ─────────────────────────────────────────────────────────────

COMMON_COUNTRY_CODES = {
    "FRA", "DEU", "GBR", "ESP", "ITA", "BEL", "PRT", "CHE", "LUX", "NLD",
    "POL", "ROU", "MAR", "TUN", "DZA", "SEN", "CIV", "CMR", "USA", "CAN",
    "BRA", "CHN", "RUS", "TUR", "UKR", "GRC", "HUN", "NGA", "GHA", "MLI",
}

SKIP_CODES = {"NOM", "SEX", "FOR", "AND", "THE", "DES", "LES", "SUR", "DU"}


def extract_nationality(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        # Ligne avec label "Nationalité"
        if re.search(r"nationalit", line, re.IGNORECASE):
            for code in re.findall(r"\b([A-Z]{3})\b", line):
                if code in COMMON_COUNTRY_CODES:
                    return code

    # Ligne "F FRA 13 07 1990" — sexe + code pays + date
    for line in lines:
        m = re.search(r"\b[FM]\s+([A-Z]{3})\b", line)
        if m and m.group(1) not in SKIP_CODES:
            return m.group(1)

    return None


# ─── Document number ─────────────────────────────────────────────────────────

WORD_BLACKLIST = {
    "NAISSANCE", "REPUBLIQUE", "FRANCAISE", "NATIONALE", "IDENTITE",
    "SIGNATURE", "SPECIMEN", "VALIDITE", "PASSEPORT", "RESIDENCE",
    "TITULAIRE", "DOMICILE", "ADRESSE", "DOCUMENT", "PASSPORT",
}


def extract_document_number(text: str) -> str | None:
    # CNI française nouvelle génération : lettre + chiffre + 7 alphanumériques
    m = re.search(r"\b([A-Z]\d[A-Z0-9]{7})\b", text)
    if m:
        return m.group(1)
    # Passeport français : 2 chiffres + 2 lettres + 5 chiffres
    m = re.search(r"\b(\d{2}[A-Z]{2}\d{5})\b", text)
    if m:
        return m.group(1)
    # Titre de séjour / carte de résident : format varié mais toujours avec chiffres
    # Exige au moins 2 chiffres pour éviter de capturer des mots courants
    for m in re.finditer(r"\b([A-Z0-9]{7,12})\b", text):
        candidate = m.group(1)
        digit_count = sum(c.isdigit() for c in candidate)
        if digit_count >= 2 and candidate not in WORD_BLACKLIST:
            return candidate
    return None


# ─── Fallback nom depuis la zone de capture haute ────────────────────────────

_NAME_BLACKLIST = {
    "SPECIMEN", "REPUBLIQUE", "FRANCAISE", "NATIONALITE", "PASSEPORT",
    "RESIDENCE", "CARTE", "IDENTITE", "PASSEPORT", "TITRE", "SEJOUR",
    "VALABLE", "PERMIS", "PREFECTURE", "SIGNATURE", "COMMUNE",
    "NAISSANCE", "DOMICILE", "ADRESSE", "FRANCE", "MINISTERE",
    "INTERIEUR", "SECURITE", "CERTIFICATE", "DELIVERY",
}


def extract_name_from_region(region_text: str) -> dict:
    """
    Extraction permissive depuis la zone nom : cherche des lignes courtes
    tout en majuscules qui ressemblent à un nom propre.
    Ne s'active qu'en dernier recours quand l'extraction structurée a échoué.
    """
    if not region_text:
        return {"last_name": None, "first_name": None, "name_found": False}

    lines = [l.strip() for l in region_text.splitlines() if l.strip()]
    candidates = []

    for line in lines:
        # On cherche des lignes : uniquement lettres (accents ok) + espaces/tirets
        clean = re.sub(r"[^A-ZÀ-Ÿa-zà-ÿ\s\-]", "", line).strip()
        tokens = clean.split()
        if not tokens:
            continue
        # Longueur : 1 à 4 mots, chaque token 2-20 lettres, ligne > 3 chars
        if not (1 <= len(tokens) <= 4 and 3 < len(clean) < 40):
            continue
        if any(len(t) < 2 for t in tokens):
            continue
        upper = line.upper()
        if any(bw in upper for bw in _NAME_BLACKLIST):
            continue
        # Doit être majoritairement en majuscules (noms de CNI)
        alpha = [c for c in clean if c.isalpha()]
        if not alpha:
            continue
        upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        if upper_ratio < 0.6:
            continue
        candidates.append(clean)

    if not candidates:
        return {"last_name": None, "first_name": None, "name_found": False}

    # Premier candidat = nom de famille (souvent en tête), deuxième = prénom
    last_name = candidates[0] if candidates else None
    first_name = candidates[1] if len(candidates) > 1 else None
    return {
        "last_name": last_name,
        "first_name": first_name,
        "name_found": bool(last_name or first_name),
    }


# ─── Point d'entrée principal ─────────────────────────────────────────────────

def extract_identity_information(text: str, name_region_text: str = "") -> dict:
    name = extract_name_fields(text)

    # Si l'extraction structurée n'a rien trouvé, on tente la zone nom
    if not name["name_found"] and name_region_text:
        name = extract_name_from_region(name_region_text)

    expiry = extract_expiration_date(text)
    dob = extract_date_of_birth(text)
    nationality = extract_nationality(text)
    doc_number = extract_document_number(text)

    return {
        **name,
        **expiry,
        "date_of_birth": dob,
        "nationality": nationality,
        "document_number": doc_number,
    }
