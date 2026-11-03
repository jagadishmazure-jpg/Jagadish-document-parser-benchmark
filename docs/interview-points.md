# Discussion points

- Why score field-level exact match rather than whole-document similarity?
  Because downstream agents act on individual fields; a document that is
  "mostly right" can still carry one wrong total into a payment.
- Why does a wrong value count as both a false positive and a false
  negative? The parser claimed something and still missed the truth; both
  errors are real.
- Why is a PII block unbypassable while a low-confidence hold is not?
  Consent can accept uncertainty, but it cannot authorise a leak.
- Why is the manual-review queue the recovery path, not re-parsing?
  Re-parsing a faded scan with the same parser reproduces the same
  misread; a human looks at the source.
- Why simulated parsers? So the benchmark harness, the gate, and the
  scoring can be built and tested offline; swapping in a real parser is
  an adapter, not a redesign.
