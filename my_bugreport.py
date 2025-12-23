"""
Command entry point for myBugReport.
This script keeps the original CLI contract but delegates work to modular helpers
for better maintainability and future extensibility.
"""

import os
import sys

# Ensure src/ is importable when running from repository root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from mybugreport.cli import execute_commands, main  # noqa: E402


if __name__ == "__main__":
    main()
