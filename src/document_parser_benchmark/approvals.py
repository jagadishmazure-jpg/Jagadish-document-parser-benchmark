"""Named-person, single-use, scoped, expiring approvals.

An approval is valid only when: an approver is named, it has not been
used before, its scope matches the document it is used for, and it has
not expired. Anything else is a reject, and a reject never unblocks.
"""

import time
import uuid


class Approval:
    def __init__(self, approver, scope_doc_id, ttl_seconds=3600):
        if not approver or not approver.strip():
            raise ValueError("approver must be a named person")
        self.approval_id = str(uuid.uuid4())
        self.approver = approver
        self.scope_doc_id = scope_doc_id
        self.expires_at = time.time() + ttl_seconds
        self.used = False

    def consume(self, doc_id, now=None):
        """Return True only for a first, in-scope, unexpired use."""
        now = time.time() if now is None else now
        if self.used:
            return False
        if doc_id != self.scope_doc_id:
            return False
        if now >= self.expires_at:
            return False
        self.used = True
        return True


class ConsentTracker:
    """Tracks a human's yes/no answers for one gate decision.

    A self-contradicting sequence ("yes, wait, no") resolves to DENIED:
    the last word is a no, and a contradicted yes is not consent. Only a
    clean, uncontradicted "yes" counts as consent.
    """

    def __init__(self):
        self.answers = []

    def answer(self, word):
        word = word.strip().lower()
        if word not in ("yes", "no", "wait"):
            raise ValueError("answer must be yes, no, or wait")
        self.answers.append(word)

    def decision(self):
        if not self.answers:
            return "absent"
        if self.answers[-1] == "no":
            return "denied"
        if "no" in self.answers or "wait" in self.answers:
            # A yes that was later qualified or contradicted is not clean.
            return "denied"
        return "granted" if self.answers == ["yes"] else "denied"
