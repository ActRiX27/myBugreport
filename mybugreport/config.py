"""
Configuration and debug helpers.
All settings remain optional and backward compatible via environment variables.
"""

import os
import sys
from typing import Iterable

# Optional debug logging (default off) for future troubleshooting / extensibility
DEBUG_ENABLED = os.environ.get("MYBUGREPORT_DEBUG", "").lower() in {"1", "true", "yes"}

# Configurable rule file paths (keep defaults for backward compatibility)
RULE_FILE = os.environ.get("MYBUGREPORT_RULE_FILE", "rule.txt")
RULE2_FILE = os.environ.get("MYBUGREPORT_SECTION_RULE_FILE", "rule2.txt")

# Optional strict validation (default off) to allow future preflight checks without changing behavior
VALIDATION_ENABLED = os.environ.get("MYBUGREPORT_STRICT_VALIDATION", "").lower() in {"1", "true", "yes"}

# Optional tolerance for missing rule files (default off). Purpose: future-proof graceful degradation.
ALLOW_MISSING_RULES = os.environ.get("MYBUGREPORT_ALLOW_MISSING_RULES", "").lower() in {"1", "true", "yes"}

# Optional warning when rules are missing but tolerance is enabled (default off)
WARN_ON_MISSING_RULES = os.environ.get("MYBUGREPORT_WARN_ON_MISSING_RULES", "").lower() in {"1", "true", "yes"}

# Optional output consistency check (default off) to validate generated files in strict scenarios
CHECK_OUTPUT_NONEMPTY = os.environ.get("MYBUGREPORT_CHECK_OUTPUT_NONEMPTY", "").lower() in {"1", "true", "yes"}


def log_debug(message: str) -> None:
    """Minimal debug logger (no-op by default).
    Controlled via MYBUGREPORT_DEBUG environment variable.
    """
    if DEBUG_ENABLED:
        sys.stderr.write(f"[DEBUG] {message}\n")


def debug_iterable(name: str, values: Iterable[str]) -> None:
    """Structured debug for iterable values (future extensibility hook)."""
    if DEBUG_ENABLED:
        joined = ", ".join(values)
        log_debug(f"{name}: [{joined}]")
