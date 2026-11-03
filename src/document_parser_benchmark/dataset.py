"""Synthetic document set.

Every document is invented. Names, amounts, codes, and addresses are
fictional; email addresses use the reserved .example domain so they can
never belong to a real person.
"""

from .models import Document, Page

PUBLISHER = "Kestrelmere Press"  # fictional publisher; see knowledge/notes.md


def _doc(doc_id, title, pages, truth):
    return Document(doc_id=doc_id, title=title, pages=tuple(pages), ground_truth=truth)


def build_dataset():
    """Return six synthetic documents with known ground-truth fields."""
    docs = [
        _doc(
            "DOC-001",
            "Autumn Catalogue",
            [
                Page("Title: Autumn Catalogue\nAuthor: Ada Wren\n", 0.98),
                Page("Reference: KM-1001\nTotal: 120.00\n", 0.96, kind="table"),
                Page("Contact: editor@kestrelmere.example\n", 0.95),
            ],
            {
                "title": "Autumn Catalogue",
                "author": "Ada Wren",
                "reference": "KM-1001",
                "total": "120.00",
                "contact": "editor@kestrelmere.example",
            },
        ),
        _doc(
            "DOC-002",
            "Spring Catalogue",
            [
                Page("Title: Spring Catalogue\nAuthor: Ben Okafor\n", 0.97),
                Page("Reference: KM-1002\nTotal: 85.50\n", 0.94, kind="table"),
                Page("Contact: rights@kestrelmere.example\n", 0.93),
            ],
            {
                "title": "Spring Catalogue",
                "author": "Ben Okafor",
                "reference": "KM-1002",
                "total": "85.50",
                "contact": "rights@kestrelmere.example",
            },
        ),
        _doc(
            "DOC-003",
            "Faded Manuscript",
            [
                Page("Title: Faded Manuscript\nAuthor: Cleo Marsh\n", 0.62),
                Page("Reference: KM-1003\nTotal: 210.75\n", 0.55, kind="table"),
                Page("Note: handwritten margin note, barely legible\n", 0.40, kind="handwritten-note"),
            ],
            {
                "title": "Faded Manuscript",
                "author": "Cleo Marsh",
                "reference": "KM-1003",
                "total": "210.75",
                "note": "margin note",
            },
        ),
        _doc(
            "DOC-004",
            "Invoice Batch Seven",
            [
                Page("Title: Invoice Batch Seven\nAuthor: Dana Iqbal\n", 0.99),
                Page("Reference: KM-1004\nTotal: 640.00\n", 0.98, kind="table"),
                Page("Contact: accounts@kestrelmere.example\n", 0.97),
            ],
            {
                "title": "Invoice Batch Seven",
                "author": "Dana Iqbal",
                "reference": "KM-1004",
                "total": "640.00",
                "contact": "accounts@kestrelmere.example",
            },
        ),
        _doc(
            "DOC-005",
            "Smudged Order Form",
            [
                Page("Title: Smudged Order Form\nAuthor: Eli Novak\n", 0.58),
                Page("Reference: KM-1005\nTotal: 42.25\n", 0.51, kind="table"),
                Page("Contact: orders@kestrelmere.example\n", 0.49),
            ],
            {
                "title": "Smudged Order Form",
                "author": "Eli Novak",
                "reference": "KM-1005",
                "total": "42.25",
                "contact": "orders@kestrelmere.example",
            },
        ),
        _doc(
            "DOC-006",
            "Clean Proof",
            [
                Page("Title: Clean Proof\nAuthor: Fay Lindqvist\n", 0.99),
                Page("Reference: KM-1006\nTotal: 15.00\n", 0.99, kind="table"),
                Page("Contact: proofs@kestrelmere.example\n", 0.99),
            ],
            {
                "title": "Clean Proof",
                "author": "Fay Lindqvist",
                "reference": "KM-1006",
                "total": "15.00",
                "contact": "proofs@kestrelmere.example",
            },
        ),
    ]
    return docs
