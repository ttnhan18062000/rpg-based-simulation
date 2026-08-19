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
