---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
artifact_type: report
tags: [feature-flags, progression]
---

# Trial Evidence — TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

Raw output of the 4-leg (2-world x OFF/ON) real calibration trial run per `plan.md` Steps 2-6.
Environment note: the worktree's bare `python3` lacks `pydantic` (a pre-existing, unrelated
environment gap all 3 prior sibling tickets in this batch also worked around the same way);
all four runs were executed with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the main checkout's venv)
instead, with `cwd` still the worktree so `data/runs/` and `data/calibration/` output landed
where the plan's commands specify.

**Headline result, stated up front**: this trial did **not** produce the expected "near-zero,
clean pass" outcome. Both ON legs crash the real `Kernel` pipeline with a deterministic,
100%-reproducible `TypeError` inside `CanonicalStateHasher.get_hash()`
(`src/engine/checkpoint.py:48`), the moment any entity's `ProgressionConversionPhase.execute()`
writes its decision trace into `property_updates["last_progression_decision"]`
(`src/domains/progression/phase.py:80`) — a raw `ProgressionDecisionResult` dataclass instance
(`src/domains/progression/schema.py:110`) is not JSON-serializable, and the canonical hasher's
`json.dumps(...)` call has no `default=` handler for it. This is a real, disclosed defect, not a
near-zero-effect result — see "Headline finding" below before the rest of this document.

## Commands run (verbatim except interpreter path)

```
# dungeon_crawl OFF
.venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_OFF
# -> data/runs/run_1788023890_5169  (exit 0, completed all 2000 ticks)

# dungeon_crawl ON
ENABLE_PROGRESSION_EVOLUTION=ON .venv/bin/python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_ON
# -> data/runs/run_1788023975_5169  (exit 1, crashed ~tick 120-121 of 2000 requested)

# frontier_extended OFF
.venv/bin/python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_OFF
# -> data/runs/run_1788024095_5169  (exit 0, completed all 1000 ticks)

# frontier_extended ON
ENABLE_PROGRESSION_EVOLUTION=ON .venv/bin/python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_ON
# -> data/runs/run_1788024161_5169  (exit 1, crashed at tick 1 of 1000 requested)
```

No `--profile` override was passed for `frontier_extended`: `config/simulation_quality/profiles/
frontier_extended.yaml` exists (confirmed via `ls` this session), and `calibrate_simq.py`'s own
`_resolve_profile()` (`tools/calibrate_simq.py:39-48`) auto-resolves the profile to the world
name whenever a matching `{name}.yaml` file exists — no `--profile default` needed here, unlike
`WORLD_EMERGENCE`'s `resource_dense_basin` sibling leg, which genuinely had no dedicated profile
file. This is a deviation from the literal command shape in the dispatch prompt (which suggested
`--profile default`), following the dispatch's own explicit fallback instruction to check for a
dedicated profile first and use it if present.

The two ON legs' `exit 1` is itself part of the evidentiary record for this trial, not a run
failure to retry — both crashes are deterministic and were independently reproduced a 3rd time via
a diagnostic replay (see "Headline finding" below), so this is not run-to-run flakiness.

## World-loading confirmation

`calibrate_simq.py`'s own stdout `entities=10` line is the `--entities` CLI argument's unrelated
default value, not a world-loading signal — matching all 3 prior sibling trials' own finding, not
re-derived from scratch here. The real fingerprint is each run's own tick-0 `chunk_0000.json`
`REFINED_UPDATE` payload's `fingerprint.entity_count`:

| World | Leg | `chunk_0000.json` tick-0 `entity_count` | `corpus_registry.yaml` documented `scale.entity_count` | `state_hash` (tick 0) | Match |
|---|---|---|---|---|---|
| `dungeon_crawl` | OFF (`run_1788023890_5169`) | 32 | 32 | `5bb702562879beaea7535e690ccdba2a` | Yes |
| `dungeon_crawl` | ON (`run_1788023975_5169`) | 32 | 32 | `5bb702562879beaea7535e690ccdba2a` (identical to OFF) | Yes |
| `frontier_extended` | OFF (`run_1788024095_5169`) | 59 | 59 | `81b4f9085fdb5118f6bd286ae23f59f3` | Yes |
| `frontier_extended` | ON (`run_1788024161_5169`) | n/a — crashed at tick 1, before the 200-event chunk-flush threshold; no `chunk_0000.json` was written to disk (`run_manifest.json` shows `"ticks_completed": 0, "status": "RUNNING"`) | 59 | n/a (not written) | Confirmed indirectly — see below |

`frontier_extended` ON's world-loading is confirmed indirectly, the same reasoning both prior
sibling trials relied on: `_load_world_state()` raises `FileNotFoundError` for any `--name` that
fails to resolve rather than silently falling back to the generic hero+goblins world
(`tools/calibrate_simq.py:143-157`+`182-184`); this run got past world loading and 1 full tick of
real phase execution (`simulation_events.jsonl` shows 8 real `diplomatic_transition` events at
`tick: 1`, naming real faction ids from the compiled world spec — `arcane_circle`, `orc_clan`,
`bandit_company`, `forest_wardens`, `dragon_cult` — not the generic scenario's hero+goblin
entities) before crashing in the persistence phase, well past the world-load step. `dungeon_crawl`'s
OFF/ON legs share an identical tick-0 `state_hash`, confirming the flag has no effect on initial
world compilation — a valid controlled A/B on identical starting state, same as the
`COMBAT_ENGAGEMENT` sibling trial's method. `dungeon_crawl`'s state_hash also matches the
`COMBAT_ENGAGEMENT` sibling trial's own recorded value for the same world/seed exactly, an
independent cross-trial determinism check.

## Headline finding — the flag crashes the real pipeline, deterministically, in both worlds

**Traceback (identical in substance across all 3 independent reproductions — 2x `dungeon_crawl`
ON, 1x `frontier_extended` ON):**
```
File ".../src/engine/kernel.py", line 1162, in _phase_persistence
    tick_hash = CanonicalStateHasher.get_hash(self._state)
File ".../src/engine/checkpoint.py", line 48, in get_hash
    compact_json = CanonicalStateHasher.to_canonical_json(state, pretty=False)
File ".../src/engine/checkpoint.py", line 60, in to_canonical_json
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
TypeError: Object of type ProgressionDecisionResult is not JSON serializable
```

**Root cause, traced this session**: `ProgressionConversionPhase.execute()`
(`src/domains/progression/phase.py:78-85`) stores the raw `ProgressionDecisionResult` dataclass
instance (not a JSON-primitive, not a typed serializer-aware model) directly into
`property_updates["last_progression_decision"]`. This is pre-existing, already-documented
behavior — `docs/simulation/domains/progression_contract.md:62` and `:124` both call it out
verbatim as a "**Debug trace property**" — and investigation.md's own Risks section had already
flagged it as adjacent to the project's Durable State Rule ("do not store durable meaning in
free-form properties... not a typed, serializable durable-state field"), but investigation.md's
own framing treated this as an architecture smell, not something known to crash the pipeline —
that distinction is new information this trial adds. Once that property write lands in
`state.entities[...].identity.properties`, the very next tick's `_phase_persistence()`
(`src/engine/kernel.py:1158-1162`) calls `CanonicalStateHasher.get_hash(self._state)` whenever
`self._current_policy.replay_richness == "FULL"` (the policy `calibrate_simq.py`'s `PROD_SMALL`
profile runs under) — this recursively JSON-serializes the *entire* `AuthoritativeState`,
including every entity's raw `properties` dict, with no `default=` handler for arbitrary
dataclasses. `json.dumps` has no way to serialize `ProgressionDecisionResult` and raises
immediately.

**Why the 10-file Phase-6 test suite and the 2 flag-referencing test files never caught this**:
directly confirms Step 1's Test Coverage Depth Assessment verdict (carried forward from
investigation.md) rather than being a separate new finding — every one of the 10
`test_phase6_*.py` files calls `ProgressionConversionPhase.execute()` or its constituent services
directly, never through a real `Kernel.tick_once()` loop, so none of them ever reach
`_phase_persistence()`'s canonical hashing step at all. `test_allocate_ap_dormancy.py` does run a
real 150-tick `Kernel` loop, but with the flag OFF the whole tick, so
`last_progression_decision` is never written and the hasher never sees it.
`test_scenario_feature_flag_defaults.py` never invokes the phase. This is exactly the gap Step 1
named: deep isolated-unit coverage, but zero coverage of the phase running inside a real
`Kernel`/pipeline loop with the flag ON — precisely the condition needed to expose this bug.

**Reproducibility — confirmed 3 independent times, not a fluke**:
1. `dungeon_crawl` ON, `tools/calibrate_simq.py` invocation 1 (`run_1788023962_5169`) — crashed,
   same traceback.
2. `dungeon_crawl` ON, `tools/calibrate_simq.py` invocation 2 (`run_1788023975_5169`, the one
   cited throughout this document) — crashed at loop iteration ~120 (tick ~121 of 2000
   requested), same traceback.
3. `frontier_extended` ON (`run_1788024161_5169`) — crashed at tick 1 of 1000 requested, same
   traceback (earlier because `frontier_extended`'s `civilian_settlement` archetype produces a
   combat/attribute-dirty entity within tick 1, versus `dungeon_crawl`'s slower initial
   engagement ramp-up — see the run/skip signal below).

A 4th, purely diagnostic reproduction was also run this session (a short standalone script that
replicates `_run_engine()`'s exact `Kernel`/world-loading/flag-override setup for `dungeon_crawl`
ON, `.venv/bin/python3`-executed, read-only inspection of the real in-memory
`AuthoritativeState` after the same crash — no fabricated or hand-seeded ledger data, no
`src/` edits) specifically to sample `last_progression_decision`'s real distribution before the
crash prevents it from ever reaching disk (see "Signal 3" below); it crashed at the identical loop
iteration (120) with the identical traceback, an independent 4th confirmation.

## Evidence tally

### Signal 1 — run/skip counters (`metric_counters["run_progression_conversion"]` / `["skip_progression_conversion"]`, summed across recorded ticks)

| | dungeon_crawl OFF (2000 ticks, full) | dungeon_crawl ON (100 recorded ticks before crash) | frontier_extended OFF (1000 ticks, full) | frontier_extended ON (0 recorded ticks — crashed before first chunk flush) |
|---|---|---|---|---|
| `run_progression_conversion` | 0 | 0 | 0 | n/a (no chunk reached disk) |
| `skip_progression_conversion` | (present, phase never runs — flag OFF, expected) | 100 | (present, flag OFF, expected) | n/a |

**This does not read as a clean 100%/0% run/skip split the way the 3 sibling trials found for
their own flags, and that discrepancy is itself a real, disclosed correction to the plan's own
assumption, not a suppression signal.** `progression_conversion`'s `PhaseMetadata`
(`src/engine/phase_graph.py:68`) sets `input_domains={"attributes", "combat"}` with no
`must_run_every_tick=True` — unlike `world_emergence`/`self_model`, which are unconditional every
tick. `PhaseDependencyGraph.should_run_phase()` (`src/engine/phase_graph.py:127-154`) increments
the *same* `skip_progression_conversion` counter whenever the tick's `dirty_set` has no
`attribute_entities`/`combat_entities`, **independent of whether the flag is ON or OFF** — so a
`skip_progression_conversion` count on the ON leg does not by itself mean the flag failed to
activate; it means no entity had a dirty attribute/combat mark that tick. This is confirmed by the
diagnostic replay (Headline finding above): the phase *did* eventually run and write
`last_progression_decision` for all 32 `dungeon_crawl` entities by the crash tick, despite 100/100
recorded ticks showing `skip_progression_conversion` — dirty-set gating, not flag gating, produced
that skip pattern. `frontier_extended`'s much faster crash (tick 1 vs. `dungeon_crawl`'s ~tick 120)
is consistent with its `civilian_settlement` archetype producing an attribute/combat-dirty entity
essentially immediately.

### Signal 2 — real mutation events (`item_equipped` / `item_unequipped` / `equipment_durability_changed` / `progression_conversion_applied`)

None of these 4 event types appear in any leg's `simulation_events.jsonl`
(`dungeon_crawl` OFF: 21711 total lines, 0 matches; `dungeon_crawl` ON partial: 116 lines, 0
matches; `frontier_extended` OFF: 24571 total lines, 0 matches; `frontier_extended` ON partial: 8
lines, 0 matches). Traced `progression_conversion_applied`/`progression_plateau_detected`'s real
gating this session (`src/observability/event_extractor.py:1144-1216`): both are emitted from a
rollback code path gated on `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` being *not* active (that flag
defaults `ON` — `src/domains/optimization/feature_flags.py`), not on
`ENABLE_PROGRESSION_EVOLUTION` at all — `progression_plateau_detected` did fire 42 times in the
`dungeon_crawl` OFF baseline and 20 times in the ON leg's partial 120-tick window, confirming it is
a pre-existing, domain-independent signal unrelated to this ticket's flag (matching PROG-116's own
description of `progression_conversion_applied` as an `unspent_ap`-decrease observability hook,
independent of this specific phase). Zero AP-driven or equip/repair mutation events attributable
to `ProgressionConversionPhase` appear anywhere, consistent with the reward-ledger-empty finding
below.

### Signal 3 — `last_progression_decision` distribution (from the diagnostic replay, since neither `tools/calibrate_simq.py` ON leg's crashed chunk data ever reached disk)

**100% `SAVE_FOR_LATER` convergence, confirmed directly — exactly as investigation.md predicted.**
All 32 `dungeon_crawl` entities' `last_progression_decision.selected` at the crash tick
(`~121`) were `(ConversionOption(kind=SAVE_FOR_LATER, ...),)`, with the identical `reason` string
`"Do nothing, keep gold and resources for later."` on every entity. `ConversionDecisionService`
never selected any other `ConversionKind` (`EQUIP_ITEM`, `REPAIR`, `ALLOCATE_AP`, etc.) for any of
the 32 entities across the ~121 ticks that ran before the crash — directly confirming the
reward-ledger-empty structural chain investigation.md traced (`ledger.entries` always empty →
`interpretation.meanings == ()` → `ConversionOptionGenerator` only emits the `SAVE_FOR_LATER`
fallback → `ConversionDecisionService.select` always picks it).

## No-suppression check

**Structural half — inconclusive by the sibling trials' own method, resolved by the diagnostic
replay instead.** Unlike `world_emergence`/`combat_engagement` (both cleanly `must_run_every_tick`
or otherwise producing an unambiguous 100%/0% split), `progression_conversion`'s dirty-set gating
means the raw `skip_progression_conversion` counter cannot on its own distinguish "flag OFF" from
"flag ON, no dirty entity this tick" (see Signal 1). The diagnostic replay resolves this directly:
the phase did activate and write real decisions for all 32 entities once a combat/attribute-dirty
tick occurred, confirming the flag *does* actually gate live execution when ON (no silent
starvation) — but this is weaker structural confirmation than the sibling trials had, since it
required a supplementary diagnostic run rather than the corpus trial's own persisted output.

**Empirical half — cannot be completed at the intended tick budget, and the reason why is itself
the finding.** A same-world OFF-vs-ON event-count comparison at 2000/1000 ticks (the method all 3
sibling trials used) is not possible here: both ON legs terminated at 120/2000 and 1/1000 ticks
respectively, before any meaningful comparison window elapsed. Within the ticks that *did*
complete before each crash, no other domain's signal collapsed — `dungeon_crawl` ON's partial
116-line `simulation_events.jsonl` shows ordinary `cooperation_event` (31), `diplomatic_transition`
(29), `contract_offer_created` (21), `contract_expired_offer` (13) activity right up to the crash
tick, consistent with `ProgressionConversionPhase.execute()`'s `replace(update,
entity_updates=new_entity_updates)` call (`phase.py:89-92` — replaces only `entity_updates`,
carrying every other field of the incoming `update` forward unchanged) continuing to behave as a
safe merge for the ticks that ran. **This is a materially different, more severe failure mode than
what the "no suppression" check is designed to catch**: a silent per-domain signal collapse (the
TCK-20260809 regression class) versus a hard process crash that halts the entire simulation for
every domain simultaneously, once triggered. The crash is not evidence of "suppression" in the
sibling tickets' technical sense; it supersedes that question entirely for any tick after it
occurs.

**Verdict: no suppression regression was observed in the phases/ticks that did execute, but the
trial cannot make a full no-suppression claim at the intended tick budget in either world, because
both ON legs crash the process well short of it.**

## Honest Gap — the reward-ledger producer gap, and the crash it (independently) surfaced

Two separate, honestly-disclosed gaps apply here, and must not be conflated:

**1. The reward-ledger producer gap (predicted by investigation.md, confirmed directly by this
trial).** `RewardLedgerService` has zero live callers anywhere in `src/` — no phase that grants
XP, gold, or items ever calls `record_entry`, and `ProgressionConversionPhase` never persists the
(always freshly-empty) ledger back into entity properties. This trial's Signal 3 directly confirms
the predicted consequence: 100% `SAVE_FOR_LATER` convergence across every entity that ran, in the
one world where the phase got a large enough sample (32/32 `dungeon_crawl` entities). Per the
parent task's explicit instruction, this must be reported as: **wiring is safe with respect to
option-generation logic — the phase correctly falls back to `SAVE_FOR_LATER` rather than
misbehaving when its input feed is empty — but behavioral safety under real reward flow (what
happens when `EQUIP_ITEM`/`REPAIR`/`ALLOCATE_AP` options actually get selected against a populated
ledger) remains genuinely untested**, not a blanket "no risk observed."

**2. The canonical-hashing crash (a new finding this trial surfaced, not predicted by
investigation.md in this specific form).** Investigation.md's Risks section had already flagged
`last_progression_decision`'s raw-dataclass storage as *adjacent* to the Durable State Rule, but
explicitly characterized it as "pre-existing behavior unrelated to this ticket's evidence-gathering
scope... not something to fix here" and did not identify that it deterministically crashes
`CanonicalStateHasher.get_hash()` the moment it fires inside a real `Kernel` loop under a
`replay_richness == "FULL"` policy (exactly the policy `tools/calibrate_simq.py`'s `PROD_SMALL`
profile runs under). **This means "wiring is safe (no crash)" — the framing both this ticket's own
plan.md and the parent dispatch's Gate Integrity instructions assumed as the likely/expected
outcome — is not what this real trial found.** The flag is not merely under-tested; turning it ON
in any real corpus run that persists a `FULL` canonical hash reliably crashes the simulation once
any entity's decision gets recorded, confirmed in both trial worlds, independently reproduced 4
times total. Per the plan's own Anti-Drift instruction ("if... Step 4's tally surfaces a genuine
new defect, the recommendation must instead disclose that as a new finding requiring a separate
ticket — never fixed inline here"), **this defect is disclosed here, not fixed** —
`src/domains/progression/phase.py` was not touched by this ticket, per its explicit Scope Guards.
A follow-up ticket (fix class: either make `property_updates["last_progression_decision"]` a
JSON-serializable typed structure, per the Durable State Rule, or strip it before persistence the
way `state_update_compaction.md` already describes stripping other "cosmetic debug properties")
is a genuine, concrete prerequisite for any future flip-ON decision — stronger and more actionable
than the reward-ledger gap alone.

## Recommendation

**Keep OFF, deferred — real trial evidence now on file; the flag does not merely lack production
evidence, it deterministically crashes the real pipeline once activated, independent of and in
addition to the reward-ledger producer gap.** `grep -rl "ENABLE_PROGRESSION_EVOLUTION"
config/simulation_quality/profiles/` returns nothing (confirmed again this session) — zero shipped
profiles enable this flag today, the same "no shipped production profile" gap that kept all 3
sibling flags (`ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`)
at "keep OFF, deferred" despite each having a clean trial — but unlike all 3 of those, this flag
does not even clear the lower bar those trials met ("no suppression regression, real execution
confirmed"). This ticket's own trial found the opposite: the flag crashes the process in both
worlds tested, well short of either world's full tick budget. This is a substantially stronger
"keep OFF" signal than any of the 3 prior siblings produced. No new
`docs/guidelines/intentional_divergences.md` entry is added — a "keep OFF, deferred" outcome does
not create a divergence from the Mechanics Bible, and no chapter of the Mechanics Bible governs
this Phase-6/Phase-10-era subsystem regardless (confirmed in investigation.md's Mechanics/Engine
Constraints section). If a future ticket wants to re-open this: it must first (a) fix the
`last_progression_decision` JSON-serialization crash disclosed above (a concrete, scoped
prerequisite, unlike the 3 siblings' vaguer "needs a shipped profile" gap), and separately (b)
either wire a real `RewardLedgerService` producer (or otherwise populate the ledger) so a future
trial can exercise the phase's non-fallback decision paths, or accept that decision-logic safety
under real reward flow remains untested indefinitely. Both (a) and (b) are named, concrete blocking
prerequisites for any flip-ON decision — not "someday" items.
