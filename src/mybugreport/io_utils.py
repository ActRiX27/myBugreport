"""
I/O utilities with optional validation hooks (default no-op for compatibility).
"""

import os
from typing import List

import sys

from .config import (
    CHECK_OUTPUT_NONEMPTY,
    VALIDATION_ENABLED,
    WARN_ON_MISSING_RULES,
    log_debug,
)


def read_lines(
    path: str,
    description: str = "file",
    validate: bool = VALIDATION_ENABLED,
    allow_missing: bool = False,
) -> List[str]:
    """
    Read all lines from a file with optional preflight validation.
    Purpose: future-proof hook for stricter checks without altering default behavior.
    """
    if not os.path.exists(path):
        if allow_missing:
            log_debug(f"{description} missing but allowed: {path}")
            if WARN_ON_MISSING_RULES:
                sys.stderr.write(f"[WARN] {description} missing (allowed): {path}\n")
            return []
        if validate:
            raise FileNotFoundError(f"{description} not found: {path}")
    log_debug(f"Reading {description} from {path}")
    with open(path, "r") as file:
        return file.readlines()


def validate_inputs(paths, description="input paths", validate: bool = VALIDATION_ENABLED):
    """
    Optional input existence validation for CLI入口（默认关闭以保持兼容）。
    """
    if not validate:
        return
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"{description} missing: {', '.join(missing)}")


def check_output_nonempty(path: str) -> None:
    """
    Optional output consistency check (默认关闭)，确保输出文件非空。
    """
    if not CHECK_OUTPUT_NONEMPTY:
        return
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        sys.stderr.write(f"[WARN] output file is empty or missing: {path}\n")
