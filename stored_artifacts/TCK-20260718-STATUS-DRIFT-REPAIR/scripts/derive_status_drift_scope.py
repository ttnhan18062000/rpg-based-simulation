"""Step 1 (one-off, read-only) — derive and freeze the authoritative Part A file list.

TCK-20260718-STATUS-DRIFT-REPAIR plan.md Step 1. Re-scans `tickets/done/*.md` with the exact
baseline regex (`^## Status\\s*\\n+\\s*(\\S+)`, multiline) used by the ticket's own investigation.md
and by Part C's checker, so the 71-file in-scope set fed to Step 2 is re-derived at implementation
time rather than trusted from the ticket body (ticket closes happen continuously).

Read-only: performs no file writes.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DONE_DIR = REPO_ROOT / "tickets" / "done"

BASELINE_STATUS_RE = re.compile(r"^## Status\s*\n+\s*(\S+)", re.MULTILINE)
SAME_LINE_STATUS_RE = re.compile(r"^## Status\b(.*)$", re.MULTILINE)

EPIC_TIER_VALUES = {"EPIC_SCOPED", "SCOPED"}

EXPECTED_IN_SCOPE_COUNT = 71
EXPECTED_EPIC_TIER_COUNT = 7
EXPECTED_LEGACY_NAMING_COUNT = 5
EXPECTED_COLON_SUFFIXED_DRIFT_COUNT = 6


def derive_scope():
    in_scope = []
    epic_tier = []
    legacy_naming = []

    for f in sorted(DONE_DIR.glob("*.md")):
        text = f.read_text(errors="ignore")
        m = BASELINE_STATUS_RE.search(text)
        if not m:
            continue
        value = m.group(1)
        if value.upper() == "DONE":
            continue
        if value.upper() in EPIC_TIER_VALUES:
            epic_tier.append((f.name, value))
            continue
        if not f.name.startswith("TCK-"):
            legacy_naming.append((f.name, value))
            continue
        in_scope.append((f.name, value))

    colon_suffixed_drift = []
    for f in sorted(DONE_DIR.glob("*.md")):
        text = f.read_text(errors="ignore")
        if BASELINE_STATUS_RE.search(text):
            continue
        m = SAME_LINE_STATUS_RE.search(text)
        if not m:
            continue
        raw = m.group(1).strip()
        if raw.startswith(":"):
            value = raw[1:].strip()
            if value and value.upper() != "DONE":
                colon_suffixed_drift.append((f.name, value))

    in_scope_names = {name for name, _ in in_scope}
    colon_names = {name for name, _ in colon_suffixed_drift}
    disjoint = in_scope_names.isdisjoint(colon_names)

    return in_scope, epic_tier, legacy_naming, colon_suffixed_drift, disjoint


def main():
    in_scope, epic_tier, legacy_naming, colon_suffixed_drift, disjoint = derive_scope()

    print(f"In-scope (Part A drift) count: {len(in_scope)}")
    for name, value in in_scope:
        print(f"  {name}\t{value}")

    print(f"\nEpic-tier exception count: {len(epic_tier)}")
    for name, value in epic_tier:
        print(f"  {name}\t{value}")

    print(f"\nLegacy-naming exception count: {len(legacy_naming)}")
    for name, value in legacy_naming:
        print(f"  {name}\t{value}")

    print(f"\nColon-suffixed drift (out of scope, informational) count: {len(colon_suffixed_drift)}")
    for name, value in colon_suffixed_drift:
        print(f"  {name}\t{value}")

    print(f"\nDisjoint (in_scope vs colon_suffixed_drift): {disjoint}")

    failed = False
    if len(in_scope) != EXPECTED_IN_SCOPE_COUNT:
        print(
            f"FAIL: in-scope count {len(in_scope)} != expected {EXPECTED_IN_SCOPE_COUNT}",
            file=sys.stderr,
        )
        failed = True
    if len(epic_tier) != EXPECTED_EPIC_TIER_COUNT:
        print(
            f"FAIL: epic-tier count {len(epic_tier)} != expected {EXPECTED_EPIC_TIER_COUNT}",
            file=sys.stderr,
        )
        failed = True
    if len(legacy_naming) != EXPECTED_LEGACY_NAMING_COUNT:
        print(
            f"FAIL: legacy-naming count {len(legacy_naming)} != expected "
            f"{EXPECTED_LEGACY_NAMING_COUNT}",
            file=sys.stderr,
        )
        failed = True
    if len(colon_suffixed_drift) != EXPECTED_COLON_SUFFIXED_DRIFT_COUNT:
        print(
            f"FAIL: colon-suffixed drift count {len(colon_suffixed_drift)} != expected "
            f"{EXPECTED_COLON_SUFFIXED_DRIFT_COUNT}",
            file=sys.stderr,
        )
        failed = True
    if not disjoint:
        print("FAIL: in-scope set and colon-suffixed drift set are not disjoint", file=sys.stderr)
        failed = True

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
