"""Analyze stage: derive findings from normalized records."""

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ...models import Finding
from ...utils import read_jsonl, write_json, write_jsonl

LEVEL_ORDER = {"V": 0, "D": 1, "I": 2, "W": 3, "E": 4, "F": 5}


def summarize_records(records_path: Path, output_path: Path) -> List[Finding]:
    records = read_jsonl(Path(records_path))
    count = len(records)
    evidence = {"records": count}
    confidence = 0.0 if count == 0 else min(1.0, 0.2 + 0.05 * count)
    finding = Finding(
        rule_id="baseline.count",
        severity="info" if count else "none",
        evidence=evidence,
        confidence=confidence,
        summary="Record count placeholder for downstream analysis",
    )
    write_json([finding], Path(output_path))
    return [finding]


def load_rules(rules_dir: Path) -> List[Dict]:
    rules: List[Dict] = []
    for path in Path(rules_dir).glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                rules.append(data)
            elif isinstance(data, list):
                rules.extend(data)
        except Exception:
            continue
    return rules


def _level_ok(level: Optional[str], threshold: Optional[str]) -> bool:
    if threshold is None or not threshold:
        return True
    if level is None:
        return False
    return LEVEL_ORDER.get(level, -1) >= LEVEL_ORDER.get(threshold, -1)


def _condition_ok(record: Dict, cond: Optional[Dict]) -> bool:
    if not cond:
        return True
    if "tag" in cond:
        tags = cond["tag"]
        if isinstance(tags, str):
            tags = [tags]
        if record.get("tag") not in tags:
            return False
    if "level_gte" in cond:
        if not _level_ok(record.get("level"), cond["level_gte"]):
            return False
    return True


def _match_record(record: Dict, match: Dict) -> bool:
    text = f"{record.get('msg','')} {record.get('raw','')}"
    if not match:
        return False
    keywords = match.get("keywords") or []
    regexes = match.get("regex") or []
    for kw in keywords:
        if kw.lower() in text.lower():
            return True
    for pattern in regexes:
        try:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


def analyze_with_rules(records_path: Path, rules_dir: Path, out_dir: Path) -> Tuple[Path, Path]:
    records = read_jsonl(Path(records_path))
    rules = load_rules(rules_dir)
    findings: List[Finding] = []
    evidence_lines: List[Dict] = []
    build_info_lines: List[Dict] = []
    dropbox_entries: List[Dict] = []
    source_counts = _source_counts(records)
    level_counts = _level_counts(records)
    tag_counts = _tag_counts(records)

    for rule in rules:
        rid = rule.get("rule_id", "unknown")
        title = rule.get("title", rid)
        severity = rule.get("severity", "info")
        desc = rule.get("description")
        match = rule.get("match", {})
        cond = rule.get("condition", {})
        evidence_limit = rule.get("evidence_limit", 20)

        hit_records = []
        for rec in records:
            if not _condition_ok(rec, cond):
                continue
            if _match_record(rec, match):
                hit_records.append(rec)

        if not hit_records:
            continue

        for rec in hit_records[:evidence_limit]:
            evidence_lines.append(
                {
                    "rule_id": rid,
                    "ts": rec.get("ts"),
                    "level": rec.get("level"),
                    "tag": rec.get("tag"),
                    "source": rec.get("source"),
                    "raw": rec.get("raw"),
                }
            )

        confidence = min(1.0, 0.2 + 0.05 * len(hit_records))
        finding = Finding(
            rule_id=rid,
            severity=severity,
            evidence={"hits": len(hit_records), "sources": _source_counts(hit_records)},
            confidence=confidence,
            summary=title or desc,
        )
        findings.append(finding)

    # Baseline: capture build fingerprint/info lines if present (optional enrichment).
    for rec in records:
        if (rec.get("tag") or "").lower() == "build_info" or rec.get("raw", "").startswith("Build fingerprint"):
            build_info_lines.append(rec)
        if (rec.get("tag") or "").lower() == "dropbox":
            dropbox_entries.append(rec)

    if build_info_lines:
        first = build_info_lines[0]
        evidence_lines.append(
            {
                "rule_id": "build.fingerprint",
                "ts": first.get("ts"),
                "level": first.get("level"),
                "tag": first.get("tag"),
                "source": first.get("source"),
                "raw": first.get("raw"),
            }
        )
        findings.append(
            Finding(
                rule_id="build.fingerprint",
                severity="info",
                evidence={"fingerprint": first.get("raw"), "count": len(build_info_lines)},
                confidence=0.1,
                summary="Build fingerprint detected",
            )
        )
    if dropbox_entries:
        first = dropbox_entries[0]
        evidence_lines.append(
            {
                "rule_id": "dropbox.entries",
                "ts": first.get("ts"),
                "level": first.get("level"),
                "tag": first.get("tag"),
                "source": first.get("source"),
                "raw": first.get("raw"),
            }
        )
        findings.append(
            Finding(
                rule_id="dropbox.entries",
                severity="info",
                evidence={"entries": len(dropbox_entries)},
                confidence=min(1.0, 0.05 * len(dropbox_entries)),
                summary="Dropbox entries detected",
            )
        )
    # Baseline record statistics (always available, low severity).
    findings.append(
        Finding(
            rule_id="baseline.stats",
            severity="info",
            evidence={"total": len(records), "sources": source_counts, "levels": level_counts},
            confidence=0.05 if records else 0.0,
            summary="Record statistics",
        )
    )
    if tag_counts:
        findings.append(
            Finding(
                rule_id="baseline.top_tags",
                severity="info",
                evidence={"top_tags": tag_counts},
                confidence=0.05,
                summary="Top log tags by count",
            )
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = Path(out_dir) / "findings.json"
    evidence_path = Path(out_dir) / "findings_evidence.jsonl"
    write_json(findings, findings_path)
    write_jsonl(evidence_lines, evidence_path)
    return findings_path, evidence_path


def _source_counts(records: Iterable[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rec in records:
        counts[rec.get("source")] = counts.get(rec.get("source"), 0) + 1
    return counts


def _level_counts(records: Iterable[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rec in records:
        level = rec.get("level") or "unknown"
        counts[level] = counts.get(level, 0) + 1
    return counts


def _tag_counts(records: Iterable[Dict], limit: int = 5) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rec in records:
        tag = rec.get("tag") or "unknown"
        counts[tag] = counts.get(tag, 0) + 1
    # Return top N to keep evidence concise
    sorted_pairs = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return {k: v for k, v in sorted_pairs if v > 0}


__all__ = ["summarize_records", "analyze_with_rules", "load_rules"]
