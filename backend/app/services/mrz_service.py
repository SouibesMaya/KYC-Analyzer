import re
from datetime import date


COUNTRY_CODES = {
    "FRA": "Française", "DEU": "Allemande", "GBR": "Britannique",
    "ESP": "Espagnole", "ITA": "Italienne", "BEL": "Belge",
    "PRT": "Portugaise", "CHE": "Suisse", "LUX": "Luxembourgeoise",
    "NLD": "Néerlandaise", "AUT": "Autrichienne", "SWE": "Suédoise",
    "NOR": "Norvégienne", "DNK": "Danoise", "FIN": "Finlandaise",
    "POL": "Polonaise", "ROU": "Roumaine", "BGR": "Bulgare",
    "HRV": "Croate", "CZE": "Tchèque", "HUN": "Hongroise",
    "SVK": "Slovaque", "GRC": "Grecque", "UKR": "Ukrainienne",
    "RUS": "Russe", "TUR": "Turque", "USA": "Américaine",
    "CAN": "Canadienne", "BRA": "Brésilienne", "MEX": "Mexicaine",
    "ARG": "Argentine", "CHN": "Chinoise", "JPN": "Japonaise",
    "KOR": "Sud-Coréenne", "IND": "Indienne", "PAK": "Pakistanaise",
    "BGD": "Bangladaise", "VNM": "Vietnamienne", "PHL": "Philippin(e)",
    "MAR": "Marocaine", "TUN": "Tunisienne", "DZA": "Algérienne",
    "EGY": "Égyptienne", "SEN": "Sénégalaise", "CIV": "Ivoirienne",
    "CMR": "Camerounaise", "MLI": "Malienne", "GUI": "Guinéenne",
    "NGA": "Nigériane", "GHA": "Ghanéenne", "COD": "Congolaise (RDC)",
    "MDG": "Malgache", "BEN": "Béninoise", "TGO": "Togolaise",
    "LBN": "Libanaise", "SYR": "Syrienne", "IRN": "Iranienne",
    "AFG": "Afghane", "SOM": "Somalienne", "ETH": "Éthiopienne",
}


def _parse_mrz_date(raw: str, is_dob: bool) -> date | None:
    try:
        yy, mm, dd = int(raw[:2]), int(raw[2:4]), int(raw[4:6])
        if is_dob:
            year = 2000 + yy if yy <= 30 else 1900 + yy
        else:
            year = 2000 + yy
        return date(year, mm, dd)
    except Exception:
        return None


def _parse_name_field(name_field: str) -> tuple[str | None, str | None]:
    parts = name_field.split("<<")
    surname = parts[0].replace("<", " ").strip() if parts else None
    given = parts[1].replace("<", " ").strip() if len(parts) > 1 else None
    return (surname or None, given or None)


def _detect_mrz_lines(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        clean = "".join(line.split()).upper()
        if re.match(r"^[A-Z0-9<]{30}$|^[A-Z0-9<]{44}$", clean):
            candidates.append(clean)
    return candidates


def _parse_td3(line1: str, line2: str) -> dict:
    country = line1[2:5].replace("<", "").strip()
    surname, given = _parse_name_field(line1[5:44])
    doc_number = line2[0:9].replace("<", "").strip()
    nationality = line2[10:13].replace("<", "").strip()
    dob = _parse_mrz_date(line2[13:19], is_dob=True)
    sex_raw = line2[20]
    sex = sex_raw if sex_raw in ("M", "F") else None
    expiry = _parse_mrz_date(line2[21:27], is_dob=False)

    return {
        "mrz_type": "TD3",
        "detected_document_type": "passport",
        "country_code": country,
        "country_label": COUNTRY_CODES.get(country),
        "last_name": surname,
        "first_name": given,
        "document_number": doc_number or None,
        "nationality": nationality,
        "nationality_label": COUNTRY_CODES.get(nationality),
        "date_of_birth": dob.isoformat() if dob else None,
        "sex": sex,
        "expiration_date": expiry.isoformat() if expiry else None,
        "is_expired": (expiry < date.today()) if expiry else None,
        "mrz_parsed": True,
    }


def _parse_td1(line1: str, line2: str, line3: str) -> dict:
    country = line1[2:5].replace("<", "").strip()
    doc_number = line1[5:14].replace("<", "").strip()
    dob = _parse_mrz_date(line2[0:6], is_dob=True)
    sex_raw = line2[7]
    sex = sex_raw if sex_raw in ("M", "F") else None
    expiry = _parse_mrz_date(line2[8:14], is_dob=False)
    nationality = line2[15:18].replace("<", "").strip()
    surname, given = _parse_name_field(line3)

    return {
        "mrz_type": "TD1",
        "detected_document_type": "identity_card",
        "country_code": country,
        "country_label": COUNTRY_CODES.get(country),
        "last_name": surname,
        "first_name": given,
        "document_number": doc_number or None,
        "nationality": nationality,
        "nationality_label": COUNTRY_CODES.get(nationality),
        "date_of_birth": dob.isoformat() if dob else None,
        "sex": sex,
        "expiration_date": expiry.isoformat() if expiry else None,
        "is_expired": (expiry < date.today()) if expiry else None,
        "mrz_parsed": True,
    }


def parse_mrz(ocr_text: str) -> dict:
    lines = _detect_mrz_lines(ocr_text)

    td3_lines = [l for l in lines if len(l) == 44]
    td1_lines = [l for l in lines if len(l) == 30]

    if len(td3_lines) >= 2 and td3_lines[0][0] == "P":
        try:
            return _parse_td3(td3_lines[0], td3_lines[1])
        except Exception:
            pass

    if len(td1_lines) >= 3 and td1_lines[0][0] in ("I", "A", "C"):
        try:
            return _parse_td1(td1_lines[0], td1_lines[1], td1_lines[2])
        except Exception:
            pass

    return {"mrz_parsed": False}
