#!/usr/bin/env python3
"""Read-only baseline inventory of agent-monitoring/*.jsonl
(TCK-20260721-BASELINE-MONITORING-MANIFEST).

Streams each of runs.jsonl/events.jsonl/tools.jsonl in a single line-lazy pass —
never a full read_text()/read()/readlines() of the whole file — to compute a
line count, byte size, SHA-256 hash, parser result, and legacy-warning count per
file. Prints a JSON array to stdout by default; never writes into
agent-monitoring/ itself.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from legacy_reader import classify_provenance  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

_FILES_BY_SOURCE = {
    "events.jsonl": "events",
    "runs.jsonl": "runs",
    "tools.jsonl": "tools",
}


def _scan_file(path: Path, source: str) -> dict:
    parsed_ok = 0
    parse_errors = 0
    legacy_warning_count = 0
    hasher = hashlib.sha256()

    with open(path, "rb") as f:
        for line_bytes in f:
            hasher.update(line_bytes)
            stripped = line_bytes.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            parsed_ok += 1
            labels = classify_provenance(record, source)
            if labels and labels != frozenset({"interactive_null"}):
                legacy_warning_count += 1

    return {
        "file": path.name,
        "line_count": parsed_ok + parse_errors,
        "byte_size": path.stat().st_size,
        "sha256": hasher.hexdigest(),
        "parser_result": {"parsed_ok": parsed_ok, "parse_errors": parse_errors},
        "legacy_warning_count": legacy_warning_count,
    }


def build_manifest(agent_monitoring_dir: Path) -> list:
    records = []
    for filename, source in sorted(_FILES_BY_SOURCE.items()):
        records.append(_scan_file(agent_monitoring_dir / filename, source))
    return records


def capture_lines(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    """Return raw monitoring-file lines in their original order without writing.

    Line-lazy single-pass read (matches _scan_file's own streaming technique) — never a full
    read_text()/read()/readlines() of the whole file, per this module's own documented invariant.
    """
    result: dict[str, list[str]] = {}
    for filename in _FILES_BY_SOURCE:
        path = agent_monitoring_dir / filename
        lines: list[str] = []
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                lines.append(line)
        result[filename] = lines
    return result


def assert_prefix_preserved(pre: dict[str, list[str]], post: dict[str, list[str]]) -> None:
    """Reject rewrites, reorders, or deletions of pre-existing monitoring lines."""
    for filename, pre_lines in pre.items():
        post_lines = post.get(filename, [])
        if post_lines[: len(pre_lines)] != pre_lines:
            raise AssertionError(
                f"{filename}: pre-existing lines were rewritten/reordered/deleted "
                f"(pre-snapshot had {len(pre_lines)} lines; post-snapshot's prefix does not match)"
            )


def _assert_safe_output_path(path: Path) -> None:
    resolved = path.resolve()
    real_monitoring_dir = _AGENT_MONITORING_DIR.resolve()
    if resolved == real_monitoring_dir or real_monitoring_dir in resolved.parents:
        raise ValueError(
            f"refusing to write manifest output under the real agent-monitoring/ "
            f"directory: {resolved}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="optional path to also write the JSON output to")
    args = parser.parse_args()

    records = build_manifest(_AGENT_MONITORING_DIR)
    output = json.dumps(records, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
