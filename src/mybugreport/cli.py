"""
CLI entry for myBugReport, reusable as a library function.
Preserves original behavior and output format while offering optional
pipeline-style subcommands for future extensions.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from .config import RULE2_FILE, RULE_FILE
from .io_utils import validate_inputs
from .models import DeviceInfo
from .pipeline.collect import collect_existing_artifact, write_artifacts_index
from .pipeline.parse import parse_artifacts_to_records, parse_bugreport_lines
from .pipeline.analyze import summarize_records, analyze_with_rules
from .pipeline.report import render_report_markdown, generate_delivery_report
from .processor import (
    apply_translations_and_time,
    extract_context_sections,
    extract_section_with_rules,
)
from .rules import load_translation_pairs, read_section_rule
from .time_utils import (
    parse_time,
    replace_time_strings_in_line as replace_time_strings_in_file,
)

# Backward-compatible global state retained for callers that rely on it.
pairs = {}


def execute_commands(dates, input_file, output_file, num_context_lines):
    """Main entry point mirroring the original script behavior."""
    validate_inputs([input_file])

    # Respect environment overrides even after the module has been imported.
    rule_file = os.environ.get("MYBUGREPORT_RULE_FILE", RULE_FILE)
    section_rule_file = os.environ.get("MYBUGREPORT_SECTION_RULE_FILE", RULE2_FILE)

    extract_context_sections(dates, input_file, output_file, num_context_lines)

    # section extraction remains optional/extendable via rule2 file and env overrides
    section_start, section_end = read_section_rule(section_rule_file)
    extract_section_with_rules(input_file, output_file, section_start, section_end)

    # 从配置文件中读取键值对
    pairs.update(load_translation_pairs(rule_file))

    apply_translations_and_time(output_file, pairs)

    # 保持原有的末尾调用（对输出无影响，兼容旧逻辑）
    replace_time_strings_in_file(output_file)


def main(argv=None):
    argv = argv or sys.argv
    dates = argv[1:-3]
    input_file = argv[-3]
    output_file = argv[-2]
    if len(argv) > 4:
        num_context_lines = argv[-1]
    else:
        num_context_lines = '1'
    execute_commands(dates, input_file, output_file, num_context_lines)


if __name__ == "__main__":
    main()


def pipeline_main(argv=None):
    """Dispatch pipeline subcommands without changing legacy CLI semantics."""

    parser = argparse.ArgumentParser(description="myBugReport pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect", help="Index existing bugreport")
    collect_parser.add_argument("bugreport", help="Path to bugreport text")
    collect_parser.add_argument("artifacts_dir", help="Directory to write artifacts index")
    collect_parser.add_argument("serial", help="Device serial")
    collect_parser.add_argument("model", nargs="?", default=None, help="Device model (optional)")

    parse_parser = subparsers.add_parser("parse", help="Convert bugreport to records.jsonl")
    parse_parser.add_argument("bugreport", help="Path to bugreport text")
    parse_parser.add_argument("records", help="Output jsonl path")
    parse_parser.add_argument("--source", default="bugreport", help="Source label")

    analyze_parser = subparsers.add_parser("analyze", help="Generate findings.json from records")
    analyze_parser.add_argument("records", help="Path to records jsonl")
    analyze_parser.add_argument("findings", help="Output findings json")

    report_parser = subparsers.add_parser("report", help="Render report markdown")
    report_parser.add_argument("findings", help="Path to findings json")
    report_parser.add_argument("report", help="Output report markdown path")
    report_parser.add_argument("--artifacts", help="Optional artifacts index json")
    report_parser.add_argument("--summary", help="Optional report summary")

    pipeline_parser = subparsers.add_parser("pipeline", help="Run collect→parse→analyze→report")
    pipeline_parser.add_argument("bugreport", help="Path to bugreport text")
    pipeline_parser.add_argument("workdir", help="Working directory for pipeline outputs")
    pipeline_parser.add_argument("serial", help="Device serial")
    pipeline_parser.add_argument("model", nargs="?", default=None, help="Device model (optional)")

    tool_parser = subparsers.add_parser("tool", help="Toolbox utilities")
    tool_sub = tool_parser.add_subparsers(dest="tool_command", required=True)

    collect_tool = tool_sub.add_parser("collect", help="Collection tools")
    collect_sub = collect_tool.add_subparsers(dest="collect_command", required=True)

    collect_adb_parser = collect_sub.add_parser("adb", help="Collect logs via adb")
    collect_adb_parser.add_argument("--serial", required=True, help="Device serial")
    collect_adb_parser.add_argument("--out", required=True, help="Output directory")
    collect_adb_parser.add_argument("--duration", type=int, default=None, help="Timeout seconds per command")
    collect_adb_parser.add_argument("--since", help="logcat -T <time> format")
    collect_adb_parser.add_argument("--buffers", help="Comma-separated buffers, e.g., main,system,crash")
    collect_adb_parser.add_argument("--dmesg", action="store_true", help="Collect dmesg if permitted")
    collect_adb_parser.add_argument("--bugreport", action="store_true", help="Collect bugreport (may be slow)")

    parse_tool = tool_sub.add_parser("parse", help="Parsing tools")
    parse_tool.add_argument("--artifacts", required=True, help="Path to artifacts.json")
    parse_tool.add_argument("--out", required=True, help="Output directory for records and summary")

    analyze_tool = tool_sub.add_parser("analyze", help="Analyze records with rules")
    analyze_tool.add_argument("--records", required=True, help="Path to records.jsonl")
    analyze_tool.add_argument("--rules", required=True, help="Directory containing rule json files")
    analyze_tool.add_argument("--out", required=True, help="Output directory for findings")

    report_tool = tool_sub.add_parser("report", help="Render delivery report")
    report_tool.add_argument("--artifacts", required=True, help="Path to artifacts.json")
    report_tool.add_argument("--findings", required=True, help="Path to findings.json")
    report_tool.add_argument("--out", required=True, help="Output directory for report")
    report_tool.add_argument("--evidence", help="Optional evidence jsonl")
    report_tool.add_argument("--records", help="Optional records jsonl for statistics")
    report_tool.add_argument("--format", default="md", help="Output format (default: md)")

    run_tool = tool_sub.add_parser("run", help="Run full pipeline for adb collection")
    run_sub = run_tool.add_subparsers(dest="run_command", required=True)
    run_adb = run_sub.add_parser("adb", help="Collect+parse+analyze+report via adb")
    run_adb.add_argument("--serial", help="Device serial")
    run_adb.add_argument("--out", help="Case directory")
    run_adb.add_argument("--rules", help="Rules directory")
    run_adb.add_argument("--config", help="Optional config.json for pipeline parameters")
    run_adb.add_argument("--duration", type=int, default=None, help="Timeout seconds per command")
    run_adb.add_argument("--since", help="logcat -T <time> format")
    run_adb.add_argument("--buffers", help="Comma-separated buffers, e.g., main,system,crash")
    run_adb.add_argument("--dmesg", action="store_true", help="Collect dmesg if permitted")
    run_adb.add_argument("--bugreport", action="store_true", help="Collect bugreport (may be slow)")
    run_adb.add_argument("--format", default="md", help="Report format (default md)")

    args = parser.parse_args(argv)

    if args.command == "collect":
        device = DeviceInfo(serial=args.serial, model=args.model)
        artifact = collect_existing_artifact(args.bugreport, device, args.artifacts_dir)
        index_path = Path(args.artifacts_dir) / "artifacts.json"
        write_artifacts_index([artifact], index_path)
        print(f"Artifacts indexed at {index_path}")
        return

    if args.command == "parse":
        parse_bugreport_lines(args.bugreport, args.records, source=args.source)
        print(f"Records written to {args.records}")
        return

    if args.command == "analyze":
        summarize_records(args.records, args.findings)
        print(f"Findings written to {args.findings}")
        return

    if args.command == "report":
        render_report_markdown(args.findings, args.report, artifacts_path=args.artifacts, summary=args.summary)
        print(f"Report generated at {args.report}")
        return

    if args.command == "pipeline":
        workdir = Path(args.workdir)
        device = DeviceInfo(serial=args.serial, model=args.model)
        artifacts_dir = workdir / "collect"
        records_dir = workdir / "parse"
        findings_path = workdir / "analyze" / "findings.json"
        report_path = workdir / "report" / "report.md"

        artifact = collect_existing_artifact(args.bugreport, device, artifacts_dir)
        artifacts_index = artifacts_dir / "artifacts.json"
        write_artifacts_index([artifact], artifacts_index)

        records_paths = parse_artifacts_to_records([args.bugreport], records_dir)
        if records_paths:
            summarize_records(records_paths[0], findings_path)
        render_report_markdown(findings_path, report_path, artifacts_path=artifacts_index)
        print(f"Pipeline finished, report at {report_path}")
        return

    if args.command == "tool":
        if args.tool_command == "collect" and args.collect_command == "adb":
            from .pipeline.collect.adb import collect_adb

            buffers = args.buffers.split(",") if args.buffers else None
            artifacts_index = collect_adb(
                serial=args.serial,
                out_dir=args.out,
                duration=args.duration,
                since=args.since,
                buffers=buffers,
                include_dmesg=args.dmesg,
                include_bugreport=args.bugreport,
            )
            print(f"ADB collection finished. Artifacts at {artifacts_index}")
            return
        if args.tool_command == "parse":
            from .pipeline.parse import parse_artifacts_manifest

            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            records_path, summary_path = parse_artifacts_manifest(Path(args.artifacts), out_dir)
            print(f"Records written to {records_path}, summary at {summary_path}")
            return
        if args.tool_command == "analyze":
            from .pipeline.analyze import analyze_with_rules

            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            findings_path, evidence_path = analyze_with_rules(Path(args.records), Path(args.rules), out_dir)
            print(f"Findings at {findings_path}, evidence at {evidence_path}")
            return
        if args.tool_command == "report":
            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = generate_delivery_report(
                artifacts_path=Path(args.artifacts),
                findings_path=Path(args.findings),
                out_dir=out_dir,
                evidence_path=Path(args.evidence) if args.evidence else None,
                records_path=Path(args.records) if args.records else None,
                fmt=args.format,
            )
            print(f"Report generated at {report_path}")
            return
        if args.tool_command == "run" and args.run_command == "adb":
            code = _run_adb_pipeline(args)
            sys.exit(code)


def _load_config(path: Optional[str]) -> Dict:
    if not path:
        return {}
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"config not found: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _run_adb_pipeline(args) -> int:
    """
    Exit codes:
    0 success; 2 arg error; 3 collect failure; 4 parse failure; 5 analyze failure; 6 report failure.
    """
    from .pipeline.collect.adb import collect_adb
    from .pipeline.parse import parse_artifacts_manifest
    from .pipeline.analyze import analyze_with_rules
    from .pipeline.report import generate_delivery_report

    try:
        config = _load_config(getattr(args, "config", None))
    except Exception as exc:
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 2

    collect_cfg = config.get("collect", {})
    parse_cfg = config.get("parse", {})
    analyze_cfg = config.get("analyze", {})
    report_cfg = config.get("report", {})
    rules_dir = args.rules or config.get("rules")
    case_dir = args.out or config.get("out")
    serial = args.serial or collect_cfg.get("serial")

    if not (rules_dir and case_dir and serial):
        print("Missing required parameters: serial, rules, out", file=sys.stderr)
        return 2

    buffers = args.buffers if args.buffers is not None else collect_cfg.get("buffers")
    buffers_list = buffers.split(",") if isinstance(buffers, str) else None

    try:
        case_dir = Path(case_dir)
        artifacts_dir = case_dir / "artifacts"
        records_dir = case_dir / "records"
        findings_dir = case_dir / "findings"
        report_dir = case_dir / "report"

        for path in (case_dir, artifacts_dir, records_dir, findings_dir, report_dir):
            path.mkdir(parents=True, exist_ok=True)

        artifacts_index = collect_adb(
            serial=serial,
            out_dir=artifacts_dir,
            duration=args.duration if args.duration is not None else collect_cfg.get("duration"),
            since=args.since if args.since is not None else collect_cfg.get("since"),
            buffers=buffers_list,
            include_dmesg=args.dmesg or collect_cfg.get("dmesg", False),
            include_bugreport=args.bugreport or collect_cfg.get("bugreport", False),
        )
    except Exception as exc:
        print(f"Collect failed: {exc}", file=sys.stderr)
        return 3

    try:
        records_path, summary_path = parse_artifacts_manifest(artifacts_index, records_dir)
    except Exception as exc:
        print(f"Parse failed: {exc}", file=sys.stderr)
        return 4

    try:
        findings_path, evidence_path = analyze_with_rules(records_path, Path(rules_dir), findings_dir)
    except Exception as exc:
        print(f"Analyze failed: {exc}", file=sys.stderr)
        return 5

    try:
        generate_delivery_report(
            artifacts_path=artifacts_index,
            findings_path=findings_path,
            out_dir=report_dir,
            evidence_path=evidence_path,
            records_path=records_path,
            fmt=args.format if hasattr(args, "format") else report_cfg.get("format", "md"),
        )
    except Exception as exc:
        print(f"Report failed: {exc}", file=sys.stderr)
        return 6

    return 0
