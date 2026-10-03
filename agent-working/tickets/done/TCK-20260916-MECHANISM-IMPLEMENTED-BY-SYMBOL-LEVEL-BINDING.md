---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING

## Title
Peer-review corrections to claims-as-tests phase 1: symbol-level `implemented_by`, a fifth real
state error corrected, and an unreliable check deleted

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Peer review of `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`'s own closed report made
three corrections and one scope-sequencing call:

1. **The 20-mechanism sample is biased.** Those 20 are the mechanisms this same session personally
   investigated and bound while fixing the four already-known state errors -- the cleanest slice of
   the registry, not a representative one. "Zero confirmed new defects" against that sample is
   close to tautological and does not answer the question phase 1 was built to answer. Corrected
   headline framing recorded in this ticket rather than left standing in the closed one.
2. **`demographic_cohort_cycle` is not a taxonomy question -- it is a defect, and `camp` already
   sets the precedent.** Real caller, invoked every tick, never has effect because
   `population_cohorts` never populates -- exactly `camp`'s own shape (correct, wired code defeated
   by absent data). Corrected to `state: done` + `verified: {code_trace, contradicted}`, the same
   disposition already used for `camp`. This is the epic's fifth real state error, not a zero-defect
   result.
3. **Delete the `skeleton_not_stub` check, don't downgrade it.** It was demonstrably wrong on its
   first real test (`temporal_pressure`) -- `skeleton` means "early/minimal," not "looks like an
   empty stub," and the heuristic conflated line count with functional completeness. A known-wrong
   check left in at low confidence becomes permanent, ignorable noise (the attribution-ratchet
   failure shape). Deleted outright.
4. **Multi-symbol aggregation moves from deferred follow-up to real work.** The concrete case
   (`demographic_cohort_cycle`'s own `cohort.py` mixing an unrelated, widely-used data class with
   the actual service class) is exactly the brittleness peer deferred symbol-level binding to wait
   for. Added `"<path>::<Symbol>"` as a real, validated `implemented_by` entry shape.

**Sequencing**: do not scope the two queued detectors (changed-code-drift, status-language) yet --
extend `implemented_by` coverage and land symbol-level binding first, so both future detectors read
a less biased, finer-grained substrate rather than needing their own assessment redone later.

## Scope
1. `implemented_by` entries may now be `"<path>"` (file-level, unchanged) or `"<path>::<Symbol>"`
   (symbol-level, new). `registry.py::parse_implemented_by_entry()` is the single place this
   format is parsed; both consumers (`mechanism_registry_completeness_check.py`,
   `mechanism_state_caller_check.py`) reuse it rather than re-deriving the split.
2. `validate()`'s invariant 7 checks a symbol-level entry's own symbol is a real top-level
   class/function in the cited file, not just that the file exists -- a renamed or deleted symbol
   now fails validation immediately, the same discipline the file-existence check already had.
3. Migrate the 15 single-symbol-per-file `implemented_by` entries to symbol-level (the
   unambiguous cases). The 4 multi-file mechanisms whose files each define multiple genuinely
   related symbols (`fame`, `fidelity_drift`, `belief_institution`,
   `commitment_pressure_consequences`) are left as file-level bindings -- forcing a single "primary"
   symbol choice there would be an editorial guess, not a real distinction, unlike
   `demographic_cohort_cycle`'s own clear-cut unrelated-symbols case.
4. `mechanism_state_caller_check.py` checks only the bound symbol's real callers when a
   symbol-level entry is given, instead of aggregating across every symbol in the file.
5. `demographic_cohort_cycle`: `state: orphan` -> `state: done` + `verified: {code_trace,
   contradicted}`, propagated to its atlas card (had one; capabilities/wiring map already agreed).
6. Delete `skeleton_not_stub` (the check, its `_is_stub_body()` helper, and its own finding) from
   `mechanism_state_caller_check.py` entirely.
7. Correct the closed ticket's own headline framing via this new ticket (not a retroactive rewrite
   of the closed one) -- "zero confirmed new defects" becomes "one real defect corrected (the
   epic's fifth), one unreliable check deleted, sample bias acknowledged."

## Out of Scope
- Extending `implemented_by` coverage beyond the 20 already-bound mechanisms -- a separate,
  larger, ongoing task; not attempted in this same hotfix.
- Migrating the 4 multi-file mechanisms to per-file symbol-level bindings -- would require an
  editorial "which symbol is primary" judgment call with no real payoff for those specific cases.
- `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION`,
  `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` -- explicitly deferred until coverage
  extension and symbol-level binding are further along.

## Acceptance Criteria
1. `parse_implemented_by_entry()` is the single parser for the `path` / `path::Symbol` shape;
   both consuming tools import and reuse it.
2. `validate()` rejects a symbol-level entry whose symbol isn't a real top-level class/function in
   the cited file.
3. `demographic_cohort_cycle` reads `state: done` with a `verified.contradicted` block citing the
   same reasoning as `camp`'s own entry, and its atlas card matches.
4. `mechanism_state_caller_check.py` contains no `skeleton_not_stub` check, `_is_stub_body`
   function, or `all_stub` tracking.
5. The real registry's own pinned finding set is now empty (verified, not just asserted).
6. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION` -- the ticket this one corrects, per
  peer review of its own closed report.
- `TCK-20260916-EPIC-MECHANISM-REGISTRY` -- `demographic_cohort_cycle` is this epic's fifth real
  state error, same family as `camp` (its own Completion Summary's "four real errors" framing is
  now five, recorded here rather than silently left stale there).

## Related Docs
None new.

## Related Stored Artifacts
None -- hotfix tier, self-evident intent (a direct peer-review correction) captured in this ticket.

## Related Code Areas
- `tools/mechanism_registry/registry.py` (`parse_implemented_by_entry`, `symbol_defined_in_file`,
  invariant 7)
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`
- `tools/mechanism_registry/mechanism_state_caller_check.py`
- `docs/brainstorm/mechanisms.yaml`, `docs/brainstorm/rpg_feature_atlas.html`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
`"<path>::<Symbol>"` was chosen over a nested `{path, symbol}` dict for two reasons: it keeps
`implemented_by` a plain list of strings (no schema-shape branching for readers that don't care
about symbol-level detail), and it mirrors pytest's own `path::Class::method` node-id convention,
already a familiar pattern in this ecosystem.

`quest_reward_distribution`'s own migration surfaced a small additional correction: its citation
named a non-existent class, `FairShareProtocol` -- actually just the module's own docstring
concept name, not a real Python symbol (the file is two free functions,
`compute_fair_share`/`build_reward_transfer_intents`). Migrated to `compute_fair_share`; the
mechanism's own `orphan` state is unaffected (both real functions still have zero real callers,
confirmed directly).

## Test Summary
181 tests passing in the full scoped suite (up from 180: no new test file, but
`test_real_registry_findings_pinned` now asserts the corrected empty finding set), both with
`graphify-out/` present and with it genuinely moved aside and restored.

## Files Changed
- `tools/mechanism_registry/registry.py` -- `parse_implemented_by_entry()`,
  `symbol_defined_in_file()`, invariant 7 extended
- `tools/mechanism_registry/__init__.py` -- re-exports the two new functions
- `tools/mechanism_registry/mechanism_registry_completeness_check.py` -- reuses
  `parse_implemented_by_entry()`
- `tools/mechanism_registry/mechanism_state_caller_check.py` -- symbol-level caller checking;
  `skeleton_not_stub` check deleted
- `docs/brainstorm/mechanisms.yaml` -- 15 `implemented_by` entries migrated to symbol-level;
  `demographic_cohort_cycle` corrected `orphan` -> `done` + `verified`
- `docs/brainstorm/rpg_feature_atlas.html` -- `demographic_cohort_cycle` badge regenerated
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md`,
  `docs/brainstorm/mechanism_registry_view.md`, `docs/brainstorm/mechanism_registry.html` --
  regenerated
- `tests/unit/tools/test_mechanism_state_caller_check.py` -- pinned-finding test corrected
- `docs/REGISTRY.yaml` -- regenerated at Finalize

## Completion Summary
Closed. Applied all three peer-review corrections plus the sequencing call. The headline number is
corrected: this is the epic's **fifth** real registry state error found (not a zero-defect phase-1
run), resolved with the exact `camp` disposition rather than left open as a taxonomy question.
`skeleton_not_stub` is deleted, not downgraded. `implemented_by` now supports symbol-level bindings
(`"<path>::<Symbol>"`), validated against real code the same way file-level bindings already were,
and the caller-count checker uses symbol-level precision wherever a binding provides it. Coverage
extension (binding more of the remaining 69 mechanisms) is real, separate, ongoing work, not
attempted here -- both queued detector tickets stay explicitly deferred until it and symbol-level
binding are further along, per peer's own sequencing call.
