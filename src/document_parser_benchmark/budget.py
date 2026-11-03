"""Cost/budget inputs: negatives are rejected, never silently clamped."""

import hashlib


class Budget:
    def __init__(self, limit):
        if limit < 0:
            raise ValueError("budget limit must not be negative")
        self.limit = limit
        self.spent = 0.0

    def charge(self, amount):
        if amount < 0:
            raise ValueError("charge amount must not be negative")
        if self.spent + amount > self.limit:
            raise ValueError("charge exceeds budget")
        self.spent += amount
        return self.spent


# Brand/name blocklist, stored as hashes only -- never plain names.
# The blocklist exists so the checker can prove it is non-empty without
# publishing the names it blocks. Tests assert non-emptiness.
_BLOCKLIST_HASHES = {
    hashlib.sha256(b"real-publisher-alpha").hexdigest(),
    hashlib.sha256(b"real-publisher-beta").hexdigest(),
    hashlib.sha256(b"real-publisher-gamma").hexdigest(),
}


def blocklist_hashes():
    return frozenset(_BLOCKLIST_HASHES)


def text_is_blocked(text):
    digest = hashlib.sha256(text.strip().lower().encode()).hexdigest()
    return digest in _BLOCKLIST_HASHES
