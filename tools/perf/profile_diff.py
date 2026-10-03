#!/usr/bin/env python3
"""Compare two folded-stack profiles: which functions and phases changed their share of samples most.

Reads two ``profile.folded`` files (as written by ``profile_tick.py``; any folded-stack file works),
and prints, as markdown or JSON, the frames whose share of all samples grew or shrank most, with both
shares. "Phases" are kernel ``_phase_*`` frames and pipeline phase lambdas; everything else is a
function. Shares, not absolute times: a profile explains where cost sits, it does not certify capacity.

    python3 tools/perf/profile_diff.py old.folded new.folded --format md

Pipeline lambdas are identified by file and line, so two profiles from different commits are not
comparable for them; the tool warns when the recorded commits differ.

Ticket: TCK-20261003-PERF-PROFILING-TOOLKIT.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.perf import _profiling_common as common  # noqa: E402


def build_diff(old_text: str, new_text: str, top: int = 15) -> Dict[str, Any]:
    old_header, new_header = common.parse_comment_header(old_text), common.parse_comment_header(new_text)
    diff = common.diff_shares(common.parse_folded(old_text), common.parse_folded(new_text), top=top)
    warnings: List[str] = []
    if old_header.get("commit") and new_header.get("commit") and old_header["commit"] != new_header["commit"]:
        warnings.append("the two profiles were recorded at different commits; pipeline phase lambdas are matched by "
                        "file and line and may not correspond")
    for key in ("scenario", "entities", "seed"):
        if old_header.get(key) and new_header.get(key) and old_header[key] != new_header[key]:
            warnings.append(f"{key} differs between the profiles ({old_header[key]} vs {new_header[key]})")
    if not old_header or not new_header:
        warnings.append("a profile has no PROVISIONAL header, so its provenance is unknown")
    diff["old_header"], diff["new_header"], diff["warnings"] = old_header, new_header, warnings
    return diff


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _table(rows: List[Dict[str, Any]], old_key: str, new_key: str, delta_key: str) -> List[str]:
    if not rows:
        return ["None.", ""]
    out = ["| Frame | Old share | New share | Change |", "|---|---|---|---|"]
    for r in rows:
        frame = r["frame"].replace("|", "\\|")
        out.append(f"| `{frame}` | {_pct(r[old_key])} | {_pct(r[new_key])} | {r[delta_key] * 100:+.2f} pts |")
    out.append("")
    return out


def render_markdown(diff: Dict[str, Any], old_path: str, new_path: str) -> str:
    fields = {"old": old_path, "new": new_path,
              "old_samples": diff["old_samples"], "new_samples": diff["new_samples"],
              "old_commit": diff["old_header"].get("commit", "unknown"),
              "new_commit": diff["new_header"].get("commit", "unknown")}
    out = [common.markdown_header(fields, "Profile difference (share of samples)")]
    for w in diff["warnings"]:
        out.append(f"> WARNING: {w}\n")
    for title, key, old_k, new_k, delta_k in (
        ("Phases: largest inclusive-share increases", "phases_inclusive", "old_inclusive", "new_inclusive", "delta_inclusive"),
        ("Functions: largest self-share increases", "functions_self", "old_self", "new_self", "delta_self"),
        ("Functions: largest inclusive-share increases", "functions_inclusive", "old_inclusive", "new_inclusive", "delta_inclusive"),
    ):
        out += [f"## {title}", ""] + _table(diff[key]["grew"], old_k, new_k, delta_k)
        out += [f"## {title.replace('increases', 'decreases')}", ""] + _table(diff[key]["shrank"], old_k, new_k, delta_k)
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("old", help="folded-stack file recorded first")
    parser.add_argument("new", help="folded-stack file recorded second")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--top", type=int, default=15, help="rows per table")
    args = parser.parse_args(argv)
    try:
        old_text = Path(args.old).read_text(encoding="utf-8")
        new_text = Path(args.new).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read a profile: {exc}", file=sys.stderr)
        return 2
    diff = build_diff(old_text, new_text, args.top)
    if not diff["old_samples"] or not diff["new_samples"]:
        print("a profile contains no samples", file=sys.stderr)
        return 2
    if args.format == "json":
        diff["header"] = common.header_lines({"old": args.old, "new": args.new}, "Profile difference (share of samples)")
        sys.stdout.write(json.dumps(diff, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(render_markdown(diff, args.old, args.new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
