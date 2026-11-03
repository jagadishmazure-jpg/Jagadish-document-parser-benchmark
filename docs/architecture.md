# Architecture

See `knowledge/architecture-diagram.md` for the diagrams. In short:
synthetic documents flow through ParserRunnerAgent to three simulated
parsers; results are redacted, then gated by QualityGateAgent; allowed
parses reach DownstreamAgent, held parses reach a manual-review queue;
BenchmarkReporterAgent scores every parser on the same documents and
verifies the hash-chained audit log.
