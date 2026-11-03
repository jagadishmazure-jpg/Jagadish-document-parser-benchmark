"""Parser behaviour and field-level metric tests."""

import pytest

from document_parser_benchmark.dataset import build_dataset
from document_parser_benchmark.metrics import aggregate, score
from document_parser_benchmark.models import ExtractedField, ParseResult
from document_parser_benchmark.parsers import (
    LayoutAwareParser,
    OcrParser,
    PlainTextParser,
)


@pytest.fixture(scope="module")
def docs():
    return {d.doc_id: d for d in build_dataset()}


def _run_all(docs):
    parsers = [LayoutAwareParser(), OcrParser(), PlainTextParser()]
    out = {}
    for doc in docs.values():
        for p in parsers:
            out[(p.name, doc.doc_id)] = p.parse(doc)
    return out


def test_dataset_has_six_docs_with_ground_truth(docs):
    assert len(docs) == 6
    for doc in docs.values():
        assert len(doc.ground_truth) >= 4


def test_layout_aware_extracts_tables_but_not_handwriting(docs):
    result = LayoutAwareParser().parse(docs["DOC-003"])
    names = result.field_map()
    assert names["reference"] == "KM-1003"
    assert "note" not in names


def test_plain_text_extracts_only_title_and_author(docs):
    result = PlainTextParser().parse(docs["DOC-001"])
    assert set(result.field_map()) == {"title", "author"}


def test_plain_text_misses_every_table_field(docs):
    result = PlainTextParser().parse(docs["DOC-004"])
    assert "total" not in result.field_map()
    assert "reference" not in result.field_map()


def test_ocr_garbles_total_on_low_quality_pages(docs):
    result = OcrParser().parse(docs["DOC-005"])
    assert result.field_map()["total"] != "42.25"


def test_ocr_drops_contact_on_low_quality_pages(docs):
    result = OcrParser().parse(docs["DOC-005"])
    assert "contact" not in result.field_map()


def test_ocr_flags_low_confidence_pages_but_not_clean_ones(docs):
    assert OcrParser().parse(docs["DOC-003"]).flagged_pages == [0, 1, 2]
    assert OcrParser().parse(docs["DOC-005"]).flagged_pages == [0, 1, 2]
    assert OcrParser().parse(docs["DOC-001"]).flagged_pages == []


def test_ocr_flagged_pages_are_never_silently_trusted(docs):
    result = OcrParser().parse(docs["DOC-003"])
    assert result.flagged_pages
    assert result.mean_confidence() < 0.70


def test_ocr_mean_confidence_below_threshold_on_faded_doc(docs):
    assert OcrParser().parse(docs["DOC-003"]).mean_confidence() < 0.70
    assert OcrParser().parse(docs["DOC-006"]).mean_confidence() > 0.90


def test_score_exact_fixture():
    truth = {"title": "A", "author": "B", "total": "10.00"}
    result = ParseResult(
        "test",
        "X",
        [
            ExtractedField("title", "A"),
            ExtractedField("author", "B"),
            ExtractedField("total", "10.01"),  # wrong value
            ExtractedField("footer", "junk"),  # spurious
        ],
    )
    s = score(result, truth)
    assert (s["tp"], s["fp"], s["fn"]) == (2, 2, 1)
    assert s["precision"] == pytest.approx(0.5)
    assert s["recall"] == pytest.approx(2 / 3)
    assert s["f1"] == pytest.approx(0.5714, abs=1e-3)


def test_score_perfect_parse_is_one(docs):
    result = ParseResult(
        "test",
        "DOC-001",
        [ExtractedField(k, v) for k, v in docs["DOC-001"].ground_truth.items()],
    )
    s = score(result, docs["DOC-001"].ground_truth)
    assert s["precision"] == 1.0 and s["recall"] == 1.0 and s["f1"] == 1.0


def test_score_empty_extraction_is_zero(docs):
    s = score(ParseResult("test", "DOC-001", []), docs["DOC-001"].ground_truth)
    assert s["precision"] == 0.0 and s["recall"] == 0.0 and s["f1"] == 0.0


def test_layout_aware_full_dataset_metrics(docs):
    pairs = [(LayoutAwareParser().parse(d), d.ground_truth) for d in docs.values()]
    s = aggregate(pairs)
    # 29 of 30 fields right; only the handwritten note is missed.
    assert (s["tp"], s["fp"], s["fn"]) == (29, 0, 1)
    assert s["precision"] == 1.0
    assert s["recall"] == pytest.approx(29 / 30)
    assert s["f1"] == pytest.approx(0.9831, abs=1e-3)


def test_ocr_full_dataset_metrics(docs):
    pairs = [(OcrParser().parse(d), d.ground_truth) for d in docs.values()]
    s = aggregate(pairs)
    # Reference survives on the faded table page; only total is garbled.
    assert (s["tp"], s["fp"], s["fn"]) == (26, 5, 4)
    assert s["precision"] == pytest.approx(26 / 31)
    assert s["recall"] == pytest.approx(26 / 30)
    assert s["f1"] == pytest.approx(0.8525, abs=1e-3)


def test_plain_text_full_dataset_metrics(docs):
    pairs = [(PlainTextParser().parse(d), d.ground_truth) for d in docs.values()]
    s = aggregate(pairs)
    assert (s["tp"], s["fp"], s["fn"]) == (12, 0, 18)
    assert s["precision"] == 1.0
    assert s["recall"] == pytest.approx(0.4)
    assert s["f1"] == pytest.approx(0.5714, abs=1e-3)


def test_head_to_head_ranking_on_f1(docs):
    scores = {}
    for p in (LayoutAwareParser(), OcrParser(), PlainTextParser()):
        pairs = [(p.parse(d), d.ground_truth) for d in docs.values()]
        scores[p.name] = aggregate(pairs)["f1"]
    assert scores["layout-aware"] > scores["ocr"] > scores["plain-text"]


def test_same_documents_for_every_parser(docs):
    # Head-to-head means identical inputs: every parser sees all six docs.
    for p in (LayoutAwareParser(), OcrParser(), PlainTextParser()):
        assert {p.parse(d).doc_id for d in docs.values()} == set(docs)
