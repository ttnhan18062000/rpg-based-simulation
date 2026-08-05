"""Deterministic static pre-checks for the `done-checker` gate.

Built for TCK-20260705-GATE-DET-DONE-CHECKER: `done-checker` (Verify phase, before Finalize)
and Finalize (after its own migration steps) both currently rely entirely on LLM judgment for
conditions that are actually machine-checkable. This module gives both call sites a deterministic
verifier for that subset:

- Part A (`run_static_precheck`): the 5 pre-Finalize conditions `done-checker` can check before
  Finalize has run (staging artifacts complete, data/runs+release_proof clean, ticket still in
  tickets/inprogress/, no working_log row yet, frontmatter valid). Called from the Verify-phase
  agent prompt in `.claude/workflows/implement-ticket.js`; a static FAIL downgrades to the
  existing `DOD_BLOCKED` status — no new status vocabulary here.
- Part B (`run_finalize_selfcheck`): the 4 post-Finalize conditions confirming Finalize's own
  migration actually landed (stored_artifacts/ complete and staging_artifacts/ gone, ticket moved
  to tickets/done/, exactly one working_log row, and — as of TCK-20260709-REGISTRY-REGEN-ON-CLOSE
  — docs/REGISTRY.yaml regenerated with an entry for the closing ticket). Called directly via
  `bash(...)` from the Finalize phase in `implement-ticket.js`; a FAIL here produces the one new
  status this ticket introduces, `FINALIZE_INCOMPLETE`.

Both parts live in one module because both are static checks for the same `done-checker` gate,
just invoked at different pipeline points (see SEQUENCE.md decision 1).

Mirrors `tools/parity_ledger_scan.py` / `tools/registry_query.py`'s shape: plain functions, plain
tuple returns, no argparse/CLI — consumed exclusively via `python3 -c "..."`.
"""

import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from validate_frontmatter import validate_file, validate_directory, extract_frontmatter  # noqa: E402
from generate_registry import generate_registry  # noqa: E402
from ticket_field_values import check_ticket_field_values  # noqa: E402
from tag_registry import load_registry, check_tags_registered  # noqa: E402
from registry_query import candidate_tags_from_text  # noqa: E402

REQUIRED_ARTIFACT_FILES = ("plan.md", "investigation.md", "test_plan.md")


def _files_complete(directory: Path, filenames) -> tuple[bool, list[str]]:
    """Return (all_present_and_nonempty, [missing_or_empty filenames]).

    A file counts as missing/empty if it doesn't exist, or exists but is blank/whitespace-only
    after `.strip()` — "present" alone is not sufficient per the ticket's own AC wording.
    """
    problems = []
    for name in filenames:
        f = directory / name
        if not f.exists() or not f.read_text(encoding="utf-8").strip():
            problems.append(name)
    return (not problems, problems)


def _jsonl_rows_for_run_id(path: Path, run_id: str) -> list[dict]:
    """Return every parsed JSON row in `path` whose run_id == run_id. Malformed lines are
    skipped, not raised — a corrupt line elsewhere in the file must not crash this check."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("run_id") == run_id:
            rows.append(row)
    return rows


def _extract_section_text(ticket_text: str, heading: str) -> str:
    """Return the body text under a `## {heading}` markdown heading, up to the next `## ` heading
    or end of file. Returns "" if the heading is not present. Body-section counterpart to
    `validate_frontmatter.extract_frontmatter()`, which only parses the YAML frontmatter block and
    never reads body sections (see TCK-20260720-TAG-RELEVANCE-VERIFY investigation.md)."""
    marker = f"## {heading}"
    start = ticket_text.find(marker)
    if start == -1:
        return ""
    body_start = start + len(marker)
    next_heading = ticket_text.find("\n## ", body_start)
    end = next_heading if next_heading != -1 else len(ticket_text)
    return ticket_text[body_start:end].strip()


def _count_rows_for_ticket(csv_path: Path, ticket_id: str) -> int:
    """Count rows in csv_path that contain ticket_id in ANY column.

    Deliberately does not use `csv.DictReader` keyed on the header — a confirmed historical bug
    class (`TCK-20260705-WORKING-LOG-BACKFILL`) has rows with `ticket_id` shifted to column 1
    instead of column 2. Scanning every column of every row is the only way to not silently miss
    those malformed rows.
    """
    if not csv_path.exists():
        return 0
    count = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # header row
        for row in reader:
            if ticket_id in row:
                count += 1
    return count


# ---------------------------------------------------------------------------
# Part A — pre-Finalize static pre-check (done-checker / Verify phase)
# ---------------------------------------------------------------------------


def check_staging_artifacts_complete(
    ticket_id: str, tier: str, base_dir: Path = Path("staging_artifacts")
) -> tuple[str, str]:
    if tier == "hotfix":
        return ("NA", "hotfix tier — staging artifacts not required")

    directory = base_dir / ticket_id
    ok, problems = _files_complete(directory, REQUIRED_ARTIFACT_FILES)
    if ok:
        return ("PASS", f"All required files present and non-empty in {directory}")
    return ("FAIL", f"Missing or empty file(s) in {directory}: {', '.join(problems)}")


def _find_flagged_data_run_files(
    start_ts: str | None,
    runs_dir: Path,
    proof_dir: Path,
) -> list[Path]:
    """Shared primitive: the canonical definition of "this session's own file" under
    data/runs/ and reports/release_proof/. A missing/unparsable start_ts is not evidence of
    cleanliness — flags any file found rather than silently passing.

    check_data_runs_clean (PASS/FAIL reporting, Verify-phase backstop) and
    clean_data_runs_early (auto-clean, post-Test checkpoint) both call this exact function so
    the two can never diverge on what counts as flaggable. Do not duplicate this walk anywhere
    else (TCK-20260708-DATA-RUNS-CLEANUP-TIMING).
    """
    start_epoch = None
    if start_ts:
        try:
            start_epoch = datetime.fromisoformat(start_ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            start_epoch = None

    flagged = []
    for directory in (runs_dir, proof_dir):
        if not directory.exists():
            continue
        for f in directory.rglob("*"):
            if not f.is_file():
                continue
            if start_epoch is None or f.stat().st_mtime >= start_epoch:
                flagged.append(f)
    return flagged


def check_data_runs_clean(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
    flagged = _find_flagged_data_run_files(start_ts, runs_dir, proof_dir)
    if flagged:
        return (
            "FAIL",
            f"File(s) at/after start_ts (or start_ts unparsable): "
            f"{', '.join(str(f) for f in flagged)}",
        )
    return ("PASS", f"{runs_dir} and {proof_dir} clean of this session's artifacts")


def clean_data_runs_early(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
    """Auto-clean this session's own data/runs/ + reports/release_proof/ artifacts immediately
    after Test phase, before Parity/Verify ever see them.

    Built for TCK-20260708-DATA-RUNS-CLEANUP-TIMING: closes the ordering gap where
    check_data_runs_clean (Verify, phase 8) ran before Finalize (phase 9, the only prior cleanup
    step) had a chance to remove anything Test phase (test-scoper) had just generated via its own
    pytest run. Invoked directly by the orchestrator (bash() call in implement-ticket.js) between
    Test and Parity — not from within an agent prompt — so it cannot be silently skipped the way
    Finalize step 6's prose cleanup instruction has been.

    Reuses _find_flagged_data_run_files's exact mtime>=start_ts / None-is-flagged definition (the
    same primitive check_data_runs_clean uses) so the two functions can never diverge on what
    counts as "this session's own file." Never a blind rm -rf: only deletes paths that definition
    flags. This guarantees only that artifacts from a session that STARTED BEFORE this session's
    start_ts are left untouched (mtime lower-bound only) — it does NOT protect against a second
    session that is concurrently/overlapping in progress at the moment this checkpoint fires,
    since data/runs/ and reports/release_proof/ have no session/PID partitioning; a file that
    other session writes with mtime >= this session's start_ts is indistinguishable from this
    session's own output and will be deleted. See "Residual Risk: Concurrent-Session Overlap
    Window" in the Anti-Drift Notes below — this is a documented, accepted tradeoff, not a
    mitigated one.

    Returns ("PASS", ...) if nothing needed cleaning, ("CLEANED", "<n> file(s) removed: ...") on
    successful auto-clean, or ("FAIL", "<error>") if deletion itself raised (e.g. permission
    error) — the one case the orchestrator escalates to a new blocking status
    (DATA_RUNS_CLEAN_FAILED) instead of silently continuing.
    """
    flagged = _find_flagged_data_run_files(start_ts, runs_dir, proof_dir)
    if not flagged:
        return ("PASS", f"{runs_dir} and {proof_dir} already clean of this session's artifacts")

    removed = []
    try:
        for f in flagged:
            f.unlink()
            removed.append(str(f))
    except OSError as e:
        remaining = [str(f) for f in flagged if str(f) not in removed]
        return (
            "FAIL",
            f"Auto-clean failed after removing {len(removed)}/{len(flagged)} file(s): {e}. "
            f"Remaining flagged: {', '.join(remaining)}",
        )
    return ("CLEANED", f"{len(removed)} file(s) removed: {', '.join(removed)}")


def check_ticket_location(
    ticket_id: str, inprogress_dir: Path = Path("tickets/inprogress")
) -> tuple[str, str]:
    path = inprogress_dir / f"{ticket_id}.md"
    if path.exists():
        return ("PASS", f"{path} exists")
    return ("FAIL", f"Expected ticket file not found at {path}")


def check_working_log_no_row_yet(
    ticket_id: str, csv_path: Path = Path("tickets/working_log.csv")
) -> tuple[str, str]:
    count = _count_rows_for_ticket(csv_path, ticket_id)
    if count == 0:
        return ("PASS", f"No existing row for {ticket_id} in {csv_path}")
    return (
        "FAIL",
        f"Found {count} row(s) for {ticket_id} in {csv_path} — a pre-existing row at Verify "
        "time — possible duplicate/re-run",
    )


def check_frontmatter_valid(
    ticket_id: str,
    tier: str,
    ticket_path: Path = None,
    staging_dir: Path = None,
) -> tuple[str, str]:
    if ticket_path is None:
        ticket_path = Path(f"tickets/inprogress/{ticket_id}.md")
    if staging_dir is None:
        staging_dir = Path(f"staging_artifacts/{ticket_id}")

    # Load the live registry so _check_tags's registry-membership branch actually runs on this
    # path — without this, an unregistered tag silently PASSes (only canonical-form violations
    # were ever caught here). Mirrors validate_frontmatter.py::main()'s own load_registry() usage.
    registry = load_registry()

    ticket_errors = validate_file(ticket_path, registry=registry)

    if tier == "hotfix" and not staging_dir.exists():
        if ticket_errors:
            return ("FAIL", "; ".join(ticket_errors))
        return ("NA", "hotfix tier — no staging artifacts to validate")

    # staging_artifacts/ paths do not auto-detect as `artifact` content type (only
    # stored_artifacts/ does) — must pass content_type_override explicitly or this silently
    # falls through to `doc`'s looser required-field set.
    results = validate_directory(staging_dir, content_type_override="artifact", registry=registry)
    artifact_errors = [err for errs in results.values() for err in errs]

    all_errors = ticket_errors + artifact_errors
    if all_errors:
        return ("FAIL", "; ".join(all_errors))
    return ("PASS", f"Frontmatter valid for {ticket_path} and {staging_dir}")


def check_ticket_field_values_valid(
    ticket_id: str,
    ticket_path: Path = None,
) -> tuple[str, str]:
    """Adapter: `check_ticket_field_values` (tools/ticket_field_values.py) validates `## Tier`/
    `## Priority` against their canonical enums and returns a single-item `list[dict]`; this
    unwraps it to the `(status, evidence)` tuple shape every other Part A check already returns,
    so it slots into `run_static_precheck`'s existing `checks` tuple unchanged.
    """
    if ticket_path is None:
        ticket_path = Path(f"tickets/inprogress/{ticket_id}.md")
    if not ticket_path.exists():
        return ("FAIL", f"{ticket_path} does not exist — cannot validate Tier/Priority")
    result = check_ticket_field_values(ticket_path)[0]
    return (result["status"], result["evidence"])


_DOCS_BULLET_RE = re.compile(r"^-\s+`(docs/[^`]+)`", re.MULTILINE)
_DOCS_NONE_PHRASES = {"", "none", "none.", "n/a"}
_DOCS_NONE_PREFIX_RE = re.compile(r"^(none|n/a)\.?\s*", re.IGNORECASE)


def _is_none_section(section_text: str) -> bool:
    """True if section_text should be treated as "no docs/ paths flagged."

    Two cases both count:
    1. An exact recognized none-phrase (`_DOCS_NONE_PHRASES`, case-insensitive,
       whitespace-stripped) — the original, still-supported exact form.
    2. A leading "None."/"N/A" prefix (case-insensitive, optional trailing period) followed by
       trailing rationale prose that itself contains no `- \`docs/...\`` bullet line. This
       tolerates the real observed failure mode (TCK-20260804-AGENT-DEF-GAP-FIXES
       investigation, corrected by architecture-review): an investigator writing
       "None. <extra rationale sentence>" instead of exactly "None." — see plan.md's Decision
       section for the confirmed real-ticket evidence (`TCK-20260803-DOCS-STRUCTURE-AUDIT`'s
       own logged Verify-failure text). A "None"-led opening that is in fact followed by a real
       bullet (e.g. "None of the above, but `docs/foo.md` needs updating") still correctly
       requires that path — case 2 only fires when no bullet is found in the remainder.
    """
    stripped = section_text.strip()
    if stripped.lower() in _DOCS_NONE_PHRASES:
        return True
    m = _DOCS_NONE_PREFIX_RE.match(stripped)
    if not m:
        return False
    remainder = stripped[m.end():]
    return _DOCS_BULLET_RE.search(remainder) is None


def _git_touched_paths(root: Path = Path(".")) -> set[str]:
    """Return every path `git status --porcelain` reports as changed, relative to `root`.

    Read-only, fail-open: any subprocess error (missing `git` binary, `root` not a repo, timeout)
    returns an empty set rather than raising — mirrors this module's established fail-open
    convention (e.g. `_find_flagged_data_run_files`'s "unparsable start_ts is not evidence of
    cleanliness" choice: an empty result here means "nothing confirmed touched," which correctly
    fails a coverage check closed rather than silently passing it open).
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()

    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain format: "XY PATH" or "XY PATH1 -> PATH2" for renames — take the rename target.
        rest = line[3:] if len(line) > 3 else line.strip()
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        paths.add(rest.strip())
    return paths


def _path_touched(path: str, touched: set[str]) -> bool:
    """True if `path` is directly in `touched`, or falls under a touched directory entry.

    `git status --porcelain` collapses a wholly-new untracked directory to just the directory
    path with a trailing slash (e.g. `?? docs/newsubsystem/`) rather than listing every file
    inside it individually — a required doc path under such a directory would never exact-match
    `touched` on its own, producing a false FAIL for a case that is, in fact, covered.
    """
    if path in touched:
        return True
    return any(t.endswith("/") and path.startswith(t) for t in touched)


def _parse_docs_to_update(section_text: str) -> list[str]:
    """Extract `docs/` paths from investigation.md's '## Docs Requiring Update' bullet list.

    Requires the tightened format (TCK-20260802-DOC-COVERAGE-CHECK): one bullet per path, each
    starting with `- ` followed immediately by a backtick-wrapped `docs/...` path. Free-text after
    the path (the reason) is not validated — only the leading path token is parsed. Returns `[]`
    for an empty section, a recognized "none applicable" phrase (case-insensitive, exact match), or
    a "None."/"N/A"-prefixed section whose remaining text contains no docs/ bullet — tolerates
    trailing rationale prose after "None." (see `_is_none_section`, TCK-20260804-AGENT-DEF-GAP-FIXES).
    """
    if _is_none_section(section_text):
        return []
    return _DOCS_BULLET_RE.findall(section_text)


def check_docs_to_update_coverage(
    ticket_id: str, tier: str, base_dir: Path = Path("staging_artifacts")
) -> tuple[str, str]:
    """Independently re-verify that every docs/ path Investigate flagged as required was actually
    touched in the final diff — deliberately reads only investigation.md and real git state, NEVER
    any Implement-phase self-report (`behavior_changed`, `files_changed`).

    Built for TCK-20260802-DOC-COVERAGE-CHECK: closes the gap where an implementer wrongly reports
    `behavior_changed=false` for a change that did introduce new logic/features/settings —
    `doc_staleness_check.py`'s gate and its `docs_to_update` advisory (both from
    TCK-20260802-DOC-UPDATE-DISCIPLINE) only ever run when `behavior_changed=true`, so a false
    `false` bypasses both silently. Investigate's `docs_to_update` obligation is derived from ticket
    scope/acceptance criteria, independent of that later self-report, so re-checking it here at
    Verify time — after Architecture-Verify/Test/Parity have already run and the implementation is
    stable — catches this silent-skip case regardless of what the implementer claimed.

    `tier == "hotfix"` → `NA` (no investigation.md exists, same as `check_staging_artifacts_complete`).
    A missing `investigation.md` for standard/epic tier is a `FAIL` — it must exist by Verify time.
    An empty/"None." section is a valid, deliberate judgment call — `PASS`, not `NA`: the section
    itself is still required to exist and be read, just found to have nothing flagged.
    A non-empty section that fails to parse any path is treated as a format regression (`FAIL`),
    not silently passed — this also enforces the tightened bullet format going forward.
    """
    if tier == "hotfix":
        return ("NA", "hotfix tier — no investigation.md, no Docs Requiring Update section")

    investigation_path = base_dir / ticket_id / "investigation.md"
    if not investigation_path.exists():
        return (
            "FAIL",
            f"{investigation_path} does not exist — cannot check docs_to_update coverage",
        )

    text = investigation_path.read_text(encoding="utf-8")
    section_text = _extract_section_text(text, "Docs Requiring Update")
    required_docs = _parse_docs_to_update(section_text)

    if not required_docs:
        if _is_none_section(section_text):
            return ("PASS", "no docs/ paths flagged as requiring update")
        return (
            "FAIL",
            f"'## Docs Requiring Update' section is non-empty but no docs/ path could be parsed "
            f"from it — expected one bullet per path (e.g. '- `docs/x.md`: reason'); "
            f"got: {section_text[:200]!r}",
        )

    touched = _git_touched_paths()
    missing = [d for d in required_docs if not _path_touched(d, touched)]
    if missing:
        return (
            "FAIL",
            f"investigation.md flagged {missing} as requiring an update but git status shows no "
            f"changes to these path(s)",
        )
    return ("PASS", f"all {len(required_docs)} flagged doc path(s) touched: {required_docs}")


def run_static_precheck(ticket_id: str, tier: str, start_ts: str | None) -> list[dict]:
    """Aggregate all 7 Part A checks. Returns one dict per check, in this fixed order, matching
    `DONE_SCHEMA.checklist`'s own item shape so the agent can transcribe directly. Does not
    collapse to a single boolean — per-check detail must survive.
    """
    checks = (
        ("staging_artifacts_complete", check_staging_artifacts_complete(ticket_id, tier)),
        ("data_runs_clean", check_data_runs_clean(start_ts)),
        ("ticket_location", check_ticket_location(ticket_id)),
        ("working_log_no_row_yet", check_working_log_no_row_yet(ticket_id)),
        ("frontmatter_valid", check_frontmatter_valid(ticket_id, tier)),
        ("ticket_field_values_valid", check_ticket_field_values_valid(ticket_id)),
        ("docs_to_update_coverage", check_docs_to_update_coverage(ticket_id, tier)),
    )
    return [
        {"condition": name, "status": status, "evidence": evidence}
        for name, (status, evidence) in checks
    ]


def _frontmatter_has_unregistered_tags(
    ticket_id: str, tier: str, ticket_path: Path = None, staging_dir: Path = None
) -> bool:
    """Independently determine whether ticket_path/staging_dir's declared `tags:` frontmatter
    includes anything not in the live tag registry — calls tag_registry.check_tags_registered()
    directly, zero dependency on validate_frontmatter.py's error TEXT. Mirrors
    check_frontmatter_valid's own path-resolution/hotfix-branching so the two functions agree on
    which files' tags to check, without sharing implementation or return shape.
    """
    if ticket_path is None:
        ticket_path = Path(f"tickets/inprogress/{ticket_id}.md")
    if staging_dir is None:
        staging_dir = Path(f"staging_artifacts/{ticket_id}")

    files = [ticket_path] if ticket_path.exists() else []
    if not (tier == "hotfix" and not staging_dir.exists()):
        files += sorted(staging_dir.rglob("*.md")) if staging_dir.exists() else []

    all_tags: list[str] = []
    for f in files:
        try:
            fm = extract_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if fm and isinstance(fm.get("tags"), list):
            all_tags.extend(fm["tags"])

    return bool(check_tags_registered(all_tags))


def classify_checklist_failure(
    checklist: list[dict], ticket_id: str | None = None, tier: str | None = None
) -> str | None:
    """Return a coarse reason code for the first FAIL entry in a done-checker checklist.

    Built for TCK-20260706-MONITORING-REASON-CODE: `DOD_BLOCKED` is the one gate status
    (`docs/agent-monitoring/schema.md`'s `final_status` values) that collapses many distinct DoD
    conditions into a single value — every other gate status maps 1:1 to a specific phase/meaning
    already. This disambiguates the two currently-evidenced DOD_BLOCKED sub-causes: an unregistered
    tag (`"tag_registry_rejection"`), or anything else (`"dod_condition_failed"`, a deliberately
    coarse fallback — not a full taxonomy of DoD failure reasons, which would be speculative rather
    than evidence-driven). Returns `None` if no entry has `status == "FAIL"`.

    Scans in order and returns on the first FAIL found — if multiple conditions fail
    simultaneously, only the first one's classification is reported (documented behavior, not an
    accident of implementation).

    As of TCK-20260720-TAG-TOUCHPOINT-CLEANUP, classification no longer scans `evidence` text for
    a marker substring (that depended on four layers of string-joining between the actual
    violation and this function, and was dead in practice — see that ticket's investigation.md).
    Instead it matches on the `condition` field (a small closed vocabulary) and, for a
    `frontmatter_valid` FAIL, independently re-derives the cause via
    `_frontmatter_has_unregistered_tags()`, which re-reads the ticket_id/tier's own frontmatter and
    calls `tag_registry.check_tags_registered()` directly. `ticket_id`/`tier` are optional so
    existing callers that only have a `checklist` still get the coarse `dod_condition_failed`
    fallback rather than erroring.

    `implement-ticket.js`'s `classifyChecklistFailure` mirrors this via `bash(python3 -c "...")`,
    shelling out to `_frontmatter_has_unregistered_tags` with `ticket_id`/`tier` as argv — never
    `evidence` text, so the quote-corruption risk that previously kept the JS side a hand-synced
    string-match mirror does not apply to this design.
    """
    for item in checklist:
        if item.get("status") == "FAIL":
            if (
                item.get("condition") == "frontmatter_valid"
                and ticket_id is not None
                and tier is not None
                and _frontmatter_has_unregistered_tags(ticket_id, tier)
            ):
                return "tag_registry_rejection"
            return "dod_condition_failed"
    return None


# ---------------------------------------------------------------------------
# Part B — post-Finalize migration self-check (Finalize phase)
# ---------------------------------------------------------------------------


def check_migration_complete(
    ticket_id: str,
    tier: str,
    staging_dir: Path = None,
    stored_dir: Path = None,
) -> tuple[str, str]:
    if tier == "hotfix":
        return ("NA", "hotfix tier — no migration expected")

    if staging_dir is None:
        staging_dir = Path(f"staging_artifacts/{ticket_id}")
    if stored_dir is None:
        stored_dir = Path(f"stored_artifacts/{ticket_id}")

    ok, problems = _files_complete(stored_dir, REQUIRED_ARTIFACT_FILES)
    if not ok:
        return ("FAIL", f"Missing or empty file(s) in {stored_dir}: {', '.join(problems)}")
    if staging_dir.exists():
        return ("FAIL", f"migration ran but source not cleaned — {staging_dir} still exists")
    return ("PASS", f"{stored_dir} complete and {staging_dir} removed")


def check_ticket_finalized(ticket_id: str) -> tuple[str, str]:
    done_path = Path(f"tickets/done/{ticket_id}.md")
    inprogress_path = Path(f"tickets/inprogress/{ticket_id}.md")

    problems = []
    if not done_path.exists():
        problems.append(f"{done_path} does not exist")
    if inprogress_path.exists():
        problems.append(f"{inprogress_path} still exists")

    if problems:
        return ("FAIL", "; ".join(problems))
    return ("PASS", f"{done_path} exists and {inprogress_path} removed")


def check_working_log_exactly_one_row(
    ticket_id: str, csv_path: Path = Path("tickets/working_log.csv")
) -> tuple[str, str]:
    count = _count_rows_for_ticket(csv_path, ticket_id)
    if count == 1:
        return ("PASS", f"Exactly 1 working_log row found for {ticket_id}")
    if count == 0:
        return ("FAIL", "no working_log row found — Finalize did not append")
    return ("FAIL", f"{count} rows found — duplicate Finalize run")


def check_monitoring_write_recorded(
    ticket_id: str,
    runs_path: Path = Path("agent-monitoring/runs.jsonl"),
    events_path: Path = Path("agent-monitoring/events.jsonl"),
) -> tuple[str, str]:
    """Verify the agent-monitoring write for this run actually landed. Deliberately has no
    `tier` parameter and no NA branch — CLAUDE.md's Hard Rule requires the monitoring write
    "including hotfix," so unlike `check_migration_complete` this applies identically
    regardless of tier; the omission of a tier parameter is itself the design decision.

    Built for TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING: wired into Finalize as a
    loud-but-non-blocking warning (a FAIL here never changes `status` away from `'DONE'`,
    per CLAUDE.md's Hard Rule that a monitoring write failure must never fail the workflow),
    not as a 4th condition in `run_finalize_selfcheck` — see that ticket's plan.md Design
    Decision 2 for why it is wired in separately, at a later call site.
    """
    run_rows = _jsonl_rows_for_run_id(runs_path, ticket_id)
    if not run_rows:
        return ("FAIL", f"No row with run_id == {ticket_id} found in {runs_path}")
    event_rows = _jsonl_rows_for_run_id(events_path, ticket_id)
    if not event_rows:
        return (
            "FAIL",
            f"{runs_path} has a row for {ticket_id} but {events_path} has zero matching rows",
        )
    return (
        "PASS",
        f"{runs_path} ({len(run_rows)} row(s)) and {events_path} ({len(event_rows)} row(s)) "
        f"both have entries for {ticket_id}",
    )


def check_tag_drift(
    ticket_id: str, ticket_path: Path = None
) -> tuple[str, str]:
    """Advisory-only: flags a possible mismatch between the closing ticket's declared `tags:`
    and the tags its own `Files Changed`/`Related Code Areas` body sections would suggest.
    Uses CLEAN/FLAGGED — never PASS/FAIL/NA — so no downstream blocking-status consumer
    (`classify_checklist_failure`, DOD_BLOCKED, FINALIZE_INCOMPLETE) can misread this as a DoD
    condition. Never returns a status that should gate ticket close — callers must not add this
    to run_finalize_selfcheck's checks tuple. Mirrors check_monitoring_write_recorded's
    deliberate placement outside the blocking-checks aggregation.
    """
    resolved_path = ticket_path
    if resolved_path is None:
        resolved_path = Path(f"tickets/done/{ticket_id}.md")
        if not resolved_path.exists():
            resolved_path = Path(f"tickets/inprogress/{ticket_id}.md")
    if not resolved_path.exists():
        return ("CLEAN", f"no ticket file found for {ticket_id} — skipping drift check")

    ticket_text = resolved_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(ticket_text) or {}
    declared_tags = set(frontmatter.get("tags") or [])

    files_changed_text = _extract_section_text(ticket_text, "Files Changed")
    related_code_areas_text = _extract_section_text(ticket_text, "Related Code Areas")
    candidate_tags = candidate_tags_from_text(files_changed_text, related_code_areas_text)

    if not candidate_tags:
        return ("CLEAN", "no candidate tags derivable from Files Changed/Related Code Areas text")

    missing = candidate_tags - declared_tags
    if not missing:
        return (
            "CLEAN",
            f"declared tags cover all derived candidates ({', '.join(sorted(candidate_tags))})",
        )
    return (
        "FLAGGED",
        f"declared tags {sorted(declared_tags)} do not include candidate tag(s) "
        f"{sorted(missing)} suggested by Files Changed/Related Code Areas text",
    )


def check_registry_entry_regenerated(
    ticket_id: str,
    root: Path = Path("."),
    registry_output: Path = Path("docs/REGISTRY.yaml"),
) -> tuple[str, str]:
    """Regenerate docs/REGISTRY.yaml and confirm the closing ticket's entry landed in it.

    Deliberately has no `tier` parameter — same design choice as
    `check_monitoring_write_recorded`: TCK-20260709-REGISTRY-REGEN-ON-CLOSE's AC #1 requires the
    regen to run "on every ticket close, all tiers including hotfix," so the absence of a
    tier-skip branch is itself the mechanism, not an oversight.

    Unlike every sibling `check_*` function in this file, this one is not read-only — calling it
    mutates a tracked file (`registry_output`) as a side effect of "checking." This is a
    deliberate reuse of the existing `run_finalize_selfcheck` call site rather than adding a
    parallel invocation site (see plan.md's Question 2 resolution): `generate_registry()` is
    called directly so the regen and the entry-presence check happen atomically together.

    `generate_registry()`'s own nonzero return (it writes the YAML unconditionally, then returns
    1 only if some *unrelated* doc elsewhere in docs/ is missing frontmatter — see
    `generate_registry.py`'s own docstring) is captured only as informational evidence text, never
    as a cause of FAIL — the only thing that can FAIL here is the closing ticket's own entry being
    absent from the regenerated file. This is AC #2's "write never fails" non-blocking handling.
    """
    resolved_root = root.resolve()
    output_path = registry_output if registry_output.is_absolute() else resolved_root / registry_output

    regen_note = ""
    try:
        exit_code = generate_registry(resolved_root, output_path)
        if exit_code != 0:
            regen_note = f"generate_registry() exited {exit_code} (unrelated doc frontmatter gap)"
    except Exception as exc:  # noqa: BLE001 - regen must never block ticket close
        regen_note = f"generate_registry() raised: {exc}"

    entries = yaml.safe_load(output_path.read_text(encoding="utf-8")) or []
    found = any(
        isinstance(entry, dict) and entry.get("ticket_id") == ticket_id for entry in entries
    )

    if found:
        return (
            "PASS",
            f"{output_path} contains an entry for {ticket_id}"
            + (f" (note: regen exited nonzero: {regen_note})" if regen_note else ""),
        )
    return (
        "FAIL",
        f"{output_path} has no entry for {ticket_id} after regeneration"
        + (f" (regen also exited nonzero: {regen_note})" if regen_note else ""),
    )


def run_finalize_selfcheck(ticket_id: str, tier: str) -> list[dict]:
    """Aggregate all 4 Part B checks. Same return shape as `run_static_precheck`."""
    checks = (
        ("migration_complete", check_migration_complete(ticket_id, tier)),
        ("ticket_finalized", check_ticket_finalized(ticket_id)),
        ("working_log_exactly_one_row", check_working_log_exactly_one_row(ticket_id)),
        ("registry_entry_regenerated", check_registry_entry_regenerated(ticket_id)),
    )
    return [
        {"condition": name, "status": status, "evidence": evidence}
        for name, (status, evidence) in checks
    ]
