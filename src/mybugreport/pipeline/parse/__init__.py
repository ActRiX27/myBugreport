"""Parse stage skeleton: normalize bugreport text into structured log records."""

from pathlib import Path
from typing import Iterable, List, Optional

from ...models import LogRecord
from ...utils import write_jsonl


def parse_bugreport_lines(
    bugreport_path: Path,
    output_path: Path,
    source: str = "bugreport",
    max_lines: Optional[int] = None,
) -> List[LogRecord]:
    bugreport_path = Path(bugreport_path)
    records: List[LogRecord] = []
    with bugreport_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if max_lines is not None and idx >= max_lines:
                break
            raw = line.rstrip("\n")
            records.append(
                LogRecord(
                    ts=None,
                    level=None,
                    tag=None,
                    msg=raw,
                    raw=raw,
                    source=source,
                )
            )
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


__all__ = ["parse_bugreport_lines", "parse_artifacts_to_records"]
