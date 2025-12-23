"""
CLI entry for myBugReport, reusable as a library function.
Preserves original behavior and output format.
"""

import sys

from .config import RULE2_FILE, RULE_FILE
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
from .io_utils import validate_inputs

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
