---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING

## Title
Add a real code binding (`implemented_by`) to the mechanism schema — the registry currently cites
atlas cards, never source

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Building `tools/mechanism_registry_completeness_check.py` (for
`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`) surfaced a structural finding: none of the
original 75 mechanisms have a source-code citation in `mechanisms.yaml` at all. Their evidence
(`stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md`) cites atlas card
IDs and wiring-map node names ("atlas `entity-cognition#13`; wiring-map MOT-->CAPT-->DEC"), never a
real file path. This epic's own other findings (17% wiring-map drift, 2 stale atlas badges, the
`camp` seeding error, `motivation_doctrine` reading "confirmed live" in three documents eight days
after its own implementing code was deleted) already established the atlas is not fully
trustworthy — so the registry currently inherits the atlas's accuracy without inheriting any way to
check it.

A hand-authored path-to-mechanism-id lookup table inside a tool was considered and rejected: it
would be a second place the code<->mechanism relationship lives, unverifiable in exactly the way
atlas citations turned out to be, and violates the user's own standing principle (a piece of
information is defined in one document only). The binding belongs in the registry itself, as a
field — the RimWorld-Def-style pattern the user asked us to borrow (every Def corresponds to a real
class) — not a second lookup structure a completeness checker happens to own.

## Scope
1. Add an optional `implemented_by: [<repo-relative path>, ...]` field to the mechanism schema in
   `docs/brainstorm/mechanisms.yaml`.
2. Extend `tools/mechanism_registry.py::validate()` to check, when present: `implemented_by` is a
   list of strings, and **each path must exist on disk** — a deleted implementing module then fails
   validation immediately, the way `motivation_doctrine`'s own 2026-09-08 deletion should have been
   caught the day it happened instead of eight days later.
3. Populate `implemented_by` for the 11 mechanisms registered by
   `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` (their citations already exist as inline
   comments with exact paths — this promotes that prose into the structured field) plus whatever
   additional real, verified bindings the in-flight sub-investigation resolves (see Related
   Tickets). **Do not attempt to populate all 86 now** — per peer review, this is a field the
   registry grows into over time (every future verification/ticket fills one in as a side effect),
   not a one-time backfill obligation.
4. Rewrite `tools/mechanism_registry_completeness_check.py` to read `implemented_by` directly
   (structured field lookup) instead of regex-searching `mechanisms.yaml`'s raw prose — the regex
   approach could only ever see the 11 mechanisms this session cited inline, producing 47 false
   "unmapped" targets on first run.
5. The checker reports binding coverage explicitly and honestly: "N of 86 mechanisms have no
   `implemented_by`" as its own named, visible gap — not silently absent, not treated as if the
   checker has full code-level coverage it doesn't have yet.

## Out of Scope
- Backfilling `implemented_by` for all 86 mechanisms — explicitly deferred, grows organically.
- A hand-authored MAPPING/lookup table anywhere — explicitly rejected, see Request Summary.
- Detection phase 1 (caller-count/stub detection) and the changed-code-without-entry-update check —
  both need this field to exist first; sequenced after, not built here.
- Status-language detection in atlas/capabilities/wiring-map descriptions — a separate, independent
  concern (see the two new todo tickets filed alongside this one).

## Acceptance Criteria
1. `implemented_by` is a recognized, validated optional field: a list of strings, each an existing
   repo-relative path, checked by `mechanism_registry.py::validate()`.
2. All 11 completeness-pass mechanisms have `implemented_by` populated from their existing evidence
   comments.
3. `mechanism_registry_completeness_check.py` reads `implemented_by` structurally; its report
   states both "N unmapped code targets" and "M of 86 mechanisms have no implemented_by" as two
   distinct, separately-true numbers — never conflated.
4. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW` — the ticket whose checker work surfaced this;
  resumes once this lands.
- `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` — source of the 11 mechanisms' own citations
  being promoted into this field.
- A background sub-investigation (dispatched this session) is classifying the checker's own first
  47 "unmapped" targets against the real registry — its output feeds this ticket's `implemented_by`
  population for whichever targets resolve to real bindings (existing or new mechanisms), rather
  than a lookup table.

## Related Docs
None new — the schema change is documented inline in `mechanisms.yaml`'s own header comment.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — confirms the
  original 75's citations are atlas/wiring-map only, motivating this ticket.
- `stored_artifacts/TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS/investigation.md` — source of
  the 11 real path citations being promoted into `implemented_by`.

## Related Code Areas
- `docs/brainstorm/mechanisms.yaml`
- `tools/mechanism_registry.py` (`validate()`)
- `tools/mechanism_registry_completeness_check.py`
- `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/rpg_simulation_wiring_map.html`
  (propagating `causal_spatial_memory`'s corrected state)

## Assumptions / Open Questions
None outstanding. The sub-investigation's ~30 remaining high-confidence candidate bindings (mostly
already-registered mechanisms under `economy_systems/`, `social_systems/`, `strategic_systems/`)
were deliberately not populated in this pass — see Completion Summary for the follow-up.

## Implementation Notes
See `stored_artifacts/TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING/investigation.md` for the full
method, the sub-investigation dispatch/verification discipline, and the per-finding evidence.

Key structural point: `implemented_by` is validated against disk (`(_REPO_ROOT / rel_path).is_file()`
in `mechanism_registry.py::validate()`), not just shape-checked — this is what makes the binding
self-correcting rather than another prose citation that can silently go stale. A deleted
implementing module now fails CI validation the day it's deleted.

Two real bugs were found and fixed as a direct side effect of populating bindings (not the ticket's
original scope, but the kind of thing this field is supposed to surface):
1. `causal_spatial_memory` was mis-registered `orphan` (zero callers) when a real caller exists
   (`engine/pipeline.py:154-157`, gated OFF by default) — corrected to `gated`, propagated to the
   atlas badge and wiring-map node.
2. `commitment_betrayal`'s own citation is namespace-adjacent to `src/domains/commitment/`, which
   implements something else entirely (mixed live/dead pressure/reputation/abandonment logic, now
   its own `commitment_pressure_consequences` mechanism) — the same namespace-collision shape as
   `progression_conversion`/`src/progression/` found in the completeness pass.

## Test Summary
See `stored_artifacts/TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING/test_plan.md`. 165 tests
passing in the scoped suite, both with `graphify-out/` present and with it genuinely moved aside
and restored.

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — `implemented_by` field added to schema; populated for 20
  mechanisms; 3 new mechanisms registered (`group_coordination`, `quest_reward_distribution`,
  `commitment_pressure_consequences`); `causal_spatial_memory` state corrected `orphan` → `gated`
  with a `verified` block recording the correction (89 mechanisms total, was 86)
- `tools/mechanism_registry.py` — `validate()` invariant 7 (`implemented_by` existence check)
- `tools/mechanism_registry_completeness_check.py` — rewritten to read `implemented_by`
  structurally instead of regex-searching prose
- `docs/brainstorm/rpg_feature_atlas.html` — `causal_spatial_memory` badge regenerated
- `docs/brainstorm/rpg_simulation_wiring_map.html` — `MEM` node hand-corrected (`:::bug` →
  `:::gated`)
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md`,
  `docs/brainstorm/mechanism_registry_view.md`, `docs/brainstorm/mechanism_registry.html` —
  regenerated for the final 89-mechanism state (the latter two owned/introduced by
  `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`, closed alongside this ticket)
- `tests/unit/tools/test_mechanism_registry.py` — 4 new `implemented_by` validation tests
- `tests/unit/tools/test_mechanism_registry_completeness_check.py` — new, 7 tests
- `tests/unit/tools/test_mechanism_atlas_regenerate.py`,
  `tests/unit/tools/test_mechanism_priority_derivation.py`,
  `tests/unit/tools/test_mechanism_registry_html.py` — regression fixes for the new registrations
  (see test_plan.md)
- `docs/REGISTRY.yaml` — regenerated at Finalize

## Completion Summary
Closed. `implemented_by` is a real, disk-validated code binding on the mechanism schema — the
RimWorld-Def-style pattern the user asked for, replacing a hand-authored lookup table that would
have been a second, unverifiable place the code<->mechanism relationship lived. 20 of 89
mechanisms now carry a real binding; the completeness checker reports this honestly as "20 of 89"
rather than either hiding it or overclaiming the other 69 as gaps.

Two real registry defects were found and fixed as a direct side effect: `causal_spatial_memory`'s
mis-registered `orphan` state (a real caller exists, just flag-gated off), and the
`commitment_betrayal`/`src/domains/commitment/` namespace-adjacency trap, which produced one new
`partial` mechanism (`commitment_pressure_consequences`) plus two new orphans found along the way
(`group_coordination`, `quest_reward_distribution`).

**Follow-up filed, not silently dropped**: the dispatched sub-investigation produced roughly 30
additional high-confidence candidate `implemented_by` bindings (mostly `economy_systems/`,
`social_systems/`, `strategic_systems/` files mapping cleanly to already-registered mechanisms per
Foundation's own prior citation table) plus 2 genuinely ambiguous domain-level findings
(`domains/information` split between `belief_institution`/`information_trust_deception`;
`domains/world_emergence` split between `opportunity_rumor_seeds`/`quest_generation_sourcing`).
None of these were populated in this pass, per peer review's explicit "don't populate all 86 (89)
now" — the field grows organically. This unblocks
`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`, closed alongside this ticket since its own
combined view and generated HTML page were regenerated against this same final 89-mechanism,
20-binding state.
