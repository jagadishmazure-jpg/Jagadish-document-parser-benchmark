"""Quality-gate tests: bypass, reject, and absent paths."""

import pytest

from document_parser_benchmark.approvals import Approval, ConsentTracker
from document_parser_benchmark.dataset import build_dataset
from document_parser_benchmark.gates import (
    ALLOW,
    BLOCK,
    NEEDS_APPROVAL,
    DownstreamAgent,
    GateError,
    QualityGateAgent,
)
from document_parser_benchmark.models import ExtractedField, ParseResult
from document_parser_benchmark.parsers import LayoutAwareParser, OcrParser

GATE = QualityGateAgent()
DOWNSTREAM = DownstreamAgent()


def _low_conf_result():
    docs = {d.doc_id: d for d in build_dataset()}
    return OcrParser().parse(docs["DOC-003"])


def _clean_result():
    # A clean parse with no PII-bearing fields: raw contact emails are
    # BLOCKed by the gate by design (the pipeline redacts before gating).
    return ParseResult(
        "layout-aware",
        "DOC-001",
        [
            ExtractedField("title", "Autumn Catalogue", 0.98),
            ExtractedField("author", "Ada Wren", 0.98),
            ExtractedField("reference", "KM-1001", 0.96),
            ExtractedField("total", "120.00", 0.96),
        ],
        [0.98, 0.96, 0.95],
    )


def test_clean_parse_is_allowed():
    assert GATE.evaluate(_clean_result()).outcome == ALLOW


def test_low_confidence_parse_needs_approval():
    decision = GATE.evaluate(_low_conf_result())
    assert decision.outcome == NEEDS_APPROVAL
    assert decision.reasons  # the hold is explained, not silent


def test_downstream_blocked_without_bypass():
    decision = GATE.evaluate(_low_conf_result())
    with pytest.raises(GateError):
        DOWNSTREAM.act(_low_conf_result(), decision)


def test_bypass_with_valid_named_approval():
    decision = GATE.evaluate(_low_conf_result())
    approval = Approval(approver="Priya Raman", scope_doc_id="DOC-003")
    bypassed = GATE.bypass(decision, approval, "DOC-003")
    assert bypassed.outcome == ALLOW
    assert bypassed.bypassed_by == "Priya Raman"
    assert DOWNSTREAM.act(_low_conf_result(), bypassed).startswith("acted on DOC-003")


def test_reject_expired_approval():
    decision = GATE.evaluate(_low_conf_result())
    approval = Approval(approver="Priya Raman", scope_doc_id="DOC-003", ttl_seconds=0)
    assert GATE.bypass(decision, approval, "DOC-003").outcome == NEEDS_APPROVAL


def test_reject_wrong_scope_approval():
    decision = GATE.evaluate(_low_conf_result())
    approval = Approval(approver="Priya Raman", scope_doc_id="DOC-001")
    assert GATE.bypass(decision, approval, "DOC-003").outcome == NEEDS_APPROVAL


def test_reject_reused_single_use_approval():
    decision = GATE.evaluate(_low_conf_result())
    approval = Approval(approver="Priya Raman", scope_doc_id="DOC-003")
    assert GATE.bypass(decision, approval, "DOC-003").outcome == ALLOW
    again = GATE.evaluate(_low_conf_result())
    assert GATE.bypass(again, approval, "DOC-003").outcome == NEEDS_APPROVAL


def test_reject_anonymous_approval():
    with pytest.raises(ValueError):
        Approval(approver="  ", scope_doc_id="DOC-003")


def test_reject_non_approval_object_as_bypass():
    decision = GATE.evaluate(_low_conf_result())
    assert GATE.bypass(decision, "yes, go ahead", "DOC-003").outcome == NEEDS_APPROVAL


def test_absent_gate_decision_refuses_downstream():
    with pytest.raises(GateError, match="absent gate decision"):
        DOWNSTREAM.act(_clean_result(), None)


def test_gate_decision_for_wrong_document_refused():
    decision = GATE.evaluate(_clean_result())
    other = LayoutAwareParser().parse(
        {d.doc_id: d for d in build_dataset()}["DOC-002"]
    )
    with pytest.raises(GateError, match="different document"):
        DOWNSTREAM.act(other, decision)


def test_unredacted_pii_blocks_and_cannot_be_bypassed():
    leaked = ParseResult(
        "test",
        "DOC-999",
        [ExtractedField("contact", "someone@example.org")],
        [0.99],
    )
    decision = GATE.evaluate(leaked)
    assert decision.outcome == BLOCK
    approval = Approval(approver="Priya Raman", scope_doc_id="DOC-999")
    assert GATE.bypass(decision, approval, "DOC-999").outcome == BLOCK
    with pytest.raises(GateError):
        DOWNSTREAM.act(leaked, decision)


def test_low_confidence_consent_sequence_yes_wait_no_is_denied():
    tracker = ConsentTracker()
    tracker.answer("yes")
    tracker.answer("wait")
    tracker.answer("no")
    assert tracker.decision() == "denied"


def test_clean_single_yes_is_granted():
    tracker = ConsentTracker()
    tracker.answer("yes")
    assert tracker.decision() == "granted"


def test_no_answers_is_absent_not_granted():
    assert ConsentTracker().decision() == "absent"


def test_yes_then_no_is_denied():
    tracker = ConsentTracker()
    tracker.answer("yes")
    tracker.answer("no")
    assert tracker.decision() == "denied"


def test_invalid_consent_word_rejected():
    tracker = ConsentTracker()
    with pytest.raises(ValueError):
        tracker.answer("maybe")
