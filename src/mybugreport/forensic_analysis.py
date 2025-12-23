"""
Optional forensic-style analysis helpers (not wired into the CLI by default).

本发明通过对移动端设备的日志分析，通过对于移动设备的电量变化，数据库变化及特定文件等分析，判断移动设备是否被取证，对取证等行为进行分析。
1. 方法概述与机理
目的：在 ADB 连接窗口内，判定设备是否出现取证式的系统化枚举/导出行为。
思路：以“ADB 握手→系统服务被批量拉起→URI 授权密集→Shell 命令族高频”的阶段链为主线，从日志中抽取多类特征并融合得到嫌疑评分 S∈[0,1]。
公式与原理：
把四类日志证据转成 0–1 强度后按重要性加权求和，再用 S 形函数压到 [0,1]，得到“是否在做系统化取证”的置信度。
参数含义：
- T：判定时间窗（如 60s）。
- L1~L4：四类原始观测（L1 连接/鉴权，L2 电量历史，L3 Provider/URI，L4 Shell 命令族）。
- f：特征映射，把观测变为 0–1 的证据强度。
- w_i：权重，表示各证据的重要性。
- b：偏置，整体灵敏度校准项。
- g：压缩函数（如逻辑函数）把实数映射到 [0,1]。
- S：嫌疑评分（越大越可疑）。
- τ：判定阈值（常态/中风险/高嫌疑分层）。

注：本模块仅提供扩展接口，未在主流程中启用，以确保向后兼容。
- 融合公式各元素含义（可选阈值分层逻辑，未默认启用）：
  - S（嫌疑评分，0–1）：融合后的置信度，越接近 1 越像系统化取证/导出行为。
  - τ_high（高阈值，常取 0.75–0.90）：S ≥ τ_high 判定高嫌疑（可用于触发证据固化/联动处置）。
  - τ_med（中阈值，常取 0.60–0.75）：τ_med ≤ S < τ_high 判定中风险预警（提高采样、延长观察再判）。
  - 其余情况视为常态，仅滚动记录。
  - 调参建议：召回优先下调阈值；精准优先上调阈值或加大 L3/L4 权重，并引入阶段链先验。
  - 可观测日志来源（ADB 只读获取）：logcat main/system/events/security；dumpsys batterystats --history、activity providers、activity uri-permissions 等。
 - “销毁/隐藏/规避”三维与 L1-L4 的关联（共性行为，不依赖进程名/MD5）：
   - 销毁：对应 L4 的清理/粉碎指令簇（tar/rm/restorecon 等）与 L3 的内容改写痕迹。
   - 隐藏：对应 L4 的路径/可见性变形（非常规路径、跳目录），以及 L3 的索引/授权异常。
   - 规避：将节奏打散，但保留 L3/L4 子序列结构（枚举→改写/导出），配合 L2 的长会话时间窗与 L1 的高权限信道确认。
"""

from dataclasses import dataclass, field
from math import exp
from typing import Dict, Iterable, Mapping, Sequence

from .config import log_debug


@dataclass
class EvidenceConfig:
    """Configuration for a single evidence channel."""

    name: str
    weight: float = 1.0


@dataclass
class FeatureGroup:
    """
    描述四类特征的含义与融合形式（用于未来扩展，当前未默认启用）。
    """

    name: str
    meaning: str
    fusion_form: str
    sub_features: Sequence[str] = field(default_factory=list)


def sigmoid(x: float) -> float:
    """S-shaped compression function to map any real value to [0, 1]."""
    return 1.0 / (1.0 + exp(-x))


def normalize_signal(value: float) -> float:
    """Clamp evidence strength to [0, 1] to maintain compatibility."""
    return max(0.0, min(1.0, value))


def compute_score(
    signals: Mapping[str, float],
    configs: Iterable[EvidenceConfig],
    bias: float = 0.0,
) -> float:
    """
    Compute forensic-style suspicion score S ∈ [0,1].
    This function is optional and not used by the default CLI.
    """
    weighted_sum = 0.0
    for cfg in configs:
        strength = normalize_signal(signals.get(cfg.name, 0.0))
        contribution = cfg.weight * strength
        log_debug(f"signal={cfg.name}, strength={strength}, weight={cfg.weight}, contrib={contribution}")
        weighted_sum += contribution

    weighted_sum += bias
    score = sigmoid(weighted_sum)
    log_debug(f"weighted_sum={weighted_sum}, bias={bias}, score={score}")
    return score


@dataclass
class Thresholds:
    """
    阈值分层配置，供未来判定高嫌疑/预警/常态。
    """

    high: float = 0.8
    medium: float = 0.5


def evaluate_score(score: float, thresholds: Thresholds = Thresholds()) -> str:
    """
    将得分映射到分层标签；仅作为可选接口，不影响主流程。
    """
    if score >= thresholds.high:
        return "high_suspicion"
    if score >= thresholds.medium:
        return "warning"
    return "normal"


# --- Feature group definitions (for documentation and optional future use) ---
FEATURE_GROUPS: Sequence[FeatureGroup] = [
    FeatureGroup(
        name="L1_connection_auth",
        meaning="ADB 上线/鉴权成功与是否具备高权限通道",
        fusion_form="子特征向量 -> 强度分数 φ1(L1)",
        sub_features=[
            "has_adbd_auth",
            "functions_has_adb",
            "adbd_root_hint",
            "adb_over_tcp_hint",
        ],
    ),
    FeatureGroup(
        name="L2_power_broadcast",
        meaning="USB 稳定连接的慢速充电窗口，用作时间窗锚点与旁证",
        fusion_form="锚点信号 φ2(L2)",
        sub_features=[
            "plugged_usb_ratio",
            "stable_power_duration",
            "battery_level_slope",
        ],
    ),
    FeatureGroup(
        name="L3_provider_uri",
        meaning="短窗内系统 Provider 被拉起与 URI 授权密集度，反映是否触达敏感数据域",
        fusion_form="强度分数 φ3(L3)",
        sub_features=[
            "distinct_providers_count",
            "uri_grants_count_rate",
            "grant_subject_class",
            "inter_event_cv",
        ],
    ),
    FeatureGroup(
        name="L4_shell_commands",
        meaning="提取型命令族的成簇出现，是否匹配“枚举→导出”模式",
        fusion_form="强度分数 φ4(L4)",
        sub_features=[
            "ngram_match_score",
            "cmd_burst_density",
            "unique_cmd_types",
            "priv_exec_hint",
        ],
    ),
]


def fuse_signals(
    signals: Mapping[str, float],
    configs: Iterable[EvidenceConfig],
    bias: float = 0.0,
    thresholds: Thresholds = Thresholds(),
) -> Dict[str, float | str]:
    """
    轻量融合示例：S = σ(w1 φ1(L1) + ... + w4 φ4(L4) + b)
    返回得分与分层标签，保持为可选接口，主流程仍未启用。
    """
    score = compute_score(signals, configs, bias=bias)
    label = evaluate_score(score, thresholds)
    return {"score": score, "label": label}


def run_analysis(
    signals: Mapping[str, float],
    configs: Iterable[EvidenceConfig],
    bias: float = 0.0,
    thresholds: Thresholds = Thresholds(),
    enabled: bool = False,
) -> Dict[str, float | str] | None:
    """
    可选入口：仅在 enabled=True 时执行融合，否则返回 None。
    目的：为未来接入主流程预留接口，默认不影响现有输出。
    """
    if not enabled:
        log_debug("Forensic analysis disabled; skipping")
        return None
    return fuse_signals(signals, configs, bias=bias, thresholds=thresholds)
