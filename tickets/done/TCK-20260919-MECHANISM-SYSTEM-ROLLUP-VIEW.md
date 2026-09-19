---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW
phase: done
date: 2026-09-19
tags: [architecture, documentation, schema]
---

# TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW

## Title
Child 3 of `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — the rollup view, deferred until the
membership foundation existed

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP`'s own SEQUENCE.md named this child but explicitly
deferred drafting it: "Deferred per the user's call until the mapping and registry exist." Both now
exist (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`, done 2026-09-19): the registry, the
`systems: []` field on all 93 mechanisms, and `registry.py::mechanisms_by_system()`. This ticket
drafts and builds the actual rollup view — a rendered doc, same family as
`mechanism_verification_view.md`/`mechanism_priority_view.md`/`mechanism_registry_view.md`, showing
what each system actually contains without reading all 93 mechanisms individually (the epic's own
stated need).

Two constraints are already known and recorded, not rediscovered here:
- **Counts, never a badge** (`docs/plans/mechanism_tier_model_initiative.md` §5, epic Assumptions
  #3): a system shows *combat — 6 mechanisms, 1 verified, 0 runtime end-to-end*, never a single
  summary status. A badge would conceal that most members are unverified, rebuilding the atlas's
  own historical failure one tier higher.
- **Rates against baseline, not in isolation** (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-
  INVESTIGATION`'s own Completion Summary): the investigation's one real failure (`faction`, 77%
  unverified / 23% bound) looked informative until checked against the whole-registry baseline and
  found statistically indistinguishable from average. A rollup that reports a system's raw
  percentage without the baseline next to it will mislead readers the same way. The baseline must be
  computed live from the current registry, never a hardcoded snapshot value (the investigation's own
  74%/30% figures are already stale — this batch alone moved the bound count).

## Scope
1. A `build_system_rollup(data)` function in `tools/mechanism_registry/registry.py`, same shape as
   the existing `build_verification_view()`/`all_mechanisms_combined_view()` — pure, read-only,
   consumes the registry data already in hand, computes no verdict or ranking (epic AC #6/
   Assumptions #2, "membership stays read-only to every computation").
2. Per system (from `mechanisms_by_system()`, including the real `"unassigned"` bucket, never
   omitted): mechanism count, `implemented_by`-bound count and rate, verified count and rate (split
   runtime vs static, matching `mechanism_verification_view.md`'s own static-vs-runtime distinction),
   and a full `state` breakdown (done/partial/gap/orphan/gated/skeleton counts — all six rendered
   explicitly per system, zero counts included, not omitted, same "explicit absence" discipline as
   the verification view's own unverified rows).
3. A whole-registry baseline row/section computed the same way, for every system's rates to be
   compared against.
4. A new generator script, `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`,
   mirroring `generate_mechanism_verification_view.py`'s own CLI shape exactly (`--output`,
   `--registry`, `--check`), writing `docs/brainstorm/mechanism_system_rollup_view.md`.
5. A new `make mechanism-system-rollup-view` target, matching the plain-view convention
   (`mechanism-verification-view`/`mechanism-priority-view`/`mechanism-registry-view` have no
   separate `--check` Make target of their own — only the atlas/capabilities *regenerators*, which
   mutate a second consumer artifact, get that pairing; a pure view generator's own `--check` CLI
   flag is exercised directly by its test, not wrapped in a Make target).
6. Tests: a synthetic-fixture test proving counts/rates compute correctly (never a badge, and a
   baseline comparison is actually present), plus a real-registry `--check` no-drift test, same
   family as `test_mechanism_verification_view.py`.

## Out of Scope
- Wiring the rollup into the atlas/capabilities pages — those are per-mechanism artifacts; this is a
  new, separate rendered view, not an existing-artifact update.
- Deriving anything (a ranking, a verdict, a "which system to fix next" ordering) from system
  membership — explicitly forbidden by the epic's own Assumptions #2 and AC #3/#6.
- Simplifying multi-membership to single-valued — the epic's own child 2 already decided to keep
  full many-to-many (8 of 93 mechanisms are genuinely multi-system); this ticket renders whatever
  membership shape the foundation already committed to, it doesn't revisit that decision.

## Acceptance Criteria
1. The rollup view shows, per system, mechanism count + rates — never a single summary status —
   proven by a test that would fail if a badge/verdict field were added to a row.
2. Every system's bound-rate and verified-rate is shown alongside the whole-registry baseline rate,
   computed live from the same registry data, not a hardcoded percentage.
3. The `"unassigned"` bucket renders with real counts, proven by a test asserting its presence with
   a nonzero-if-real-data-has-one count, mirroring the foundation ticket's own AC #5 discipline for
   `mechanisms_by_system()` itself.
4. `--check` mode fails (exit 1) when the rendered file is stale against the real registry, mirroring
   every other `mechanism-*-view` generator.
5. Nothing in this ticket's own code computes a ranking, verdict, or priority from system membership.

## Related Tickets
- `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — parent epic, child 3.
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION` — done; supplies `systems: []` and
  `mechanisms_by_system()`, both consumed here unmodified.
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION` — done; supplies the
  baseline-comparison requirement this ticket's AC #2 exists to satisfy.
- `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` — ongoing, same session; this rollup's
  own bound-rate numbers will keep moving as that ticket's batches land, same as the verification
  view's own numbers already do.

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` §5, §6 — the rollup constraint and sequencing.

## Related Stored Artifacts
None yet — standard tier, artifacts created alongside implementation in this same session.

## Related Code Areas
- `tools/mechanism_registry/registry.py`
- `tools/mechanism_registry/generate_mechanism_verification_view.py` (structural precedent)
- `registries/mechanisms.yaml`, `registries/system_registry.jsonl`
- `Makefile`

## Assumptions / Open Questions
- Per-system rows are sorted alphabetically (matching `mechanisms_by_system()`'s own key order),
  not by size or by any derived signal — sorting by a computed value would be a soft ranking,
  against Assumptions #2's own read-only rule.
- The baseline row is rendered once, at the top, not repeated per row — kept as a single reference
  point rather than duplicated prose, but every system row still states its own rate numerically
  next to that reference (not just "see baseline above").

## Implementation Notes
`build_system_rollup(data)` added to `tools/mechanism_registry/registry.py`, sharing a
`_rollup_stats(ids, by_id)` helper across the per-system, `unassigned`, and whole-registry baseline
computations (three call sites, one counting path — a real correctness requirement here, not just
DRY: if baseline and per-system used different counting logic, a comparison between them would be
meaningless). Returns `{"baseline": {...}, "systems": [...], "unassigned": {...}}` — count, bound
count/rate, verified count/rate split runtime/static, and a full 6-state breakdown (every
`VALID_STATES` value present with a real 0 where a system has no members in that state, never
omitted).

`generate_mechanism_system_rollup_view.py` renders it, mirroring
`generate_mechanism_verification_view.py`'s CLI shape exactly (`--output`/`--registry`/`--check`).
One real edge case found and fixed while building it: a 0-member group (would apply to
`unassigned` whenever it's genuinely empty, as it is on the real registry today) computes
`bound_rate`/`verified_rate` as `0.0` by construction (division guarded in `_rollup_stats`), which
would render as "-35.5pt vs baseline" — misrepresenting "no members" as "worse than baseline." Fixed
in the renderer: a 0-count row shows `n/a` for both rate cells instead of a real but meaningless
delta.

Real registry output (2026-09-19, 93 mechanisms, 7 systems): `combat` clearly stands out
(71.4% bound / 71.4% verified vs a 35.5%/26.9% baseline — the only system where verified rate beats
bound rate, driven by 4 runtime-verified mechanisms), `economy` and `social` show 0% verified
against the same baseline. This is the actual "loose versus deep" signal the epic's Request Summary
asked for, visible without reading any of the 21 (`social`+`economy`) or 7 (`combat`) mechanisms
individually.

## Test Summary
`tests/unit/tools/test_mechanism_system_rollup_view.py` (10 tests, new): fixture-based tests proving
no badge/status/verdict key ever appears in a rollup row (AC #1), all six states render explicitly
including zero counts (AC #1), baseline is computed live from the fixture's own data rather than a
fixed value and correctly discriminates a system above/below it (AC #2), `unassigned` renders with
its real count (AC #3), and systems sort alphabetically rather than by any computed rate (AC #5, no
ranking derived from membership). Plus the standard generator-CLI trio: `--check` mode detects
staleness, the Make target runs clean, and the real committed file matches a fresh render (mirroring
`test_mechanism_registry_view.py`'s own structure exactly). Full suite: `tests/unit/tools/` 216
passed (206 pre-existing + 10 new), `registry.py`'s own `validate()` passes clean (93 mechanisms).

## Files Changed
- `tools/mechanism_registry/registry.py` — new `_rollup_stats()`, `build_system_rollup()`.
- `tools/mechanism_registry/__init__.py` — re-exports `build_system_rollup`.
- `tools/mechanism_registry/generate_mechanism_system_rollup_view.py` — new generator script.
- `docs/brainstorm/mechanism_system_rollup_view.md` — new, generated (do not hand-edit).
- `Makefile` — new `mechanism-system-rollup-view` target.
- `tests/unit/tools/test_mechanism_system_rollup_view.py` — new, 10 tests.
- `docs/plans/mechanism_tier_model_initiative.md` — status block updated to record child 3 landing.

## Completion Summary
**Done.** Child 3 of `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — the last named child, closing
the epic's own scope (though the epic ticket itself is left open/`EPIC_SCOPED` per its own
convention of tracking rather than closing). Both known constraints from the epic's Assumptions #3
and the value investigation's own finding are satisfied and directly tested: counts only, never a
badge, and every rate shown against a live-computed baseline rather than in isolation. Nothing
computed here feeds a ranking or verdict (AC #5/#6 lineage from the foundation ticket held). All
93 mechanisms accounted for across 7 systems plus a real, currently-empty `unassigned` bucket.
