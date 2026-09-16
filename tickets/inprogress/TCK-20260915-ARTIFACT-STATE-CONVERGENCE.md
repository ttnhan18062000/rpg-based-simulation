---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-ARTIFACT-STATE-CONVERGENCE
phase: open
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-ARTIFACT-STATE-CONVERGENCE

## Title
The brainstorm artifacts render mechanism state from the registry; their hand-maintained duplicates
are removed

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Five artifacts each maintain mechanism state by hand, with no shared source. Measured against
`origin/main`, 2026-09-15:

| Artifact | State vocabulary | Volume |
|---|---|---|
| `rpg_feature_atlas.html` | `gap` 58, `done` 43, `partial` 25, `orphan` 12, `gated` 7, `skeleton` 2 | 139 cards |
| `simulation_design_taxonomy.html` | `Implemented` 35, `Partial` 15 — nothing else | 50 rows |
| `simulation_capabilities.html` | 3-tier plain language | 77 cards |
| `rpg_simulation_wiring_map.html` | `classDef live` / `classDef bug` | 3 flowcharts |
| `design_merit_scorecard.html` | Groundedness / Efficiency / Leverage | ideas 1–65 |

They already disagree, and the disagreement is not cosmetic. The atlas carries `orphan` and `gated` —
the built-but-never-runs distinction this arc established — and the taxonomy has no vocabulary for it
at all, so all 50 of its rows read as at least partly working. Opening the taxonomy returns the
pre-arc picture, confidently and with no indication it is stale.

Converge them on the registry.

## Scope
1. **Atlas** — card `state` derives from the registry; cards map to mechanism ids. Cards not
   corresponding to any mechanism (design ideas not yet built) keep their own state and are marked as
   idea-level rather than mechanism-level.
2. **Taxonomy** — verdicts derive from registry `state`, gaining the `orphan`/`gated` distinction it
   currently cannot express.
3. **Capabilities** — its 3-tier plain language maps from registry `state` by a declared mapping, so
   the non-dev view cannot silently diverge.
4. **Wiring map** — `classDef` assignments derive from registry `state` (chart generation itself is
   child 3's scope).
5. **Scorecard** — assess only. It scores *design ideas* on merit (Groundedness/Efficiency/Leverage),
   not mechanism state, so it may legitimately stay independent. Record the conclusion either way
   rather than converging it reflexively.

## Out of Scope
- **Merging artifact prose.** Only `state` and `verified` converge. The capabilities page is
  deliberately non-dev language, the taxonomy carries design verdicts, the atlas carries per-feature
  detail — merging their writing would destroy what makes each useful.
- Restructuring any artifact's layout or navigation.
- `entity_capabilities.html`, already stale and unmaintained — confirm superseded, do not converge.

## Acceptance Criteria
1. No artifact retains an independently hand-maintained copy of mechanism `state`.
2. A state change in the registry propagates to every consuming artifact with no per-artifact edit —
   proven by changing one mechanism's state and asserting all consumers move.
3. The taxonomy can express `orphan` and `gated`, and at least the known instances show as such.
4. The capabilities mapping from registry state to plain-language tier is declared in one place, not
   reimplemented per card.
5. The scorecard's convergence decision is recorded with its reasoning.
6. Artifacts remain viewable as standalone HTML — if generation is a build step, the committed output
   stays openable without a toolchain.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — dependency
- `TCK-20260915-MECHANISM-VERIFICATION-AXIS` — dependency (`verified` must exist before it renders)

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §2 Gap 3 — the share-state-not-prose scope limit

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html` — cards already JSON (`CARD_SECTIONS`), the easiest consumer
- `docs/brainstorm/simulation_design_taxonomy.html`
- `docs/brainstorm/simulation_capabilities.html`
- `docs/brainstorm/rpg_simulation_wiring_map.html`
- `docs/brainstorm/design_merit_scorecard.html`

## Assumptions / Open Questions
1. Do the atlas's 139 cards map cleanly onto mechanism ids, or many-to-one with a remainder? This is
   the largest unknown in the epic and should be measured early — it may justify splitting this
   ticket per artifact.
2. Does the capabilities page's 3-tier language survive a mechanical mapping from six states, or does
   it need editorial judgement per card? If the latter, the mapping becomes a default that can be
   overridden with a recorded reason, never silently.
3. Is the scorecard genuinely a different axis (design merit vs implementation state)? Current
   reading: yes, leave independent.

## Implementation Notes
The standing rule that every atlas edit with gameplay-visible impact is mirrored into
`simulation_capabilities.html` the same turn exists precisely because these two drift. This ticket
should make that rule unnecessary for *state* — it stays necessary for prose.

**The epic's own scoping document was itself wrong (the fourth measured drift finding, and the
first inside the scoping document itself).** `docs/plans/mechanism_registry_initiative.md`'s
Finding 1 claimed five artifacts independently record mechanism state (`simulation_design_
taxonomy.html` and `design_merit_scorecard.html` included), reached by grepping the taxonomy for a
couple of guessed vocabulary words rather than reading it — the taxonomy is actually a 108-card,
6-value catalogue of generic simulation-engine architecture patterns (Agent-Based Modeling, GOAP,
Lamport Clocks, CRDT-Based State Convergence), not a mechanism catalogue at all; a direct check
against every mechanism id currently `orphan`/`gated` in the registry found zero textual overlap.
Corrected in place (Finding 1, Gap 2) and in the epic ticket's own Request Summary/Scope/Related
Code Areas, with the correction's own cause recorded rather than silently rewritten over. Peer
independently re-verified the count before accepting the correction.

**`camp`'s registry `state: done` was itself wrong going in** (the epic's third measured finding,
and the first where the registry itself — not a downstream artifact — was wrong): `CampState` is
real, correct, wired code, but no compiled or procedurally-generated world ever seeds `state.camps`.
Peer corrected an initial `state: orphan` proposal to the right decomposition:
`state: done` (code is not defective) + `verified: {verdict: contradicted}` (never observed
working) — the schema's first real instance of this exact combination. Filed
`TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` as a separate follow-up (not swept into
this ticket) to re-read all 73 mechanism-mapped atlas cards' full descriptions for the same class
of caveat, since `camp`'s own seeding read the badge/title and missed a caveat sitting in the
description — a real methodology gap in Foundation's original seed, not a one-off.

Found two more real instances of the exact same self-contradictory shape (a `planned`/"not built"
tier paired with a label admitting "built") while building the capabilities mapping:
`demographic_cohort_cycle` ("Population Ebb & Flow") and, after regeneration, a related tier/label
mismatch on `cross_episode_grief_nemesis` (a stale "built" label predating this same epic's own
live-by-default confirmation for that mechanism). All fixed in the same pass as `camp`.

**Peer's sharpest correction on implementation approach**: an initial framing of the atlas
regenerator as "lowest risk because `cls` already matches the registry vocabulary" was wrong — the
regeneration mechanism itself, not the mapping, is the ticket's highest risk, since the atlas's
value is concentrated in hand-written card descriptions a template-based regenerator could silently
destroy. Both regenerators (atlas, capabilities) are surgical single-field mutations (`cls` only;
`tier`/`tierLabel` only), proven safe by an exact JSON round-trip check plus a dedicated
prose/body-preservation test on each, and applied against the real files with `diff`-verified
minimal changesets (3 lines in a 3000+ line atlas file; 6 lines in a 1060-line capabilities file).

## Test Summary
135 tests total in the scoped suite (`tests/unit/tools/ tests/unit/engine/test_capability_registry.py`),
all passing, re-verified with `graphify-out/` genuinely moved aside and restored (standing
discipline every ticket this epic):
- `test_mechanism_atlas_regenerate.py` (11 tests) — mapping integrity, diff computation, and the
  load-bearing prose-preservation test (every non-`cls` field byte-identical after a regeneration
  that DOES have real diff work to do, proven against a mutated fixture, not the already-synced
  real file).
- `test_mechanism_capabilities_tier.py` (18 tests) — the full `(state, verified)` mapping table,
  including the `camp` case (`done`+`contradicted`→`built`) asserted independently from
  `done`+no-verdict→`live`, and the `partial`-only override enforcement (non-empty reason required,
  targets a real `partial` mechanism).
- `test_mechanism_capabilities_regenerate.py` (12 tests) — mapping integrity and the equivalent
  body-preservation test for `title`/`desc`.
- `test_mechanism_artifact_convergence.py` (2 tests) — the AC #2 propagation proof: one real
  mechanism (`combat_resolution`) mutated to two different states, asserted to move the atlas
  badge, the capabilities tier, AND the wiring map's own classdef derivation together in one test,
  with no other card/mechanism/node moving alongside it; a second test proves capabilities moves on
  `verified.verdict` alone while atlas/wiring-map correctly do not (both are state-only by design).
- Existing `test_mechanism_wiring_map_classdef.py` (7 tests, T3) reconfirmed passing unmodified —
  no code change needed for scope item 4.

## Files Changed
- `tools/mechanism_atlas_card_mapping.py` (new) — 73-mechanism atlas card↔id mapping, reused from
  Foundation's own citation table
- `tools/mechanism_atlas_regenerate.py` (new) — surgical `badge.cls`-only regenerator + `--check`
- `tools/mechanism_capabilities_card_mapping.py` (new) — 76-entry, 69-mechanism capabilities
  card↔id mapping, built fresh with numbered, evidence-cited Judgment Calls
- `tools/mechanism_capabilities_tier.py` (new) — the single `(state, verified) → tier` function +
  `PARTIAL_TIER_OVERRIDES`
- `tools/mechanism_capabilities_regenerate.py` (new) — surgical `tier`/`tierLabel`-only regenerator
  + `--check` + reviewed `TIER_LABEL_OVERRIDES`
- `docs/brainstorm/mechanisms.yaml` — `camp` gains `verified: {contradicted}` (state unchanged)
- `docs/brainstorm/rpg_feature_atlas.html` — 3 badge `cls` fixes (`committed_intentions`,
  `succession`, `camp`)
- `docs/brainstorm/simulation_capabilities.html` — 4 tier/label fixes (`combat_engagement`,
  `demographic_cohort_cycle`, `camp`, `cross_episode_grief_nemesis`)
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md` —
  regenerated (verified count 6→7)
- `docs/plans/mechanism_registry_initiative.md` — Finding 1/Gap 2 corrected (5-artifact → 3+2 framing)
- `tickets/todos/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md` — matching correction
- `Makefile` — `mechanism-atlas-check/-regenerate`, `mechanism-capabilities-check/-regenerate`
- `tests/unit/tools/test_mechanism_atlas_regenerate.py`,
  `test_mechanism_capabilities_tier.py`, `test_mechanism_capabilities_regenerate.py`,
  `test_mechanism_artifact_convergence.py` (all new)
- `tickets/todos/TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT.md` (new, filed not fixed)
- `staging_artifacts/TCK-20260915-ARTIFACT-STATE-CONVERGENCE/` — investigation.md, plan.md, test_plan.md

## Completion Summary
DONE. 3 of the 5 artifacts converge on the registry (atlas, capabilities: new surgical regenerators;
wiring map: already converged by T3, reconfirmed). The other 2 (taxonomy, scorecard) are confirmed
independent axes, not converged — a real check, not an assumption: taxonomy catalogues generic
engine-architecture patterns (zero overlap with any registry mechanism id), scorecard scores
design-idea merit keyed by idea number, neither is a mechanism-state surface. AC #1 applies only to
the 3 real consumers; AC #3/#5 are satisfied by recording that a real mapping was sought for
taxonomy and found not to exist, and that scorecard's independence was checked and confirmed, not
converged reflexively.

All 6 acceptance criteria met: AC #2 (propagation) proven by a single-fixture, three-consumer test
per peer's explicit "two of three would look like success" correction; AC #4 (capabilities mapping
declared once) via `mechanism_capabilities_tier.py`'s single function plus a reason-required,
`partial`-only override table; AC #6 (standalone viewability) preserved by construction — both
regenerators mutate the existing embedded JSON in place, no build step, and are proven surgical by
dedicated prose/body-preservation tests, not just eyeballed diffs.

This ticket is the epic's fourth and last child; found 3 more real, measured defects along the way
(the epic's 3rd and 4th overall findings: `camp`'s own wrong registry seed, and the scoping
document's own wrong "five artifacts" claim), on top of fixing the two originally-known convergence
targets (`succession`, `committed_intentions`) and finding two further self-contradictory
tier/label pairs (`demographic_cohort_cycle`, `cross_episode_grief_nemesis`) during implementation.
Filed one genuine follow-up (`TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT`) rather than
absorbing it as scope creep. `TCK-20260915-EPIC-MECHANISM-REGISTRY` closes alongside this ticket —
all 4 children done.
