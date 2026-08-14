"""Retrospective, read-only audit of stored_artifacts/ migration completeness for done tickets.

Built for TCK-20260705-GATE-DET-DONE-CHECKER Part C. The investigation measured a 39.2% historical
gap (338/862 standard/epic done tickets have an absent or incomplete stored_artifacts/{id}/), still
~23-26% in the two most recent months — a real, ongoing gap, not a negligible curiosity (GO decision,
see stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/investigation.md).

Mirrors `tools/agent-monitoring/validate.py`'s established shape exactly: read-only, disclose-don't-fix,
warn-only (never blocking), no automated exit-code gate tied to findings. Never moves, creates, or
deletes any file — it reports, it does not fix.

Legacy scope guard (explicit, permanent, per direct user instruction — see plan.md's Anti-Drift Notes):
tickets with no parseable `## Tier` field (91 pre-frontmatter-era tickets, e.g. METRICS-01.md) are
skipped with a single WARNING line and never appear in the missing/incomplete counts. This audit does
not classify, infer, or investigate why they lack the field — that is out of scope, permanently.
"""

import sys
from pathlib import Path

_GATE_CHECKS_DIR = Path(__file__).resolve().parent
_TOOLS_DIR = _GATE_CHECKS_DIR.parent
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_registry import parse_body_section  # noqa: E402
from done_checker_static import REQUIRED_ARTIFACT_FILES, _files_complete  # noqa: E402

_EXCLUDED_FILENAMES = {"README.md", "SEQUENCE.md"}
_RECOGNISED_TIERS = {"standard", "epic", "hotfix"}


def scan_done_tickets(done_dir: Path = Path("tickets/done")) -> list[dict]:
    """Walk tickets/done/*.md and tickets/done/{folder}/*.md (excluding README.md/SEQUENCE.md).

    Returns a list of {"ticket_id", "path", "tier"} dicts. `tier` is the lowercased, stripped
    `## Tier` section text, or None if the ticket has no parseable Tier field at all (legacy
    pre-frontmatter-era tickets).
    """
    entries = []
    md_files = sorted(done_dir.glob("*.md")) + sorted(done_dir.glob("*/*.md"))
    for md_file in md_files:
        if md_file.name in _EXCLUDED_FILENAMES:
            continue
        text = md_file.read_text(encoding="utf-8")
        tier_text = parse_body_section(text, "Tier").strip().lower()
        entries.append({
            "ticket_id": md_file.stem,
            "path": md_file,
            "tier": tier_text or None,
        })
    return entries


def audit_stored_artifacts_migration(
    done_dir: Path = Path("tickets/done"),
    stored_base: Path = Path("stored_artifacts"),
) -> dict:
    """Read-only audit: for every standard/epic done ticket, check stored_artifacts/{id}/
    completeness. Never mutates any file. hotfix tickets are skipped (no stored_artifacts/
    expected — not a gap). Legacy/unrecognised-tier tickets are skipped with a WARNING, never
    counted as missing/incomplete.
    """
    ok = []
    missing = []
    incomplete = {}
    hotfix_skipped = 0
    legacy_skipped = 0

    for entry in scan_done_tickets(done_dir):
        ticket_id = entry["ticket_id"]
        tier = entry["tier"]

        if tier is None or tier not in _RECOGNISED_TIERS:
            print(f"WARNING: {ticket_id} — no ## Tier field, skipped")
            legacy_skipped += 1
            continue

        if tier == "hotfix":
            hotfix_skipped += 1
            continue

        stored_dir = stored_base / ticket_id
        if not stored_dir.exists():
            missing.append(ticket_id)
            continue

        complete, problems = _files_complete(stored_dir, REQUIRED_ARTIFACT_FILES)
        if complete:
            ok.append(ticket_id)
        else:
            incomplete[ticket_id] = problems

    return {
        "ok": ok,
        "missing": missing,
        "incomplete": incomplete,
        "hotfix_skipped": hotfix_skipped,
        "legacy_skipped": legacy_skipped,
    }


def print_report(summary: dict) -> None:
    total_checked = len(summary["ok"]) + len(summary["missing"]) + len(summary["incomplete"])
    print("Part C — stored_artifacts migration audit (read-only, disclose-don't-fix)")
    print(f"standard/epic tickets checked: {total_checked}")
    print(f"  ok: {len(summary['ok'])}")
    print(f"  missing stored_artifacts/: {len(summary['missing'])}")
    print(f"  incomplete stored_artifacts/: {len(summary['incomplete'])}")
    print(f"hotfix tickets skipped (no stored_artifacts expected): {summary['hotfix_skipped']}")
    print(f"legacy/no-Tier-field tickets skipped: {summary['legacy_skipped']}")
    if summary["missing"]:
        print("Missing:")
        for ticket_id in summary["missing"]:
            print(f"  - {ticket_id}")
    if summary["incomplete"]:
        print("Incomplete:")
        for ticket_id, files in summary["incomplete"].items():
            print(f"  - {ticket_id}: missing {', '.join(files)}")


def main() -> None:
    summary = audit_stored_artifacts_migration()
    print_report(summary)


if __name__ == "__main__":
    main()
