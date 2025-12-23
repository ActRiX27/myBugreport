import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mybugreport.pipeline.analyze import analyze_with_rules


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
