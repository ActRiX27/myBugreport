"""
CLI entry for myBugReport, reusable as a library function.
Preserves original behavior and output format while offering optional
pipeline-style subcommands for future extensions.
"""

import argparse
import sys
from pathlib import Path

from .config import RULE2_FILE, RULE_FILE
from .io_utils import validate_inputs
from .models import DeviceInfo
from .pipeline.collect import collect_existing_artifact, write_artifacts_index
from .pipeline.parse import parse_artifacts_to_records, parse_bugreport_lines
from .pipeline.analyze import summarize_records
from .pipeline.report import render_report_markdown
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

    extract_context_sections(dates, input_file, output_file, num_context_lines)

    # section extraction remains optional/extendable via rule2 file and env overrides
    section_start, section_end = read_section_rule(RULE2_FILE)
    extract_section_with_rules(input_file, output_file, section_start, section_end)

    # 从配置文件中读取键值对
    pairs.update(load_translation_pairs(RULE_FILE))

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
