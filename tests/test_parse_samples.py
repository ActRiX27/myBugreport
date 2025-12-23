import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mybugreport.pipeline.parse.parsers import (
    parse_bugreport_lines,
    parse_dmesg_line,
    parse_logcat_threadtime_line,
)
from mybugreport.pipeline.parse.manifest import parse_artifacts_manifest
from mybugreport.utils import write_json
from mybugreport.models import CollectArtifact


def test_logcat_parser_sample():
    sample = (repo_root / "samples" / "logcat_threadtime.txt").read_text().splitlines()
    ok = 0
    for line in sample:
        rec, parsed = parse_logcat_threadtime_line(line)
        assert rec.raw == line
        ok += int(parsed)
    assert ok == 2


def test_dmesg_parser_sample():
    sample = (repo_root / "samples" / "dmesg.txt").read_text().splitlines()
    ok = 0
    for line in sample:
        rec, parsed = parse_dmesg_line(line)
        assert rec.raw == line
        ok += int(parsed)
    assert ok >= 1


def test_manifest_parse(tmp_path):
    artifacts = [
        CollectArtifact(path=str(repo_root / "samples" / "logcat_threadtime.txt"), captured_at="now", device=None, artifact_type="logcat"),
        CollectArtifact(path=str(repo_root / "samples" / "dmesg.txt"), captured_at="now", device=None, artifact_type="dmesg"),
        CollectArtifact(path=str(repo_root / "samples" / "bugreport.txt"), captured_at="now", device=None, artifact_type="bugreport"),
    ]
    artifacts_path = tmp_path / "artifacts.json"
    write_json([a for a in artifacts], artifacts_path)

    records_path, summary_path = parse_artifacts_manifest(artifacts_path, tmp_path)
    records = (records_path).read_text().splitlines()
    assert len(records) >= 3
    summary = summary_path.read_text()
    assert "total" in summary
    assert "sources" in summary
