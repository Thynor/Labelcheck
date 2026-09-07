"""
rules.py
--------
Extraction + validation logic for the six mandatory declarations under
Rule 6 of the Legal Metrology (Packaged Commodities) Rules, 2011:

  1. Name & address of manufacturer / packer / importer
  2. Common / generic name of the commodity
  3. Net quantity, in standard units
  4. Month & year of manufacture / pre-packing / import
  5. Retail Sale Price (MRP), inclusive of all taxes
  6. Consumer care / complaint contact details
  7. Country of origin (mandatory only for imported goods)

This is intentionally regex/keyword based rather than a trained NLP model —
label declarations follow fairly fixed legal phrasing, so this is fast,
explainable, and easy to extend with more keyword variants over time.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class FieldResult:
    key: str
    label: str
    status: str  # "compliant" | "non_compliant" | "not_detected"
    detected_value: Optional[str]
    note: str

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Individual field checks
# ---------------------------------------------------------------------------

def check_mrp(text: str) -> FieldResult:
    """Rule 6(1)(e) / Rule 18: MRP must be printed inclusive of all taxes."""
    mrp_match = re.search(
        r"(?:mrp|m\.r\.p|maximum\s+retail\s+price)\D{0,15}(?:rs\.?|inr|₹)?\s*([0-9]+(?:[.,][0-9]{1,2})?)",
        text, re.IGNORECASE,
    )
    if not mrp_match:
        return FieldResult("mrp", "MRP (inclusive of all taxes)", "not_detected", None,
                            "No MRP value found on the label.")

    value = mrp_match.group(0).strip()
    incl_tax = re.search(r"incl(?:usive|\.)?\s*(?:of)?\s*(?:all)?\s*tax", text, re.IGNORECASE)
    if incl_tax:
        return FieldResult("mrp", "MRP (inclusive of all taxes)", "compliant", value,
                            "MRP found with the required 'inclusive of all taxes' declaration.")
    return FieldResult("mrp", "MRP (inclusive of all taxes)", "non_compliant", value,
                        "MRP found, but the mandatory 'inclusive of all taxes' wording is missing (Rule 18).")


def check_net_quantity(text: str) -> FieldResult:
    """Rule 6(1)(c): net quantity in standard units (g, kg, ml, l, etc.)."""
    match = re.search(
        r"(?:net\s*(?:qty|quantity|wt|weight)?)\D{0,10}([0-9]+(?:\.[0-9]+)?)\s*(g|gm|gms|kg|ml|l|litre|liter)\b",
        text, re.IGNORECASE,
    )
    if match:
        return FieldResult("net_quantity", "Net Quantity", "compliant", match.group(0).strip(),
                            "Net quantity found with a standard unit.")
    loose = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(g|gm|gms|kg|ml|l)\b", text, re.IGNORECASE)
    if loose:
        return FieldResult("net_quantity", "Net Quantity", "non_compliant", loose.group(0).strip(),
                            "A weight/volume value was found, but it isn't clearly labelled 'Net Qty' — verify manually.")
    return FieldResult("net_quantity", "Net Quantity", "not_detected", None,
                        "No net quantity declaration found.")


def check_mfg_date(text: str) -> FieldResult:
    """Rule 6(1)(d): month and year of manufacture / packing / import."""
    match = re.search(
        r"(?:mfg|mfd|manufactured|packed|packing)\D{0,10}"
        r"((?:[0-9]{1,2}[\/\-])?[0-9]{1,2}[\/\-][0-9]{2,4}|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*[0-9]{2,4})",
        text, re.IGNORECASE,
    )
    if match:
        return FieldResult("mfg_date", "Month & Year of Manufacture", "compliant", match.group(0).strip(),
                            "Manufacture/packing date declaration found.")
    return FieldResult("mfg_date", "Month & Year of Manufacture", "not_detected", None,
                        "No manufacture/packing date found.")


def check_manufacturer(text: str) -> FieldResult:
    """Rule 6(1)(a): name and address of manufacturer/packer/importer."""
    match = re.search(
        r"(?:mfd\.?\s*by|manufactured\s*by|marketed\s*by|packed\s*by|packer)\s*[:\-]?\s*([^\n]{5,80})",
        text, re.IGNORECASE,
    )
    if match:
        return FieldResult("manufacturer", "Manufacturer / Packer / Importer", "compliant",
                            match.group(0).strip(), "Manufacturer/packer declaration found.")
    return FieldResult("manufacturer", "Manufacturer / Packer / Importer", "not_detected", None,
                        "No manufacturer, packer, or importer name/address found.")


def check_consumer_care(text: str) -> FieldResult:
    """Rule 6(1)(f): consumer care / complaint contact details."""
    phone = re.search(r"(?:\+91[\-\s]?)?[6-9][0-9]{9}\b", text)
    email = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    keyword = re.search(r"consumer\s*care", text, re.IGNORECASE)

    if keyword and (phone or email):
        value = " / ".join(filter(None, [phone.group(0) if phone else None,
                                          email.group(0) if email else None]))
        return FieldResult("consumer_care", "Consumer Care Contact", "compliant", value,
                            "Consumer care contact details found.")
    if phone or email:
        value = " / ".join(filter(None, [phone.group(0) if phone else None,
                                          email.group(0) if email else None]))
        return FieldResult("consumer_care", "Consumer Care Contact", "non_compliant", value,
                            "A phone number/email was found, but it isn't explicitly labelled 'Consumer Care' — verify manually.")
    return FieldResult("consumer_care", "Consumer Care Contact", "not_detected", None,
                        "No consumer care phone number or email found.")


def check_country_of_origin(text: str) -> FieldResult:
    """Rule 6(1)(h) / 27: mandatory only for imported goods."""
    match = re.search(r"(?:country\s*of\s*origin|made\s*in)\s*[:\-]?\s*([a-zA-Z ]{3,30})", text, re.IGNORECASE)
    if match:
        return FieldResult("country_of_origin", "Country of Origin", "compliant", match.group(0).strip(),
                            "Country of origin declared (required for imported goods).")
    return FieldResult("country_of_origin", "Country of Origin", "not_detected", None,
                        "No country-of-origin declaration found. Only mandatory if this is an imported product.")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

CHECKS = [
    check_manufacturer,
    check_net_quantity,
    check_mfg_date,
    check_mrp,
    check_consumer_care,
    check_country_of_origin,
]


def run_all_checks(raw_text: str) -> list[FieldResult]:
    return [check(raw_text) for check in CHECKS]


def compute_verdict(results: list[FieldResult]) -> dict:
    # Country of origin is conditional (imports only), so it never fails the
    # overall verdict on its own -- it's informational unless declared and wrong.
    blocking = [r for r in results if r.key != "country_of_origin"]

    if any(r.status == "not_detected" for r in blocking):
        verdict = "non_compliant"
        summary = "One or more mandatory Rule 6 declarations could not be found on this label."
    elif any(r.status == "non_compliant" for r in blocking):
        verdict = "non_compliant"
        summary = "All mandatory fields were found, but at least one doesn't meet the required format."
    else:
        verdict = "compliant"
        summary = "All mandatory Rule 6 declarations were found and meet the required format."

    return {"verdict": verdict, "summary": summary}
