---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
phase: done
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL

## Title
Add a schema-validating write path for `docs/parity_ledger/*.yaml` and close the index-freshness
gap after ledger edits

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/parity_ledger/schema.json` exists (`id` pattern, required fields per `status`, P0 requiring
`test_path`, `divergent` requiring `divergence_note`) but nothing enforces it when a ledger shard
is actually written. `.claude/agents/parity-updater.md`'s "What to Do" section edits YAML via raw
`Read`/`Edit` with no validation step, and hand-orchestrated sessions do the same (confirmed:
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`'s session directly `Edit`ed
`combat_movement.yaml` and `substrate.yaml`, and its own tool history shows it searching for a
validator — `find ... validate_parity*`, `grep ... parity_ledger.*schema|jsonschema` — and finding
none).

Separately, `tools/parity_index.py` builds a derived, read-only SQLite index over the ledger
(`entry`/`impact`/`health` commands), reviewed in `docs/ai/parity_readpath_gate_a_decision.md`
(Gate A: **GO**, 66.7% vs. 4.8% recall vs. the legacy scan). That index is never kept fresh
automatically: `compute_tool_safety_metrics`'s `parity_write_safety` audit over the last 14 days
found **0** `docs/parity_ledger/*.yaml` writes that co-occurred with a `parity_index.py build` call
in the same run — every real edit leaves the derived index silently stale.

## Scope
- **Investigate (mandatory before Plan):** confirm the exact schema-validation surface
  `docs/parity_ledger/schema.json` currently expresses (which fields, which conditional
  requirements) and how `parity_index_baseline.py`/`context_packet_assembler.py` currently consume
  it read-side, to reuse rather than reinvent that logic.
- Add a schema-validating writer (CLI or importable function) that mutates a `docs/parity_ledger/
  *.yaml` shard only after validating the resulting entry against `schema.json` — reject on: bad
  `id` pattern, missing `v2_evidence`/`test_path` for `verified`/`divergent` status, missing
  `divergence_note` for `divergent`, non-null `test_path` violation for P0.
- After a successful validated write, either trigger `tools/parity_index.py`'s `build` in the same
  run, or make the resulting staleness impossible to miss (e.g. a mandatory `check-staleness` call
  wired into the same command) — pick one and justify the choice; do not leave both undone.
- Update `.claude/agents/parity-updater.md`'s "What to Do" (currently: "Read the relevant YAML
  file" / "Update the entry") to use the new write path instead of raw `Read`/`Edit`.
- Explicitly decide, and record in `investigation.md`, whether this ticket also resolves Gate A's
  two disclosed structural gaps (`docs/ai/parity_readpath_gate_a_decision.md` §6.2: `_PATH_REF_RE`
  doesn't recognize `.claude/`-prefixed paths; §6.3: `find_p0_intersection` raises uncaught
  `yaml.YAMLError` on a malformed shard) or defers them with a stated reason — do not silently
  ignore either.

## Out of Scope
- Wiring `tools/parity_index.py`'s **read** path (`entry`/`impact`/`health`) into `parity-updater`'s
  discovery step, or any other live workflow gate. `docs/ai/parity_readpath_gate_a_decision.md`'s
  GO verdict is explicitly scoped to the read-path review only and states in its own §5 that a
  **separate** Phase-3 scoping ticket must resolve §6.2/§6.3 "before writing any code" for that
  purpose — this ticket's write-safety scope is a different, narrower thing and must not be used
  to backdoor that larger decision.
- Any change to `docs/parity_ledger/*.yaml` content itself — this ticket builds tooling, not ledger
  edits.
- Broadening `schema.json` itself beyond what's needed to express the existing entry schema
  documented in CLAUDE.md's "Entry Schema" section.

## Acceptance Criteria
- [x] The writer rejects a malformed entry (each of the conditions listed in Scope) with a clear,
      specific error — verified by a real test per condition, not one generic "invalid" test.
- [x] A successful validated write either rebuilds the derived index in the same run or leaves an
      unmissable staleness signal — verified by a test asserting the chosen behavior actually
      happens.
- [x] `.claude/agents/parity-updater.md` is updated to use the new write path; its existing
      "Entry Schema" section either stays accurate or is updated to match.
- [x] Gate A's §6.2/§6.3 gaps are either fixed (with tests) or explicitly deferred with a written
      rationale in `investigation.md`/`plan.md` — not silently dropped.
- [x] Scoped pytest run passes.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260731-PARITY-READPATH-GATE (DONE; Gate A review this ticket's write-safety scope sits
  alongside, without reopening its read-path decision)
- TCK-20260731-PARITY-INDEX-IMPORTER, TCK-20260731-PARITY-INDEX-BASELINE, TCK-20260731-PARITY-IMPACT-PROOF
  (DONE; built the index this ticket keeps fresh)
- TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY (DONE; built `check-staleness` — reuse, don't
  reimplement)
- TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE (DONE; defined the exact
  `parity_write_safety` co-occurrence semantics this ticket's evidence relies on)

## Related Docs
- `docs/ai/parity_readpath_gate_a_decision.md`
- `docs/parity_ledger/schema.json`
- CLAUDE.md's "Parity Ledger Files" / "Entry Schema" sections

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/parity_index.py`
- `tools/parity_ledger_scan.py`
- `tools/gate_checks/parity_updater_static.py`
- `.claude/agents/parity-updater.md`
- `docs/parity_ledger/*.yaml`
- `tests/tools/test_parity_index.py`

## Assumptions / Open Questions
- Whether the writer lives inside `tools/parity_index.py` itself or a sibling module — `parity_index.py`'s
  own docstring currently states it "implements no mutation CLI," so adding one may be better as a
  clearly-separate module rather than changing that file's own stated contract; not decided here,
  left to Investigate/Plan.
- Whether index-rebuild-on-write is the right default vs. a lighter staleness-flag — Gate A's own
  scope explicitly left workflow wiring undecided; this ticket should pick the narrowest option
  that closes the measured gap (0% co-occurrence) without reopening the broader Phase-3 question.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL/plan.md`'s 8 steps:

1. Fixed `docs/parity_ledger/schema.json`'s duplicate top-level `"if"` key by restructuring the
   `items` object's two conditionals into `items.allOf`, and added a third `allOf` entry for the
   previously prose-only P0 → non-null-`test_path` rule. Added
   `tests/tools/test_parity_ledger_schema.py::test_schema_json_parses_and_has_fixed_allof_structure`
   as a direct, runtime, regression-blocking proof (parses the raw JSON, asserts no top-level
   `if`/`then` survives under `items`, asserts `len(items["allOf"]) == 3`).
2. Updated `tools/parity_index_baseline.py::_schema_coverage_as_parsed()` to detect the fixed
   `allOf` shape and report `known_defect: None` with a note citing this ticket, keeping the old
   `items.get("if")` branch as a defensive fallback for older git revisions.
3. Fixed Gate A §6.3: added `class ShardParseError(Exception)` to `tools/parity_ledger_scan.py`
   (mirrors `tools/parity_index.py`'s `ShardParseError` shape) and wrapped
   `find_p0_intersection`'s `yaml.safe_load` call in `try/except yaml.YAMLError`, re-raising as
   `ShardParseError`. New regression test
   `tests/tools/test_parity_ledger_scan.py::test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`.
4. Reconciled `tests/tools/test_gate_a_readpath_review.py::_safe_find_p0_intersection` to import
   and catch `ShardParseError` alongside `yaml.YAMLError`.
5+6. Built `tools/parity_ledger_writer.py`: `EntryValidationError`, `validate_entry()` (four
   rejection rules mirroring `schema.json`'s three `allOf` branches plus the `id` pattern check,
   each cited to its exact schema.json branch in a code comment), and `write_entry()` (validates
   first, then upserts the shard by `id` via a single `yaml.safe_dump` call-site, then calls
   `parity_index.build()` in-process on success — see plan.md's Deviations section for why Steps 5
   and 6 landed as one file write rather than two sequential edits). New test file
   `tests/tools/test_parity_ledger_writer.py` (13 tests): one rejection test per condition, an
   acceptance test, an anti-drift "missing status without evidence still accepted" test, a static
   architecture guard proving `validate_entry(` always precedes the module's one write call-site
   and no `yaml.dump(` bypass exists, a rebuild-on-success test (`check_staleness()` reports
   `FRESH`), a rebuild-never-fires-on-failure test (monkeypatched `build` call-counting stub), and
   the parity-updater.md doc-sync test.
7. Updated `.claude/agents/parity-updater.md`'s "What to Do" steps 2-5 to construct the entry dict
   and invoke `parity_ledger_writer.write_entry()` via a single Bash `python3 -c` call instead of
   raw `Read`/`Edit`, followed by an explicit, separate, visible
   `python3 tools/parity_index.py build` Bash call (required because
   `generate_retro.py::_is_parity_index_build_call` only pattern-matches literal Bash command
   text, not in-process Python calls — recorded in plan.md's Design Decisions).
8. Ran the full scoped verification. All new/touched-by-this-ticket test files pass 100%
   (`test_parity_ledger_schema.py`, `test_parity_ledger_writer.py`, `test_parity_index.py` — all
   34 tests including both `TestArchitectureGuards` mutation-guard tests, `test_gate_a_readpath_review.py`'s
   `TestNoMutation::test_gate_a_review_leaves_protected_files_byte_identical`, and
   `test_parity_ledger_scan.py`). Two pre-existing, unrelated test-data problems were found and
   confirmed (via `git stash` before/after comparison) to be identical before and after this
   ticket's changes: `test_gate_a_readpath_review.py` is missing its `gate_a_corpus.json`/
   `gate_a_results.json` fixture files (never committed to the repo per `git log --all
   --diff-filter=A`), and `test_parity_index_baseline.py` has a stale hardcoded historical count
   (1347 vs. the live ledger's actual 1343) plus a reference to a missing doc file. Neither is
   caused by, or in scope for, this ticket — documented in plan.md's new Deviations section per
   the "never silently deviate" rule.

Gate A §6.2 (`_PATH_REF_RE` not recognizing `.claude/`-prefixed paths) was deferred, not fixed,
per investigation.md's and plan.md's explicit rationale: it is read-path internals both this
ticket's and its parent epic's Out of Scope sections wall off for a future Phase-3 scoping ticket.

## Test Summary
New tests added: `tests/tools/test_parity_ledger_schema.py` (1), `tests/tools/test_parity_ledger_writer.py`
(13), `tests/tools/test_parity_ledger_scan.py` (+1, `test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`).
All new tests pass. Full regression surface re-run: `test_parity_index.py` (34/34 pass, including
both `TestArchitectureGuards` write-path guards), `test_parity_ledger_scan.py` (4/4 pass),
`test_gate_a_readpath_review.py`'s `TestNoMutation` (byte-identity guard, passes). Pre-existing,
ticket-unrelated failures in `test_parity_index_baseline.py` (3) and the rest of
`test_gate_a_readpath_review.py` (3 failed / 7 errors, all from two missing fixture/doc files) were
confirmed via `git stash` to be identical before and after this ticket's changes — see plan.md
Deviations.

## Files Changed
- `docs/parity_ledger/schema.json` (fixed duplicate `"if"` key; added P0 conditional)
- `tools/parity_index_baseline.py` (`_schema_coverage_as_parsed()` updated for fixed schema)
- `tools/parity_ledger_scan.py` (added `ShardParseError`; wrapped `yaml.safe_load` in `find_p0_intersection`)
- `tools/parity_ledger_writer.py` (new — `validate_entry()`, `write_entry()`)
- `.claude/agents/parity-updater.md` ("What to Do" section rewritten to use the new writer + build call)
- `tests/tools/test_parity_ledger_schema.py` (new)
- `tests/tools/test_parity_ledger_writer.py` (new)
- `tests/tools/test_parity_ledger_scan.py` (added malformed-shard regression test)
- `tests/tools/test_gate_a_readpath_review.py` (`_safe_find_p0_intersection` reconciled to catch `ShardParseError`)

## Completion Summary
Built a schema-validating write path for `docs/parity_ledger/*.yaml` (`tools/parity_ledger_writer.py`:
`validate_entry()` + `write_entry()`) that rejects malformed entries on all four scoped conditions
before any file I/O, and rebuilds the derived parity SQLite index in-process on every successful
write. Along the way, fixed two real, previously-disclosed defects the writer would otherwise have
inherited: `docs/parity_ledger/schema.json`'s duplicate top-level `"if"` key (which silently
dropped the verified/divergent evidence-required rule) and Gate A §6.3's uncaught
`yaml.YAMLError` crash in `find_p0_intersection`. `.claude/agents/parity-updater.md` now calls the
new writer instead of raw `Read`/`Edit`, plus a separate visible `parity_index.py build` Bash call
so the `parity_write_safety` retro metric keeps registering a signal. Gate A §6.2 stays explicitly
deferred to a future Phase-3 ticket, per both this ticket's and its parent epic's Out of Scope
sections. All new/touched tests pass; two pre-existing, ticket-unrelated test-data gaps (missing
Gate A corpus fixtures, a stale historical count in the baseline test) were found, confirmed
unrelated via before/after `git stash` comparison, and documented rather than silently worked
around.
