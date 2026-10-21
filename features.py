"""Conservative text normalization; keep negation and avoid target metadata."""

import re, unicodedata


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", str(text)).lower().split())


def tokens(text):
    # ASCII-only tokenization is intentional so Python and browser inference agree.
    return re.findall(r"[a-z0-9]{2,}", normalize(text))


def route(product):
    p = product.lower()
    if "credit report" in p:
        return "Credit reporting"
    if "credit card" in p:
        return "Credit card"
    if "mortgage" in p:
        return "Mortgage"
    if "debt collection" in p:
        return "Debt collection"
    if "student loan" in p:
        return "Student loan"
    if "bank account" in p or "checking or savings" in p:
        return "Bank accounts"
    return None
