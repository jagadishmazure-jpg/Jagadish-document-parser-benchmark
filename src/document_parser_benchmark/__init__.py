"""Document parser benchmark."""

from .agents import BenchmarkReporterAgent, ParserRunnerAgent, Pipeline
from .dataset import build_dataset
from .gates import DownstreamAgent, QualityGateAgent
from .parsers import ALL_PARSERS, LayoutAwareParser, OcrParser, PlainTextParser

__all__ = [
    "ALL_PARSERS",
    "BenchmarkReporterAgent",
    "DownstreamAgent",
    "LayoutAwareParser",
    "OcrParser",
    "ParserRunnerAgent",
    "Pipeline",
    "PlainTextParser",
    "QualityGateAgent",
    "build_dataset",
]
