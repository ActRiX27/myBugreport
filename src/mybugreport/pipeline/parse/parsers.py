"""Parsers for converting logs into LogRecord entries."""

import re
from pathlib import Path
from typing import Iterable, List, Tuple

from ...models import LogRecord

ParsedRecord = Tuple[LogRecord, bool]

THREADTIME_RE = re.compile(
    r"^(?P<date>\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\s+"
    r"(?P<pid>\d+)\s+(?P<tid>\d+)\s+(?P<level>[VDIWEF])\s+"
    r"(?P<tag>[^:]+):\s*(?P<msg>.*)$"
)

DMESG_RE = re.compile(r"^<(?P<level>\d+)>?\[?(?P<ts>\d+\.\d+)\]?\s*(?P<msg>.*)$")
DMESG_ALT_RE = re.compile(r"^\[(?P<ts>\d+\.\d+)\]\s*(?P<msg>.*)$")


def parse_logcat_threadtime_line(line: str) -> ParsedRecord:
    line = line.rstrip("\n")
    m = THREADTIME_RE.match(line)
    if not m:
        return LogRecord(ts=None, level=None, tag=None, msg=line, raw=line, source="logcat"), False
    ts = f"{m.group('date')} {m.group('time')}"
    msg = m.group("msg")
    tag = m.group("tag")
    level = m.group("level")
    return (
        LogRecord(
            ts=ts,
            level=level,
            tag=tag,
            msg=msg,
            raw=line,
            source="logcat",
        ),
        True,
    )


def parse_dmesg_line(line: str) -> ParsedRecord:
    line = line.rstrip("\n")
    for regex in (DMESG_RE, DMESG_ALT_RE):
        m = regex.match(line)
        if m:
            ts = m.group("ts")
            msg = m.group("msg")
            level = m.groupdict().get("level")
            return (
                LogRecord(
                    ts=ts,
                    level=level,
                    tag="dmesg",
                    msg=msg,
                    raw=line,
                    source="dmesg",
                ),
                True,
            )
    return LogRecord(ts=None, level=None, tag="dmesg", msg=line, raw=line, source="dmesg"), False


BUGREPORT_INFO_KEYS = [
    "Build fingerprint:",
    "Kernel Version:",
    "Kernel version",
]


def _try_parse_enriched(line: str) -> ParsedRecord:
    """
    Try to parse bugreport lines using existing logcat/dmesg parsers to enrich level/tag fields.
    Returns (record, parsed_ok).
    """
    parsers = (
        parse_logcat_threadtime_line,
        parse_dmesg_line,
    )
    for parser in parsers:
        rec, parsed = parser(line)
        if parsed:
            # Normalize source to bugreport while preserving parsed metadata.
            rec.source = "bugreport"
            return rec, True
    return LogRecord(ts=None, level=None, tag="bugreport", msg=line.rstrip("\n"), raw=line.rstrip("\n"), source="bugreport"), False


def parse_bugreport_lines(lines: Iterable[str]) -> List[LogRecord]:
    records: List[LogRecord] = []
    in_dropbox = False
    dropbox_tag = "dropbox"
    for line in lines:
        raw = line.rstrip("\n")
        parsed_rec, parsed = _try_parse_enriched(raw)
        if parsed:
            records.append(parsed_rec)
            continue
        # Build info lines
        if any(key in raw for key in BUGREPORT_INFO_KEYS):
            records.append(
                LogRecord(ts=None, level=None, tag="build_info", msg=raw, raw=raw, source="bugreport")
            )
            continue
        # Dropbox section heuristics
        if raw.startswith("==== dropbox entries"):
            in_dropbox = True
            records.append(LogRecord(ts=None, level=None, tag=dropbox_tag, msg=raw, raw=raw, source="bugreport"))
            continue
        if in_dropbox:
            if raw.startswith("====") and "entries" not in raw:
                in_dropbox = False
            else:
                records.append(LogRecord(ts=None, level=None, tag=dropbox_tag, msg=raw, raw=raw, source="bugreport"))
                continue
        # Fallback: store raw lines with minimal tagging
        records.append(LogRecord(ts=None, level=None, tag="bugreport", msg=raw, raw=raw, source="bugreport"))
    return records
