# Jagadish-document-parser-benchmark

> **Independent project, not affiliated with any vendor or publisher.**
> All companies, people, documents, and data in this repo are fictional
> and synthetic. Parsers are simulated behaviours, not real products.

## Recruiter summary

Choosing a document parser by claim is guesswork, so this project measures
it: three simulated parsers with distinct behaviours run over the same six
synthetic documents and are scored head-to-head on field-level precision,
recall, and F1. More important than the ranking, a quality gate blocks
downstream agents from acting on low-confidence or PII-leaking parses —
held parses go to a manual-review queue, and only a named-person,
single-use, scoped, unexpired approval can bypass a low-confidence hold.

## Measured results (from a real run)

Run with `python3 run_demo.py` on the 6-document synthetic set (18 parses
scored; a wrong field value counts as both a false positive and a false
negative):

| Parser | Precision | Recall | F1 | TP | FP | FN |
| --- | --- | --- | --- | --- | --- | --- |
| layout-aware | 1.0000 | 0.9667 | 0.9831 | 29 | 0 | 1 |
| ocr | 0.8387 | 0.8667 | 0.8525 | 26 | 5 | 4 |
| plain-text | 1.0000 | 0.4000 | 0.5714 | 12 | 0 | 18 |

Best parser by F1: **layout-aware**. Flagged low-confidence documents:
`DOC-003`, `DOC-005`. Parses held for manual review: **4**. Audit chain
valid: **True**.

These numbers describe the simulated parsers on this small synthetic set.
They are regression checks, not quality claims about any real parser.

## Purpose and who it is for

For anyone evaluating document parsers or building agent pipelines that
act on extracted content: it shows how to compare extraction quality
fairly (same documents, same ground truth) and how to stop poor parses
from reaching downstream actions.

## How it works, step by step

1. **Prevent** — `ParserRunnerAgent` runs every parser; the pipeline
   redacts card numbers, email addresses, phone numbers, and SSNs before
   any result reaches a gate or downstream agent.
2. **Detect** — the OCR parser flags pages below 0.70 confidence; it
   garbles totals and drops contacts on poor scans instead of silently
   trusting them.
3. **Respond** — `QualityGateAgent` returns ALLOW, NEEDS_APPROVAL
   (low confidence / flagged pages), or BLOCK (unredacted PII, never
   bypassable).
4. **Recover** — held parses land in a manual-review queue.
5. **Govern** — every step is recorded in a hash-chained audit log;
   bypasses need a named, single-use, scoped, expiring approval.
6. **Measure** — `BenchmarkReporterAgent` scores precision, recall, and
   F1 per parser and verifies the audit chain.

## Architecture

See [knowledge/architecture-diagram.md](knowledge/architecture-diagram.md)
for Mermaid flow and sequence diagrams, and
[knowledge/notes.md](knowledge/notes.md) for distilled design notes.

## Real code excerpt and its real output

```python
from document_parser_benchmark.agents import Pipeline
from document_parser_benchmark.dataset import build_dataset

report = Pipeline().run(build_dataset())
print(report["best_parser_by_f1"])
print(report["per_parser"]["layout-aware"])
```

Output (from `python3 run_demo.py`):

```
Best parser by F1: layout-aware
layout-aware  precision=1.0000 recall=0.9667 F1=0.9831 (TP=29 FP=0 FN=1)
ocr           precision=0.8387 recall=0.8667 F1=0.8525 (TP=26 FP=5 FN=4)
plain-text    precision=1.0000 recall=0.4000 F1=0.5714 (TP=12 FP=0 FN=18)
```

## How to run

```bash
PYTHONPATH=src python3 -m pytest -q   # full suite, stdlib only, no network, no .venv
python3 run_demo.py    # benchmark report
```

Tests use the `src/` layout, so `PYTHONPATH=src` is required for pytest.

## Guardrails and security controls

- PII redaction checklist: card numbers, email addresses, phone numbers,
  SSNs — each covered by tests.
- Quality gates with bypass, reject (expired / reused / wrong-scope /
  anonymous approval), and absent-path (no gate decision → downstream
  refuses) tests.
- Self-contradicting consent ("yes, wait, no") resolves to denied, as do
  "yes, then no" sequences; only a clean single "yes" grants.
- Cost/budget inputs reject negatives and over-limit charges.
- Brand/name blocklist stored as hashes only; tests assert it is non-empty.
- Hash-chained audit log with tamper-detection tests.

## Limitations and known failures

- Parsers are simulated, not real OCR/layout engines; results do not
  transfer to real products.
- Only six synthetic documents: small-sample regression checks.
- The layout-aware parser cannot read handwriting at all (the one field
  it misses); the OCR parser misreads totals on poor scans by design.
- CI workflow is included but unrun (see status table).

## Built / Written-not-run / Planned

| Item | Status |
| --- | --- |
| Simulated parsers + field-level scoring | Built, 64 tests green |
| OCR confidence flagging + quality gates | Built, 64 tests green |
| Agents (ParserRunner, QualityGate, BenchmarkReporter) | Built, 64 tests green |
| Hash-chained audit, approvals, budget, brand check | Built, 64 tests green |
| CI workflow (`.github/workflows/ci.yml`) | Written, NOT verified (unrun; action SHAs pinned) |
| Real-parser adapter (e.g. wrapping an actual OCR engine) | Planned |
| Larger, multi-format document set | Planned |

## Docs

- [docs/implementation-guide.md](docs/implementation-guide.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/threat-model.md](docs/threat-model.md)
- [docs/interview-points.md](docs/interview-points.md)
- [docs/adr/](docs/adr/)
