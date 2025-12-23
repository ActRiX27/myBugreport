"""Data models for the myBugReport pipeline (JSON-serializable)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DeviceInfo:
    """设备信息基模，便于采集/报告时复用。"""

    serial: str
    model: Optional[str] = None
    android_version: Optional[str] = None
    build_fingerprint: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CollectArtifact:
    """采集阶段产物索引（记录文件路径与指纹）。"""

    path: str
    captured_at: str
    device: Optional[DeviceInfo]
    artifact_type: str = "bugreport"
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class LogRecord:
    """解析后的统一日志记录格式。"""

    ts: Optional[str]
    level: Optional[str]
    tag: Optional[str]
    msg: str
    raw: str
    source: str


@dataclass
class Finding:
    """分析结论：可被报告阶段直接消费。"""

    rule_id: str
    severity: str
    evidence: Dict[str, Any]
    confidence: float
    summary: Optional[str] = None


@dataclass
class ReportData:
    """报告渲染输入数据。"""

    device: Optional[DeviceInfo]
    artifacts: List[CollectArtifact] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    summary: Optional[str] = None
    template: Optional[str] = None


__all__ = [
    "DeviceInfo",
    "CollectArtifact",
    "LogRecord",
    "Finding",
    "ReportData",
]
