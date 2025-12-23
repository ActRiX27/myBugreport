"""Analyze stage skeleton: derive findings from normalized records."""

from pathlib import Path
from typing import List

from ...models import Finding
from ...utils import read_jsonl, write_json


def summarize_records(records_path: Path, output_path: Path) -> List[Finding]:
    records = read_jsonl(Path(records_path))
    count = len(records)
    evidence = {"records": count}
    confidence = 0.0 if count == 0 else min(1.0, 0.2 + 0.05 * count)
    finding = Finding(
        rule_id="baseline.count",
        severity="info" if count else "none",
        evidence=evidence,
        confidence=confidence,
        summary="Record count placeholder for downstream analysis",
    )
    write_json([finding], Path(output_path))
    return [finding]


__all__ = ["summarize_records"]
