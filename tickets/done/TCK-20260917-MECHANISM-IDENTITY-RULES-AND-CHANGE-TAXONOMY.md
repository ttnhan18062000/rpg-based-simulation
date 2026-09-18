---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
phase: done
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY

## Title
Define what makes one mechanism one mechanism, and what a design proposal does to the registry —
then test both against the registry's own bundled entries

## Status
DONE

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

**Second test case, added 2026-09-17, a different shape than `action_pacing_readiness`.**
`combat_resolution` is reached by two structurally different callers at wildly different real
volumes: the decision-driven path (`tactical_decision` → `ActionRouter.execute_action()` →
`CombatResolutionSystem.resolve_attack()`, 0-2 calls per 1000-2000 ticks across three corpus
worlds) and the incidental opportunity-attack path (`movement`'s own mechanic calling
`resolve_multi_attack()` directly, 181-2177 calls per 1000 ticks in the same worlds) — see
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum. This is **not
obviously a split** the way `action_pacing_readiness` is: both callers invoke the *same*
combat-resolution logic, correctly, and there is no `state` divergence between them the way there
is between the gate and the scaling half of `action_pacing_readiness` — `combat_resolution` itself
is `done` regardless of which caller reached it. The candidate shape here is closer to "one
mechanism, two entry points, wildly different real utilization" than "two mechanisms sharing an
id." The identity rule (§1) needs an explicit answer for this shape: does "smallest unit that can
independently succeed or fail" apply per-entry-point, or does a mechanism stay one unit as long as
its own internal logic is single and correct, regardless of how many callers reach it and how
unevenly? Record the answer, and whether `combat_resolution` splits or not, with the same reasoning
rigor as `action_pacing_readiness`.

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
6. `combat_resolution`'s own multiple-entry-path shape (Scope §3, added 2026-09-17) is assessed
   explicitly against the rule, with a stated answer for whether "smallest independently
   succeed-or-fail unit" is per-entry-point or per-implementation — not left as an unaddressed
   second case alongside `action_pacing_readiness`.

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
5. **Whether `depends_on` means "requires to exist" or "execution-flow," added 2026-09-17, not
   resolved here — genuinely open, not a definitional nicety.** The registry's own stated rule for
   `depends_on` is "requires to exist in order to function," not "invokes" or "runs before." Two
   already-declared edges on `combat_resolution` test this concretely, not hypothetically:
   `movement` (measured 2026-09-17: its own opportunity-attack mechanic is what actually triggers
   181-2177 of `combat_resolution`'s real calls per 1000 ticks in three corpus worlds — a real
   trigger, but does `combat_resolution` *require* `movement` to exist, or does it just happen to be
   invoked from there today?) and `tactical_decision` (0-2 real calls in the same worlds — the
   "requires to exist" claim is even harder to defend for an edge this rarely exercised). Neither
   edge obviously satisfies the stated rule as written. **This has a real consequence beyond
   semantics**: derived priority (`tools/mechanism_registry/generate_mechanism_priority_view.py`) is
   computed from these same `depends_on` edges. If some declared dependencies are actually
   execution-flow rather than genuine existence-requirements, the derived priority ranking is
   measuring something other than real blast radius — and "what to fix next" rests on that ranking.
   Whoever resolves this identity-rules ticket should give `depends_on` a real, checkable definition
   (or explicitly two edge kinds) rather than leave it looser in practice than the one sentence that
   currently defines it.

## Implementation Notes
These rules were derived from roughly six real cases. That is enough to be worth writing down and
not enough to be confident — hence §3 testing them against entries that were *not* used to derive
them, before anything is applied.

**Landed in `docs/plans/mechanism_identity_and_change_taxonomy.md`** (full reasoning there, see
`stored_artifacts/TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY/investigation.md` for
the methodology, including a forked sub-agent that returned an unverified "split everything" claim
that was independently re-checked and partially reversed before being trusted).

**Result: 4 splits, 5 keeps — the rule discriminates (AC #3).**
- SPLIT: `regional_trauma_hazards_sovereignty` → `regional_trauma`/`regional_sovereignty`;
  `buildings_town_services` → `buildings`/`town_services`; `calamities_boss_spawns` →
  `calamity_intensity`/`world_boss_spawn`; `action_pacing_readiness` → itself (gate) +
  `readiness_speed_scaling` (the falsification test — it does split, AC #4).
- KEEP: `inventory_trade_conservation`, `cognition_capacity_fatigue`, `information_trust_deception`,
  `attributes_biology` (an early, unverified fork claim said SPLIT; direct re-check found no real
  divergence and reversed it), and `combat_resolution` (the multiple-entry-point case — multiple
  callers at wildly different volumes is not itself a split signal, since both callers invoke
  identical internal logic with no possible `state` divergence between them).
- The `depends_on` semantics question resolved by applying the registry's own already-stated
  definition (not inventing a new one): `combat_resolution`'s `tactical_decision` edge removed
  (execution-order, not a functional dependency); its `movement` edge kept (a genuine functional
  dependency, despite the call direction pointing the other way).
- A real defect caught and fixed along the way: `regional_sovereignty`'s first-guessed
  `implemented_by` binding (`RegionalSovereigntyService`) has zero real callers; corrected to the
  actual live implementation (`FactionInfluenceService`) before this ticket closed.
- 4 pre-existing pinned tests updated for real, explained reasons (see investigation.md) — none
  routed around.

## Test Summary
`tests/unit/tools/`, `tests/unit/engine/test_capability_registry.py`, `tests/mechanic_scenarios/` →
181 passed. `graphify-out/` moved aside and restored as a sanity check (only registry/mapping data
changed, not `src/`/`tests/` code).

## Files Changed
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — new, the identity rule + taxonomy.
- `registries/mechanisms.yaml` — 4 splits performed, `combat_resolution`'s `tactical_decision` edge
  removed, `regional_sovereignty`'s `implemented_by` corrected.
- `tools/mechanism_registry/mechanism_atlas_card_mapping.py`,
  `mechanism_capabilities_card_mapping.py` — 3 stale mapping entries repointed at split successors.
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html` — 2 badge/tier fixes
  from the resulting drift check.
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_priority_view.md`,
  `mechanism_registry_view.md`, `mechanism_registry.html` — all 4 regenerated (93 mechanisms).
- `tests/unit/tools/test_mechanism_priority_derivation.py`,
  `test_mechanism_atlas_regenerate.py` — 3 pinned-count/assertion updates.
- `staging_artifacts/TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY/` — this ticket's
  own investigation.md/plan.md/test_plan.md.

## Completion Summary
Done. The identity rule and change taxonomy are recorded in a real doc, tested against all 9 real
cases (7 bundled entries plus the two special cases), and the rule demonstrably discriminates (4
splits, 5 keeps) rather than splitting everything or nothing. Every split propagated to
`depends_on`, dependents, `verified` blocks, and consumer artifacts. A real defect
(`regional_sovereignty`'s wrong `implemented_by` binding) was caught and fixed as a direct
consequence of doing this investigation properly rather than trusting an unverified sub-agent
report. `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` is now unblocked.
