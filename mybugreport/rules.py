"""
Rule loading and escaping helpers.
These keep the original rule formats while providing extension points.
"""

from typing import Dict, Tuple

from .config import (
    ALLOW_MISSING_RULES,
    RULE2_FILE,
    RULE_FILE,
    VALIDATION_ENABLED,
    log_debug,
)
from .io_utils import read_lines


def read_section_rule(file_path: str = RULE2_FILE) -> Tuple[str, str]:
    """
    Read section extraction rule (two colon-separated patterns).
    """
    lines = read_lines(
        file_path,
        description="section rules",
        validate=VALIDATION_ENABLED,
        allow_missing=ALLOW_MISSING_RULES,
    )
    if not lines:
        log_debug("Section rules missing or empty; skipping extraction")
        return "", ""
    start, end = lines[0].strip().split(":")
    return start, end


def load_translation_pairs(file_path: str = RULE_FILE) -> Dict[str, str]:
    """
    Parse key/value replacements with tolerance for malformed lines.
    """
    log_debug(f"Loading translation rules from {file_path}")
    local_pairs: Dict[str, str] = {}
    for line in read_lines(
        file_path,
        description="translation rules",
        validate=VALIDATION_ENABLED,
        allow_missing=ALLOW_MISSING_RULES,
    ):
        try:
            key, value = line.strip().split(':')
            local_pairs[key] = value
        except ValueError:
            log_debug(f"Skipping malformed rule line: {line.strip()}")
            pass  # 如果不能正确分割就跳过
    if not local_pairs:
        log_debug("Translation rules missing or empty; nothing to replace")
    return local_pairs


def escape_pattern(pattern: str) -> str:
    """Escape delimiters for awk-compatible regex usage."""
    return (
        pattern.replace('.', '\\.')
        .replace('/', '\\/')
        .replace('{', '\\{')
        .replace('}', '\\}')
    )
