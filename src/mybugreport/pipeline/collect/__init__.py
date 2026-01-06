"""Collect stage skeleton: index bugreport artifacts for downstream stages."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List

from ...models import CollectArtifact, DeviceInfo
from ...utils import write_json


def fingerprint_file(path: Path) -> str:
    data = Path(path).read_bytes()
    return sha256(data).hexdigest()


def collect_existing_artifact(
    bugreport_path: Path,
    device: DeviceInfo,
    artifacts_dir: Path,
    artifact_type: str = "bugreport",
) -> CollectArtifact:
    bugreport_path = Path(bugreport_path)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    digest = fingerprint_file(bugreport_path)
    size_bytes = bugreport_path.stat().st_size
    return CollectArtifact(
        path=str(bugreport_path),
        captured_at=captured_at,
        device=device,
        artifact_type=artifact_type,
        sha256=digest,
        size_bytes=size_bytes,
    )


def write_artifacts_index(artifacts: Iterable[CollectArtifact], output_path: Path) -> Path:
    artifacts_list: List[CollectArtifact] = list(artifacts)
    write_json([artifact for artifact in artifacts_list], output_path)
    return Path(output_path)


__all__ = [
    "collect_existing_artifact",
    "write_artifacts_index",
    "fingerprint_file",
]
