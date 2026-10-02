---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# Test Plan — TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION

Tests numbered R1–R9 (distinct from the death batch's T-series and the hazard ticket's H-series).

**Homes:** a combat-outcome unit home for the lattice tests, `tests/unit/progression/test_lifecycle.py`
for classification, serialization tests beside the existing component round-trips,
`tests/mechanic_scenarios/test_entity_death_authority_boundary.py` for the zombie contract,
`src/certification/scenarios.py`'s own tests for S4.6.

**Note on fixtures (from `rpg-implementer`):** `V2EntityBuilder` defaults to role **HERO, gen 1**. Every
fixture that does not explicitly set `.identity(role=...)` is a hero, so the "former hero" cases are the
*default* path, not an exotic one. Check each fixture rather than assuming.

## The retirement itself

**R1 — a lethal hit on a former hero records an ordinary combat death.** Formerly-rebirth-eligible
defender (role HERO), `generation` irrelevant now, driven to 0 HP. Assert `outcome_kind == "KILL"` (not
`REBIRTH`, not `PERMADEATH`), `death_reason == "COMBAT"`, `death_tick` set, `is_permadeath is True`, and
**succession / heir / heirloom dispatch fired**. The lineage half matters: the whole justification for
retirement is that continuity runs through reproduction and succession, so a test that only checks the
label would miss the point. Covers AC1.

**R2 — BOTH rebirth sites are retired.** Parameterise over `resolve_attack` **and**
`resolve_multi_attack`, asserting neither produces `REBIRTH`/`PERMADEATH` at any `generation` value
(test 1, 3, 4, 5 to cover the old `< 4` boundary on both sides). This is the investigation's Finding 1 —
retiring only `combat.py:183` would leave rebirth live on the only path the AI actually calls, and a test
hitting just `resolve_attack` would pass while the mechanic still ran. Covers AC1.

**R3 — the `REBIRTH` zombie class is closed.** On the branch that carries the death batch's R1, assert
**zero** entities end `hp == 0` with `lifecycle.active=True` via the former rebirth path, on the same
scenario that exposed it. This is the merge-blocker test: it must fail on a tree with the death batch but
without this ticket. Covers AC2.

**R7 — the death batch's HERO hold is genuinely released.** A hero starving to death records a real
passive `death_reason` with `is_permadeath=True` and full lineage — i.e. the role-blind passive branch
now behaves identically for heroes and non-heroes. Assert the *same* outcome for a HERO and a non-HERO
fixture with identical bio state; equality between the two is the assertion, since that is what "no role
is exempt" means. Covers AC5.

## `generation` removal (AC3)

**~~R4~~ — DROPPED (architecture review + rule-owner withdrawal, 2026-10-01).** v1 required
`LifecycleComponent.from_dict` and `CorpseState` deserialization to tolerate a legacy `"generation"`
key. **Neither deserializer exists** — both types define only `to_canonical_dict()`, consumed
write-only, and the only `from_dict`s in `src/core/state.py` are `SiegeState`/`FactionSentiment`/
`FactionState`/`ClanState`. Writing this test would have required *inventing* a deserializer on a frozen
durable component with no caller, purely to satisfy it. The rule owner withdrew the condition
("adding a deserializer with no caller just to satisfy my condition would be new durable surface for
nothing"). There is nothing left for R4 to assert.

**R4′ — the pinned-expectation sweep is performed and its result stated.** Removing the field from
`to_canonical_dict()` changes canonical state hashes. Search for every pinned expectation that moves:
stored state hashes, checkpoint/certification golden values, canonical-JSON fixtures, and determinism
tests comparing against a *recorded* hash rather than two live runs. **The architecture review searched
and found none** — the determinism gates compare two runs to each other
(`test_world_compile_determinism.py:56`, `:141`; `test_event_observability_parity.py:55`) and
`tests/regression/baseline_5k.json` is metrics-keyed, not hash-keyed. **Verify that independently and
record the outcome either way.** "Searched, none found" is a valid result but must be stated, not
implied. Anything found is re-baselined in the same change per
`TCK-20260824-TOWN-CENTER-POINTER-FIX` — disclosed, never loosened — with a follow-up filed for
anything out of scope.

**R4″ — no recorded-event consumer reads the `"generation"` payload back.** Condition 3 from the rule
owner: S4.5's sweep is written for *writers* of `life_arc_incoherent`; this asserts there is no
**reader** of the emitted payload's `"generation"` value. If one exists it must be handled in the same
change.

**R5 — no consumer still reads `generation`.** A structural check: assert no `src/` reference to
`lifecycle.generation`, `CorpseState.generation` or `generation_delta` survives. Prevents the
dead-plumbing outcome the investigation's Finding 4 warns about.

**The exclusion list must be mechanical, or a naive `generation` grep drowns** — same-word,
deliberately-unrelated hits: `ApplyPath.apply_generation`; the lab `generation` directory/status in
`audit.py`/`session.py`; `src/api/agent_ops_dashboard/ingest.py:240` ("legacy generations");
`GeneticsSystem`'s "first-generation parent" prose; and the `*_generation` identifiers
(`quest_generation`, `lead_generation_system`, `baseline_generator`). Match on the specific attribute
accesses, not the bare word.

**R6 — `life_arc_incoherent` leaves no orphaned literal. (v1's first clause was VACUOUS — deleted.)**
v1 said "assert the detector no longer emits". **It never emitted** — its own closed record
(`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`) shows 0 firings, and the `generation >= 2`
threshold was structurally unreachable per `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`.
Worse, `event_extractor.py:1283` reads `getattr(..., "generation", 1)`, so after removal the detector
would read the default `1`, fall below the threshold, and go **silently inert if left in place** —
non-emission proves nothing either way.

So assert **absence of the literals**, across the full set in plan S4.5: `event_extractor.py:66-67`,
`:100` (`_emitted_life_arc_incoherent`), `:116`, `:1283-1297`;
`simulation_quality/scorers/progression.py:27, :160, :162, :163-164`;
`config/simulation_quality/scoring_weights.yaml:106`;
`config/simulation_quality/entity_lifecycle_weights.yaml:31-36, :73, :160`;
`tools/entity_lifecycle_score.py:454-458`; the six docs; and the two parity entries
(`progression.yaml:1364-1391`, `infrastructure.yaml:8879`). **Carve out
`docs/audits/D21_entity_lifecycle_foundation_layers.md`** — dated audit, must NOT be swept.

**R6b — `conclusion_coherence`'s fate is decided, not defaulted.** `conclusion_incoherent_tags` has
exactly **one** member. Deleting it leaves the published metric structurally always "coherent". Assert
whichever the ticket decides — the metric is retired, or it is explicitly flag-less pending a
replacement signal. A silently-always-passing scored metric is the failure this guards.

**R8 — `src/certification/scenarios.py:170` ("One away from permadeath") is retired or rewritten, not
stripped.** That scenario exists to test rebirth. Assert either that it is gone, or that its rewritten
form asserts the new contract. Merely dropping its `generation=` argument would leave a scenario whose
name and intent no longer match anything — the exact drift this ticket is cleaning up.

## Architecture tests

**RA1 — `is_permadeath` survives as a separately tracked fact. (v1 was near-tautological — strengthen
it.)** Asserting "the field exists and is written" passes trivially. Pin the **writer**: assert
`resolve_lifecycle`'s death classification is what sets `is_permadeath_set`, and that nothing derives it
from `death_reason` or `active`. The assertion must be able to **fail** if someone replaces the write
with a derivation.

This is the STR-02 hook: a future declared resurrection process is the only thing permitted to produce a
recorded death with `is_permadeath False`. **This test's job is to make a future "simplification" fail
loudly**, so its docstring must say that in as many words.

**RA1b — the right `is_permadeath_set` is removed and the right one kept.** Two fields share the name
and have opposite fates (plan S5). Assert `LifecycleUpdate.is_permadeath_set` and `patches.py:83`
survive, **and** that `CombatUpdate.is_permadeath_set` and `patches.py:82` are gone along with all four
lift guards. Without this, v1's contradictory instructions ("don't remove `is_permadeath`" + "the guards
reduce to `is_permadeath_set is not None`") would leave four guards that can never be true feeding a
field that can never be set.

**RA2 — no role-gated lifecycle exemption remains on this path.** Assert no code path grants different
*lifecycle* outcomes on the basis of `EntityRole` (ID-02, CAUSE-04). Scope it to the lifecycle/death
path — the wider `HERO` privilege sweep is the separate de-hero epic, and this test must not be written
so broadly that it fails on reward or content coupling that is deliberately still in place.

**RA3 — determinism, re-pointed at the REAL exposure (v1 guarded the wrong thing).** v1 said "the
corpus baseline hash will shift once". **That has no referent** — no canonical-hash literal is pinned
anywhere (see R4′). The self-consistency assertion (same seed/world → identical results across two
runs) is still worth keeping, but it is not where the risk is.

**The real exposure is behavioural.** Removing `combat.py:136` makes `EntityRole.HERO` entities lethally
killable through `resolve_attack` for the first time, and `V2EntityBuilder` defaults to role HERO — so
mortality and population dynamics move **corpus-wide**. That lands on grade anchors, corpus-diversity
floors, `baseline_5k.json` **metrics**, and the **certification suite, a
`docs/testing/regression_policy.md` §2 hard gate** whose registered scenario list includes
`COMBAT_ARENA_MORTALITY` (`src/certification/scenarios.py:525`, `:559`).

So RA3 must: (a) keep the two-run self-consistency check; (b) **name and re-run the certification
suite explicitly** (plan S2b), stating its result; (c) treat moved metrics as a disclosed re-baseline
under `regression_policy.md` §9-11, never a loosened assertion.

**RA4 — inventory the tests that pin the removed mechanism BEFORE editing them.** The plan's "Starting
state" names two files; the architecture review found **at least ten**:
`tests/unit/progression/test_lifecycle.py`, `tests/unit/combat/test_combat_rewards.py`,
`tests/unit/combat/test_rpg_core_recovery.py`, `tests/unit/movement/test_tactical_movement.py` (incl.
`:121`), `tests/unit/domains/combat_engagement/test_learning_outcome.py`,
`tests/unit/engine/test_combat_actions_learning_wiring.py`,
`tests/unit/world/test_world_lifecycle_regression.py:17`,
`tests/unit/observability/test_event_extractor_progression.py`,
`tests/simulation_quality/test_progression_scorer.py`, `tests/tools/test_entity_lifecycle_score.py`.
Deleting a test that pins deliberately-removed behaviour is legitimate under `regression_policy.md` §6,
**but two of these are parity `test_path`s** (COMB-297, COMB-311) — so each deletion must be an
**itemized decision recorded with the parity update**, not discovered mid-implementation.

## Regression-prone paths

- `resolve_lifecycle:202`'s outcome tuple — the death batch is adding `DEFEAT` while this ticket removes
  `PERMADEATH`. **Run both tickets' lifecycle tests together after both land**, not separately.
- The four `generation_delta` lift guards reducing to `is_permadeath_set is not None` — this is the same
  code the hazard ticket's R4 finding concerns; re-read it rather than assuming the reduction is safe.
- `_DEFEATED_OUTCOME_KINDS` membership after the fold — assert it still yields "LOST" for the defender
  of a lethal hit, so combat learning is unchanged.

## Out of scope

No new `@slow` tests. **SimQ is not a valid signal** — 13 of 15 grade anchors are red on untouched
`main`, ~10 non-deterministic by construction, and the nightly corpus-diversity CI step has been failing
since at least 2026-09-07 (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`). Expect the corpus
anchors to shift when `REBIRTH`/`PERMADEATH` stop being emitted; that is a re-baseline under
`regression_policy.md` §9-11, not evidence about this change.
