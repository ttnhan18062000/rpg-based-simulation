---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED
phase: done
date: 2026-09-16
tags: [architecture, bug, schema]
---

# TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED

## Title
`priority = layer rank × transitive dependents` rewards rare layers instead of frequent ones —
inverted relative to the epic's own stated rule

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/brainstorm/mechanisms.yaml`'s `layers` block ranks by rarity, ascending:
`entity: rank 1` (per_tick, most frequent) ... `world: rank 5` (rare, least frequent).
`tools/mechanism_registry.py::priority()` computes `rank * transitive_dependent_count`. Multiplying
by `rank` therefore **rewards the rarest layers and penalizes the most frequent one** — the exact
opposite of the epic's own stated design rule ("lower layers first... more frequency is more
priority", `docs/plans/mechanism_registry_initiative.md` Gap 1).

Confirmed on real, committed output, not just the formula's logic — `docs/brainstorm/
mechanism_priority_view.md`'s own top row:

| Mechanism | Layer | Dependents | Priority |
|---|---|---|---|
| `betrayal_siege_war` | faction (rank 3) | 11 | **33** (top of the list) |
| `action_pacing_readiness` | entity (rank 1) | **23** | 23 |

`action_pacing_readiness` runs every tick for every entity and has more than double
`betrayal_siege_war`'s transitive dependents, yet ranks below it. `buildings_town_services`
(world, rank 5, only 1 dependent) scores 5 — a single dependent on the rarest layer outranks
several entity-layer mechanisms with far more real dependents.

**Two independent confirmations this is a defect, not a surprising-but-correct result:**
1. `betrayal_siege_war` (faction war) ranking #1 directly contradicts
   `[[feedback_bottom_up_rpg_feature_priority]]`/`project_faction_war_foundation_only` — the user
   has explicitly deprioritized driving the war chain upward, in favor of the starved lower systems
   that feed it. A priority view whose top recommendation is the one thing already flagged
   don't-build-more-of-this-yet is miscomputing, not surfacing insight.
2. `buildings_town_services` outranking multiple entity-layer mechanisms on a single dependent has
   no defensible reading under the stated rule.

**Root cause, traced to its origin**: `TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own
investigation.md (Assumption #2) explicitly flagged this exact risk — "this... could outrank a
rank-1 entity leaf... may be correct or may violate the bottom-up rule... check against a
known-correct ordering" — and then recorded it as "intentional... not re-litigated" **without ever
performing the check the ticket's own text called for**. The verification step was asserted as done
without evidence. This ticket performs the check that was skipped.

## Scope
1. Add an explicit `weight` field to each layer in `docs/brainstorm/mechanisms.yaml`'s `layers`
   block, stating "how often this runs" directly rather than deriving it implicitly from `rank`
   (which means "position from the bottom," not "frequency multiplier" — the exact implicit
   inversion that caused this bug). `entity: 5, group: 4, faction: 3, region: 2, world: 1` — the
   mirror of `rank` across the 5 layers, made explicit and independently settable so a future layer
   addition doesn't silently re-derive the wrong direction again.
2. `tools/mechanism_registry.py::priority()` uses `weight`, not `rank`.
3. Regenerate `docs/brainstorm/mechanism_priority_view.md`; sanity-check the new top rows against
   the stated rule before treating the fix as complete.
4. Fix the one existing test that baked the bug in as a passing assertion
   (`test_real_registry_top_row_matches_expected_shape` asserted
   `betrayal_row["priority"] > apr_row["priority"]` — exactly backwards). Update all fixture-based
   priority tests to use `weight`, with correct expected values.
5. Add a new regression test asserting the corrected direction explicitly on real data
   (`action_pacing_readiness` outranks `betrayal_siege_war`), so this can't silently invert again.

## Out of Scope
- Re-litigating whether `rank` itself (the ordinal, used elsewhere for lane/lineage purposes) should
  be removed — it stays; only the priority formula's own multiplier changes source field.
- Re-deriving `depends_on` edges or any other part of the registry — this is a single-field formula
  fix.
- Reopening `TCK-20260915-EPIC-MECHANISM-REGISTRY` or any of its 4 closed children — the derivation
  machinery, views, and tests all function correctly; only the weighting constant was wrong.

## Acceptance Criteria
1. `priority()` computes `weight * transitive_dependent_count`, `weight` read from the registry's
   own `layers` block, not derived from `rank` at call time.
2. Regenerated `mechanism_priority_view.md`'s top rows favor high-frequency, high-dependent
   mechanisms (`action_pacing_readiness` at or near the top) over rare-layer, low-dependent ones.
3. `betrayal_siege_war` no longer ranks #1 among unverified mechanisms.
4. The corrected direction is asserted by a real test, not just eyeballed on the regenerated doc.

## Related Tickets
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION` — where the bug was introduced and its own risk
  flagged but not checked
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent epic, already closed; not reopened by this hotfix

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` Gap 1 — the stated priority rule this corrects
  against

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-PRIORITY-DERIVATION/investigation.md` — Assumption #2,
  the flagged-but-unchecked risk this ticket resolves

## Related Code Areas
- `docs/brainstorm/mechanisms.yaml`
- `tools/mechanism_registry.py`
- `tools/generate_mechanism_priority_view.py`, `tools/generate_mechanism_charts.py` (docstring
  references to "rank" need updating to "weight")
- `docs/brainstorm/mechanism_priority_view.md`
- `tests/unit/tools/test_mechanism_priority_derivation.py`

## Assumptions / Open Questions
None — this is a mechanical fix of a verified, quantified defect.

## Implementation Notes
This is the epic's **fifth** measured error, and the first caught by reading the artifact the epic
itself produced rather than by checking an upstream source by hand. Every prior finding (2 stale
atlas badges, 17% wiring-map drift, `camp`'s own registry seeding error, the scoping document's
"five artifacts" claim) was found by comparing an artifact against something else. This one was
found because the registry's own generated output, once written down in one place, was legible
enough that a wrong answer was immediately recognizable against a rule the user had already stated
elsewhere — which is the entire argument for building the registry in the first place.

## Test Summary
134 tests in the scoped suite (`tests/unit/tools/ tests/unit/engine/test_capability_registry.py`),
all passing, re-verified with `graphify-out/` genuinely moved aside and restored.
- `test_priority_uses_weight_not_rank` (new): gives a rare-but-light layer and a frequent-and-heavy
  layer opposite `rank`/`weight` orderings and asserts the frequent one wins — proves the function
  reads `weight`, not `rank`, rather than merely happening to produce a correct-looking number.
- `test_real_registry_top_row_favors_frequent_layer_over_rare_layer` (renamed from the test that
  previously asserted the bug's own behavior): on real data, `action_pacing_readiness` now
  outranks `betrayal_siege_war`, and `betrayal_siege_war` is asserted OUT of the top 3 by name —
  a direct regression guard against this exact defect recurring silently.
- All other fixture-based priority tests updated to include `weight` alongside `rank` and to use
  correct expected values under the corrected formula.

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — `layers` block gains an explicit `weight` field per layer
  (mirrors `rank` today: `weight = 6 - rank`), plus a header comment explaining why `rank` and
  `weight` are deliberately separate, never derived from each other in code
- `tools/mechanism_registry.py` — `priority()` reads `weight`, not `rank`; docstrings updated
- `tools/generate_mechanism_priority_view.py`, `tools/generate_mechanism_charts.py` — docstring/
  rendered-text references to "rank" corrected to "weight"
- `docs/brainstorm/mechanism_priority_view.md` — regenerated; `action_pacing_readiness` now #1,
  `betrayal_siege_war` dropped from #1 to #7
- `tests/unit/tools/test_mechanism_priority_derivation.py` — fixtures updated, the bug-asserting
  test corrected, one new explicit regression test added

## Completion Summary
DONE. `priority()` now multiplies by the registry's own explicit `weight` field, not `rank` (an
ordinal that means "position from the bottom," not "priority multiplier" — the exact implicit
inversion that caused the original defect). Verified on real data: `action_pacing_readiness`
(entity, per-tick, 23 transitive dependents) is now the #1 unverified-priority mechanism;
`betrayal_siege_war` (the deliberately deprioritized faction-war mechanism) dropped from #1 to #7,
out of the top 3. The one test that had baked the bug in as a passing assertion is corrected and
a new explicit regression test guards the direction going forward. 134/134 tests passing.

This is the epic's fifth measured error, and the first caught by reading the artifact the epic
itself produced rather than by checking an upstream source by hand — the registry's own output was
wrong in a way that was immediately recognizable once written down in one place, against a rule the
user had already stated elsewhere. `TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own
investigation.md had flagged this exact risk and recorded it as "checked" without the check ever
happening; this ticket performs it.
