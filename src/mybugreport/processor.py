"""
Processing pipeline utilities that keep behavior backward compatible
while providing clear extension points for future enhancements.
"""

import subprocess
from typing import Dict, Iterable

from typing import Callable, Optional

from .config import debug_iterable, log_debug
from .io_utils import check_output_nonempty
from .hooks import apply_hooks
from .rules import escape_pattern
from .time_utils import replace_time_strings_in_line


def extract_context_sections(dates: Iterable[str], input_file: str, output_file: str, num_context_lines: str) -> None:
    """Run grep with context around provided timestamps (original behavior)."""
    dates_arg_list = ['-e ' + d for d in dates]
    debug_iterable("date_patterns", dates_arg_list)

    command = ['grep', '-A', num_context_lines, '-B', num_context_lines] + dates_arg_list + [input_file]
    log_debug(f"Running grep command: {' '.join(command)}")
    with open(output_file, "w") as outfile:
        subprocess.run(command, stdout=outfile, shell=False)


def extract_section_with_rules(input_file: str, output_file: str, start_pattern: str, end_pattern: str) -> None:
    """Extract a log section using rule2 patterns via awk (unchanged output)."""
    if not start_pattern or not end_pattern:
        log_debug("Section extraction skipped: missing start/end patterns")
        return
    escaped_start = escape_pattern(start_pattern)
    awk_command = f"awk '/{escaped_start}/ {{p=1; print; next}} /{end_pattern}/ && p {{exit}} p' {input_file}"
    log_debug(f"Running awk command: {awk_command}")
    with open(output_file, "a") as outfile:
        subprocess.run(awk_command, stdout=outfile, shell=True)


def apply_translations_and_time(
    output_file: str,
    replacements: Dict[str, str],
    post_processors: Optional[Iterable[Callable[[str], None]]] = None,
) -> None:
    """Apply keyword translations and time conversions to the output file.

    post_processors: optional callable list for future plugin-style hooks (default no-op).
    """
    with open(output_file, 'r') as file_in:
        lines = file_in.readlines()

    processed_lines = []
    for line in lines:
        updated_line = line
        for key, value in replacements.items():
            updated_line = updated_line.replace(key, value)
            updated_line = replace_time_strings_in_line(updated_line)
        processed_lines.append(updated_line)

    with open(output_file, 'w') as file_out:
        file_out.writelines(processed_lines)

    # Maintain compatibility with previous side-effects
    log_debug("Finished applying translations and time conversions")

    # Optional post-processing hooks for future extensibility (default None)
    apply_hooks(output_file, post_processors)
    check_output_nonempty(output_file)
