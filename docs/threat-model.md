# Threat model (STRIDE, condensed)

- **Spoofing:** a bypass approval presented for another document or by an
  unnamed party is rejected (scope + named approver checks).
- **Tampering:** the audit log is hash-chained; editing any entry breaks
  verification (tested).
- **Information disclosure:** extracted fields are redacted for card
  numbers, emails, phone numbers, and SSNs before downstream use; a
  result that still carries PII is BLOCKed, never bypassed.
- **Denial of service:** a held parse blocks only its own document's
  downstream action; other documents flow.
- **Elevation of privilege:** approvals are single-use and expiring, so a
  captured approval cannot be replayed or reused.

Out of scope: real OCR engines, real document stores, and any handling of
genuinely sensitive documents — all fixtures are synthetic.
