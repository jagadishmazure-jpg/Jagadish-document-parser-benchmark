"""Document parser benchmark: simulated parsers measured on synthetic documents.

All data is fictional and synthetic. No real documents, people, or businesses
are involved. The publisher name used in fixtures is an invented brand.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Page:
    """One synthetic page: its text and a simulated scan quality."""

    text: str
    scan_quality: float  # 0.0 (illegible) to 1.0 (pristine)
    kind: str = "typed"  # typed | table | handwritten-note


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    pages: tuple
    ground_truth: dict  # field name -> expected value


@dataclass
class ExtractedField:
    name: str
    value: str
    confidence: float = 1.0


@dataclass
class ParseResult:
    parser_name: str
    doc_id: str
    fields: list = field(default_factory=list)
    page_confidences: list = field(default_factory=list)
    flagged_pages: list = field(default_factory=list)

    def field_map(self):
        return {f.name: f.value for f in self.fields}

    def mean_confidence(self):
        if not self.page_confidences:
            return 0.0
        return sum(self.page_confidences) / len(self.page_confidences)
