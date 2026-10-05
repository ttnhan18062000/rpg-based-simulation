#!/usr/bin/env python3
"""tools/agent-monitoring/manual_actions.py: the session-layer headline metric, manual orchestration actions
(TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT; plan docs/plans/agent_infrastructure/
session_layer_working_process.md section 11).

The metric counts CATEGORIES OF REPEATED INSTRUCTION the owner types to keep sessions on track: role reminder,
routing correction, manual wake, worktree correction, boundary reminder, handover recovery. It does NOT count
decisions, design feedback or new requirements; a raw count of prompts is explicitly not the metric.

Tagging method (M0j, verified: `UserPromptSubmit` carries `prompt`, `session_id`, `session_title`, so the hook can
sample): a deliberately CONSERVATIVE phrase tagger. A prompt is tagged only when a short, imperative message
matches a category phrase; anything long (more than MAX_PROMPT_CHARS), a question-led message or one that matches
nothing is untagged, so decisions and requirements fall out. It under-counts rather than over-counts. The
authoritative fallback and correction channel is the owner-side tally (`tally` subcommand): one line per batch.

PRIVACY: only the category, timestamp, session id and resolved role are recorded, never the prompt text. Records go
to `agent-working/agent-monitoring/data/<iso-week>/manual_actions.jsonl` (own file family, like `role_boundary`).
Never raises; a failure to record never blocks a prompt.

  python3 tools/agent-monitoring/manual_actions.py hook            # UserPromptSubmit hook: payload on stdin
  python3 tools/agent-monitoring/manual_actions.py tally <category> [--batch BATCH] [--count N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

CATEGORIES = (
    "role_reminder", "routing_correction", "manual_wake", "worktree_correction", "boundary_reminder",
    "handover_recovery",
)
MAX_PROMPT_CHARS = 300
_PATTERNS: dict[str, tuple[str, ...]] = {
    "handover_recovery": (
        r"\b(re-?read|read|check|use|follow)\b[^.\n]{0,30}\b(your |the )?handover\b",
        r"\bcontinue as\b",
        r"\bresume (from|as|your)\b[^.\n]{0,30}\bhandover\b",
    ),
    "role_reminder": (
        r"\byou are (the |an? )?[\w-]*(implementer|planner|designer|reviewer)\b",
        r"\bremember (that )?you are\b",
        r"\byour (role|seat) is\b",
        r"\bact as (the |an? )?[\w-]*(implementer|planner|designer)\b",
    ),
    "routing_correction": (
        r"\b(send|ask|route|take|bring)\b[^.\n]{0,40}\b(to|via|through|with)\b[^.\n]{0,20}\b(the )?(planner|designer|implementer)\b",
        r"\b(ask|tell)\b[^.\n]{0,15}\b(the )?(planner|designer|implementer)\b[^.\n]{0,15}\b(not|instead of)\b[^.\n]{0,10}\b(me|the user)\b",
        r"\bnot (to )?me\b[^.\n]{0,25}\b(planner|designer|implementer)\b",
        r"\bwrong (seat|session|recipient|owner)\b",
    ),
    "manual_wake": (
        r"\b(wake|ping|nudge|poke)\b[^.\n]{0,25}\b(up|the|your|\w+-(implementer|planner|designer))\b",
        r"\bcheck (on|with) (the |your )?[\w-]*(implementer|planner|designer)\b",
        r"\bany (update|news|reply|response) from\b",
        r"\b(did|has|have) (it|they|the \w+) (reply|replied|respond|responded|answer|answered)\b",
    ),
    "worktree_correction": (
        r"\bwrong (worktree|branch|directory|dir|checkout)\b",
        r"\b(use|switch to|go to|work in|cd (in)?to)\b[^.\n]{0,15}\b(the |your )?(own )?worktree\b",
        r"\bnot (in|on) (the |your )?(shared|main|primary) (tree|worktree|checkout|directory)\b",
    ),
    "boundary_reminder": (
        r"\b(that|this)('s| is| isn't| is not) (not )?(yours|your (job|domain|seat|area|files?))\b",
        r"\bstay in (your )?(lane|domain|role)\b",
        r"\b(not|outside) your (domain|lane|scope|ownership)\b",
        r"\b(don'?t|do not) (edit|touch|change)\b[^.\n]{0,30}\b(not yours|other (domain|seat)|someone else'?s)\b",
    ),
}
_COMPILED = {cat: tuple(re.compile(p, re.IGNORECASE) for p in pats) for cat, pats in _PATTERNS.items()}
_QUESTION_LED = re.compile(r"^\W*(should|can|could|would|what|why|how|which|do you|does|is there|are there)\b", re.IGNORECASE)


def tag_prompt(prompt: str) -> str | None:
    """The category of a repeated-instruction prompt, or None (decision, feedback, requirement, anything long)."""
    text = (prompt or "").strip()
    if not text or len(text) > MAX_PROMPT_CHARS or _QUESTION_LED.match(text):
        return None
    for category in CATEGORIES:
        if any(rx.search(text) for rx in _COMPILED[category]):
            return category
    return None


def _write(record: dict, data_dir: Path | None = None) -> bool:
    try:
        from tools.agent_working_paths import AGENT_MONITORING
        from writer import write_line

        base = Path(data_dir) if data_dir is not None else Path(AGENT_MONITORING) / "data"
        target = base / datetime.now(timezone.utc).strftime("%G-W%V") / "manual_actions.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        return bool(write_line(target, json.dumps(record, separators=(",", ":"))))
    except Exception:  # noqa: BLE001
        return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def record_prompt(payload: dict, data_dir: Path | None = None) -> dict | None:
    """Sample one UserPromptSubmit payload; writes (and returns) a record only for a tagged prompt. Never raises."""
    try:
        category = tag_prompt(str(payload.get("prompt") or ""))
        if category is None:
            return None
        from session_role import resolve_session_role

        sid = str(payload.get("session_id") or "")
        record = {"ts": _now(), "category": category, "source": "sample", "session_id": sid or None,
                  "session_role": resolve_session_role(sid, str(payload.get("cwd") or ".")), "batch": None, "count": 1}
        _write(record, data_dir)
        return record
    except Exception:  # noqa: BLE001
        return None


def record_tally(category: str, batch: str | None = None, count: int = 1, data_dir: Path | None = None) -> dict:
    """The owner-side tally: authoritative, so it is recorded as typed. Raises ValueError for an unknown category."""
    if category not in CATEGORIES:
        raise ValueError(f"unknown category {category!r}; known: {', '.join(CATEGORIES)}")
    if count < 1:
        raise ValueError("count must be at least 1")
    record = {"ts": _now(), "category": category, "source": "tally", "session_id": None,
              "session_role": None, "batch": batch, "count": count}
    _write(record, data_dir)
    return record


def count_by_category(records: list[dict]) -> dict[str, dict[str, int]]:
    """`{category: {"sample": n, "tally": n}}` for every category (zeros included). Unknown categories are dropped."""
    out = {c: {"sample": 0, "tally": 0} for c in CATEGORIES}
    for r in records:
        cat, src = r.get("category"), r.get("source")
        if cat in out and src in out[cat]:
            out[cat][src] += int(r.get("count") or 1)
    return out


def main(argv: list[str] | None = None, stdin=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hook")
    tally = sub.add_parser("tally")
    tally.add_argument("category", choices=CATEGORIES)
    tally.add_argument("--batch")
    tally.add_argument("--count", type=int, default=1)
    args = parser.parse_args(argv)
    if args.cmd == "hook":
        try:
            payload = json.loads((stdin or sys.stdin).read())
            if isinstance(payload, dict):
                record_prompt(payload)
        except Exception:  # noqa: BLE001 - a hook must never block a prompt
            pass
        return 0
    try:
        record = record_tally(args.category, args.batch, args.count)
    except ValueError as exc:
        print(f"tally: {exc}", file=sys.stderr)
        return 2
    print(f"tallied {record['count']} x {record['category']}" + (f" for {record['batch']}" if record["batch"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
