"""Helpers to parse artifacts.json into records and summary outputs."""

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ...models import CollectArtifact, LogRecord
from ...utils import read_json, write_json, write_jsonl
from .parsers import parse_bugreport_lines, parse_dmesg_line, parse_logcat_threadtime_line


def load_artifacts(path: Path) -> List[CollectArtifact]:
    data = read_json(Path(path))
    artifacts: List[CollectArtifact] = []
    for item in data:
        artifacts.append(
            CollectArtifact(
                path=item.get("path", ""),
                captured_at=item.get("captured_at", ""),
                device=item.get("device"),
                artifact_type=item.get("artifact_type", "unknown"),
                sha256=item.get("sha256"),
                size_bytes=item.get("size_bytes"),
                command=item.get("command"),
                metadata=item.get("metadata"),
            )
        )
    return artifacts


def parse_artifacts_manifest(artifacts_json: Path, out_dir: Path) -> Tuple[Path, Path]:
    artifacts = load_artifacts(artifacts_json)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records: List[LogRecord] = []
    failures: List[Dict[str, str]] = []

    for artifact in artifacts:
        path = Path(artifact.path)
        if not path.exists():
            failures.append({"artifact": artifact.path, "error": "file not found"})
            continue
        try:
            if artifact.artifact_type == "logcat":
                recs, fail = _parse_logcat_file(path)
                records.extend(recs)
                failures.extend(_failures(path, fail))
            elif artifact.artifact_type == "dmesg":
                recs, fail = _parse_dmesg_file(path)
                records.extend(recs)
                failures.extend(_failures(path, fail))
            elif artifact.artifact_type == "bugreport":
                recs = _parse_bugreport_file(path)
                records.extend(recs)
            else:
                failures.append({"artifact": artifact.path, "error": f"unknown type {artifact.artifact_type}"})
        except Exception as exc:
            failures.append({"artifact": artifact.path, "error": str(exc)})

    records_path = out_dir / "records.jsonl"
    write_jsonl(records, records_path)
    summary = {
        "total": len(records),
        "failures": failures,
        "sources": _source_counts(records),
    }
    summary_path = out_dir / "parse_summary.json"
    write_json(summary, summary_path)
    return records_path, summary_path


def _parse_logcat_file(path: Path) -> Tuple[List[LogRecord], List[int]]:
    records: List[LogRecord] = []
    failures: List[int] = []
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for idx, line in enumerate(handle, 1):
            rec, ok = parse_logcat_threadtime_line(line)
            records.append(rec)
            if not ok:
                failures.append(idx)
    return records, failures


def _parse_dmesg_file(path: Path) -> Tuple[List[LogRecord], List[int]]:
    records: List[LogRecord] = []
    failures: List[int] = []
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for idx, line in enumerate(handle, 1):
            rec, ok = parse_dmesg_line(line)
            records.append(rec)
            if not ok:
                failures.append(idx)
    return records, failures


def _parse_bugreport_file(path: Path) -> List[LogRecord]:
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        return parse_bugreport_lines(handle)


def _failures(path: Path, lines: List[int]) -> List[Dict[str, str]]:
    return [{"artifact": str(path), "line": str(num), "error": "unparsed"} for num in lines]


def _source_counts(records: Iterable[LogRecord]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rec in records:
        counts[rec.source] = counts.get(rec.source, 0) + 1
    return counts


__all__ = ["parse_artifacts_manifest"]
