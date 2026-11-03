"""PII redaction checklist: card numbers, email addresses, phone, SSN.

Every pattern in the checklist is exercised by tests; the checklist itself
is the contract, and a missing pattern is a failing test, not a footnote.
"""

import re

PATTERNS = {
    # Card numbers: 13-19 digits, optionally space/dash separated.
    "card_number": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\b(?:\+?1[-. ]?)?(?:\(?\d{3}\)?[-. ]?)\d{3}[-. ]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

REDACTED = "[REDACTED]"


def redact(text):
    """Replace every checklist pattern; return (redacted_text, kinds_found)."""
    found = []
    out = text
    for kind, pattern in PATTERNS.items():
        if pattern.search(out):
            found.append(kind)
            out = pattern.sub(REDACTED, out)
    return out, found


def contains_pii(text):
    return [kind for kind, pattern in PATTERNS.items() if pattern.search(text)]
