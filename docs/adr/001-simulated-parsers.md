# ADR 001 — Simulated parsers, not real engines

Simulated parsers keep the project offline, deterministic, and testable.
The benchmark harness, gates, and scoring are the deliverable; a real
parser is a future adapter that must implement the same `parse(doc)`
contract and confidence reporting.
