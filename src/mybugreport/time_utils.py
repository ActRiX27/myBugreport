"""
Time parsing utilities kept compatible with the original script.
"""

import re
from typing import List

from .config import log_debug


def parse_time(time_str):
    time_str = time_str.strip()

    day = 0
    hour = 0
    minute = 0
    second = 0
    ms = 0

    matches = re.findall(r'(-?\d+)(d|h|m|s|ms)', time_str)

    for val, unit in matches:
        val = int(val)
        if unit == 'd':
            day = val
        elif unit == 'h':
            hour = val
        elif unit == 'm':
            minute = val
        elif unit == 's':
            second = val
        elif unit == 'ms':
            ms = val

    time_parts: List[str] = []
    if day:
        time_parts.append(f'{day}天')
    if hour:
        time_parts.append(f'{hour}小时')
    if minute:
        time_parts.append(f'{minute}分钟')
    if second:
        time_parts.append(f'{second}秒')
    if ms:
        time_parts.append(f'{ms}毫秒')

    return ''.join(time_parts)


def replace_time_strings_in_line(line: str) -> str:
    regex = r"(-?\d+d|-?\d+h|-?\d+m|-?\d+s|-?\d+ms)"
    matches = re.findall(regex, line)

    for match_str in matches:
        time_length = parse_time(match_str)
        line = line.replace(match_str, str(time_length))
    line = re.sub(r'(\d+)分钟s', r'\1毫秒', line)
    return line
