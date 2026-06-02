import re
from datetime import date, datetime


def extract_name_fields(extracted_text: str) -> dict:
    """
    Extrait le nom et le prénom à partir du texte OCR.
    V1 simple basée sur des mots-clés.
    """

    last_name = None
    first_name = None

    lines = extracted_text.splitlines()

    for line in lines:
        clean_line = line.strip()

        if re.search(r"\bnom\b", clean_line, re.IGNORECASE):
            parts = clean_line.split(":")
            if len(parts) > 1:
                last_name = parts[1].strip()

        if re.search(r"\bprenom\b|\bprénom\b|\bgiven names\b", clean_line, re.IGNORECASE):
            parts = clean_line.split(":")
            if len(parts) > 1:
                first_name = parts[1].strip()

    return {
        "last_name": last_name,
        "first_name": first_name,
        "name_found": bool(last_name and first_name)
    }


def extract_dates_from_text(extracted_text: str) -> list[str]:
    """
    Extrait les dates au format JJ/MM/AAAA, JJ-MM-AAAA ou AAAA-MM-JJ.
    """

    date_patterns = [
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    dates = []

    for pattern in date_patterns:
        matches = re.findall(pattern, extracted_text)
        dates.extend(matches)

    return dates


def parse_date(date_value: str):
    """
    Convertit une date texte en objet date Python.
    """

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d"
    ]

    for date_format in formats:
        try:
            return datetime.strptime(date_value, date_format).date()
        except ValueError:
            continue

    return None


def extract_expiration_date(extracted_text: str) -> dict:
    """
    Extrait une date d'expiration.
    V1 : cherche une ligne contenant expiration/expiry/expires.
    """

    expiration_date = None
    is_expired = None

    lines = extracted_text.splitlines()

    for line in lines:
        if re.search(r"expiration|expiry|expires|valid", line, re.IGNORECASE):
            dates = extract_dates_from_text(line)

            if dates:
                parsed_date = parse_date(dates[0])

                if parsed_date:
                    expiration_date = parsed_date
                    is_expired = parsed_date < date.today()
                    break

    return {
        "expiration_date": expiration_date.isoformat() if expiration_date else None,
        "is_expired": is_expired,
        "expiration_found": expiration_date is not None
    }


def extract_identity_information(extracted_text: str) -> dict:
    """
    Regroupe les extractions utiles pour une pièce d'identité.
    """

    name_result = extract_name_fields(extracted_text)
    expiration_result = extract_expiration_date(extracted_text)

    return {
        **name_result,
        **expiration_result
    }