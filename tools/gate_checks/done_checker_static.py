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
- Part B (`run_finalize_selfcheck`): the 3 post-Finalize conditions confirming Finalize's own
  migration actually landed (stored_artifacts/ complete and staging_artifacts/ gone, ticket moved
  to tickets/done/, exactly one working_log row). Called directly via `bash(...)` from the
  Finalize phase in `implement-ticket.js`; a FAIL here produces the one new status this ticket
  introduces, `FINALIZE_INCOMPLETE`.

Both parts live in one module because both are static checks for the same `done-checker` gate,
just invoked at different pipeline points (see SEQUENCE.md decision 1).

Mirrors `tools/parity_ledger_scan.py` / `tools/registry_query.py`'s shape: plain functions, plain
tuple returns, no argparse/CLI — consumed exclusively via `python3 -c "..."`.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from validate_frontmatter import validate_file, validate_directory  # noqa: E402

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


def check_data_runs_clean(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
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
            # A missing/unparsable start_ts is not evidence of cleanliness — flag any file found
            # rather than silently passing (per investigation's resolved recommendation).
            if start_epoch is None or f.stat().st_mtime >= start_epoch:
                flagged.append(str(f))

    if flagged:
        return ("FAIL", f"File(s) at/after start_ts (or start_ts unparsable): {', '.join(flagged)}")
    return ("PASS", f"{runs_dir} and {proof_dir} clean of this session's artifacts")


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

    ticket_errors = validate_file(ticket_path)

    if tier == "hotfix" and not staging_dir.exists():
        if ticket_errors:
            return ("FAIL", "; ".join(ticket_errors))
        return ("NA", "hotfix tier — no staging artifacts to validate")

    # staging_artifacts/ paths do not auto-detect as `artifact` content type (only
    # stored_artifacts/ does) — must pass content_type_override explicitly or this silently
    # falls through to `doc`'s looser required-field set.
    results = validate_directory(staging_dir, content_type_override="artifact")
    artifact_errors = [err for errs in results.values() for err in errs]

    all_errors = ticket_errors + artifact_errors
    if all_errors:
        return ("FAIL", "; ".join(all_errors))
    return ("PASS", f"Frontmatter valid for {ticket_path} and {staging_dir}")


def run_static_precheck(ticket_id: str, tier: str, start_ts: str | None) -> list[dict]:
    """Aggregate all 5 Part A checks. Returns one dict per check, in this fixed order, matching
    `DONE_SCHEMA.checklist`'s own item shape so the agent can transcribe directly. Does not
    collapse to a single boolean — per-check detail must survive.
    """
    checks = (
        ("staging_artifacts_complete", check_staging_artifacts_complete(ticket_id, tier)),
        ("data_runs_clean", check_data_runs_clean(start_ts)),
        ("ticket_location", check_ticket_location(ticket_id)),
        ("working_log_no_row_yet", check_working_log_no_row_yet(ticket_id)),
        ("frontmatter_valid", check_frontmatter_valid(ticket_id, tier)),
    )
    return [
        {"condition": name, "status": status, "evidence": evidence}
        for name, (status, evidence) in checks
    ]


# Substring unique to validate_frontmatter.py's tag-registry-membership rejection message (via
# tools/tag_registry.py's canonical_form_violation / is_tag_registered) — confirmed via
# `grep -rn "is not in the tag registry" tools/` to not collide with any other validation error
# text (canonical-form, forbidden-priority-tag, and synonym-map messages all read differently).
_TAG_REGISTRY_REJECTION_MARKER = "is not in the tag registry"


def classify_checklist_failure(checklist: list[dict]) -> str | None:
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

    Not invoked directly by `implement-ticket.js`'s orchestrator via subprocess — passing
    `doneCheck.checklist`'s arbitrary evidence text (which can contain quotes and backticks, e.g.
    from `validate_frontmatter.py`'s own error messages) through a shell command risks exactly the
    quote-corruption failure mode that file's `p0ScanOutput` comment already documents. Instead,
    `implement-ticket.js` has a hand-synced JS mirror of this exact logic
    (`classifyChecklistFailure`, same marker string). This Python function remains the tested
    reference implementation the JS mirror must match, and is directly reusable by any future
    offline/retro tooling that wants to re-classify a historical checklist.
    """
    for item in checklist:
        if item.get("status") == "FAIL":
            if _TAG_REGISTRY_REJECTION_MARKER in item.get("evidence", ""):
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


def run_finalize_selfcheck(ticket_id: str, tier: str) -> list[dict]:
    """Aggregate all 3 Part B checks. Same return shape as `run_static_precheck`."""
    checks = (
        ("migration_complete", check_migration_complete(ticket_id, tier)),
        ("ticket_finalized", check_ticket_finalized(ticket_id)),
        ("working_log_exactly_one_row", check_working_log_exactly_one_row(ticket_id)),
    )
    return [
        {"condition": name, "status": status, "evidence": evidence}
        for name, (status, evidence) in checks
    ]
