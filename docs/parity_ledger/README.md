---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Parity Ledger

`docs/parity_ledger/*.yaml` is the **sole authoritative parity-tracking mechanism** for this
repository. Its historical predecessor, `docs/logic_checklist_exhaustive.md`, was archived by
`TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP` (see
`docs/archive/logic_checklist_exhaustive.md` and
`docs/archive/specs/2026-05-03-checklist-governance-design.md` for the migration record) — do
not reintroduce a parallel checklist-based tracking system; extend the YAML shards here instead,
via `tools/parity_ledger_writer.py`'s schema-validating write path, and keep
`tools/parity_index.py`'s derived SQLite index (`python3 tools/parity_index.py build`) fresh
after any edit.

## Schema check and baseline

`schema.json` is validated against the shards by a ratchet, `python3 -m codebase.gates.parity_ledger_schema check`
(`make parity-ledger-schema-check`; it also runs as a test, `tests/codebase/test_parity_ledger_schema_gate.py`, in the
`tools-a-e` CI job on every PR, so it blocks). It counts the schema errors per ledger file and rule (the failing schema
path without its leading `items/`, for example `allOf/0/then/properties/test_path/type`) and compares them with
`codebase/baselines/parity_ledger_schema_baseline.json`. The ledger started with 2,862 errors; they are being fixed by
`TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC`.

- **A PR may not add an error.** If a count rose or a rule is new, the check fails and names the file, the rule and the entry
  ids. Fix the entry (a verified or divergent entry needs `v2_evidence` and a `test_path`; a P0 entry needs a `test_path`
  unless it is `missing` or `unsupported` with a `support_boundary`). Do not loosen `schema.json` and do not raise the
  baseline.
- **Any domain may lower a count.** When you fix ledger entries, run
  `python3 -m codebase.gates.parity_ledger_schema tighten --yes` and commit the baseline in the same PR as the ledger fix
  (without `--yes` it is a dry run that lists what would change). `tighten` refuses to write if any count rose or a rule is
  new.
- **Raising a count by hand is never allowed.** A schema change that raises counts (for example a stricter rule) needs the
  codebase domain and an owner decision first; it is not a drive-by edit.
- **Exit codes:** 0 clean, 1 a count rose or a rule is new, 2 the check could not run (an unparsable shard, or a missing or
  invalid baseline or schema). Exit 2 is never a pass; the CI test fails on it.
- **Limit:** counts per file and rule cannot see a swap (one entry fixed and another broken in the same file and rule leave the
  count equal). Review entry changes as usual; the check is a floor, not a proof of entry-level correctness.
