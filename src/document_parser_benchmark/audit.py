"""Hash-chained audit log: tampering with any entry breaks the chain."""

import hashlib
import json


class AuditLog:
    def __init__(self):
        self.entries = []
        self._prev = "GENESIS"

    def record(self, event, detail):
        payload = json.dumps({"event": event, "detail": detail, "prev": self._prev}, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        self.entries.append({"event": event, "detail": detail, "prev": self._prev, "hash": digest})
        self._prev = digest
        return digest

    def verify(self):
        prev = "GENESIS"
        for entry in self.entries:
            payload = json.dumps(
                {"event": entry["event"], "detail": entry["detail"], "prev": prev}, sort_keys=True
            )
            if hashlib.sha256(payload.encode()).hexdigest() != entry["hash"]:
                return False
            prev = entry["hash"]
        return True
