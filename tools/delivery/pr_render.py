"""Renders a PR title and body from the ticket files on the current branch, instead of composing
them by hand each time (TCK-20260924-DELIVERY-PR-RENDERER).

The organising idea (plan.md §3.1): the PR title and body are *rendered* from the tickets already
on the branch, not separately authored. Everything above `## Review notes` in the body comes from
ticket content; `## Review notes` is never generated — see its own docstring note below.

Consumes `tools/delivery/pr_template_spec.json` (from `TCK-20260924-DELIVERY-CONTRACT-AND-
TEMPLATES`) for the section list/order rather than hardcoding it, so the renderer and
`.github/pull_request_template.md` cannot disagree.

**Title format**: always `"<scope>: <text> (<N> ticket(s))"`, for every N >= 1. Plan §3.5's
abstract template shows a bare `<scope>: <what landed>` for a single ticket with no count suffix,
but its own three worked real-repo examples (PRs #240, #237, #229) — including the two
single-ticket ones — all end with `(1 ticket)`/`(N tickets)`. This module follows the worked
examples, per the ticket's own Implementation Notes instruction to use them as fixtures, rather
than the abstract block's single-ticket shorthand.

**`## Verification` reads each ticket's own recorded `## Test Summary`/`## Completion Summary`
text, never a live re-run of `done_checker_static.py`.** A live re-run reflects the *current*
working tree (e.g. `data_runs_clean` scans `data/runs/` as it exists right now, which drifts
constantly in a shared worktree), not what was true when that ticket actually closed. The ticket's
own recorded text is the historically accurate answer a PR reviewer wants. "Known gaps" is a literal
scan for the substring `FAIL` in those two sections, surfacing the containing line — formalizing the
convention this repo's own tickets already use by hand.

**Ticket discovery**: commit-subject `TCK-` IDs (`git log <base>..HEAD --format=%s`) are the
*primary* signal (Scope item 2); ticket IDs implied by changed paths under `tickets/` are a
secondary, reconciling signal. A mismatch between the two is reported as a warning, never resolved
silently — the render still uses the commit-subject set.

Out of scope, deliberately: opening/editing/posting to a PR (`gh pr create`/`gh pr edit` remain
user-authorized actions taken deliberately, never a side effect of rendering), ticket IDs in the
title (settled: `Closes:` in the body only), any attribution trailer (structurally absent, not
merely omitted — no `Co-Authored-By`, no session link, no "Generated with" line, ever), generating
`## Review notes` (if it can be generated it is not review), and rewriting ticket content to make a
better body (a thin Request Summary renders a thin body — that is the correct, honest signal).
`--check` never exits non-zero for a real difference; only a genuine internal error does.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from tools.validate_frontmatter import extract_frontmatter
    from tools.generate_registry import parse_body_section, _strip_frontmatter
    from tools.delivery.pr_status import CommandResult, default_run_command
except ImportError:
    # Fallback for direct script execution (`python3 tools/delivery/pr_render.py`), where `tools/`
    # has no __init__.py and isn't a namespace package relative to the invocation's own sys.path[0].
    _TOOLS_DIR = Path(__file__).resolve().parent.parent
    if str(_TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR))
    if str(_TOOLS_DIR / "delivery") not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR / "delivery"))
    from validate_frontmatter import extract_frontmatter  # noqa: E402
    from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402
    from pr_status import CommandResult, default_run_command  # noqa: E402

_TICKET_ID_RE = re.compile(r"TCK-[0-9]{8}-[A-Z0-9-]+")
_REVIEW_NOTES_PLACEHOLDER = "<!-- UNFILLED: write review notes by hand before opening the PR -->"
_DEFAULT_SPEC_PATH = Path("tools/delivery/pr_template_spec.json")
_DEFAULT_TICKETS_ROOT = Path("tickets")
_DEFAULT_LAYER_REGISTRY = Path("registries/layer_registry.jsonl")


def _dedup_preserve_order(items: list) -> list:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def discover_commit_ticket_ids(run_command=default_run_command, base_ref: str = "origin/main") -> list:
    result = run_command(["git", "log", f"{base_ref}..HEAD", "--format=%s"])
    if result.returncode != 0:
        return []
    ids = []
    for line in result.stdout.splitlines():
        ids.extend(_TICKET_ID_RE.findall(line))
    return _dedup_preserve_order(ids)


def discover_changed_ticket_ids(run_command=default_run_command, base_ref: str = "origin/main") -> list:
    result = run_command(["git", "diff", "--name-only", f"{base_ref}..HEAD", "--", "tickets/"])
    if result.returncode != 0:
        return []
    ids = []
    for line in result.stdout.splitlines():
        ids.extend(_TICKET_ID_RE.findall(line))
    return _dedup_preserve_order(ids)


def find_ticket_file(ticket_id: str, tickets_root: Path = _DEFAULT_TICKETS_ROOT) -> Optional[Path]:
    matches = sorted(tickets_root.rglob(f"{ticket_id}.md"))
    return matches[0] if matches else None


def load_ticket(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text) or {}
    body = _strip_frontmatter(text)
    return {
        "ticket_id": fm.get("ticket_id") or path.stem,
        "layer": fm.get("layer"),
        "title": parse_body_section(body, "Title"),
        "tier": parse_body_section(body, "Tier"),
        "request_summary": parse_body_section(body, "Request Summary"),
        "test_summary": parse_body_section(body, "Test Summary"),
        "completion_summary": parse_body_section(body, "Completion Summary"),
        "path": path,
    }


def discover_tickets(
    run_command=default_run_command,
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
    base_ref: str = "origin/main",
):
    """Returns (tickets, warnings). `tickets` follows commit-subject discovery order (the primary
    signal); `warnings` names any mismatch against the changed-files signal, and any commit-subject
    ID with no matching ticket file anywhere under `tickets_root`."""
    commit_ids = discover_commit_ticket_ids(run_command, base_ref)
    changed_ids = discover_changed_ticket_ids(run_command, base_ref)

    warnings = []
    commit_set, changed_set = set(commit_ids), set(changed_ids)
    if commit_set != changed_set:
        only_commits = sorted(commit_set - changed_set)
        only_changed = sorted(changed_set - commit_set)
        parts = []
        if only_commits:
            parts.append(f"in commit subjects but no changed ticket file: {only_commits}")
        if only_changed:
            parts.append(f"changed ticket file but no commit-subject mention: {only_changed}")
        warnings.append("commit-subject/changed-file ticket ID mismatch — " + "; ".join(parts))

    tickets = []
    for ticket_id in commit_ids:
        path = find_ticket_file(ticket_id, tickets_root)
        if path is None:
            warnings.append(f"{ticket_id}: no ticket file found under {tickets_root}/")
            continue
        tickets.append(load_ticket(path))
    return tickets, warnings


def _load_layer_registry(path: Path = _DEFAULT_LAYER_REGISTRY) -> set:
    if not path.exists():
        return set()
    layers = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            layers.add(json.loads(line)["layer"])
        except (json.JSONDecodeError, KeyError):
            continue
    return layers


def choose_scope(tickets: list, layer_registry_path: Path = _DEFAULT_LAYER_REGISTRY):
    """Most-common layer among `tickets`; ties broken by first-discovered order. Returns
    (scope, tie_warning_or_None, unregistered_warning_or_None)."""
    if not tickets:
        return None, None, None

    counts = {}
    order = []
    for t in tickets:
        layer = t.get("layer")
        if layer not in counts:
            counts[layer] = 0
            order.append(layer)
        counts[layer] += 1

    max_count = max(counts.values())
    tied = [layer for layer in order if counts[layer] == max_count]
    scope = tied[0]
    tie_warning = None
    if len(tied) > 1:
        tie_warning = f"scope tie among layers {tied}; picked {scope!r} (first-discovered)"

    registry = _load_layer_registry(layer_registry_path)
    unregistered_warning = None
    if registry and scope not in registry:
        unregistered_warning = f"scope {scope!r} is not in {layer_registry_path} — reported, not defaulted"

    return scope, tie_warning, unregistered_warning


def extract_known_gaps(ticket: dict) -> list:
    gaps = []
    for section in ("test_summary", "completion_summary"):
        for line in ticket.get(section, "").splitlines():
            if "FAIL" in line:
                gaps.append(line.strip().lstrip("-").strip())
    return gaps


def render_title(tickets: list, scope: str, theme: Optional[str] = None) -> str:
    n = len(tickets)
    unit = "ticket" if n == 1 else "tickets"
    if theme is not None:
        text = theme
    elif n == 1:
        text = tickets[0]["title"]
    else:
        text = tickets[0]["title"]  # stated default (investigation.md #6) — not real synthesis
    return f"{scope}: {text} ({n} {unit})"


def _first_paragraph(text: str) -> str:
    return text.split("\n\n", 1)[0].strip()


def _render_section(heading: str, tickets: list, warnings: list) -> str:
    if heading == "## What landed":
        if len(tickets) == 1:
            return _first_paragraph(tickets[0]["request_summary"])
        return "\n".join(f"- {t['ticket_id']}: {t['title']}" for t in tickets)
    if heading == "## Tickets":
        rows = "\n".join(
            f"| {t['ticket_id']} | {t['tier']} | {t['title']} |" for t in tickets
        )
        return "| ticket | tier | title |\n|---|---|---|\n" + rows
    if heading == "## Why":
        return "\n\n".join(
            f"**{t['ticket_id']}**: {_first_paragraph(t['request_summary'])}" for t in tickets
        )
    if heading == "## Verification":
        lines = []
        for t in tickets:
            lines.append(f"- {t['ticket_id']} Tests: {t['test_summary'] or '(none recorded)'}")
        gaps = [gap for t in tickets for gap in extract_known_gaps(t)]
        lines.append(f"- Known gaps: {'; '.join(gaps) if gaps else 'none stated'}")
        if warnings:
            lines.append(f"- Discovery warnings: {'; '.join(warnings)}")
        return "\n".join(lines)
    if heading == "## Review notes":
        return _REVIEW_NOTES_PLACEHOLDER
    return ""


def render_body(tickets: list, spec: dict, warnings: list) -> str:
    parts = []
    for section in spec["sections"]:
        heading = section["heading"]
        if heading == "Closes:":
            continue
        parts.append(heading)
        parts.append(_render_section(heading, tickets, warnings))
        parts.append("")
    ids = ", ".join(t["ticket_id"] for t in tickets)
    parts.append(f"Closes: {ids}")
    return "\n".join(parts).strip() + "\n"


def render(
    theme: Optional[str] = None,
    base_ref: str = "origin/main",
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
    spec_path: Path = _DEFAULT_SPEC_PATH,
    layer_registry_path: Path = _DEFAULT_LAYER_REGISTRY,
    run_command=default_run_command,
) -> dict:
    tickets, warnings = discover_tickets(run_command, tickets_root, base_ref)
    if not tickets:
        return {"title": None, "body": None, "warnings": warnings + ["no tickets discovered"]}

    scope, tie_warning, unregistered_warning = choose_scope(tickets, layer_registry_path)
    for w in (tie_warning, unregistered_warning):
        if w:
            warnings.append(w)

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    title = render_title(tickets, scope, theme)
    body = render_body(tickets, spec, warnings)
    return {"title": title, "body": body, "warnings": warnings}


def check_against_live(pr: Optional[str] = None, run_command=default_run_command, **render_kwargs) -> dict:
    pr_args = ["pr", "view", "--json", "title,body"]
    if pr:
        pr_args.insert(2, str(pr))
    result = run_command(["gh"] + pr_args)
    if result.returncode != 0:
        return {"matches": None, "error": f"could not fetch live PR: {result.stderr.strip()[:300]}"}
    try:
        live = json.loads(result.stdout)
    except (ValueError, TypeError):
        return {"matches": None, "error": "gh pr view returned unparseable output"}

    rendered = render(run_command=run_command, **render_kwargs)
    title_diff = None if live.get("title") == rendered["title"] else (live.get("title"), rendered["title"])
    body_diff = None if live.get("body") == rendered["body"] else "body differs"
    return {"matches": title_diff is None and body_diff is None, "title_diff": title_diff, "body_diff": body_diff}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a PR title/body from the ticket files on the current branch. "
        "Read-only: writes nothing, never calls gh pr create/edit."
    )
    parser.add_argument("--pr", default=None, help="PR number, used only by --check")
    parser.add_argument("--theme", default=None)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.check:
            result = check_against_live(pr=args.pr, theme=args.theme, base_ref=args.base_ref)
        else:
            result = render(theme=args.theme, base_ref=args.base_ref)
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print("MARKER:" + json.dumps(result))
    elif args.check:
        print(f"matches: {result['matches']}")
        if result.get("title_diff"):
            print(f"title differs: live={result['title_diff'][0]!r} rendered={result['title_diff'][1]!r}")
        if result.get("body_diff"):
            print("body differs")
        if result.get("error"):
            print(f"error: {result['error']}")
    else:
        print(f"TITLE: {result['title']}\n")
        print(result["body"] or "")
        for w in result["warnings"]:
            print(f"WARNING: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
