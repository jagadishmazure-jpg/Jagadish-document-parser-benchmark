"""Demo: run the full benchmark and print the measured report."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from document_parser_benchmark.agents import Pipeline
from document_parser_benchmark.dataset import build_dataset

if __name__ == "__main__":
    report = Pipeline().run(build_dataset())
    print("Head-to-head parser benchmark (simulated parsers, synthetic documents)")
    print("Documents: 6, parsers: 3, parses scored: 18")
    for name, s in sorted(report["per_parser"].items()):
        print(
            f"  {name:13s} precision={s['precision']:.4f} "
            f"recall={s['recall']:.4f} F1={s['f1']:.4f} "
            f"(TP={s['tp']} FP={s['fp']} FN={s['fn']})"
        )
    print(f"Best parser by F1: {report['best_parser_by_f1']}")
    print(f"Flagged low-confidence docs: {report['flagged_docs']}")
    print(f"Held for manual review: {len(report['manual_review_queue'])} parses")
    print(f"Audit chain valid: {report['audit_chain_valid']}")
