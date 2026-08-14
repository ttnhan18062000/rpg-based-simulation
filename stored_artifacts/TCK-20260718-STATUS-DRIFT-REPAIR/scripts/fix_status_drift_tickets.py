"""Step 2 (one-off) — bulk-fix `## Status` on the 71 in-scope `tickets/done/*.md` files.

TCK-20260718-STATUS-DRIFT-REPAIR plan.md Step 2. Consumes Step 1's derivation inline (imported,
not hand-copied) so the file list acted on is always freshly re-derived, never a stale static
list. For each in-scope file, replaces only the captured `## Status` value token with `DONE`,
preserving the file's existing blank-line convention (some files have a blank line between
`## Status` and the value, others do not — only the token itself changes).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_status_drift_scope import (  # noqa: E402
    BASELINE_STATUS_RE,
    DONE_DIR,
    derive_scope,
)


def fix_file(path: Path) -> None:
    text = path.read_text(errors="ignore")
    matches = list(BASELINE_STATUS_RE.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"{path.name}: expected exactly 1 baseline ## Status match, found {len(matches)}"
        )
    m = matches[0]
    value_start, value_end = m.span(1)
    new_text = text[:value_start] + "DONE" + text[value_end:]
    if new_text.count("\n") != text.count("\n"):
        raise RuntimeError(f"{path.name}: substitution changed line count, aborting")
    path.write_text(new_text)


def main():
    in_scope, epic_tier, legacy_naming, colon_suffixed_drift, disjoint = derive_scope()
    if len(in_scope) != 71:
        print(f"FAIL: expected 71 in-scope files, got {len(in_scope)}", file=sys.stderr)
        sys.exit(1)
    if not disjoint:
        print("FAIL: in-scope set overlaps colon-suffixed drift set", file=sys.stderr)
        sys.exit(1)

    epic_tier_names = {name for name, _ in epic_tier}
    legacy_names = {name for name, _ in legacy_naming}
    colon_names = {name for name, _ in colon_suffixed_drift}

    fixed = []
    for name, _value in in_scope:
        assert name not in epic_tier_names
        assert name not in legacy_names
        assert name not in colon_names
        path = DONE_DIR / name
        fix_file(path)
        fixed.append(name)

    print(f"Fixed {len(fixed)} files.")
    for name in fixed:
        print(f"  {name}")


if __name__ == "__main__":
    main()
