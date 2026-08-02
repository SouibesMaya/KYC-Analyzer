import re
from datetime import date, datetime


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.upper())


def extract_iban(text: str) -> str | None:
    # IBAN : code pays (2L) + 2 chiffres + jusqu'à 30 caractères alphanumériques
    # Format brut (avec ou sans espaces)
    pattern = r"\b([A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){4,7})\b"
    matches = re.findall(pattern, _normalize(text))
    for m in matches:
        clean = m.replace(" ", "")
        # IBAN France = 27 chars, d'autres pays 15-34 chars
        if 15 <= len(clean) <= 34:
            # Formatage lisible : groupes de 4
            formatted = " ".join(clean[i:i+4] for i in range(0, len(clean), 4))
            return formatted
    return None


def extract_bic(text: str) -> str | None:
    # BIC/SWIFT : 8 ou 11 caractères
    pattern = r"\b([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b"
    matches = re.findall(pattern, _normalize(text))
    # Filtre les faux positifs (évite les mots courants)
    excluded = {"FRAN", "DATE", "NOM", "PAYS", "CODE", "BIEN", "DANS"}
    for m in matches:
        if m[:4] not in excluded and len(m) in (8, 11):
            return m
    return None


def extract_account_holder(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if re.search(r"titulaire|titulaire du compte|account holder|nom du titulaire", line, re.IGNORECASE):
            # Valeur sur la même ligne après ":"
            if ":" in line:
                candidate = line.split(":", 1)[1].strip()
                if candidate:
                    return candidate
            # Ou ligne suivante
            if i + 1 < len(lines):
                candidate = lines[i + 1]
                if candidate and len(candidate) > 2:
                    return candidate
    return None


def extract_bank_name(text: str) -> str | None:
    known_banks = [
        "BNP Paribas", "Société Générale", "Crédit Agricole", "Crédit Mutuel",
        "Caisse d'Épargne", "Banque Populaire", "LCL", "La Banque Postale",
        "CIC", "HSBC", "Boursorama", "Fortuneo", "Hello Bank", "Orange Bank",
        "Revolut", "N26", "Qonto", "Shine", "Nickel", "Lydia",
        "Crédit Lyonnais", "BPE", "BPCE",
    ]
    for bank in known_banks:
        if bank.lower() in text.lower():
            return bank
    return None


def extract_statement_period(text: str) -> dict:
    """Extrait la période d'un relevé bancaire (du XX/XX/XXXX au XX/XX/XXXX)."""
    date_patterns = [
        r"\b(\d{2}/\d{2}/\d{4})\b",
        r"\b(\d{2}\.\d{2}\.\d{4})\b",
        r"\b(\d{2}-\d{2}-\d{4})\b",
        r"\b(\d{2}\s+\d{2}\s+\d{4})\b",
    ]

    date_from = None
    date_to = None

    for line in text.splitlines():
        if re.search(r"du\s+\d|from\s+\d|période|period|du :", line, re.IGNORECASE):
            all_dates = []
            for pat in date_patterns:
                all_dates.extend(re.findall(pat, line))
            if len(all_dates) >= 2:
                date_from = all_dates[0]
                date_to = all_dates[1]
                break
            elif len(all_dates) == 1:
                date_from = all_dates[0]

    is_recent = None
    if date_to:
        try:
            clean = re.sub(r"\s+", "/", date_to)
            for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y"):
                try:
                    parsed = datetime.strptime(clean, fmt).date()
                    delta = (date.today() - parsed).days
                    is_recent = delta <= 92  # moins de 3 mois
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    return {
        "period_from": date_from,
        "period_to": date_to,
        "is_recent": is_recent,
    }


def extract_banking_information(text: str, doc_type: str) -> dict:
    iban = extract_iban(text)
    bic = extract_bic(text)
    holder = extract_account_holder(text)
    bank = extract_bank_name(text)

    result = {
        "iban": iban,
        "bic": bic,
        "account_holder": holder,
        "bank_name": bank,
    }

    if doc_type == "bank_statement":
        result.update(extract_statement_period(text))

    return result
