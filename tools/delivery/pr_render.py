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
from typing import Dict, Optional

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
# TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION: an intentional exclusion of a commit-
# subject-discovered ticket (e.g. one named only as context in a bookkeeping commit, already
# closed on a prior PR) is recorded as an HTML comment in the rendered body itself, never a
# git-committed file — a committed file would land on `main` at squash-merge and accumulate across
# every PR that ever used it (see this ticket's own investigation.md for the retracted first-pass
# design and why). Same "invisible in GitHub's rendered view, present in raw body text" convention
# `_REVIEW_NOTES_PLACEHOLDER` above already uses.
_EXCLUSION_COMMENT_RE = re.compile(
    r'<!--\s*pr-render:exclude\s+(TCK-[0-9]{8}-[A-Z0-9-]+)\s+reason="([^"]*)"\s*-->'
)
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


def render_exclusion_comment(ticket_id: str, reason: str) -> str:
    """Formats one `pr-render:exclude` HTML comment line -- the single place the literal comment
    shape is written, so `_EXCLUSION_COMMENT_RE` above always matches what this emits.

    Raises `ValueError` if `reason` contains `"` or `-->`, neither of which can be safely embedded
    unescaped in `reason="..."` inside an HTML comment: a `"` truncates `_EXCLUSION_COMMENT_RE`'s
    `[^"]*` capture at the first occurrence, silently dropping the rest of the reason AND the
    exclusion itself on the next round-trip through `extract_recorded_exclusions()` -- with no
    warning anywhere, which recreates the exact "silent, unexplained drift" symptom this ticket
    exists to fix, one level down. A `-->` inside the reason closes the HTML comment early in
    GitHub's own renderer, spilling the remainder as visible text on the rendered PR page. Found
    by design-peer review before this ticket's PR was ever opened, verified directly against this
    module before accepting the finding -- validated here, at the single write path, rather than
    only in the CLI argument parser, so every caller (CLI, `check_against_live()`'s own internal
    re-render, direct test/API use) is protected, not just the interactive `--exclude-reason` flag.
    """
    if '"' in reason:
        raise ValueError(
            f"exclusion reason for {ticket_id!r} contains a double quote, which would silently "
            f"truncate the recorded reason (and drop the exclusion entirely) on the next "
            f"round-trip through extract_recorded_exclusions() -- rewrite the reason without a "
            f'literal " character: {reason!r}'
        )
    if "-->" in reason:
        raise ValueError(
            f"exclusion reason for {ticket_id!r} contains '-->', which would close the HTML "
            f"comment early in GitHub's own renderer and spill the remainder as visible text on "
            f"the rendered PR page -- rewrite the reason without a literal '-->': {reason!r}"
        )
    return f'<!-- pr-render:exclude {ticket_id} reason="{reason}" -->'


def extract_recorded_exclusions(body: str) -> Dict[str, str]:
    """Returns {ticket_id: reason} for every `pr-render:exclude` comment found in `body`. `{}`
    (never raises) if none are present -- the common case, every PR that has never needed one."""
    return dict(_EXCLUSION_COMMENT_RE.findall(body))


def discover_tickets(
    run_command=default_run_command,
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
    base_ref: str = "origin/main",
    exclusions: Optional[Dict[str, str]] = None,
):
    """Returns (tickets, warnings). `tickets` follows commit-subject discovery order (the primary
    signal), minus any ID present in `exclusions`; `warnings` names any mismatch against the
    changed-files signal, any commit-subject ID with no matching ticket file anywhere under
    `tickets_root`, and any excluded ID that was never in the discovered commit-subject set to
    begin with (an exclusion recorded for a ticket that isn't there does nothing, and that fact is
    reported rather than silently ignored).

    The mismatch warning below is computed from the full, unexcluded `commit_ids`/`changed_ids`
    sets -- recording an exclusion changes what gets *rendered*, never whether the underlying
    commit-subject/changed-file disagreement gets *reported* (TCK-20260927-PR-RENDER-NO-RECORDED-
    TICKET-EXCLUSION AC5)."""
    exclusions = exclusions or {}
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

    for excluded_id in sorted(exclusions):
        if excluded_id not in commit_set:
            warnings.append(
                f"{excluded_id}: excluded but not in the discovered commit-subject set — "
                f"exclusion had no effect"
            )

    tickets = []
    for ticket_id in commit_ids:
        if ticket_id in exclusions:
            continue
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
        text = _collapse_whitespace(tickets[0]["title"])
    else:
        # stated default (investigation.md #6) — not real synthesis
        text = _collapse_whitespace(tickets[0]["title"])
    return f"{scope}: {text} ({n} {unit})"


def _first_paragraph(text: str) -> str:
    return text.split("\n\n", 1)[0].strip()


_WHITESPACE_RE = re.compile(r"\s+")


def _collapse_whitespace(text: str) -> str:
    """Collapses all whitespace (including embedded newlines from a ticket's own multi-line `##
    Title` prose) to single spaces, so a value that legitimately wraps across several lines in the
    ticket source still renders as exactly one line wherever one line is required (a table row, a
    bullet)."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def _render_table_cell(text: str) -> str:
    """Collapses whitespace (see `_collapse_whitespace`) and escapes a literal `|`, which would
    otherwise be read as an extra column separator by a markdown table."""
    return _collapse_whitespace(text).replace("|", "\\|")


def _render_section(heading: str, tickets: list, warnings: list) -> str:
    if heading == "## What landed":
        if len(tickets) == 1:
            return _first_paragraph(tickets[0]["request_summary"])
        return "\n".join(f"- {t['ticket_id']}: {_collapse_whitespace(t['title'])}" for t in tickets)
    if heading == "## Tickets":
        rows = "\n".join(
            f"| {_render_table_cell(t['ticket_id'])} | {_render_table_cell(t['tier'])} | "
            f"{_render_table_cell(t['title'])} |"
            for t in tickets
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
        gaps_by_ticket = [(t["ticket_id"], gap) for t in tickets for gap in extract_known_gaps(t)]
        if not gaps_by_ticket:
            lines.append("- Known gaps: none stated")
        else:
            # One bullet per gap, tagged with its owning ticket -- a single semicolon-joined line
            # across tickets left a reader unable to tell where one ticket's gap ended and
            # another's began, or distinguish "one ticket, two gaps" from "two tickets, one gap
            # each" (TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS).
            lines.append("- Known gaps:")
            for ticket_id, gap in gaps_by_ticket:
                lines.append(f"  - {ticket_id}: {gap}")
        if warnings:
            lines.append(f"- Discovery warnings: {'; '.join(warnings)}")
        return "\n".join(lines)
    if heading == "## Review notes":
        return _REVIEW_NOTES_PLACEHOLDER
    return ""


def render_body(tickets: list, spec: dict, warnings: list, exclusions: Optional[Dict[str, str]] = None) -> str:
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
    if exclusions:
        for ticket_id in sorted(exclusions):
            parts.append(render_exclusion_comment(ticket_id, exclusions[ticket_id]))
    return "\n".join(parts).strip() + "\n"


def render(
    theme: Optional[str] = None,
    base_ref: str = "origin/main",
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
    spec_path: Path = _DEFAULT_SPEC_PATH,
    layer_registry_path: Path = _DEFAULT_LAYER_REGISTRY,
    run_command=default_run_command,
    exclusions: Optional[Dict[str, str]] = None,
) -> dict:
    tickets, warnings = discover_tickets(run_command, tickets_root, base_ref, exclusions=exclusions)
    if not tickets:
        return {"title": None, "body": None, "warnings": warnings + ["no tickets discovered"]}

    scope, tie_warning, unregistered_warning = choose_scope(tickets, layer_registry_path)
    for w in (tie_warning, unregistered_warning):
        if w:
            warnings.append(w)

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    title = render_title(tickets, scope, theme)
    body = render_body(tickets, spec, warnings, exclusions=exclusions)
    hints = []
    if theme is None and len(tickets) > 1:
        hints.append(
            f"{len(tickets)} tickets rendered without --theme, so the title names the most "
            "recently closed ticket; pass --theme \"<one-line batch headline>\" (also to --check)."
        )
    return {"title": title, "body": body, "warnings": warnings, "hints": hints}


_CLOSES_RE = re.compile(r"^Closes:\s*(.*)$", re.MULTILINE)
_ANY_H2_RE = re.compile(r"^##\s.+$", re.MULTILINE)


def _extract_closes_line(body: str) -> Optional[str]:
    match = _CLOSES_RE.search(body)
    return match.group(1).strip() if match else None


def parse_generated_sections(body: str, spec: dict) -> dict:
    """Splits `body` back into {heading: content_or_None} for every `##`-prefixed heading in
    `spec["sections"]` (both `rendered: true` and `rendered: false` entries -- callers decide
    which to compare). The structural inverse of `render_body()`'s own construction (heading line,
    then content, then a blank line before the next heading or the trailing `Closes:` line), so
    parsing is exact for anything this renderer itself produced. A heading absent from `body` maps
    to `None` rather than raising, so a hand-edited live body with a missing/reordered section
    degrades to a reportable difference instead of a crash."""
    known_headings = [s["heading"] for s in spec["sections"] if s["heading"].startswith("##")]
    sections = {h: None for h in known_headings}
    current = None
    buffer: list = []

    def flush():
        if current is not None:
            sections[current] = "\n".join(buffer).strip()

    for line in body.splitlines():
        stripped = line.strip()
        if stripped in sections:
            flush()
            current = stripped
            buffer = []
            continue
        if stripped.startswith("Closes:"):
            flush()
            current = None
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    flush()
    return sections


def find_unexpected_sections(body: str, spec: dict) -> list:
    """Every `## ...` heading line in `body` that is not one of `spec`'s known headings --
    reported for visibility, never counted as a difference (a human adding a section to a live PR
    body is normal, not drift; see investigation.md's Open Question 2)."""
    known_headings = {s["heading"] for s in spec["sections"] if s["heading"].startswith("##")}
    return [
        line.strip() for line in _ANY_H2_RE.findall(body)
        if line.strip() not in known_headings
    ]


def compare_generated_body(live_body: str, rendered_body: str, spec: dict) -> dict:
    """Section-aware comparison replacing whole-body string equality (TCK-20260927-PR-RENDER-
    CHECK-ALWAYS-DIFFERS): `## Review notes` (or any `rendered: false` spec section) is never
    compared, since it is permanently, deliberately hand-authored and would otherwise make every
    real PR report a difference regardless of whether the *generated* content had drifted."""
    live_sections = parse_generated_sections(live_body, spec)
    rendered_sections = parse_generated_sections(rendered_body, spec)

    generated_headings = [s["heading"] for s in spec["sections"] if s.get("rendered") and s["heading"].startswith("##")]
    differing = [
        heading for heading in generated_headings
        if _collapse_whitespace(live_sections.get(heading) or "")
        != _collapse_whitespace(rendered_sections.get(heading) or "")
    ]

    live_closes = _extract_closes_line(live_body)
    rendered_closes = _extract_closes_line(rendered_body)
    if _collapse_whitespace(live_closes or "") != _collapse_whitespace(rendered_closes or ""):
        differing.append("Closes:")

    review_heading = next((s["heading"] for s in spec["sections"] if not s.get("rendered")), None)
    live_review = live_sections.get(review_heading) if review_heading else None
    review_notes_hand_filled = bool(live_review) and live_review.strip() != _REVIEW_NOTES_PLACEHOLDER

    return {
        "differing_sections": differing,
        "review_notes_hand_filled": review_notes_hand_filled,
        "unexpected_sections": find_unexpected_sections(live_body, spec),
    }


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

    # AC2/AC3 (TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION): the exclusion set is read
    # from the live body itself, not from any caller-supplied argument -- so a --check run with
    # no operator-supplied flags reproduces whatever was already recorded, and the comparison
    # target is built with the SAME exclusions the live body claims to reflect. `setdefault` means
    # an explicit caller-supplied `exclusions` kwarg is used as-is instead (a caller checking a
    # hypothetical body before any comment exists yet); the common case passes none and gets
    # whatever the live body itself records.
    recorded_exclusions = extract_recorded_exclusions(live.get("body") or "")
    render_kwargs.setdefault("exclusions", recorded_exclusions or None)

    rendered = render(run_command=run_command, **render_kwargs)
    title_diff = None if live.get("title") == rendered["title"] else (live.get("title"), rendered["title"])

    spec_path = render_kwargs.get("spec_path", _DEFAULT_SPEC_PATH)
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    comparison = compare_generated_body(live.get("body") or "", rendered["body"] or "", spec)

    matches = title_diff is None and not comparison["differing_sections"]
    return {
        "matches": matches,
        "title_diff": title_diff,
        "differing_sections": comparison["differing_sections"],
        "review_notes_hand_filled": comparison["review_notes_hand_filled"],
        "unexpected_sections": comparison["unexpected_sections"],
    }


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
    parser.add_argument(
        "--exclude-ticket", action="append", default=[], metavar="TICKET_ID",
        help="Exclude a commit-subject-discovered ticket ID from the rendered body (repeatable). "
             "Ignored by --check, which reads exclusions back from the live PR body instead. "
             "Requires --exclude-reason for each one, in the same order.",
    )
    parser.add_argument(
        "--exclude-reason", action="append", default=[], metavar="TEXT",
        help="Reason text for the corresponding --exclude-ticket, same order, one per exclusion.",
    )
    args = parser.parse_args(argv)

    if len(args.exclude_ticket) != len(args.exclude_reason):
        print(
            "INTERNAL ERROR: --exclude-ticket and --exclude-reason must be given the same "
            f"number of times ({len(args.exclude_ticket)} vs {len(args.exclude_reason)})",
            file=sys.stderr,
        )
        return 1
    exclusions = dict(zip(args.exclude_ticket, args.exclude_reason)) or None

    try:
        if args.check:
            result = check_against_live(pr=args.pr, theme=args.theme, base_ref=args.base_ref)
        else:
            result = render(theme=args.theme, base_ref=args.base_ref, exclusions=exclusions)
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print("MARKER:" + json.dumps(result))
    elif args.check:
        print(f"matches: {result['matches']}")
        if result.get("title_diff"):
            print(f"title differs: live={result['title_diff'][0]!r} rendered={result['title_diff'][1]!r}")
        if "differing_sections" in result:
            if result["differing_sections"]:
                print(f"generated sections differ: {result['differing_sections']}")
            else:
                print("generated sections match")
            if result.get("review_notes_hand_filled"):
                print("(## Review notes is hand-filled, as expected -- not compared)")
            if result.get("unexpected_sections"):
                print(f"unexpected sections in live body (not a failure): {result['unexpected_sections']}")
        if result.get("error"):
            print(f"error: {result['error']}")
    else:
        print(f"TITLE: {result['title']}\n")
        print(result["body"] or "")
        for w in result["warnings"]:
            print(f"WARNING: {w}", file=sys.stderr)
        for h in result.get("hints", []):
            print(f"HINT: {h}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
