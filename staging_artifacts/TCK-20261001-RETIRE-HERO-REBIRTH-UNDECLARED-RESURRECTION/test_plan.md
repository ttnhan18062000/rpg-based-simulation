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

**R4 — legacy `"generation"` keys load without error.** `LifecycleComponent.from_dict` **and**
`CorpseState` deserialization each accept a dict containing a legacy `"generation"` key and **ignore**
it. Required by the rule owner so old saves, replays and fixtures still load. Assert no exception and no
attribute created. **This is the test most likely to be skipped and most likely to matter** — a hard
failure here breaks replay of every pre-retirement run.

**R5 — no consumer still reads `generation`.** A structural check: assert no `src/` reference to
`lifecycle.generation`, `CorpseState.generation` or `generation_delta` survives, excluding the
deliberately-unrelated `ApplyPath.apply_generation` and the lab `generation` directory/status. Prevents
the dead-plumbing outcome the investigation's Finding 4 warns about, where a field exists, is threaded
through four lift sites and a patch, and can never be non-zero.

**R6 — `life_arc_incoherent` is retired cleanly, with nothing orphaned.** Assert the detector no longer
emits, and that no registered or consumed `life_arc_incoherent` literal remains in the event-type
registry, SimQ scorers, tests, docs or parity entries. The failure mode this guards is a scorer or
registry entry left pointing at an event type that can never fire again — silent dead weight that looks
like coverage.

**R8 — `src/certification/scenarios.py:170` ("One away from permadeath") is retired or rewritten, not
stripped.** That scenario exists to test rebirth. Assert either that it is gone, or that its rewritten
form asserts the new contract. Merely dropping its `generation=` argument would leave a scenario whose
name and intent no longer match anything — the exact drift this ticket is cleaning up.

## Architecture tests

**RA1 — `is_permadeath` survives as a separately tracked fact.** Assert the field still exists and is
still written by a lifecycle death classification, **not** derived from `death_reason` being non-`None`.
This is the STR-02 hook: a future declared resurrection process is the only thing permitted to produce a
recorded death with `is_permadeath False`. **This test's job is to make a future "simplification" fail
loudly**, so its docstring must say that in as many words.

**RA2 — no role-gated lifecycle exemption remains on this path.** Assert no code path grants different
*lifecycle* outcomes on the basis of `EntityRole` (ID-02, CAUSE-04). Scope it to the lifecycle/death
path — the wider `HERO` privilege sweep is the separate de-hero epic, and this test must not be written
so broadly that it fails on reward or content coupling that is deliberately still in place.

**RA3 — determinism.** A named seed/world produces identical results across two runs after the change.
Field removal changes canonical dicts, so the corpus baseline hash will shift **once** — re-baseline
deliberately, state the old and new values, and never loosen an assertion to absorb it.

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
