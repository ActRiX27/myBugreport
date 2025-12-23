"""Pipeline package: collect → parse → analyze → report.

This package defines callable skeletons for each stage while preserving the
legacy CLI behavior. The stages share JSON-serializable dataclasses defined in
``mybugreport.models`` and write artifacts in predictable locations to serve as
contracts for future implementations.
"""

__all__ = ["collect", "parse", "analyze", "report"]
