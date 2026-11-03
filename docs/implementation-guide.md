# Implementation guide

## Running

```bash
python3 -m pytest -q        # full suite, stdlib only
python3 run_demo.py         # benchmark report on the synthetic set
```

No network, no API keys, no virtual environment needed.

## Adding a parser

1. Add a class with a `name` attribute and a `parse(doc)` method returning
   a `ParseResult` in `src/document_parser_benchmark/parsers.py`.
2. Register it in `ALL_PARSERS` (or pass it to `ParserRunnerAgent`).
3. Add tests that pin its behaviour: which fields it extracts, which it
   drops, and how it reports confidence.

## Adding a document

Add an entry in `build_dataset()` with its ground-truth fields. The
benchmark numbers in the README must then be regenerated from a real run
(`python3 run_demo.py`), never edited by hand.

## Changing a gate threshold

`QualityGateAgent(min_mean_confidence=...)` and
`LOW_CONFIDENCE_THRESHOLD` in `parsers.py` are the two knobs. Changing
either changes which parses are held; update the gate tests and the
README numbers in the same change.
