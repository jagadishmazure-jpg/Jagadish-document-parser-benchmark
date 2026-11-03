"""Agent pipeline and end-to-end scenario tests."""

import pytest

from document_parser_benchmark.agents import BenchmarkReporterAgent, ParserRunnerAgent, Pipeline
from document_parser_benchmark.approvals import Approval
from document_parser_benchmark.budget import Budget
from document_parser_benchmark.dataset import build_dataset
from document_parser_benchmark.gates import DownstreamAgent
from document_parser_benchmark.models import ExtractedField, ParseResult


def test_runner_runs_every_parser_on_every_doc():
    results = ParserRunnerAgent().run(build_dataset())
    assert len(results) == 18  # 3 parsers x 6 docs
    assert {r.parser_name for r in results} == {"layout-aware", "ocr", "plain-text"}


def test_pipeline_report_ranks_layout_aware_first():
    report = Pipeline().run(build_dataset())
    assert report["best_parser_by_f1"] == "layout-aware"
    per = report["per_parser"]
    assert per["layout-aware"]["f1"] == pytest.approx(0.9831, abs=1e-3)
    assert per["ocr"]["f1"] == pytest.approx(0.8525, abs=1e-3)
    assert per["plain-text"]["f1"] == pytest.approx(0.5714, abs=1e-3)


def test_pipeline_flags_low_quality_docs():
    report = Pipeline().run(build_dataset())
    assert report["flagged_docs"] == ["DOC-003", "DOC-005"]


def test_pipeline_holds_poor_parses_for_manual_review():
    report = Pipeline().run(build_dataset())
    assert report["manual_review_queue"]
    held_docs = {doc for _, doc, _ in report["manual_review_queue"]}
    assert "DOC-003" in held_docs and "DOC-005" in held_docs


def test_pipeline_audit_chain_valid():
    report = Pipeline().run(build_dataset())
    assert report["audit_chain_valid"] is True
    assert report["audit_entries"] > 0


def test_pipeline_bypass_lets_approved_doc_through():
    docs = build_dataset()
    # One approval is single-use, so it frees exactly one held parse:
    # the layout-aware parse of DOC-003. (The plain-text parse of DOC-003
    # was never held; the OCR parse stays held because the approval is spent.)
    report = Pipeline().run(docs, approvals={"DOC-003": Approval("Priya Raman", "DOC-003")})
    assert "acted on DOC-003 via layout-aware" in report["actions"]
    assert ("ocr", "DOC-003", "NEEDS_APPROVAL") in report["manual_review_queue"]


def test_pipeline_downstream_never_sees_raw_email():
    report = Pipeline().run(build_dataset())
    for action in report["actions"]:
        assert "@" not in action
    # And held entries never carry field values at all.
    for entry in report["manual_review_queue"]:
        assert "@" not in str(entry)


def test_pipeline_budget_negative_rejected_upfront():
    with pytest.raises(ValueError):
        Pipeline(budget=Budget(-1.0))


def test_pipeline_budget_overrun_raises():
    with pytest.raises(ValueError):
        Pipeline(budget=Budget(0.05)).run(build_dataset())


def test_reporter_audit_chain_valid_after_reporting():
    docs = build_dataset()
    results = ParserRunnerAgent().run(docs)
    reporter = BenchmarkReporterAgent()
    report = reporter.report(results, docs, {})
    assert report["audit_chain_valid"] is True


def test_end_to_end_scenario_faded_and_clean_docs():
    """A faded manuscript is held; a clean proof flows straight through."""
    docs = {d.doc_id: d for d in build_dataset()}
    pipeline = Pipeline()
    report = pipeline.run([docs["DOC-003"], docs["DOC-006"]])
    assert any("DOC-006" in a for a in report["actions"])
    assert any(doc == "DOC-003" for _, doc, _ in report["manual_review_queue"])
    assert report["per_parser"]["layout-aware"]["f1"] > report["per_parser"]["plain-text"]["f1"]


def test_downstream_act_returns_parse_identity():
    # No PII-bearing fields: the gate allows this parse outright.
    result = ParseResult(
        "layout-aware",
        "DOC-006",
        [
            ExtractedField("title", "Clean Proof", 0.99),
            ExtractedField("author", "Fay Lindqvist", 0.99),
            ExtractedField("reference", "KM-1006", 0.99),
            ExtractedField("total", "15.00", 0.99),
        ],
        [0.99, 0.99, 0.99],
    )
    from document_parser_benchmark.gates import QualityGateAgent

    decision = QualityGateAgent().evaluate(result)
    assert DownstreamAgent().act(result, decision) == "acted on DOC-006 via layout-aware"


def test_no_real_personal_data_in_dataset():
    for doc in build_dataset():
        for page in doc.pages:
            # Any "@" must sit inside a reserved .example address.
            assert "@" not in page.text or ".example" in page.text
