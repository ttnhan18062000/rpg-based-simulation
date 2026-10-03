---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# Plan — TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION

**v2**, incorporating `architecture-reviewer`'s `NEEDS_CHANGES` verdict of 2026-10-01. Read
`investigation.md` first.

Both design questions are closed: **Q1** fold `REBIRTH`+`PERMADEATH` into `KILL`, keep `is_permadeath`;
**Q2** remove `lifecycle.generation` (rule owner, on the user's explicit delegation).

## Architecture review — verdict `NEEDS_CHANGES`, five substantive corrections

The reviewer did **not** re-litigate the retirement and endorsed: both rebirth sites and no third;
removing `rebirth_eligible` outright; keeping `is_permadeath` as the STR-02 hook; retiring rather than
re-pointing `life_arc_incoherent`; removing `generation` rather than re-grounding it; retiring rather
than stripping the mortality scenario; refusing to leave `generation_delta` as dead plumbing; and not
rewriting dated evidence. It also confirmed no durable state is created, no decision logic gains
mutation authority, and no raw domain model reaches an API (no `generation`/`REBIRTH`/`PERMADEATH`
anywhere in `src/api/`, `src/views/`, `src/rendering/`).

The planner independently re-verified the three load-bearing claims before accepting (no deserializer;
`TERMINAL_COMBAT_OUTCOME_KINDS` absent on this branch; `COMB-311` P1 and on the reduced tuple).

### RESOLVED — correction 1: straight removal, no shim (rule owner, 2026-10-01)

**The legacy-key tolerance is WITHDRAWN by the rule owner**, which confirmed the finding on
`origin/main` and said plainly: "I wrote `to_dict` and assumed a load path without checking. Adding a
deserializer with no caller just to satisfy my condition would be new durable surface for nothing."
**Straight removal, no compatibility shim.** Three conditions replace it:

1. **Find and re-baseline every pinned expectation the canonical-dict change moves** — stored state
   hashes, checkpoint/certification golden values, canonical-JSON fixtures, and any determinism test
   comparing against a *recorded* hash rather than two live runs. Re-baseline them **in the same
   change**, list each one in the ticket, follow the `TCK-20260824-TOWN-CENTER-POINTER-FIX` precedent
   (disclose and re-baseline, **never loosen the assertion**), and file a follow-up for anything that
   cannot be re-baselined in scope rather than leaving one red.
   **Reconcile with the reviewer first:** it searched and found **no pinned canonical-hash literal
   anywhere** — the determinism gates compare two runs to each other
   (`tests/certification/test_world_compile_determinism.py:56`, `:141`;
   `test_event_observability_parity.py:55`) and `tests/regression/baseline_5k.json` is **metrics-keyed**
   (`version/world_id/seed/ticks/metrics`), not hash-keyed. So this condition may well come back empty.
   **Verify rather than assume either way**, and record the result — "searched, none found" is a valid
   and useful answer here, but it must be stated, not implied.
2. **The forward-compatibility point goes in the divergence entry, as prose, not code:** existing
   `final_state.canonical.json` evidence keeps its `"generation"` key and its original meaning (a
   rebirth count as of the emitting run). Dated evidence; not rewritten.
3. **Re-check the `life_arc_incoherent` retirement under the same lens:** if any recorded-event consumer
   reads the payload's `"generation"` **back** (as opposed to only writing it), handle that in the same
   change. S4.5's sweep is written for writers; this asks specifically about readers.

**R4 is dropped** — it cannot be written without inventing the deserializer, and there is now nothing
for it to assert. C1–C5 are unaffected (they never mention the field's serialization).

The finding, for the record. Verified at
`2f7e74b0c`: `LifecycleComponent` (`state.py:157`) and `CorpseState` (`:1217`) define **only**
`to_canonical_dict()` — **no `from_dict`, no `to_dict`**. The only `from_dict`s in that file are
`SiegeState` (`:259`), `FactionSentiment` (`:742`), `FactionState` (`:792`), `ClanState` (`:846`). There
is no `from_canonical_data` and no restore path; `to_canonical_dict` is consumed **write-only** (hashing
in `engine/checkpoint.py`, and `final_state.canonical.json` evidence in `certification/harness.py`).
`LifecycleComponent(...)` is constructed in one place (`core/builder.py:106`), `CorpseState(...)` in one
(`engine/apply_plan.py:341`).

So "old saves/replays/fixtures still load" is not a live failure mode — **nothing loads state from a
dict**. Implementing it would mean adding a deserializer to a frozen durable component with no caller,
purely to satisfy a test: new durable surface created to pass a check.

Note the planner's own error here too: the per-consumer list said "the field *and its `to_dict`*" and
the planner passed that through without checking that a `to_dict` existed.

## Starting state — this lands ON TOP of the death batch + hazard diff

From `rpg-implementer`'s in-progress worktree (`entity-death-cause-at-writer`, uncommitted):

- **`combat.py` is untouched** — S1/S2/S3 start from pre-batch `combat.py`.
- **`lifecycle.py` has gained** `DEFEAT`, `HAZARD` and passive-cause branches behind **one shared
  idempotency guard**; the `("KILL", "PERMADEATH")` tuple is still intact.
- **`patches.py` is clean** and `updates.py` differs from S4.2's list **only** by a new
  `CombatUpdate.hazard_damage` field (the hazard fix's independent hazard signal). So both
  `is_permadeath_set` producers and all the `generation_delta` producers are **untouched by the batch**
  and can be treated as pre-batch.
- **Nothing is committed or pushed** in that worktree — there is no authorization to commit before the
  batch is complete. The diff is readable at
  `/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/entity-death-cause-at-writer`
  (`git diff HEAD` there) if the exact ground matters.
- **Sweep result on the batch + hazard fix** (broad non-slow scope incl. certification, architecture,
  docs, integrity, static): **11361 passed, 7 failed** — 3 pre-existing on base
  (`test_behavioral_5k_regression`, `test_long_run_stability`,
  `test_bravery_quartile_combat_rate_2x`), and 4 that pass individually on both branch and base
  (`test_startup_validation.py::test_aggressive_budget_warning`,
  `test_envelope_violations.py::test_harness_detects_missing_degradation_mode`,
  `test_harness_contract.py::test_certification_detects_semantic_drift`,
  `test_resilience_recovery.py::test_harness_catches_failed_recovery`), treated as load-sensitive in a
  20-minute run. **Do not read those 7 as caused by this ticket.**
- Two test files reference `REBIRTH`/`generation`:
  `tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py` and the boundary
  test. (The reviewer found **at least ten** in total — see S6.)

## Steps

### S1 — Retire BOTH rebirth sites (verified: there is no third)
`combat.py:182-188` (`resolve_attack`) **and** `:407-413` (`resolve_multi_attack`). The second is the
live one; `resolve_attack`'s own comment records "0 real calls in 2000-tick runs". The reviewer
confirmed the other resolution entry points (`resolve_skill_usage:256`, `resolve_aoe_attack:457`,
`resolve_opportunity_attack:246`) call the same classifier but **never read `rebirth_eligible`**.

**Stale doc warning:** `docs/guidelines/intentional_divergences.md:695` claims `resolve_aoe_attack`
reads `classification.rebirth_eligible`. **It does not.** Don't hunt a fourth site; correct that line
(S5).

Remove `rebirth_eligible` from `RewardClassification` **entirely** (approved — per-call, non-durable,
no serialization, no API exposure; always-`False` would be the dead structure this ticket deletes):
`combat_rewards.py:24, :41, :49, :59, :68, :106`.

**Incidental:** `combat.py:136` sits *before* `resolve_attack`'s docstring, making the docstring a no-op
string expression. Removing the line (S3) fixes that — do not preserve the odd ordering.

### S2 — Fold `REBIRTH`/`PERMADEATH` into `KILL`
A lethal hit records an ordinary `COMBAT` death: `death_tick`, `is_permadeath=True`, and
succession/heirs/heirlooms firing as for any subject.

**Conditional, because the constant does not exist on this branch** (planner verified:
`TERMINAL_COMBAT_OUTCOME_KINDS` appears nowhere in `src/` or `tests/`; `combat_constants.py` holds only
`NEAR_DEATH_HP_RATIO`; `learning_outcome.py:33` is still a literal tuple):
- **If `TERMINAL_COMBAT_OUTCOME_KINDS` is present** (the batch's diff): remove `"REBIRTH"` and
  `"PERMADEATH"` from that single constant and let `_DEFEATED_OUTCOME_KINDS` follow.
- **If absent:** edit `learning_outcome.py:33` directly.
Either way `KILL` remains, so the combat-learning layer sees an unchanged "defender lost" signal.

`resolve_lifecycle`'s `("KILL", "PERMADEATH")` tuple reduces to `("KILL",)`. **Merged-edit invariant to
satisfy, stated because two changes interact:** removing `combat.py:136` means a lethal hit on a former
hero now yields `KILL` where it previously yielded `DEFEAT`, while the death batch is simultaneously
adding a `DEFEAT` branch. The invariant is **every outcome kind meaning "the defender died" is handled
by exactly one branch, and the shared idempotency guard still fires exactly once.** Assert branch
membership against the single terminal-outcome constant rather than a hand-written tuple — that also
makes the S2 conditional moot.

### S2b — MANDATORY: re-run the certification suite after S3
`docs/testing/regression_policy.md` §2 makes certification a **hard gate**, and removing
`combat.py:136` makes `EntityRole.HERO` entities lethally killable through `resolve_attack` for the
first time — with `V2EntityBuilder` defaulting to role HERO, mortality and population dynamics move
corpus-wide. `COMBAT_ARENA_MORTALITY` is in the registered scenario list
(`src/certification/scenarios.py:525`, `:559`). **Re-run certification explicitly after S3 and state the
result**; do not rely on it being swept up by a broad run. Confirmed required by `rpg-implementer`.

### S3 — Remove `combat.py:136`'s role clause
`is_lethal = is_lethal and (defender.identity.role != EntityRole.HERO)` → `is_lethal` means only what
the caller passed. **The only `EntityRole.HERO` coupling in scope**; rewards, hero-guild content,
`hero_adventurers` and `HERO_*` event names belong to the de-hero epic.

### S4 — Remove `generation` (S4.1/S4.4 migration shape HELD, see above)

1. `LifecycleComponent.generation` — `state.py:169`, and its entry in `to_canonical_dict` at `:191`.
   `builder.py:586`, `:606` (the `V2EntityBuilder.lifecycle(generation=...)` **construction kwarg** —
   do **not** make it silently swallow unknown kwargs; that would swallow typos too).
2. **`src/core/updates.py` — missing from v1 entirely:** `CombatUpdate.generation_delta` (`:115`) with
   its `is_noop` (`:129`) and `merge` (`:149`); `LifecycleUpdate.generation_delta` (`:447`) with
   `is_noop` (`:462`) and `merge` (`:476`). Producers `combat.py:235`, `:448`. The four lift sites
   (`movement.py:250-252`, `domain/combat_actions.py:111-113`, `domain/skill_actions.py:125-127`,
   `domain/aoe_actions.py:75-77`) and **`patches.py:82`**. Test
   `tests/unit/movement/test_tactical_movement.py:121`.
   **`is_noop`/`merge` participate in update coalescing, which is determinism-adjacent — editing them is
   behaviour-neutral *only because* the field is provably always 0 after S1/S2.** Say that in the diff.
3. The rebirth branches — gone via S1.
4. `CorpseState.generation` (`state.py:1224`, `:1236`), written at `apply_plan.py:347`. Exactly **one
   producer and no consumer at all**, which strengthens removal.
5. **`life_arc_incoherent` — retire the detector entirely, sweep wider than v1 said.** Its premise is "a
   completed Hero's Journey rebirth already occurred". Full consumer set:
   - `event_extractor.py:66-67` (`_LATE_GENERATION_THRESHOLD` + comment), **`:100`
     (`_emitted_life_arc_incoherent` dedupe set) and `:116` (its reset)**, `:1283-1297`.
   - `src/simulation_quality/scorers/progression.py:27, :160, :162, :163-164`.
   - **`config/simulation_quality/scoring_weights.yaml:106`** (`life_arc_incoherent: -15.0`).
   - **`config/simulation_quality/entity_lifecycle_weights.yaml:31-36`**
     (`life_arc_generation_threshold: 2`, "mirrors `_LATE_GENERATION_THRESHOLD`"), **`:73`**, **`:160`**
     (`conclusion_incoherent_tags`).
   - **`tools/entity_lifecycle_score.py:454-458`** — emits `"life_arc_detector_reachable": None`.
   - Docs: `docs/simulation_quality/quality_scoring_contract.md` §7.6, `current_state.md`,
     `event_type_coverage.md`, `extension_points.md`, `entity_lifecycle_score.md`,
     `docs/guides/entity_lifecycle_score.md`. **Carve out
     `docs/audits/D21_entity_lifecycle_foundation_layers.md` — dated audit, do not rewrite.**
   - Tests: `tests/unit/observability/test_event_extractor_progression.py`,
     `tests/simulation_quality/test_progression_scorer.py`, `tests/tools/test_entity_lifecycle_score.py`.

   **Decide, do not discover:** `conclusion_incoherent_tags` has exactly **one** member. Deleting it
   leaves the published `conclusion_coherence` metric with no incoherent signal, i.e. structurally
   always "coherent". **Decide that metric's fate in this ticket** — retire it, or state in writing that
   it is flag-less pending a replacement signal. Do not just delete the literal.
6. `src/certification/scenarios.py` — `build_mortality_test` (`:146`) exists *for* this mechanic
   (docstring "Setup a hero dying to verify rebirth/permadeath"; `.lifecycle(generation=3) # One away
   from permadeath` at `:170`). **Retire or rewrite the scenario**, don't strip the argument. Registry
   coordinates it must touch: the `"COMBAT_ARENA_MORTALITY"` dispatch at `:525-526`, the scenario-ID
   list at `:559`, and its consumer `tests/unit/combat/test_rpg_core_recovery.py:54`, `:86`. The other
   six `.lifecycle(generation=1)` sites (`:119, :131, :298, :322, :365, :377`) are plain defaults and
   can simply be dropped.

**Out of scope — same word, unrelated:** `ApplyPath.apply_generation`; the lab `generation`
directory/status in `audit.py`/`session.py`; `src/api/agent_ops_dashboard/ingest.py:240` ("legacy
generations"); `GeneticsSystem`'s "first-generation parent" prose; and `*_generation` identifiers
(`quest_generation`, `lead_generation_system`, `baseline_generator`).

### S5 — `is_permadeath`: two lists, opposite fates (correction 3)
v1 said "do not remove `is_permadeath`" **and** "the guards reduce to `is_permadeath_set is not None`",
which together would have kept four guards that can never be true feeding a field that can never be
set — the symmetric mistake to the one this ticket correctly refuses for `generation_delta`.

- **STAYS:** `LifecycleComponent.is_permadeath` (`state.py:166`, `:188`);
  `LifecycleUpdate.is_permadeath_set` (`updates.py:448`, `:463`, `:477`); the `resolve_lifecycle:214`
  writer; **`patches.py:83`**.
- **GOES:** `CombatUpdate.is_permadeath_set` (`updates.py:116`, `:150`); its only producers
  `combat.py:236` and `:449` (`perma_set` is set *only* inside the deleted PERMADEATH branch, so it
  becomes permanently `None`); therefore **all four lift guards**; and **`patches.py:82`**.

**Useful for the comment:** `resolve_lifecycle:214` **already** sets `is_permadeath_set=True` for every
death including old age, so the fold changes nothing about its distribution and creates no new dead
state. Say that, plus that it is *currently uniformly True by design* and is the STR-02 hook — so a
future reader holding the Durable State Rule doesn't read it as undeclared redundancy.

### S6 — Docs, law and parity
- `docs/mechanics/02_combat_laws.md:62-66` — rewrite §"The Hero's Journey (Generations)".
- **`docs/mechanics/04_strategic_cognition.md:1696`, `:1716-1718`** — a **Certified L1** chapter that
  enumerates `outcome_kind`'s real values and reasons that "under `REBIRTH` specifically, [the memory]
  is real signal". Leaving it is a parity violation against a chapter declared bit-identical to source.
- **`docs/mechanics/damage_formula_contract.md:137-139`** — documents "not rebirth eligible" per reward
  category; goes with the `rebirth_eligible` removal.
- **`docs/guidelines/intentional_divergences.md` §2.34 — SUPERSEDE, do not delete.** The implementer owns
  the wording (it is a guidelines doc, not the catalog), under two constraints from the rule owner:
  - **Mark §2.34 `SUPERSEDED`** with the date and a pointer to this ticket's new entry; **update its
    table row at `:36`** to match; and **leave the original body readable below the marker as history**.
    The superseded marker must **say explicitly that the old `Verification` path no longer exists** —
    otherwise a reader takes it for a broken reference rather than a retired one.
  - **Correct the false `:695` claim in place as a dated erratum *inside* the superseded entry** —
    e.g. "Erratum <date>: `resolve_aoe_attack` never read `rebirth_eligible`; verified at <sha>".
    **Do not silently edit it.** As the owner put it: a ratified record that was wrong when ratified
    should show that it was wrong.
  - Then add the new entry (class **Intentional Gameplay Change**, citing STR-02/ID-02/CAUSE-04 and the
    reproduction continuity model) carrying current behaviour and its own `Verification` path, including
    the owner's line in substance: *lineage depth, if needed, is derived from the birth record's parent
    links when lineage design declares it (ID-06)*, plus condition 2's forward-compatibility note.
- **Parity — `COMB-311` was missing from v1 and is the load-bearing one.** Planner verified:
  `status: verified`, `priority: P1`, and its text **is** about `resolve_lifecycle`'s combat-death check
  matching only `"KILL"` and never `"PERMADEATH"` — exactly the tuple S2 reduces. Its `test_path`
  (`tests/unit/progression/test_lifecycle.py::test_permadeath_death_classification`) is invalidated by
  S2, and **a P1 entry requires a passing `test_path`**, so it must be rewritten with a new one (or
  re-statused) in this same session. Plus `combat_movement.yaml::COMB-297` (P2 — its `test_path`
  `test_opportunity_attack_lethal_hero_defender_triggers_rebirth` is deleted by this ticket),
  `progression.yaml:1364-1391` (the `life_arc_incoherent`/`generation >= 2` entry and its 2026-08-08
  divergence note), and `infrastructure.yaml:8879`. Re-check `PROG-030` is unaffected. **No P0 entries
  are affected.**
- Catalog text **C1–C5** in `catalog_edits.md` lands in this ticket's commit.

## Scope guards

- **Do not** touch the broader `EntityRole.HERO` privileges — separate epic, inventory first.
- **Do not** design resurrection.
- **Do not** remove `LifecycleComponent.is_permadeath` / `LifecycleUpdate.is_permadeath_set` /
  `patches.py:83` — but **do** remove `CombatUpdate.is_permadeath_set` / `patches.py:82` (S5).
- **Do not** rewrite the roadmap §3.1 addendum, or
  `docs/audits/D21_entity_lifecycle_foundation_layers.md`, or previously recorded events — dated
  evidence.
- **Do not** re-point `life_arc_incoherent`; retire it.
- **Do not** add a deserializer to satisfy a legacy-key test (HELD, above).

## Acceptance-criteria map

| AC | Steps | Verified by |
|---|---|---|
| 1 — no `rebirth_eligible`, no `REBIRTH`; lethal hit records `COMBAT` + lineage | S1, S2, S3 | R1, R2 |
| 2 — `REBIRTH` zombie class closed | S1, S2 | R3 |
| 3 — `generation` removed; every consumer agrees | S4 | R5, R6 |
| 4 — Bible + divergence + parity updated | S6 | S6 diff |
| 5 — death batch's HERO hold released | S1, S2 | R7 |
| 6 — catalog text lands in this commit | S6 | `catalog_edits.md` |
