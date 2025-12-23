"""Serialization helpers for dataclasses and JSON/JSONL I/O."""

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, List


def _to_serializable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


def write_json(obj: Any, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = _to_serializable(obj)
    path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2))


def write_jsonl(items: Iterable[Any], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for item in items:
        lines.append(json.dumps(_to_serializable(item), ensure_ascii=False))
    path.write_text("\n".join(lines))


def read_json(path: Path) -> Any:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    return json.loads(path.read_text())


def read_jsonl(path: Path) -> List[Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")
    content = path.read_text().strip()
    if not content:
        return []
    return [json.loads(line) for line in content.splitlines()]


__all__ = [
    "write_json",
    "write_jsonl",
    "read_json",
    "read_jsonl",
]
