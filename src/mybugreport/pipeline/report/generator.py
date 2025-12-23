"""Generate delivery report from artifacts and findings."""

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ...utils import read_json, read_jsonl, write_json


SEVERITY_ORDER = ["high", "warning", "info", "none"]


def _load_artifacts(path: Path) -> List[Dict]:
    return read_json(path) if path else []


def _load_findings(path: Path) -> List[Dict]:
    return read_json(path) if path else []


def _load_evidence(path: Optional[Path]) -> List[Dict]:
    if not path:
        return []
    try:
        return read_jsonl(path)
    except FileNotFoundError:
        return []


def _load_records(path: Optional[Path]) -> List[Dict]:
    if not path:
        return []
    try:
        return read_jsonl(path)
    except FileNotFoundError:
        return []


def _count_field(records: Iterable[Dict], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rec in records:
        val = rec.get(field) or "unknown"
        counts[val] = counts.get(val, 0) + 1
    return counts


def _overall_risk(findings: List[Dict]) -> str:
    severities = [f.get("severity", "info") for f in findings]
    for sev in SEVERITY_ORDER:
        if sev in severities:
            return sev
    return "none"


def generate_delivery_report(
    artifacts_path: Path,
    findings_path: Path,
    out_dir: Path,
    evidence_path: Optional[Path] = None,
    records_path: Optional[Path] = None,
    fmt: str = "md",
) -> Path:
    artifacts = _load_artifacts(artifacts_path)
    findings = _load_findings(findings_path)
    evidence = _load_evidence(evidence_path)
    records = _load_records(records_path)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "report.md"

    overall = _overall_risk(findings)
    summary_lines = ["# myBugReport 交付报告", "", f"总体风险：{overall}", f"发现数量：{len(findings)}", ""]

    # 采集说明
    summary_lines.append("## 采集说明")
    if not artifacts:
        summary_lines.append("- 未找到采集产物索引")
    else:
        for art in artifacts:
            summary_lines.append(
                f"- 类型: {art.get('artifact_type','n/a')} 路径: {art.get('path')} 时间: {art.get('captured_at','n/a')} "
                f"命令: {art.get('command','n/a')} sha256: {art.get('sha256','n/a')}"
            )
            device = art.get("device") or {}
            if device:
                summary_lines.append(
                    f"  - 设备: serial={device.get('serial','n/a')}, model={device.get('model','n/a')}, "
                    f"android={device.get('android_version','n/a')}, fingerprint={device.get('build_fingerprint','n/a')}"
                )
    summary_lines.append("")

    # 日志统计
    summary_lines.append("## 日志统计")
    if records:
        level_counts = _count_field(records, "level")
        tag_counts = _count_field(records, "tag")
        src_counts = _count_field(records, "source")
        summary_lines.append(f"- 按 level：{json.dumps(level_counts, ensure_ascii=False)}")
        summary_lines.append(f"- 按 tag：{json.dumps(tag_counts, ensure_ascii=False)}")
        summary_lines.append(f"- 按 source：{json.dumps(src_counts, ensure_ascii=False)}")
    else:
        summary_lines.append("- 未提供 records.jsonl，统计为空")
    summary_lines.append("")

    # 发现列表
    summary_lines.append("## 发现列表")
    if not findings:
        summary_lines.append("- 无发现")
    else:
        sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER.index(f.get("severity", "info")) if f.get("severity", "info") in SEVERITY_ORDER else len(SEVERITY_ORDER))
        for fitem in sorted_findings:
            summary_lines.append(
                f"- [{fitem.get('severity','info')}] {fitem.get('rule_id')} (hits={fitem.get('evidence',{}).get('hits','n/a')}, "
                f"confidence={fitem.get('confidence','n/a')}) — {fitem.get('summary') or fitem.get('description','')}"
            )
    summary_lines.append("")

    # 证据索引
    summary_lines.append("## 证据索引")
    if evidence:
        summary_lines.append("证据文件：findings_evidence.jsonl")
        for idx, ev in enumerate(evidence, 1):
            summary_lines.append(
                f"- #{idx} rule={ev.get('rule_id')} level={ev.get('level')} tag={ev.get('tag')} source={ev.get('source')}"
            )
    else:
        summary_lines.append("- 未提供 evidence 记录")

    md_path.write_text("\n".join(summary_lines))

    # 产出 JSON 便于自动化消费
    write_json(
        {
            "overall_risk": overall,
            "findings_count": len(findings),
            "level_counts": _count_field(records, "level") if records else {},
            "tag_counts": _count_field(records, "tag") if records else {},
            "source_counts": _count_field(records, "source") if records else {},
        },
        md_path.with_suffix(".json"),
    )

    return md_path


__all__ = ["generate_delivery_report"]
