"""
Pluggable hook utilities (optional, not used by default).
Purpose: provide future extension points without altering current outputs.
"""

from typing import Callable, Iterable

from .config import log_debug


def apply_hooks(target: str, hooks: Iterable[Callable[[str], None]] | None = None) -> None:
    """Run a list of hooks on the target file path (default no-op)."""
    if not hooks:
        return
    for hook in hooks:
        log_debug(f"Running hook {hook.__name__} on {target}")
        hook(target)


# 示例 Hook（可选，默认未使用）：用于未来扩展时参考
def sample_append_footer(path: str) -> None:
    """
    示例：为输出追加一行标记。未在主流程中调用，避免改变默认输出。
    """
    with open(path, "a") as file:
        file.write("\n# processed by myBugReport (sample hook)\n")
