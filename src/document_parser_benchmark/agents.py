"""The three agents and the pipeline that wires them together.

Lifecycle covered end to end:
- prevent: PII is redacted before any field reaches a downstream agent.
- detect: ParserRunnerAgent runs every parser; OCR flags low-confidence pages.
- respond: QualityGateAgent holds poor parses; a human approval may bypass.
- recover: blocked documents land in a manual-review queue, not the bin.
- govern: every step is hash-chained in the audit log.
- measure: BenchmarkReporterAgent scores precision, recall, and F1.
"""

from . import metrics
from .audit import AuditLog
from .gates import ALLOW, BLOCK, NEEDS_APPROVAL, DownstreamAgent, QualityGateAgent
from .models import ExtractedField, ParseResult
from .parsers import ALL_PARSERS
from .redaction import redact


class ParserRunnerAgent:
    """Runs every parser over every document.

    Results stay raw here on purpose: the reporter scores true extraction
    quality against ground truth. Redaction happens in the pipeline, before
    any result reaches a gate or a downstream agent.
    """

    def __init__(self, parsers=None, audit=None):
        self.parsers = list(parsers) if parsers else list(ALL_PARSERS)
        self.audit = audit or AuditLog()

    def run(self, docs):
        results = []
        for doc in docs:
            for parser in self.parsers:
                result = parser.parse(doc)
                results.append(result)
                self.audit.record("parsed", {"parser": parser.name, "doc": doc.doc_id})
        return results


class BenchmarkReporterAgent:
    """Scores parsers head-to-head on the same document set."""

    def __init__(self, audit=None):
        self.audit = audit or AuditLog()

    def report(self, results, docs, gate_outcomes):
        truth_by_id = {d.doc_id: d.ground_truth for d in docs}
        per_parser = {}
        for parser in sorted({r.parser_name for r in results}):
            pairs = [(r, truth_by_id[r.doc_id]) for r in results if r.parser_name == parser]
            per_parser[parser] = metrics.aggregate(pairs)
        flagged = sorted({r.doc_id for r in results if r.flagged_pages})
        held = set()
        for key, outcome in gate_outcomes.items():
            if outcome in (BLOCK, NEEDS_APPROVAL):
                held.add(key[1] if isinstance(key, tuple) else key)
        blocked = sorted(held)
        report = {
            "per_parser": per_parser,
            "flagged_docs": flagged,
            "held_docs": blocked,
            "best_parser_by_f1": max(per_parser, key=lambda p: per_parser[p]["f1"]),
            "audit_chain_valid": self.audit.verify(),
            "audit_entries": len(self.audit.entries),
        }
        self.audit.record("reported", {"parsers": sorted(per_parser)})
        return report


class Pipeline:
    """Prevent -> detect -> respond -> recover -> govern -> measure."""

    def __init__(self, budget=None):
        self.audit = AuditLog()
        self.runner = ParserRunnerAgent(audit=self.audit)
        self.gate = QualityGateAgent()
        self.reporter = BenchmarkReporterAgent(audit=self.audit)
        self.downstream = DownstreamAgent()
        self.manual_review_queue = []
        self.budget = budget

    def run(self, docs, approvals=None):
        approvals = approvals or {}
        results = self.runner.run(docs)
        gate_outcomes = {}
        actions = []
        for result in results:
            # Prevent: redact before the gate or any downstream agent sees it.
            redacted = ParseResult(
                result.parser_name,
                result.doc_id,
                [ExtractedField(f.name, redact(f.value)[0], f.confidence) for f in result.fields],
                list(result.page_confidences),
                list(result.flagged_pages),
            )
            decision = self.gate.evaluate(redacted)
            if decision.outcome == NEEDS_APPROVAL and result.doc_id in approvals:
                decision = self.gate.bypass(decision, approvals[result.doc_id], result.doc_id)
            gate_outcomes[(result.parser_name, result.doc_id)] = decision.outcome
            if decision.actionable:
                actions.append(self.downstream.act(redacted, decision))
            else:
                self.manual_review_queue.append((result.parser_name, result.doc_id, decision.outcome))
                self.audit.record("held", {"parser": result.parser_name, "doc": result.doc_id})
            if self.budget is not None:
                self.budget.charge(0.01)  # simulated per-parse cost
        report = self.reporter.report(results, docs, gate_outcomes)
        report["actions"] = actions
        report["manual_review_queue"] = self.manual_review_queue
        return report
