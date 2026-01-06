"""Parse stage skeleton: normalize bugreport text into structured log records."""

from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from ...models import LogRecord
from ...utils import write_jsonl
from .manifest import parse_artifacts_manifest
from .parsers import (
    parse_bugreport_lines as parse_bugreport_content,
    parse_dmesg_line,
    parse_logcat_threadtime_line,
)


def parse_bugreport_lines(
    bugreport_path: Path,
    output_path: Path,
    source: str = "bugreport",
    max_lines: Optional[int] = None,
) -> List[LogRecord]:
    bugreport_path = Path(bugreport_path)
    with bugreport_path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = []
        for idx, line in enumerate(handle):
            if max_lines is not None and idx >= max_lines:
                break
            lines.append(line)
    records = parse_bugreport_content(lines)
    # Normalize source label for downstream consumers that rely on caller-provided source.
    for rec in records:
        rec.source = source
    write_jsonl(records, Path(output_path))
    return records


def parse_artifacts_to_records(
    artifacts: Iterable[Path], output_dir: Path, source: str = "bugreport"
) -> List[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    for artifact in artifacts:
        artifact = Path(artifact)
        output_path = output_dir / f"{artifact.stem}.records.jsonl"
        parse_bugreport_lines(artifact, output_path, source=source)
        outputs.append(output_path)
    return outputs


__all__ = [
    "parse_bugreport_lines",
    "parse_artifacts_to_records",
    "parse_artifacts_manifest",
    "parse_logcat_threadtime_line",
    "parse_dmesg_line",
]
