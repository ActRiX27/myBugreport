import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mybugreport.pipeline.report.generator import generate_delivery_report


def test_generate_delivery_report(tmp_path):
    artifacts = repo_root / "samples" / "artifacts.json"
    # build artifacts.json from existing sample logcat file
    logcat = repo_root / "samples" / "logcat_threadtime.txt"
    artifacts_data = [
        {
            "path": str(logcat),
            "captured_at": "2024-01-01T00:00:00Z",
            "device": {"serial": "demo", "model": "demo"},
            "artifact_type": "logcat",
            "sha256": "dummy",
            "command": "adb logcat",
        }
    ]
    artifacts.write_text(__import__("json").dumps(artifacts_data))

    findings = repo_root / "samples" / "findings.json"
    evidence = repo_root / "samples" / "findings_evidence.jsonl"
    evidence.write_text("{}\n")
    records = repo_root / "samples" / "records.jsonl"

    out_dir = tmp_path / "report"
    report_path = generate_delivery_report(artifacts, findings, out_dir, evidence_path=evidence, records_path=records)
    assert report_path.exists()
    data_json = report_path.with_suffix(".json")
    assert data_json.exists()
    content = data_json.read_text()
    assert "overall_risk" in content
