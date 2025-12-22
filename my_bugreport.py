"""
Command entry point for myBugReport.
This script keeps the original CLI contract but delegates work to modular helpers
for better maintainability and future extensibility.
"""

import sys

from mybugreport.config import RULE2_FILE, RULE_FILE
from mybugreport.processor import (
    apply_translations_and_time,
    extract_context_sections,
    extract_section_with_rules,
)
from mybugreport.rules import load_translation_pairs, read_section_rule
from mybugreport.time_utils import (
    parse_time,
    replace_time_strings_in_line as replace_time_strings_in_file,
)
from mybugreport.io_utils import validate_inputs

# Backward-compatible global state retained for callers that rely on it.
pairs = {}


def execute_commands(dates, input_file, output_file, num_context_lines):
    """
    Main entry point that preserves original behavior while allowing optional configurability.
    """
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


if __name__ == "__main__":
    dates = sys.argv[1:-3]
    input_file = sys.argv[-3]
    output_file = sys.argv[-2]
    # 如果行数参数未输入，使用默认值
    if len(sys.argv) > 4:
        num_context_lines = sys.argv[-1]
    else:
        num_context_lines = '1'  # 默认值: 上下各一行

    execute_commands(dates, input_file, output_file, num_context_lines)
