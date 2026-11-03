"""Redaction checklist, budget, brand blocklist, and audit-chain tests."""

import pytest

from document_parser_benchmark.audit import AuditLog
from document_parser_benchmark.budget import Budget, blocklist_hashes, text_is_blocked
from document_parser_benchmark.redaction import PATTERNS, contains_pii, redact


def test_redaction_checklist_covers_card_email_phone_ssn():
    # The checklist itself is the contract: all four kinds must be present.
    assert {"card_number", "email", "phone", "ssn"} <= set(PATTERNS)


def test_card_number_redacted():
    text, found = redact("card 4111-1111-1111-1111 on file")
    assert "4111" not in text and "card_number" in found


def test_email_redacted():
    text, found = redact("write to editor@example.org please")
    assert "editor@example.org" not in text and "email" in found


def test_phone_redacted():
    text, found = redact("call 555-123-4567 after noon")
    assert "555-123-4567" not in text and "phone" in found


def test_ssn_redacted():
    text, found = redact("ssn 123-45-6789 on record")
    assert "123-45-6789" not in text and "ssn" in found


def test_clean_text_untouched():
    text, found = redact("Autumn Catalogue, reference KM-1001")
    assert text == "Autumn Catalogue, reference KM-1001" and found == []


def test_contains_pii_lists_every_kind_present():
    kinds = contains_pii("mail editor@example.org or call 555-123-4567")
    assert kinds == ["email", "phone"]


def test_budget_rejects_negative_limit():
    with pytest.raises(ValueError):
        Budget(-5.0)


def test_budget_rejects_negative_charge():
    budget = Budget(10.0)
    with pytest.raises(ValueError):
        budget.charge(-1.0)


def test_budget_rejects_over_limit_charge():
    budget = Budget(1.0)
    with pytest.raises(ValueError):
        budget.charge(1.01)


def test_budget_accepts_in_limit_charges():
    budget = Budget(1.0)
    assert budget.charge(0.4) == pytest.approx(0.4)
    assert budget.charge(0.4) == pytest.approx(0.8)


def test_brand_blocklist_is_non_empty():
    # Required by the standing rule: the check must assert non-emptiness.
    assert len(blocklist_hashes()) >= 1


def test_blocklist_stores_hashes_not_plain_names():
    for entry in blocklist_hashes():
        assert len(entry) == 64  # sha256 hex, not a readable name


def test_blocked_text_detected_and_clean_text_passes():
    assert text_is_blocked("real-publisher-alpha")
    assert not text_is_blocked("Kestrelmere Press")


def test_audit_chain_verifies():
    log = AuditLog()
    log.record("parsed", {"parser": "ocr", "doc": "DOC-001"})
    log.record("held", {"parser": "ocr", "doc": "DOC-003"})
    assert log.verify()


def test_audit_chain_detects_tampering():
    log = AuditLog()
    log.record("parsed", {"parser": "ocr", "doc": "DOC-001"})
    log.entries[0]["detail"] = {"parser": "ocr", "doc": "DOC-002"}
    assert not log.verify()


def test_audit_entries_are_hash_chained():
    log = AuditLog()
    log.record("a", {})
    log.record("b", {})
    assert log.entries[1]["prev"] == log.entries[0]["hash"]
