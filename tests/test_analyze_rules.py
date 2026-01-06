import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mybugreport.pipeline.analyze import analyze_with_rules
from mybugreport.pipeline.parse.parsers import parse_bugreport_lines
from mybugreport.utils import write_jsonl


def test_analyze_with_rules(tmp_path):
    records = repo_root / "samples" / "records.jsonl"
    rules_dir = repo_root / "samples" / "rules"
    out_dir = tmp_path / "out"
    findings_path, evidence_path = analyze_with_rules(records, rules_dir, out_dir)

    findings = findings_path.read_text()
    evidence = evidence_path.read_text().splitlines()

    assert "network.failure" in findings
    assert "security.selinux" in findings
    assert evidence  # should not be empty


def test_analyze_bugreport_threadtime_levels(tmp_path):
    lines = [
        "Build fingerprint: vendor/device/model:11/AAA/20240101:user/release-keys",
        "01-01 00:00:00.000  100  200 E AndroidRuntime: FATAL EXCEPTION: main",
        "01-01 00:00:01.000  100  200 W NetworkMonitor: connection reset by peer",
        "01-01 00:00:02.000      0      0 E SELinux: avc: denied { read } for name=\"/data\"",
        "==== dropbox entries (timestamp):",
        "anr_01",
        "==== end",
    ]
    records = parse_bugreport_lines(lines)
    records_path = tmp_path / "records.jsonl"
    write_jsonl(records, records_path)

    rules_dir = repo_root / "samples" / "rules"
    out_dir = tmp_path / "out"
    findings_path, evidence_path = analyze_with_rules(records_path, rules_dir, out_dir)

    findings_text = findings_path.read_text()
    assert "crash.anr" in findings_text
    assert "network.failure" in findings_text
    assert "security.selinux" in findings_text
    assert "build.fingerprint" in findings_text
    assert "dropbox.entries" in findings_text
    assert "baseline.top_tags" in findings_text
    assert "baseline.stats" in findings_text
    assert evidence_path.read_text().strip()
