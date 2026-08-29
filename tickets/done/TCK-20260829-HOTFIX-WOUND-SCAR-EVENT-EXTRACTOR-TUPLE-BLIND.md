---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND
phase: done
date: 2026-08-29
tags: [combat, observability]
---

# TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND

## Title
`event_extractor.py`'s wound/scar diff blocks are `isinstance(x, list)`-gated, but the real apply
path always commits tuples -- no `wound_sustained`/`wound_healed`/`scar_gained` event has ever
fired through a real `Kernel.tick_once()` run

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found live during `TCK-20260824-WOUND-HEALING-DECISION` (`m1-quick-wins` batch), while attempting
to prove via a real `Kernel.tick_once()` run that wound-related events fire correctly.
`src/observability/event_extractor.py:280-281,302-303` gate the wound and scar diff-extraction
blocks with `entity.combat.wounds if isinstance(entity.combat.wounds, list) else []` (and the
matching pattern for `.scars`). But `WoundPatch.apply()` (`src/engine/patches.py:638`) always
commits via `replace(new_com, wounds=tuple(new_wounds), scars=tuple(new_scars))`, and
`AuthoritativeState`'s freeze logic (`src/core/state.py:846`) explicitly coerces both fields to
`tuple` if they aren't already. So `isinstance(entity.combat.wounds, list)` is **always `False`** on
real, frozen, authoritative state -- `entity_wounds`/`prior_wounds`/`entity_scars`/`prior_scars` are
always `[]`, and the `wound_sustained`, `wound_healed`, and `scar_gained` event-emission blocks
(lines ~282-307) never produce a single event, regardless of real wound/scar state changes. The same
file already uses the correct `isinstance(x, (list, tuple))` pattern elsewhere (confirmed at lines
~1499, ~1583), confirming this is an inconsistency/bug in this one spot, not an intentional
list-only contract.

## Scope
- Fix the `isinstance(x, list)` checks at `event_extractor.py:280-281,302-303` to
  `isinstance(x, (list, tuple))`, matching the pattern already used correctly elsewhere in the same
  file
- Add a real, non-mocked `Kernel.tick_once()` regression test proving `wound_sustained` fires when a
  wound is inflicted in a real tick (this is the exact proof `TCK-20260824-WOUND-HEALING-DECISION`'s
  plan needed and could not produce because of this bug)
- Correct `docs/parity_ledger/combat_movement.yaml` COMB-296 and `docs/event_ledger/entity.yaml`
  ENTITY-018 to reflect the real, now-fixed producer status for `wound_sustained` (this ticket's own
  fix) -- coordinate with `TCK-20260824-WOUND-HEALING-DECISION`'s own correction of the same two
  entries for `wound_healed`'s zero-producer status (wounds are permanent, so `wound_healed` stays
  correctly zero-producer; only `wound_sustained`/`scar_gained` become real via this fix) so the two
  tickets' edits to the same entries don't conflict -- whichever lands second should read the other's
  landed state first

## Out of Scope
- The wound-healing-permanence decision itself (owned by `TCK-20260824-WOUND-HEALING-DECISION`,
  already decided: wounds are permanent, no healing)
- The `should_inflict_wound()` 40% threshold dead-code decision (owned by
  `TCK-20260824-WOUND-THRESHOLD-DECISION`)

## Acceptance Criteria
- [x] `event_extractor.py`'s wound/scar diff blocks use `isinstance(x, (list, tuple))`, matching the
      pattern already correct elsewhere in the file
- [x] A real, non-mocked `Kernel.tick_once()` test proves `wound_sustained` fires when a wound is
      inflicted in a real tick
- [x] COMB-296/ENTITY-018 are corrected to reflect the real producer status post-fix, coordinated
      with `TCK-20260824-WOUND-HEALING-DECISION`'s own edits to the same entries

## Related Tickets
- TCK-20260824-WOUND-HEALING-DECISION (where this was found live; also edits COMB-296/ENTITY-018)
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (already landed; wounds now carry real severity-scaled
  penalties, making this event-visibility bug more consequential than before)

## Related Docs
- docs/parity_ledger/combat_movement.yaml
- docs/event_ledger/entity.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/event_extractor.py
- src/engine/patches.py
- src/core/state.py

## Assumptions / Open Questions
None -- self-evident intent, minimal targeted fix (a 2-line isinstance widening, matching an
existing correct pattern in the same file) plus a real regression test.

## Implementation Notes
1. **`src/observability/event_extractor.py:280-281,302-303`**: widened the wound/scar diff-gate
   checks from `isinstance(x, list)` to `isinstance(x, (list, tuple))`, matching the pre-existing
   correct pattern already used elsewhere in the same file (`event_extractor.py:1499`, `:1583`).
   The real, authoritative apply path (`WoundPatch.apply()`, `src/engine/patches.py:639`;
   `AuthoritativeState`'s freeze logic, `src/core/state.py:846`) always commits
   `entity.combat.wounds`/`.scars` as tuples, so the old `list`-only check was always `False` on
   real state and silently zeroed `entity_wounds`/`prior_wounds`/`entity_scars`/`prior_scars` —
   confirmed directly by reading both cited call sites.
2. **New regression test**: `tests/integration/observability/test_kernel_event_recording.py::test_wound_sustained_fires_through_real_tick_once_loop`
   reuses the exact deterministic combat fixture from
   `tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers`
   (attacker ATK 80 vs. defender max_hp 100, hostile factions, adjacent, `ENABLE_COMBAT_ENGAGEMENT`
   ON, seed 42) — a real wound is inflicted at tick 9 through a real `Kernel.tick_once()` loop
   (`ObservabilityMode.NORMAL`, required since the wound/scar diff block is gated `mode not in
   (LIGHT, LONG_RUN)`), and the test asserts `wound_sustained` actually lands in
   `kernel._event_recorder.events` — proving the fix, not just the underlying state-level producer
   (which the sibling wound-healing-permanence test already covers).
3. **`docs/parity_ledger/combat_movement.yaml` COMB-296**: corrected via the sanctioned
   `tools/parity_ledger_writer.py` write path (schema-validating, upsert-by-id, rebuilds the
   derived parity index in-process). Read the entry's current content first — it already carried
   `TCK-20260824-WOUND-HEALING-DECISION`'s own correction of `wound_healed`/`scar_gained`'s
   zero-producer status, which is preserved verbatim in substance. Added on top of that: the
   isinstance bug is now fixed, `wound_sustained` genuinely fires through the real
   event-observability layer (cites the new test above), and `wound_healed`/`scar_gained` remain
   zero-producer regardless of the fix (the fix corrects event-layer *reachability* uniformly for
   all three event types, but cannot make an event fire when no producer ever constructs it).
   Verified via entry-count equality (315 before/after) and per-entry content equality against
   `git show HEAD:docs/parity_ledger/combat_movement.yaml` for every entry except COMB-296 itself
   (script-checked, zero mismatches). `git diff --stat`: 1 file changed, 38 insertions(+), 35
   deletions(-) — small surgical diff despite the full-shard-rewrite writer convention.
4. **`docs/event_ledger/entity.yaml` ENTITY-018**: corrected directly (no sanctioned writer exists
   for this file, matching `TCK-20260824-WOUND-HEALING-DECISION`'s own precedent) — same
   wound_healed/scar_gained-preserved, wound_sustained-now-real correction. Entry-count equality
   (20 before/after) and per-entry content equality verified against `git show HEAD:...` (only
   ENTITY-018 changed). `git diff --stat`: 1 file changed, 2 insertions(+), 2 deletions(-).
   `tests/tools/test_entity_event_ledger.py::test_entity_ledger_evidence_citations_are_real_files`
   initially failed twice during drafting (bare `event_extractor.py:1499/1583` and bare
   `test_wound_healing_permanence.py` references instead of full `src/...`/`tests/...` paths) —
   fixed both, then it passed. `test_entity_ledger_covers_every_entity_update_field` fails both
   before and after this ticket's changes (`cognition_bundle_set` missing a ledger entry) —
   confirmed pre-existing via `git stash`/re-run, unrelated to this ticket, not touched (matches
   the documented `docs/testing/regression_policy.md` hardcoded-baseline-drift category; a
   separate ticket would be needed to add the missing entry).

## Test Summary
- `pytest tests/unit/observability/test_event_extractor_vitals.py tests/unit/observability/test_event_extractor_agency2.py tests/integration/observability/test_kernel_event_recording.py tests/integration/combat/test_wound_healing_permanence.py -m "not slow" -q` — 36 passed.
- `pytest tests/tools/test_entity_event_ledger.py tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_index.py -m "not slow" -q` — 57 passed, 1 pre-existing unrelated failure (`test_entity_ledger_covers_every_entity_update_field`, confirmed present on unmodified `HEAD` via `git stash`).
- `pytest tests/unit/observability/ tests/integration/observability/ -m "not slow" -q` — full-directory regression sweep: 1152 passed, 6 skipped, 0 failed.

## Files Changed
- `src/observability/event_extractor.py` (the 2-line isinstance fix)
- `tests/integration/observability/test_kernel_event_recording.py` (new regression test:
  `test_wound_sustained_fires_through_real_tick_once_loop`)
- `docs/parity_ledger/combat_movement.yaml` (COMB-296 corrected)
- `docs/event_ledger/entity.yaml` (ENTITY-018 corrected)

## Completion Summary
Fixed `src/observability/event_extractor.py`'s `isinstance(x, list)` blindness (lines 280-281,
302-303) to `isinstance(x, (list, tuple))`, matching the file's own pre-existing correct pattern.
The real, authoritative apply path always commits `entity.combat.wounds`/`.scars` as tuples, so the
old check silently dropped all wound/scar event-diffing regardless of real state changes. Added a
real, non-mocked `Kernel.tick_once()` regression test proving `wound_sustained` now fires through
the real event-observability layer (reusing the deterministic fixture from
`TCK-20260824-WOUND-HEALING-DECISION`'s own state-level producer-existence test). Corrected
`COMB-296`/`ENTITY-018` to reflect the real, now-fixed event-layer reachability for
`wound_sustained`, explicitly coordinated with (not overwriting) `TCK-20260824-WOUND-HEALING-DECISION`'s
prior correction of the same two entries for `wound_healed`'s permanently-zero-producer status —
`wound_healed`/`scar_gained` remain correctly zero-producer (no code anywhere constructs
`wounds_heal`/`scars_add`), independent of this event-layer fix. All acceptance criteria met.
