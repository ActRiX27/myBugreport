"""Report stage skeleton: render findings into Markdown."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ...models import CollectArtifact, DeviceInfo, Finding, ReportData
from ...utils import read_json, write_json
from .generator import generate_delivery_report


def load_findings(path: Path) -> List[Finding]:
    data = read_json(Path(path))
    findings: List[Finding] = []
    for item in data:
        findings.append(
            Finding(
                rule_id=item.get("rule_id", "unknown"),
                severity=item.get("severity", "info"),
                evidence=item.get("evidence", {}),
                confidence=float(item.get("confidence", 0.0)),
                summary=item.get("summary"),
            )
        )
    return findings


def load_artifacts(path: Optional[Path]) -> List[CollectArtifact]:
    if path is None:
        return []
    data = read_json(Path(path))
    artifacts: List[CollectArtifact] = []
    for item in data:
        device_data = item.get("device")
        device = None
        if isinstance(device_data, dict):
            device = DeviceInfo(
                serial=device_data.get("serial", ""),
                model=device_data.get("model"),
                android_version=device_data.get("android_version"),
                build_fingerprint=device_data.get("build_fingerprint"),
                notes=device_data.get("notes"),
            )
        artifacts.append(
            CollectArtifact(
                path=item.get("path", ""),
                captured_at=item.get("captured_at", ""),
                device=device,
                artifact_type=item.get("artifact_type", "bugreport"),
                sha256=item.get("sha256"),
                size_bytes=item.get("size_bytes"),
            )
        )
    return artifacts


def render_report_markdown(
    findings_path: Path,
    output_path: Path,
    artifacts_path: Optional[Path] = None,
    summary: Optional[str] = None,
) -> ReportData:
    findings = load_findings(findings_path)
    artifacts = load_artifacts(artifacts_path)
    report = ReportData(
        device=artifacts[0].device if artifacts else None,  # type: ignore[arg-type]
        artifacts=artifacts,
        findings=findings,
        summary=summary,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# myBugReport 检测结果", ""]
    if report.summary:
        lines.append(f"摘要：{report.summary}")
        lines.append("")
    lines.append(f"生成时间：{report.generated_at}")
    lines.append("")
    lines.append("## 分析结论")
    if not findings:
        lines.append("- 未生成任何结论")
    else:
        for item in findings:
            lines.append(
                f"- [{item.severity}] {item.rule_id} (confidence={item.confidence:.2f}) — {item.summary or '占位摘要'}"
            )
    lines.append("")
    lines.append("## 采集产物")
    if not artifacts:
        lines.append("- 未记录采集产物索引")
    else:
        for art in artifacts:
            lines.append(
                f"- {art.artifact_type}: {art.path} (sha256={art.sha256 or 'n/a'}, size={art.size_bytes or 'n/a'})"
            )
    output.write_text("\n".join(lines))

    # 以 JSON 形式输出完整结构，便于机器消费
    write_json(report, output.with_suffix(".json"))
    return report


__all__ = ["render_report_markdown", "load_findings", "load_artifacts"]
__all__.append("generate_delivery_report")
