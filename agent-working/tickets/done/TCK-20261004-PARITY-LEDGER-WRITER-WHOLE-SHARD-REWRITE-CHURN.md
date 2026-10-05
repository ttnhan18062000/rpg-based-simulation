---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN
phase: done
date: 2026-10-04
tags: [ai, process-improvement]
---

# TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN

## Title
`parity_ledger_writer.write_entry` rewrites the whole shard, so agents route around the mandated tool

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Reported by `rpg-feature-planning` from a full implement-ticket run: the parity-updater spec mandates `tools/parity_ledger_writer.py::write_entry`, but the agent measured the cost first and deliberately deviated. Its figures: a `yaml.safe_dump` round-trip of the unmodified shards reformats 496 lines of `infrastructure.yaml` and 31 of `substrate.yaml` for a ~20-line real edit. It then used targeted Edits plus the writer's own `validate_entry()` over every entry and `parity_index.py build`, final diff +27/-2.

Verified here: `write_entry` ends with `shard_path.write_text(yaml.safe_dump(entries, sort_keys=False))` (line 148), i.e. a full-shard dump. The exact churn figure was not reproduced (a naive line-diff of a default dump is noisy; measure it with `git diff --stat` after a real write). The structural cause is confirmed. A mandated tool that agents knowingly violate their own spec to avoid is the defect; the third path the agent found (surgical edit plus the writer's validation and index rebuild) is better than either, but it should be the tool, not a deviation.

## Scope
- Make `write_entry` entry-local and format-preserving: replace only the target entry's text span (add: append; update: replace its block) and leave every other byte of the shard unchanged. Options to evaluate and record: `ruamel.yaml` round-trip (check it is already a dependency or acceptable), or a text-span writer keyed on the `- id:` line. Choose by measured diff size on the real shards.
- Keep `validate_entry()` and the index rebuild as part of the call (the two guarantees the writer exists for).
- Parity-updater spec (`.claude/agents/parity-updater.md`) text updated to match, same change; the "surgical edit" deviation path is removed from guidance once the tool is surgical.

## Out of Scope
- Fixing the existing invalid entries (below), reformatting shards once, changing the ledger schema.

## Acceptance Criteria
1. Updating one entry in the real `infrastructure.yaml` through `write_entry` yields a diff limited to that entry's lines (assert the changed-line count against the entry's own span; positive control: the old writer on the same input changes far more).
2. Adding an entry appends without touching other lines; an invalid entry is rejected before any write and the shard is byte-identical afterwards.
3. The index rebuild still runs and `parity_index.py build` output is unchanged for untouched entries.
4. Existing writer tests green; the parity-updater spec matches the new behaviour. Docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20260930-*` parity-ledger writer tickets, if any (find via `tools/parity_ledger_writer.py` history).

## Related Docs
- `.claude/agents/parity-updater.md` (where relevant), `docs/guides/delivery_process.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/parity_ledger_writer.py`, `tools/parity_index.py`, `docs/parity_ledger/*.yaml`, `.claude/agents/parity-updater.md`, tests.

## Assumptions / Open Questions
- **Recorded observation, not in scope:** `validate_entry` fails 170 of 423 entries in `infrastructure.yaml` and 355 of 405 in `substrate.yaml` (verified 2026-10-04; 166 and 355 are `test_path` that must be a non-empty string, 4 unparseable), so it cannot serve as a repo-wide gate today. Whether to file a separate repair ticket (null `test_path` on non-P0 entries: relax the rule or backfill) is a planner decision; it also determines whether a whole-ledger validation can ever be added to CI.
- If `ruamel.yaml` is not an accepted dependency, the text-span writer is the default.

## Implementation Notes
- `tools/parity_ledger_writer.py`: no `ruamel.yaml` in the venv, so a text-span writer was chosen (no new dependency). `_splice_entry` finds column-0 `- ` item starts; the i-th start is the i-th entry. An update replaces that entry's block (blank/comment lines trailing it are kept), an add appends one block. The spliced text must parse back to exactly the intended entry list, else (item-count mismatch, odd indentation, YAML error) it falls back to the old whole-shard dump, so the result is always correct. `validate_entry()` still runs before any I/O and the index rebuild still runs after; the module still has exactly one `write_text` and one `safe_dump` (a single `_dump` helper), so the existing lockstep guard test passes unchanged.
- **Measured** on the real `docs/parity_ledger/infrastructure.yaml` (423 entries), one valid entry's `v2_evidence` changed: entry-local writer changes 4 lines, the old whole-shard dump changes 586.
- `.claude/agents/parity-updater.md` now states the writer is entry-local; the spec had no "surgical edit" deviation text to remove (it already said never to edit the YAML directly).
- Existing invalid entries in the real shards were not touched (out of scope); a write of such an entry is still rejected by `validate_entry`.

## Test Summary
`tests/tools/test_parity_ledger_writer.py`: 41 pass; plus `test_parity_index.py` and `test_parity_updater_static.py` green. New `TestEntryLocalWrites`: one real-shard update changes at most two spans' worth of lines and the old whole-dump changes over 10x more (AC1 with positive control); an add appends and leaves every earlier byte (AC2); an invalid entry leaves the shard byte-identical (AC2); hand-formatting and comments between untouched entries survive; an unexpected shape falls back to a correct dump. The index rebuild tests are the existing ones (AC3).

## Files Changed
- tools/parity_ledger_writer.py
- tests/tools/test_parity_ledger_writer.py
- .claude/agents/parity-updater.md

## Completion Summary
`write_entry` now edits only the target entry's lines, with the whole-shard dump kept as a verified fallback; a one-entry edit on the real infrastructure shard drops from 586 changed lines to 4.
