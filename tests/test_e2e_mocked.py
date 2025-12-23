import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import mybugreport.cli as cli


def test_run_adb_pipeline_mock(monkeypatch, tmp_path):
    # Mock collect/parse/analyze/report to avoid adb
    artifacts_index = tmp_path / "artifacts" / "artifacts.json"
    artifacts_index.parent.mkdir(parents=True, exist_ok=True)
    artifacts_index.write_text("[]")

    records_path = tmp_path / "records.jsonl"
    records_path.write_text("{}\n")

    findings_path = tmp_path / "findings.json"
    findings_path.write_text("[]")

    evidence_path = tmp_path / "findings_evidence.jsonl"
    evidence_path.write_text("{}\n")

    report_path = tmp_path / "case" / "report" / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# report")

    def fake_collect_adb(**kwargs):
        return artifacts_index

    def fake_parse_manifest(artifacts, out_dir):
        return records_path, tmp_path / "parse_summary.json"

    def fake_analyze(records, rules, out_dir):
        return findings_path, evidence_path

    def fake_report(**kwargs):
        return report_path

    monkeypatch.setattr("mybugreport.pipeline.collect.adb.collect_adb", fake_collect_adb)
    monkeypatch.setattr("mybugreport.pipeline.parse.parse_artifacts_manifest", fake_parse_manifest)
    monkeypatch.setattr("mybugreport.pipeline.analyze.analyze_with_rules", fake_analyze)
    monkeypatch.setattr("mybugreport.pipeline.report.generate_delivery_report", fake_report)

    class Args:
        command = "tool"
        tool_command = "run"
        run_command = "adb"
        serial = "demo"
        out = str(tmp_path / "case")
        rules = str(repo_root / "samples" / "rules")
        config = None
        duration = None
        since = None
        buffers = None
        dmesg = False
        bugreport = False
        format = "md"

    code = cli._run_adb_pipeline(Args())
    assert code == 0
    assert (tmp_path / "case" / "report" / "report.md").exists()
