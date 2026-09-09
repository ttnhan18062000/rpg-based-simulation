---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE
phase: open
date: 2026-09-09
tags: [testing, architecture]
---

# TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE

## Title
`test_phase18_import_boundaries.py`'s `_DOMAINS_OBSERVABILITY_PINNED` keys grandfathered exceptions by line number — brittle, and its failure mode is diff-indistinguishable from a prohibited gate-weakening edit

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`tests/architecture/test_phase18_import_boundaries.py`'s `_DOMAINS_OBSERVABILITY_PINNED` dict keys
each grandfathered `domains -> observability` import exception by `(file_path, line_number)`. Any
unrelated code addition above a pinned import shifts its line number, breaking the pin and failing
CI for a reason that has nothing to do with the actual change — the import itself is unchanged and
still legitimate.

**This has now happened twice, per the dict's own comments**:
1. `TCK-20260905-FAME-DERIVER-LEGEND-FACT` — adding `FameExporter.export()` shifted
   `orchestrator.py`'s pinned import from line 437 to 440.
2. `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — adding `CatalogRepository`/
   `WorldModuleRepository`/`CatalogScenarioStateBuilder` construction shifted the same file's
   pinned import from line 447 to 487.

**Why this is worse than ordinary test fragility**: the correct fix (re-pin the line number to
match reality) is diff-indistinguishable from the exact edit the Gate Integrity rule prohibits
(silently editing a gate/check to make it pass instead of fixing the underlying issue) — both are
a one-line change to `_DOMAINS_OBSERVABILITY_PINNED`. A reviewer (human or peer-review agent)
cannot tell "the import is unchanged and this is legitimate maintenance" from "the gate was
weakened to pass" without independently re-deriving the actual current line number and confirming
the import content is identical — real scrutiny cost on every occurrence, not just an inconvenience.

## Scope
- Change `_DOMAINS_OBSERVABILITY_PINNED`'s keying scheme to something stable across unrelated
  line-shifting edits — candidates: key by `(file_path, module_being_imported, tuple_of_imported_names)`
  and match any `ImportFrom` node in that file with that module/names combination (regardless of
  line), or key by a nearby stable anchor (e.g. the enclosing function name) instead of a raw line
  number.
- Preserve the existing guard: expanding the exception set (adding a NEW file/import pair) must
  still require updating this test AND `docs/audits/D14_coupling_depth.md` together — only the
  keying mechanism for existing entries changes, not the review discipline around adding new ones.
- Confirm the new scheme still correctly REJECTS an import that isn't pinned (the test's own
  negative-case behavior must be unchanged).

## Out of Scope
- Any other line-keyed pinning mechanism elsewhere in the test suite, if one exists — not surveyed
  here; file separately if found.
- The Gate Integrity rule itself — this ticket makes gate maintenance safer to distinguish from
  gate weakening, it does not change the rule.

## Acceptance Criteria
- [ ] `_DOMAINS_OBSERVABILITY_PINNED`'s exceptions are keyed on something that survives an
      unrelated line-shifting edit above them (verified with a real test: add dummy lines above a
      pinned import in a scratch/temp scenario and confirm the pin still matches).
- [ ] The test still correctly fails for a genuinely new, unpinned `domains -> observability`
      import.
- [ ] No regression in `tests/architecture/`.

## Related Tickets
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (first occurrence)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (second occurrence; origin of this ticket)

## Related Docs
- `docs/audits/D14_coupling_depth.md` (must stay in sync with any NEW exception added, per the
  existing convention this ticket preserves)

## Related Code Areas
- `tests/architecture/test_phase18_import_boundaries.py` (`_DOMAINS_OBSERVABILITY_PINNED`,
  `test_domains_do_not_import_observability_outside_pinned_exceptions`)

## Assumptions / Open Questions
- Whether a symbol/import-content key alone is sufficiently unambiguous (e.g. if a file somehow
  imported `SimulationEvent` from `src.observability.events` twice) is worth checking during
  Investigate — likely a non-issue in practice, but worth confirming rather than assuming.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
