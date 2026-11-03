"""Quality gates: nothing downstream acts on poorly parsed content.

Gate outcomes:
- ALLOW: clean parse, downstream may act.
- NEEDS_APPROVAL: low confidence or flagged pages; blocked unless a valid
  named-person, single-use, scoped, unexpired approval bypasses it.
- BLOCK: unredacted PII in extracted fields; never bypassable by approval,
  because consent cannot launder a leak.

Downstream agents refuse when no gate decision exists at all (absent path).
"""

from .approvals import Approval
from .parsers import LOW_CONFIDENCE_THRESHOLD
from .redaction import contains_pii

ALLOW = "ALLOW"
NEEDS_APPROVAL = "NEEDS_APPROVAL"
BLOCK = "BLOCK"


class GateError(Exception):
    pass


class GateDecision:
    def __init__(self, outcome, doc_id, reasons):
        self.outcome = outcome
        self.doc_id = doc_id
        self.reasons = list(reasons)
        self.bypassed_by = None

    @property
    def actionable(self):
        return self.outcome == ALLOW


class QualityGateAgent:
    """Detect poor parses and hold them; never pass them silently."""

    def __init__(self, min_mean_confidence=LOW_CONFIDENCE_THRESHOLD):
        self.min_mean_confidence = min_mean_confidence

    def evaluate(self, result):
        reasons = []
        for f in result.fields:
            if contains_pii(f.value):
                reasons.append(f"unredacted PII in field {f.name}")
        if reasons:
            return GateDecision(BLOCK, result.doc_id, reasons)
        if result.flagged_pages:
            reasons.append(f"flagged low-confidence pages: {result.flagged_pages}")
        if result.mean_confidence() < self.min_mean_confidence:
            reasons.append(f"mean confidence {result.mean_confidence():.3f} below {self.min_mean_confidence}")
        if reasons:
            return GateDecision(NEEDS_APPROVAL, result.doc_id, reasons)
        return GateDecision(ALLOW, result.doc_id, [])

    def bypass(self, decision, approval, doc_id):
        """Bypass a NEEDS_APPROVAL hold with a valid approval, else refuse."""
        if decision.outcome != NEEDS_APPROVAL:
            return decision
        if not isinstance(approval, Approval):
            return decision
        if approval.consume(doc_id):
            bypassed = GateDecision(ALLOW, doc_id, decision.reasons)
            bypassed.bypassed_by = approval.approver
            return bypassed
        return decision


class DownstreamAgent:
    """Acts on parsed content only after an ALLOW gate decision."""

    def act(self, result, decision):
        if decision is None:
            raise GateError("absent gate decision: refusing to act on unreviewed parse")
        if decision.doc_id != result.doc_id:
            raise GateError("gate decision is for a different document")
        if not decision.actionable:
            raise GateError(f"gate outcome {decision.outcome}: downstream action blocked")
        return f"acted on {result.doc_id} via {result.parser_name}"
