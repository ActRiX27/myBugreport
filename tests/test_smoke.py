import os
import importlib
import sys
from pathlib import Path


def test_smoke_run(tmp_path, monkeypatch=None):
    # Ensure src is on path for editable-like import in test
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Prepare temporary rules and input/output
    rule_file = tmp_path / "rule.txt"
    rule_file.write_text("key:值\n")

    section_rule = tmp_path / "rule2.txt"
    section_rule.write_text("START:END\n")

    input_file = tmp_path / "bugreport.txt"
    input_file.write_text("""2024-01-01 key
START
payload key
END
""")

    output_file = tmp_path / "out.txt"

    # Set env before import to ensure config picks them up
    os.environ["MYBUGREPORT_RULE_FILE"] = str(rule_file)
    os.environ["MYBUGREPORT_SECTION_RULE_FILE"] = str(section_rule)

    # Reload package to pick up env overrides
    import mybugreport.cli as cli
    importlib.reload(cli)

    cli.execute_commands(["2024-01-01"], str(input_file), str(output_file), "0")

    content = output_file.read_text()
    assert "值" in content  # translation applied
    assert "payload" in content


def test_pipeline_contract(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from mybugreport.models import DeviceInfo
    from mybugreport.pipeline.collect import collect_existing_artifact, write_artifacts_index
    from mybugreport.pipeline.parse import parse_artifacts_to_records
    from mybugreport.pipeline.analyze import summarize_records
    from mybugreport.pipeline.report import render_report_markdown

    bugreport = tmp_path / "bugreport.txt"
    bugreport.write_text("line1\nline2\n")

    device = DeviceInfo(serial="demo", model="Demo")
    artifacts_dir = tmp_path / "collect"
    artifact = collect_existing_artifact(bugreport, device, artifacts_dir)
    artifacts_index = artifacts_dir / "artifacts.json"
    write_artifacts_index([artifact], artifacts_index)

    records_dir = tmp_path / "parse"
    records = parse_artifacts_to_records([bugreport], records_dir)
    findings_path = tmp_path / "findings.json"
    summarize_records(records[0], findings_path)

    report_dir = tmp_path / "report"
    report_path = report_dir / "report.md"
    render_report_markdown(findings_path, report_path, artifacts_path=artifacts_index)

    assert artifacts_index.exists()
    assert findings_path.exists()
    assert report_path.exists()
