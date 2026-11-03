"""Three SIMULATED parsers with deliberately distinct behaviours.

These are not real OCR or layout engines: each parser applies a fixed,
documented extraction rule to the synthetic page text so that a benchmark
can compare extraction quality head-to-head on identical input. The rules
are the behaviour under test, not a claim about any real product.
"""

import re

from .models import ExtractedField, ParseResult

LOW_CONFIDENCE_THRESHOLD = 0.70

_LINE = re.compile(r"^(Title|Author|Reference|Total|Contact):\s*(.+)$")
_FIELD_NAMES = {
    "Title": "title",
    "Author": "author",
    "Reference": "reference",
    "Total": "total",
    "Contact": "contact",
}


def _labelled_fields(page):
    """Yield (field_name, value) pairs from labelled lines on a page."""
    out = []
    for line in page.text.splitlines():
        m = _LINE.match(line.strip())
        if m:
            out.append((_FIELD_NAMES[m.group(1)], m.group(2).strip()))
    return out


def _garble_total(value):
    """Simulate an OCR misread: swap the final digit."""
    if value and value[-1].isdigit():
        return value[:-1] + ("0" if value[-1] != "0" else "1")
    return value + "?"


class LayoutAwareParser:
    """Reads structure: every labelled field except handwritten notes."""

    name = "layout-aware"

    def parse(self, doc):
        fields, confidences, flagged = [], [], []
        for page in doc.pages:
            confidences.append(page.scan_quality)
            if page.kind == "handwritten-note":
                continue  # layout model has no handwriting path
            for fname, value in _labelled_fields(page):
                fields.append(ExtractedField(fname, value, confidence=page.scan_quality))
        return ParseResult(self.name, doc.doc_id, fields, confidences, flagged)


class OcrParser:
    """Reads everything, but low-quality pages misread values.

    Pages below LOW_CONFIDENCE_THRESHOLD are flagged, never silently
    trusted: the flag travels with the result to the quality gate.
    """

    name = "ocr"

    def parse(self, doc):
        fields, confidences, flagged = [], [], []
        for idx, page in enumerate(doc.pages):
            conf = round(page.scan_quality * 0.95, 4)
            confidences.append(conf)
            if conf < LOW_CONFIDENCE_THRESHOLD:
                flagged.append(idx)
            for fname, value in _labelled_fields(page):
                if page.scan_quality < 0.70 and fname == "total":
                    value = _garble_total(value)
                if page.scan_quality < 0.70 and fname == "contact":
                    continue  # dropped: unreadable on a poor scan
                fields.append(ExtractedField(fname, value, confidence=conf))
            if page.kind == "handwritten-note":
                # Best-effort handwriting guess, marked uncertain, wrong value.
                fields.append(ExtractedField("note", "margin note (uncertain)", confidence=conf))
            if page.scan_quality < 0.70:
                fields.append(ExtractedField("footer", "unreadable", confidence=conf))
        return ParseResult(self.name, doc.doc_id, fields, confidences, flagged)


class PlainTextParser:
    """Reads running text only: title and author, nothing tabular."""

    name = "plain-text"

    def parse(self, doc):
        fields, confidences, flagged = [], [], []
        for page in doc.pages:
            if page.kind != "typed":
                continue  # tables and notes are invisible to plain text
            confidences.append(1.0)
            for fname, value in _labelled_fields(page):
                if fname in ("title", "author"):
                    fields.append(ExtractedField(fname, value, confidence=1.0))
        return ParseResult(self.name, doc.doc_id, fields, confidences, flagged)


ALL_PARSERS = [LayoutAwareParser(), OcrParser(), PlainTextParser()]
