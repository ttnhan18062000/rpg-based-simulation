"""Deterministic per-entry test_path verification for the `mechanics-auditor` agent.

Built for TCK-20260705-GATE-DET-MECHANICS-AUDITOR: `mechanics-auditor` renders a `PARITY` verdict
for a parity-ledger entry (ledger `status: verified`) purely on LLM judgment today — nothing checks
whether the entry's cited `test_path` actually exists and passes. This module gives the agent's own
"Checking Parity" step a deterministic backstop for that narrow question: does the cited `test_path`
exist and currently pass? It never decides whether the code itself diverges from the Mechanics
Bible — that remains the agent's own bit-identical comparison.

Scoped strictly to explicit entry ID(s) the agent is actively rendering a verdict for in the current
session — never a ledger-wide sweep (82% of `status: verified` entries have no `test_path` at all;
see investigation.md, so a bulk run would produce a wall of unrelated FAILs unrelated to any actual
regression).

Mirrors `tools/gate_checks/parity_updater_static.py` / `tools/gate_checks/done_checker_static.py`'s
shape: plain functions, plain tuple/dict returns, no argparse/CLI — consumed exclusively via
`python3 -c "..."`.
"""

import re
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import yaml
from parity_ledger_scan import CANONICAL_LEDGER_FILES  # noqa: E402
from gate_checks.parity_updater_static import expected_subsystems_for_files  # noqa: E402

_BACKTICK_FULL_RE = re.compile(r"^`([^`]+)`$")
_DELIM_SPLIT_RE = re.compile(r"\s*[,+;]\s*")
_NODE_ID_RE = re.compile(r"^[\w./\-]+\.py(::[\w \[\]./:\-]+)?$")


def _strip_full_backtick(s: str) -> str:
    match = _BACKTICK_FULL_RE.match(s)
    return match.group(1) if match else s


def parse_test_path_citations(raw) -> "tuple[list[str] | None, str | None]":
    """Parse a ledger entry's raw `test_path` string into a list of invocable citations.

    Returns (citations, None) on success, or (None, error) on a hard-FAIL/unparseable case. Never
    raises. Handles the four legacy shapes found in the real ledger (investigation.md's format
    survey): clean node-id, single backtick-wrapped, comma/`+`/`;`-joined multi-citation, and
    unparseable parenthetical-annotated prose.
    """
    if raw is None or not str(raw).strip():
        return (None, "test_path is null/missing")

    stripped = str(raw).strip()
    parts = _DELIM_SPLIT_RE.split(stripped)

    if len(parts) > 1:
        resolved = []
        for part in parts:
            candidate = _strip_full_backtick(part.strip())
            if not _NODE_ID_RE.match(candidate):
                return (
                    None,
                    "unparseable test_path (multi-citation candidate but one segment did not "
                    f"resolve to a clean path): {raw!r}",
                )
            resolved.append(candidate)
        return (resolved, None)

    candidate = _strip_full_backtick(stripped)
    if _NODE_ID_RE.match(candidate):
        return ([candidate], None)

    return (None, f"unparseable test_path: {raw!r}")


def check_test_path(test_path_raw, base_dir: Path = Path(".")) -> "tuple[str, str]":
    """Verify every citation in test_path_raw exists on disk and passes when run scoped, alone.

    Checks ALL citations in a multi-citation string (not just the first) — a single failing
    citation among several still fails the overall result. Every citation's individual verdict is
    visible in the returned evidence string. Never raises.
    """
    citations, err = parse_test_path_citations(test_path_raw)
    if citations is None:
        return ("FAIL", err)

    results = []
    for citation in citations:
        file_part = citation.split("::", 1)[0]
        if file_part.startswith("tests_v2/"):
            results.append((
                citation,
                "FAIL",
                "legacy path, tests_v2/ directory does not exist in this repo: " + citation,
            ))
            continue

        target_path = Path(base_dir) / file_part
        if not target_path.exists():
            results.append((citation, "FAIL", f"file does not exist: {target_path}"))
            continue

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", citation, "-x", "-q"],
                cwd=str(base_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except Exception as exc:
            results.append((citation, "FAIL", f"error invoking pytest: {exc}"))
            continue

        if proc.returncode == 0:
            results.append((citation, "PASS", f"{citation} passed"))
        else:
            output = (proc.stdout + proc.stderr)[-2000:]
            results.append((
                citation,
                "FAIL",
                f"{citation} failed (exit {proc.returncode}): {output}",
            ))

    overall = "FAIL" if any(status == "FAIL" for _, status, _ in results) else "PASS"
    evidence = "; ".join(f"{citation}: {msg}" for citation, _, msg in results)
    return (overall, evidence)


def find_entry(entry_id: str, ledger_dir="docs/parity_ledger") -> "tuple[dict | None, str | None]":
    """Return (entry, filename) for the first canonical ledger file containing entry_id.

    Returns the instant a match is found — never collects or surfaces information about any other
    entry encountered while scanning. Skips a file silently if it doesn't exist, and skips (continues
    past) any file that fails to parse as YAML — legacy-data tolerance, mirrors
    `parity_updater_static.derive_mapping`'s own `except Exception: continue`.
    """
    ledger_path = Path(ledger_dir)
    for filename in CANONICAL_LEDGER_FILES:
        path = ledger_path / filename
        if not path.exists():
            continue
        try:
            entries = yaml.safe_load(path.read_text()) or []
        except Exception:
            continue
        for entry in entries:
            if entry.get("id") == entry_id:
                return (entry, filename)
    return (None, None)


def verify_entry_test_path(
    entry_id: str, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")
) -> dict:
    """Look up entry_id in the canonical ledger files and verify its test_path. Scoped to exactly
    this one entry — never reports on sibling entries in the same YAML file."""
    entry, filename = find_entry(entry_id, ledger_dir)
    if entry is None:
        return {
            "entry_id": entry_id,
            "status": "FAIL",
            "evidence": f"entry {entry_id} not found in any canonical ledger file under {ledger_dir}",
            "verified_by": ["static:mechanics_auditor_static"],
        }

    status, evidence = check_test_path(entry.get("test_path"), base_dir)
    return {
        "entry_id": entry_id,
        "ledger_file": filename,
        "status": status,
        "evidence": evidence,
        "verified_by": ["static:mechanics_auditor_static"],
    }


def verify_entries(
    entry_ids, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")
) -> list:
    """Verify a small explicit set of entry IDs. Does not change verify_entry_test_path's
    single-entry contract — this satisfies the ticket Scope's "a set of entries" wording."""
    return [verify_entry_test_path(eid, ledger_dir, base_dir) for eid in entry_ids]


def candidate_ledger_files_for_module(src_files, ledger_dir="docs/parity_ledger") -> dict:
    """Discover which ledger YAML file(s) a set of `src/` files are cited in, for the case where
    `mechanics-auditor` is auditing an entire mechanics chapter/module rather than a single named
    entry ID and needs to know which subsystem file(s) to load candidate entries from, before it has
    entry IDs to pass to verify_entry_test_path. A direct pass-through reuse of
    `parity_updater_static.expected_subsystems_for_files` — this is the only genuinely reusable piece
    from that module for this ticket (it solves a different problem, git-diff-vs-ledger
    cross-reference, with zero test-execution logic; `derive_mapping`/`cross_reference_touched` are
    not reused beyond this discovery step)."""
    return expected_subsystems_for_files(src_files, ledger_dir)


def audit_verified_by_claims(rows, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")) -> list:
    """Post-hoc cross-check of a mechanics-auditor agent's own self-reported `verified_by` claims
    against an independently recomputed Step 0 result. Scoped strictly to the rows passed in — never
    a ledger-wide sweep (see module docstring).

    Each item in `rows` is one row of a mechanics-auditor agent's own output table, shaped:
        {"entry_id": str, "status": <agent's PARITY|DIVERGENT|MISSING|UNDOCUMENTED classification>,
         "verified_by": list[str], "Finding": str (optional, default "")}

    Only rows whose underlying parity-ledger entry has ledger status == "verified" are evaluated —
    Step 0 is mandatory only for that branch per .claude/agents/mechanics-auditor.md's "Checking
    Parity" section. Rows mapping to missing/divergent/unsupported/legacy_verified ledger entries, or
    to an entry_id not found at all, are skipped entirely: never flagged, never included in the
    returned list.

    Returns a list of dicts, one per evaluated row:
        {"entry_id": str, "honesty_status": "PASS" | "FAIL", "evidence": str}
    `honesty_status` reuses this module's own existing PASS/FAIL vocabulary (see check_test_path /
    verify_entry_test_path) rather than inventing a new status string, and is never named
    "status"/"Status" — it must never be read as, or substituted for, the agent's own
    PARITY/DIVERGENT/MISSING/UNDOCUMENTED classification for entry_id.
    """
    results = []
    for row in rows:
        entry_id = row.get("entry_id")
        entry, _filename = find_entry(entry_id, ledger_dir)
        if entry is None or entry.get("status") != "verified":
            continue

        claimed_static = "static:mechanics_auditor_static" in (row.get("verified_by") or [])
        finding_text = str(row.get("Finding") or "")

        if not claimed_static:
            results.append({
                "entry_id": entry_id,
                "honesty_status": "FAIL",
                "evidence": (
                    f"ledger status is 'verified' (Step 0 is mandatory) but row's verified_by "
                    f"{row.get('verified_by')!r} omits 'static:mechanics_auditor_static' — Step 0 "
                    "appears to have been skipped."
                ),
            })
            continue

        recompute = verify_entry_test_path(entry_id, ledger_dir, base_dir)
        if recompute["status"] == "FAIL" and "FAIL" not in finding_text.upper():
            results.append({
                "entry_id": entry_id,
                "honesty_status": "FAIL",
                "evidence": (
                    "row claims static corroboration but a fresh recompute of "
                    f"verify_entry_test_path returned FAIL ({recompute['evidence']}) with no FAIL "
                    "caveat disclosed in the row's Finding text — falsely cited static PASS."
                ),
            })
            continue

        results.append({
            "entry_id": entry_id,
            "honesty_status": "PASS",
            "evidence": f"verified_by claim corroborated by fresh recompute: {recompute['evidence']}",
        })

    return results
