# Document parser benchmark — distilled notes

These notes summarise the design of this project.

## The problem

Choosing a document parser by vendor claim is guesswork. The same pile of
documents run through different parsers produces different fields, and the
differences are not random: a layout-aware parser reads tables well and
skips handwriting; an OCR parser reads everything but misreads poor scans;
a plain-text parser is precise and blind to anything tabular. A benchmark
makes those trade-offs measurable instead of anecdotal.

## What is compared

Three simulated parsers run over the same six synthetic documents, and each
extracted field is scored against ground truth: exact match counts as a
true positive, a wrong value counts as both a false positive and a false
negative, and a missing field counts as a false negative. Precision, recall,
and F1 are reported per parser. Because the parsers are simulated, the
numbers describe the simulated behaviours, not any real product.

## Why a quality gate matters more than the ranking

A ranking answers "which parser is best on average". A gate answers "can
anyone act on this particular parse". Low-confidence pages are flagged by
the OCR parser and held by the gate; downstream agents refuse held parses,
refuse when no gate decision exists at all, and refuse when a bypass
approval is expired, reused, or scoped to another document. A held parse
goes to a manual-review queue, not to the bin and not to production.

## The fictional publisher

All documents are invented for a fictional publisher, Kestrelmere Press.
A web check found no business operating under that exact name (a
similarly named real printing firm is a different name and is not used
here). Email addresses use the reserved `.example`
domain. Nothing in the fixtures refers to a real person or business.

## Agents

- **ParserRunnerAgent** — runs every parser over every document.
- **QualityGateAgent** — holds low-confidence or PII-leaking parses; a
  named-person, single-use, scoped, expiring approval can bypass a
  low-confidence hold, never a PII block.
- **BenchmarkReporterAgent** — scores precision, recall, and F1 per parser
  and verifies the hash-chained audit log.

## Lifecycle coverage

Prevent (PII redaction before downstream use), detect (parsing plus
low-confidence flagging), respond (gating and holds), recover (manual
review queue), govern (hash-chained audit, named approvals), measure
(per-parser precision, recall, and F1).
