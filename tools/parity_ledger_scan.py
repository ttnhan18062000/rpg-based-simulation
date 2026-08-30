"""Substring scan of P0 parity-ledger entries' v2_evidence against a changed-files list.

Built for TCK-20260705-WORKFLOW-PARITY-SKIP: the Parity phase in `.claude/workflows/implement-ticket.js`
skips its `parity-updater` agent call when a ticket touches no `src/` file and reports no behavior
change. Before that skip is allowed to fire, `find_p0_intersection` checks that no P0 ledger entry's
`v2_evidence` text already depends on one of the ticket's changed files — protecting a P0 entry from
silently going stale. Scans all 9 canonical parity-ledger files the Parity phase prompt itself lists
(`implement-ticket.js` Parity agent call), including `faction.yaml` (added by
TCK-20260826-PARITY-FACTION-CANONICAL-SCAN once its `FAC-013` entry became `priority: P0`).

This check is empirically inert today (no P0 `v2_evidence` currently cites a non-`src/`/non-`tests/`
path — see investigation.md), but must still be implemented for real: it protects against future ledger
entries that could violate that invariant.

Assumes `files_changed` paths and `v2_evidence` path citations use the same repo-relative,
forward-slashed form (consistent with how `files_changed` is populated everywhere else in
implement-ticket.js today) — a path written with a different form (absolute, backslashed) would not
be matched by this substring check.
"""

import yaml
from pathlib import Path


class ShardParseError(Exception):
    def __init__(self, filename: str, message: str):
        self.filename = filename
        self.message = message
        super().__init__(f"failed to parse shard {filename!r}: {message}")


CANONICAL_LEDGER_FILES = (
    "substrate.yaml",
    "combat_movement.yaml",
    "strategic_cognition.yaml",
    "town_resource.yaml",
    "progression.yaml",
    "social_narrative.yaml",
    "world_dynamics.yaml",
    "infrastructure.yaml",
    "faction.yaml",
)


def find_p0_intersection(files_changed, ledger_dir="docs/parity_ledger"):
    """Return (ledger_filename, entry_id, changed_path) triples for every P0 entry whose `v2_evidence`
    text contains one of `files_changed` as a substring. Empty list means no P0 entry depends on any
    changed file — the caller may safely skip the Parity agent call.

    Only scans CANONICAL_LEDGER_FILES — never a file under `ledger_dir` outside that tuple.
    """
    ledger_path = Path(ledger_dir)
    hits = []
    for filename in CANONICAL_LEDGER_FILES:
        path = ledger_path / filename
        if not path.exists():
            continue
        try:
            entries = yaml.safe_load(path.read_text()) or []
        except yaml.YAMLError as exc:
            raise ShardParseError(filename, str(exc)) from exc
        for entry in entries:
            if entry.get("priority") != "P0":
                continue
            evidence = entry.get("v2_evidence") or ""
            if not evidence:
                continue
            for changed_path in files_changed:
                if changed_path and changed_path in evidence:
                    hits.append((filename, entry.get("id"), changed_path))
    return hits
