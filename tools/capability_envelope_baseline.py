#!/usr/bin/env python3
"""
Manage the append-only capability-envelope baseline registry
(registries/capability_envelope_registry.jsonl) and audit the live
`.claude/settings.local.json` against it.

Built for TCK-20260904-CAPABILITY-ENVELOPE-BASELINE. Mirrors `tools/tag_registry.py` /
`tools/layer_registry.py`'s registry convention exactly: JSONL, one entry per line, keyed on a
unique key, `add_entry()` refuses to re-add an existing key, `load_registry()` raises on a
duplicate key found on disk. See those modules first if this one is unclear — they are the direct
template, per this ticket's own Scope section.

The registry covers all 4 of `settings.local.json`'s real top-level schema fields — not just
`permissions.allow` — keyed on `(field, value)` (not `value` alone), so a `permissions.allow`
string can never collide with an MCP server name that happens to be spelled the same:

  {"field": "permissions.allow", "value": "Bash(git *)", "added_date": "2026-09-05",
   "reviewed": true, "note": "..."}

Each entry carries a typed `reviewed: bool` field — the durable, queryable fact of whether it was
individually reviewed (`add_entry`, default `True`) or bulk-seeded from an ungoverned live file and
never individually reviewed (`seed_registry`, always `False`). This is a typed field, not something
recovered by string-matching `note`'s prose: `note` stays supplementary human-readable context
only. A prior revision of this module's design stored this same fact only in `note`'s text; that
was corrected before implementation because it violated this project's Durable State Rule (durable
meaning must never live only in a free-form string).

AUDIT-ONLY: the `diff`/`seed`/`add`/`list` subcommands never write to any `settings*.json` file —
the only file this module ever writes is `registries/capability_envelope_registry.jsonl`. There is
no confirmed runtime-enforcement mechanism today; `diff`'s report is evidence for human review, not
a security control.

Usage:
  python3 tools/capability_envelope_baseline.py add <field> <value> --note "why"
  python3 tools/capability_envelope_baseline.py seed --settings-path <path> --note "why"
  python3 tools/capability_envelope_baseline.py list
  python3 tools/capability_envelope_baseline.py diff --settings-path <path>
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_REL_PATH = Path("registries/capability_envelope_registry.jsonl")

# The exact 4 top-level schema fields confirmed live in settings.local.json — permissions.allow
# plus the 3 MCP fields. permissions.deny/permissions.ask are absent in the live file and are not
# part of this envelope.
FIELDS = frozenset(
    {
        "permissions.allow",
        "enableAllProjectMcpServers",
        "enabledMcpjsonServers",
        "disabledMcpjsonServers",
    }
)

AUDIT_ONLY_DISCLAIMER = (
    "AUDIT-ONLY REPORT: this diff has no runtime-enforcement effect. It is evidence for human "
    "review, not a security control. See docs/ai/capability_envelope_baseline.md."
)

DEFAULT_SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.local.json"


# ---------------------------------------------------------------------------
# Registry file I/O
# ---------------------------------------------------------------------------


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else REPO_ROOT
    return base / REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {(field, value): entry_dict} for every registered entry. Empty dict if the file
    doesn't exist yet.

    Raises ValueError on a duplicate (field, value) registration — the file must never contain the
    same key twice; that would violate the append-only-unique-key invariant `add_entry()`
    otherwise guarantees.
    """
    path = registry_path(root)
    if not path.exists():
        return {}

    registry: dict = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        key = (entry["field"], entry["value"])
        if key in registry:
            raise ValueError(
                f"{path}: duplicate registration for {key!r} at line {lineno} — "
                f"the registry must contain each (field, value) pair exactly once"
            )
        registry[key] = entry
    return registry


def add_entry(
    field: str,
    value: object,
    note: str = "",
    reviewed: bool = True,
    root: Path | str | None = None,
) -> dict:
    """Append a new (field, value) registration. Returns the entry written.

    Raises ValueError if `field` is not one of `FIELDS`, or if `(field, value)` is already
    registered — entries can only be added, never updated or re-added (mirrors
    `tag_registry.py::add_tag`'s refuse-on-duplicate contract).

    `reviewed` defaults to `True`: a direct call to `add_entry` (the CLI's `add` subcommand) is by
    construction a single, deliberate, individually-reviewed governance addition. `seed_registry`
    is the one caller that overrides this to `False` for its bulk, ungoverned bootstrap entries —
    do not unify the two defaults; a future reader might otherwise "fix" the apparent inconsistency
    and erase the reviewed/unreviewed distinction this field exists to preserve.
    """
    if field not in FIELDS:
        raise ValueError(f"field must be one of {sorted(FIELDS)}, got {field!r}")

    registry = load_registry(root)
    key = (field, value)
    if key in registry:
        existing = registry[key]
        raise ValueError(
            f"{key!r} is already registered (added {existing['added_date']}) — "
            f"entries cannot be re-added or changed"
        )

    entry = {
        "field": field,
        "value": value,
        "added_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "reviewed": reviewed,
        "note": note,
    }

    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry


# ---------------------------------------------------------------------------
# Live-file parsing and bulk seed
# ---------------------------------------------------------------------------


def load_settings_local(path: Path | str) -> dict | None:
    """Return the parsed settings JSON object, or None if `path` does not exist.

    Never raises FileNotFoundError — a missing settings.local.json is a real, common condition
    (this worktree itself has none) that callers must handle as a clean reported state, not an
    exception.
    """
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def extract_entries(settings: dict) -> list:
    """Flatten a settings dict into a list of (field, value) tuples covering all 4 schema fields.

    permissions.deny/permissions.ask are read defensively via .get(...) but are not part of this
    envelope's fields — only permissions.allow is.
    """
    entries: list = []

    for value in settings.get("permissions", {}).get("allow", []):
        entries.append(("permissions.allow", value))

    if "enableAllProjectMcpServers" in settings:
        entries.append(("enableAllProjectMcpServers", settings["enableAllProjectMcpServers"]))

    for value in settings.get("enabledMcpjsonServers", []):
        entries.append(("enabledMcpjsonServers", value))

    for value in settings.get("disabledMcpjsonServers", []):
        entries.append(("disabledMcpjsonServers", value))

    return entries


def seed_registry(settings_path: Path | str, root: Path | str | None = None, note: str = "") -> list:
    """Bulk-register every entry found in the live settings file, skipping any (field, value)
    pair already registered. Returns only the entries actually appended.

    Deliberately different contract from `add_entry`'s raise-on-duplicate behavior: `add_entry`
    (called directly) is for one deliberate, individually-reviewed governance addition, where a
    mistake re-adding an existing key should be loud. `seed_registry` is a bulk bootstrap/re-sync
    operation where hitting already-registered entries on a re-run is the expected, idempotent
    common case, not an error. Do not unify these two contracts.

    Every entry written here has `reviewed=False` — seeded entries are, by construction, a bulk
    snapshot of an ungoverned live file, never individually reviewed one at a time.
    """
    settings = load_settings_local(settings_path)
    if settings is None:
        return []

    appended = []
    for field, value in extract_entries(settings):
        try:
            appended.append(add_entry(field, value, note=note, reviewed=False, root=root))
        except ValueError:
            continue
    return appended


# ---------------------------------------------------------------------------
# Diff / report
# ---------------------------------------------------------------------------


def compute_diff(live_settings: dict | None, registry: dict) -> dict:
    """Per-field live-vs-baseline set diff. Treats every field uniformly, including the
    scalar-shaped `enableAllProjectMcpServers` (compared as a one-element set) — no special-cased
    boolean branch.
    """
    if live_settings is None:
        return {"status": "no_local_file", "fields": {}}

    live_entries = extract_entries(live_settings)
    fields_report = {}
    for field in FIELDS:
        live_values = {value for f, value in live_entries if f == field}
        baseline_values = {value for (f, value) in registry if f == field}
        fields_report[field] = {
            "in_envelope": sorted(live_values & baseline_values, key=str),
            "out_of_envelope": sorted(live_values - baseline_values, key=str),
        }

    return {"status": "ok", "fields": fields_report}


def build_report(settings_path: Path | str, root: Path | str | None = None) -> dict:
    live_settings = load_settings_local(settings_path)
    registry = load_registry(root)
    report = compute_diff(live_settings, registry)
    report["audit_only_disclaimer"] = AUDIT_ONLY_DISCLAIMER
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser(
        "add", help="Register a new (field, value) entry (append-only — cannot update or delete)"
    )
    add_p.add_argument("field", choices=sorted(FIELDS))
    add_p.add_argument("value")
    add_p.add_argument("--note", default="", help="Why this entry is being added")
    add_p.add_argument("--root", default=None)

    seed_p = sub.add_parser(
        "seed", help="Bulk-register every entry found in a live settings.local.json (idempotent)"
    )
    seed_p.add_argument("--settings-path", default=str(DEFAULT_SETTINGS_PATH))
    seed_p.add_argument("--note", default="", help="Why this seed batch is being added")
    seed_p.add_argument("--root", default=None)

    list_p = sub.add_parser("list", help="Print every registered (field, value) entry")
    list_p.add_argument("--root", default=None)

    diff_p = sub.add_parser(
        "diff", help="Compare a live settings.local.json against the registered baseline"
    )
    diff_p.add_argument("--settings-path", default=str(DEFAULT_SETTINGS_PATH))
    diff_p.add_argument("--root", default=None)

    args = parser.parse_args(argv)

    if args.command == "add":
        try:
            entry = add_entry(args.field, args.value, note=args.note, root=args.root)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Registered {entry['field']!r}={entry['value']!r} ({entry['added_date']}).")
        return

    if args.command == "seed":
        appended = seed_registry(args.settings_path, root=args.root, note=args.note)
        print(f"Seeded {len(appended)} new entr{'y' if len(appended) == 1 else 'ies'}.")
        return

    if args.command == "list":
        registry = load_registry(args.root)
        for field, value in sorted(registry, key=lambda k: (k[0], str(k[1]))):
            entry = registry[(field, value)]
            print(
                f"{field:<28} {value!r:<40} reviewed={entry['reviewed']!s:<5} "
                f"{entry['added_date']}  {entry.get('note', '')}"
            )
        return

    if args.command == "diff":
        report = build_report(args.settings_path, root=args.root)
        print(json.dumps(report, indent=2, sort_keys=True))
        return


if __name__ == "__main__":
    main()
