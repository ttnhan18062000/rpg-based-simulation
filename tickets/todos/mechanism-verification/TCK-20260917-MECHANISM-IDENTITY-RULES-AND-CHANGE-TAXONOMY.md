---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
phase: open
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY

## Title
Define what makes one mechanism one mechanism, and what a design proposal does to the registry —
then test both against the registry's own bundled entries

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The registry holds 89 mechanisms and **no rule decides what one mechanism is.** The granularity was
inherited twice over from decisions nobody made deliberately:

- **71 entries came from atlas cards** — whatever the atlas author thought deserved a card, across 69
  revisions.
- **11 came from code enumeration** — one per `src/domains/` directory or `src/systems/*_systems/`
  file cluster, which is the filesystem's granularity, reflecting how files were organised rather
  than how the simulation is structured.

The inconsistency is visible in the ids themselves. Some are a single concept — `movement`,
`emotion`, `perception`. Others bundle two or three: `regional_trauma_hazards_sovereignty`,
`inventory_trade_conservation`, `information_trust_deception`, `cognition_capacity_fatigue`,
`attributes_biology`, `buildings_town_services`, `calamities_boss_spawns`. Meanwhile combat is split
three ways across `combat_engagement`, `tactical_decision` and `combat_resolution`. One domain gets
three rows; another gets three concepts in one row.

This is not cosmetic. Accidental granularity **hides real findings** — see `action_pacing_readiness`
in Assumptions below.

## Scope

### 1. State the identity rule

Proposed, derived from splits this project already made by instinct:

> A mechanism is the smallest unit that is both **(a)** intended as a capability by someone, and
> **(b)** able to independently succeed or fail.

Both clauses are load-bearing. Intent alone yields atlas cards, which bundle. Independent failure
alone yields every function in the codebase.

**Operational test: if the two halves could sit in different `state` values, they are two
mechanisms.** That is self-justifying for this registry — recording whether things work is its whole
purpose, so anything requiring two answers requires two rows.

It reproduces both splits made during Foundation (`aging_death`/`succession`,
`xp_leveling`/`breakthrough_bonuses`) — each split precisely because one half was `done` and the
other `orphan`.

### 2. Record the change taxonomy

What a design proposal does to the registry. Seven kinds, each with a predictable consequence:

| Kind | Registry effect |
|---|---|
| **Introduce** | new entry |
| **Extend** | same entry, may move `partial` → `done` |
| **Wire** | state change only (`orphan`/`gated` → `done`), no new logic |
| **Tune** | **no registry change** — values are not in the registry |
| **Split** | one entry becomes two, because the halves diverged |
| **Retire** | entry → `gap`, plus a verdict recording why |
| **Interpose** | an **edge** change: `A → B` becomes `A → C → B` |

**`Wire` versus `Introduce` is the distinction that matters most historically.** Most of the
dormant-mechanism arc was wiring — the code existed and was correct, and only the state changed.
Describing that as "implementing a feature" is how documents came to claim things worked.

**`Interpose` is the only kind that changes graph structure rather than node content** — one edge
removed, two added, when an existing dependency is judged inefficient and a new mechanism is placed
between. It is `Introduce` plus a declared edge rewrite, and it needs naming separately because the
registry's `depends_on` is the thing being restructured.

### 3. Test the identity rule against the bundled entries

Apply it to `inventory_trade_conservation`, `cognition_capacity_fatigue`,
`information_trust_deception`, `regional_trauma_hazards_sovereignty`, `attributes_biology`,
`buildings_town_services`, `calamities_boss_spawns`. Record per entry: split, or leave alone, with
the reason.

**A rule that splits all of them is too aggressive; one that splits none is doing no work.** Report
which it is before acting on the results.

## Out of Scope
- **Implementing the declared-versus-actual diff check.** A proposal stating its registry diff, then
  checked against what actually landed, is the natural follow-up — but the rules must survive contact
  with real entries first.
- **Forcing uniform granularity.** `inventory_trade_conservation` may be genuinely cohesive. The goal
  is a stated criterion, not symmetry.
- **Re-splitting the combat mechanisms.** They are already fine-grained; this ticket asks whether the
  coarse entries are wrong, not whether the fine ones should be merged.
- **Changing `layer`.** It encodes frequency and scope, not abstraction level, and that is correct.

## Acceptance Criteria
1. The identity rule and the seven-kind change taxonomy are recorded in
   `docs/plans/mechanism_claims_as_tests_initiative.md` or a sibling, not in a ticket body alone.
2. Every bundled entry named in Scope §3 has a recorded split-or-keep decision with its reason.
3. The rule demonstrably discriminates — it splits some entries and leaves others alone. If it does
   neither, report that as the finding and do not apply it.
4. `action_pacing_readiness` is assessed explicitly against the rule (see Assumptions).
5. Any split performed propagates to `depends_on`, derived priority, and the affected `verified`
   blocks — a split that leaves one verdict covering two mechanisms reproduces the defect it fixes.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-VERIFICATION` — sibling concern; this is registry semantics rather
  than verification tooling
- `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` — same shape: re-examine existing entries
  against a stated criterion
- `TCK-20260831-READINESS-SPEED-FORMULA` — the agility-scaling half of `action_pacing_readiness`

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md`
- `docs/plans/mechanism_registry_initiative.md` §2 — the six-state vocabulary the rule keys on

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — the atlas-card
  seed and its two splits

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py` — validation, would enforce any schema consequence
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — splits change dependent-counts

## Assumptions / Open Questions
1. **`action_pacing_readiness` is the live case, and it is why this ticket exists.** It is one entry
   at `partial`, but it is two things with *different* states: a readiness gate that is
   runtime-verified and works, and agility-derived `readiness_speed`, which has a real formula on a
   recalculation path that fires for no entity in any corpus world. Under the rule we already applied
   twice, that is two mechanisms — a verified `done` gate and an orphaned scaling half. As one row it
   carries a single verdict covering a working half and a broken half, with the distinction buried in
   prose. **If the rule does not split this, the rule is wrong.**
2. A split changes transitive dependent-counts and therefore derived priority. `action_pacing_readiness`
   currently shows 25 dependents; those presumably depend on the *gate*, not the scaling. The split
   may move priority substantially.
3. Whether the change taxonomy belongs in the proposal template itself is unresolved — that decision
   waits on the rules proving useful.
4. The taxonomy applies to **gameplay** proposals. Infrastructure work (the registry epic itself)
   introduces no mechanisms and is out of its scope.

## Implementation Notes
These rules were derived from roughly six real cases. That is enough to be worth writing down and
not enough to be confident — hence §3 testing them against entries that were *not* used to derive
them, before anything is applied.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
