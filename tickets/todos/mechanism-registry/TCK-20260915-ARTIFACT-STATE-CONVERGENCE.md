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
OPEN

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

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
