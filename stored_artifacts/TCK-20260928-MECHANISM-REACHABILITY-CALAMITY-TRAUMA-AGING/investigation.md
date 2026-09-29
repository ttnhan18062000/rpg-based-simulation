---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING
artifact_type: investigation
tags: [simulation-quality, world, root-cause]
---

# Investigation — TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING

This is a bounded assessment ticket (Card J), not a fix. J1 and J2 adopt existing open tickets and
are mapped onto the four reachability levels without re-deriving their evidence from scratch. J3 has
no existing ticket and is assessed fresh against the current, post-merge engine state. All source
citations below were spot-checked against the current worktree HEAD, `702c3af83`, not taken on trust
from prior documents alone.

## Current Behavior

### J1 — `calamity_intensity` (adopts `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`)

- **Producer**: `CalamityService.apply_calamity_consequences()` (`src/world/calamity.py:80`) — the
  sole producer, `+0.05` per `entity.kind == "hero"` death inside a `region.hazard_level > 0.5`
  region, capped at `1.0`.
- **Propagator**: `CalamityPressurePropagator.propagate_seasonal()` — spreads *existing* intensity
  above `PROPAGATION_THRESHOLD = 0.10` to adjacent regions every `SEASONAL_PROPAGATION_INTERVAL =
  500` ticks; cannot create intensity from nothing.
- **Reader**: `CalamityService.process_world_dynamics()`, the method actually called from
  `src/world/world_dynamics.py:133`, only *reads* `region.calamity_intensity` for boss-spawn region
  selection — it never writes the stat.
- **Level 1 (trigger reachability) — FAILS, and at a deeper level than the adopted ticket's own
  original framing.** Re-confirmed directly against current HEAD: `grep -rn
  "apply_calamity_consequences" src/` finds only the method's own definition
  (`src/world/calamity.py:80`) and one unrelated comment in `src/world/displacement.py:27` — never a
  real call, anywhere. Nothing invokes the producer at all, so its internal `hero`-kind/hazard-level
  check is never even evaluated. This is the adopted ticket's own 2026-09-20 addendum
  (`TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION`), re-verified here
  rather than trusted.
- **Compounding, secondary finding (the adopted ticket's original 2026-09-15 scope)**: even if the
  producer were wired to a real caller, its trigger condition is separately unreachable in the tested
  worlds — `frontier_living_world` (the reference world for the original 5000-tick probe) composes
  zero `hero`-kind entities at all (`hero_adventurers` is absent from its module list); `crowded_
  frontier` composes 3 real heroes, but `hero_adventurers.yaml`'s own population recipes hardcode
  `spawn_region: "hometown"` (`hazard_level: 0.0`) for all three, unconditionally.
- **Level 2 (feasible run horizon) — moot, not answered by a longer run.** Level 1 already fails
  definitively (zero callers, a structural fact independent of tick count): no run length, however
  long, changes a call graph with no edge into the producer. Method: static call-graph confirmation
  (`grep`), not a corpus run — the minimum evidence AC4 asks for.
- **Level 3 (actual state effects) — none.** `region.calamity_intensity` stays `0.0` in every tested
  world for the full run length observed (5000 ticks). Its only real consumer,
  `process_world_dynamics()`'s boss-spawn region selection, always sees `0.0`.
- **Level 4 (observer evidence, recorded never required)** — none found; not investigated further,
  since the mechanism never produces a state change for an observer to encounter.
- **Exit claim: DEFECT.** The registry's own `state: done` / `verified.verdict: contradicted` no
  longer accurately describes this case — the 2026-09-20 finding is "closer to `orphan` than
  `done`+`contradicted`" (registry's own words, `registries/mechanisms.yaml:2160-2174`), i.e. dead
  code with zero callers, not correct-but-data-starved code. This is a wiring defect, not a
  legitimate composition condition, even though a real composition gap also independently exists.
  **Per this ticket's Out of Scope, this exit claim is recorded here as a recommendation only — the
  registry write for `calamity_intensity` belongs to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-
  RESOLUTION`, not this ticket.**
- **Where the adopted ticket's scope does not fit (AC3)**: the adopted ticket's own Scope and
  Acceptance Criteria were written before the 2026-09-20 zero-callers finding existed — they ask for
  "a proposed wiring fix... that would make `calamity_intensity` demonstrably nonzero," framed
  entirely around the composition gap (Level-1-if-wired). They do not cover the now-primary Level 1
  failure (the producer is never called at all), which is a different, more fundamental defect class.
  The adopted ticket's Implementation Notes already record this gap themselves ("this ticket's own
  eventual scope needs to cover both the wiring gap and the composition gap when picked up, not the
  composition gap alone") — this investigation confirms that self-correction is still accurate.

### J2 — `regional_trauma` (adopts `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`)

- **Producer/accumulator**: combat/death events accrue `region.trauma_score` (`+1.0` per real entity
  death in that death's own region, `src/engine/world_dynamics.py`'s "Death-triggered Trauma"
  block). Natural decay/recovery: `RegionalConsequenceService.process_recovery()`
  (`src/world/consequences.py`), real caller confirmed at `src/engine/apply_plan.py:101`
  (`registries/mechanisms.yaml:1998-2000`).
- **Readers**: `camp.py`, `boss.py::check_for_lair_spawn()`/`check_for_boss_spawn()`,
  `creature_territory.py`, `threat.py` — all real, wired code.
- **Level 1 (trigger reachability) — FAILS, confirmed as a composition gap, not a wrong threshold.**
  `generated_frontier_3_42`'s `moon_cave` region (the corpus's only real `LAIR`-kind Place) recorded
  `trauma_score == 0.0` for a full real 5000-tick `Kernel.tick_once()` run — zero deaths were ever
  recorded there. Root cause (adopted ticket, re-confirmed here): spatial isolation. `moon_cave`'s
  `grid_bounds: [100, 70, 130, 110]` sits ~30 units from the nearest populated region
  (`orc_clan_territory`, `[160, 60, 200, 100]`); `moon_cult_ruins` places only
  `moon_cult_apprentice_circle` there with no hostile faction ever composed within combat range.
- **Level 2 (feasible run horizon) — answered with the same 5000-tick run already cited, no longer
  run needed.** Spatial isolation is a fixed geometric fact of the world's composition, not a
  "not-yet-enough-ticks" problem — running longer does not change `moon_cave`'s distance from any
  hostile faction. The already-observed 5000-tick zero-accumulation result is sufficient evidence
  that the horizon is not the limiting factor here; composition is.
- **Level 3 (actual state effects) — none for the isolated region.** `moon_cave.trauma_score` stays
  `0.0`; `check_for_lair_spawn()`'s occupant-spawn gate can never open there, at any threshold above
  `0.0`. Elsewhere in the corpus, real trauma accumulation and decay do occur (the accumulation/decay
  code itself is correct and wired — this is region-specific, not a general mechanism failure).
- **Level 4 (observer evidence)** — not separately investigated by the adopted ticket; the adopted
  ticket's own Implementation Notes flag an unresolved sub-question (whether any entity paths into
  `moon_cave` for non-combat, quest-driven reasons) as still open. Not resolved here — out of this
  assessment's scope to trace further.
- **Exit claim: CONDITION.** The accrual/decay code is real, correct, and wired — this matches the
  registry's own `STARVED` framing (`docs/plans/status_axis_model.md` §4: "correct code, wired,
  data-starved"). The precondition (a death event inside `moon_cave` specifically) never arises
  because of a real, static world-composition fact, not broken or unreachable logic. The current
  registry label (`state: done`, `verified.verdict: contradicted`, dated 2026-09-17) already states
  this accurately — **no registry label correction is warranted for `regional_trauma`.**
- **Where the adopted ticket's scope does not fit (AC3)**: the adopted ticket's Scope asks for "a
  proposed fix... bring findings + options to peer/user review" — a design decision, not a
  classification. It does not ask the trigger-reachability/horizon/state-effects/observer-evidence
  question this ticket asks explicitly; those four levels are implicit in its findings but were never
  stated as four separate, individually-answered levels until now. The adopted ticket's own scope is
  otherwise a superset (it also asks whether the pattern generalizes to future LAIR places), which
  this assessment does not re-derive.

### J3 — `aging_death` / `succession` (no existing ticket; assessed fresh, all findings against commit `702c3af83`, current worktree HEAD — the natural-aging fix landed as `5d4e4a237`/PR#254, already merged into this ancestry)

- **Old-age check**: `LifecycleSystem.resolve_lifecycle()`
  (`src/systems/lifecycle_systems/lifecycle.py:193-195`): `if entity.lifecycle.age_ticks >=
  entity.lifecycle.max_age_ticks: is_dead = True; death_reason = "OLD_AGE"`. Called every tick, no
  flag gate, from `src/engine/pipeline.py:414` (`run_phase("lifecycle", ...,
  LifecycleSystem.resolve_lifecycle)`). Already-inactive entities are skipped at the loop guard
  (`lifecycle.py:147-148`).
- **Passive apply-path branch (the prior dual-writer)**: `src/engine/apply.py:94-109`. Read and
  confirmed at current HEAD: line 109 reads exactly `active=(new_hp > 0 and (life.active or new_age <
  life.max_age_ticks))` — the post-fix formula from the now-merged
  `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` (commit `5d4e4a237`, PR #254). The passive
  branch no longer independently deactivates an already-active entity for old age;
  `resolve_lifecycle`'s OLD_AGE branch is now the sole declared authority for old-age deactivation
  (matches the ticket's own claim in Related Code Areas exactly).
- **Succession dispatch**: `lifecycle.py:206-265` — on `is_dead`, resolves `heir_entity_id` (falls
  back to `LifecycleSystem._select_default_heir()`'s bond-strength scoring when unset), dispatches
  `_transfer_inherited_feud()` and `_seed_dying_wish()`, and builds a `ResourceTransferIntent`
  transferring the dead entity's inventory + heirlooms to the heir.
- **Default lifespan / Level-2 horizon arithmetic**: `src/core/state.py:165`,
  `max_age_ticks: int = 70 * TICKS_PER_FANTASY_YEAR`; `TICKS_PER_FANTASY_YEAR = 288,000`
  (`src/core/calendar.py:13`) ⇒ `max_age_ticks = 20,160,000` ticks. Corpus runs cited throughout this
  registry area run 1,000–5,000 ticks. `20,160,000 / 5,000 = 4,032`; `20,160,000 / 1,000 = 20,160`.
- **Level 1 (trigger reachability) — now real.** Confirmed by the merged fix: the dual-writer race
  that previously deactivated an entity one tick before `resolve_lifecycle`'s OLD_AGE check ever ran
  is closed. `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (present at current
  HEAD) demonstrates the OLD_AGE branch fires correctly for an entity reaching `max_age_ticks` through
  ordinary per-tick progression, not only a staged starting state.
- **Level 2 (feasible run horizon) — NOT reachable within any real corpus run at default settings;
  answered with the arithmetic above, not an open-ended long run, per AC4.** Natural full accumulation
  from `age_ticks=0` to `max_age_ticks=20,160,000` is roughly 4,000×–20,000× longer than any real
  corpus run this repo's own test/scenario evidence cites. The fix's own positive-control evidence
  (both this entry's `verified` block and the dual-writer-race ticket's own regression test) comes
  from a **staged scenario** — `age_ticks` fixed directly near the threshold, not organic per-tick
  accumulation over a real long run. No real corpus run has been observed to produce a natural
  old-age death through ordinary accumulation; this is stated as an open, unconfirmed-in-practice
  fact, not assumed either way.
- **Level 3 (actual state effects) — confirmed, via the merged fix's own regression evidence.** When
  triggered (staged or, in principle, ordinary progression), the entity is recorded
  `active=False`, `death_reason_set="OLD_AGE"`, `is_permadeath_set=True`,
  `death_tick_set=state.tick`; the heir (resolved via bond-strength scoring if not preset) receives
  inherited feud, a dying wish, and inventory/heirloom transfer via a real
  `ResourceTransferIntent`. All confirmed passing in `tests/mechanic_scenarios/
  test_natural_aging_old_age_dispatch.py::test_natural_aging_death_is_recorded_as_old_age_and_
  dispatches_succession` (cited in `registries/mechanisms.yaml`'s 2026-09-28 addenda for both
  `aging_death` and `succession`, and in `docs/parity_ledger/progression.yaml`'s `PROG-030`).
- **Level 4 (observer evidence, recorded never required) — real, non-combat-channel evidence found.**
  `src/observability/event_extractor.py:462-503` deliberately **excludes** OLD_AGE deaths from
  `CombatKillEvent` (only `death_reason == "COMBAT"` emits one) — an old-age death is not surfaced as
  a `combat_kill`/`entity_killed` observer event, by design
  (`TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`). Instead: (a) `demographic_
  mortality` credit fires separately when the corpse is later removed via `entities_remove`
  (event_extractor.py comment, lines 485-487), and (b) if the dead entity held a
  `SHOPKEEPER`/`WORKER` role, `EconomicVacancyService.check_and_emit()`
  (`src/economy/vacancy.py:24-70`) emits a real `WorldEvent(category=PRODUCTION_ROLE_VACATED)` —
  confirmed by the merged fix's own "Vacancy-signal interaction" finding to now correctly fire for
  OLD_AGE deaths via the same-tick `recent_deaths` aggregate (pre-fix, it never fired for this path
  at all, because the entity was silently deactivated before ever entering `recent_deaths`). This is
  recorded evidence, not a claim that any situated observer can encounter it — that
  encounterability question is Card B0's scope (combat deaths specifically), not this ticket's.
- **Exit claim: CONDITION.** The mechanism is correctly built and its own defect (the dual-writer
  race) is already fixed and merged (`5d4e4a237`) — Level 1 and Level 3 are both confirmed working.
  The remaining gap is purely a real-corpus-horizon reachability condition: the default lifespan is
  roughly four orders of magnitude longer than any run this repo's evidence currently covers, so
  natural aging death by ordinary accumulation is proven correct by staged-scenario technique but
  unobserved in any real corpus run. Not a defect (nothing is broken) and not a mislabel (the
  registry's `aging_death`/`succession` entries already carry accurate, dated 2026-09-28 evidence
  describing exactly this state, added by the now-closed dual-writer-race ticket itself) — **no
  further registry write is warranted by this assessment.**

## Mechanics/Engine Constraints

- `docs/mechanics/05_world_evolution.md` describes the calamity-intensity propagation constants
  (`PROPAGATION_THRESHOLD`, `SEASONAL_PROPAGATION_INTERVAL = 500`, and the
  `calamity_intensity > 0.3` spawn gate at line 456-457) and `trauma_multiplier = 1.5 if
  region.trauma_score > 50.0` (line 339). These formulas match the source exactly — confirmed by the
  parity ledger's own `verified` status on the corresponding entries (`WORLD-105`, `WORLD-106`,
  `WORLD-118`, `WORLD-121`, `WORLD-123`, all unit-test-backed). **The Mechanics Bible's formulas are
  not wrong; this ticket's finding is entirely about real-world trigger reachability**, an axis the
  Bible's formula-level prose does not, and structurally cannot, capture on its own.
- `docs/plans/status_axis_model.md` §1 defines the axis this whole assessment operates on: Axis A
  (`state`, implementation completeness) and Axis B (`verified.verdict`, evidentiary strength) are
  both registry-enforced and directly load-bearing for every exit claim above; Axis C (runtime
  reach/liveness, `STARVED` etc.) is the vocabulary this investigation's "condition" exit claims map
  onto, but is explicitly unenforced/prose-only per that doc — no new registry field is created here,
  consistent with that doc's own §4 decision.
- `docs/engine/authoritative_mutation_pipeline_contract.md` governs the apply-path law J3's now-merged
  fix operates under; this investigation cites it but does not modify it.
- `src/core/state.py`'s `LifecycleComponent` and `src/core/calendar.py`'s `TICKS_PER_FANTASY_YEAR`
  jointly determine J3's Level-2 horizon arithmetic; neither is modified here.

## Docs Requiring Update

None.

This ticket's own scope routes every label correction through `registries/mechanisms.yaml` (J1's
write is further routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` as a
recommendation only, per this ticket's Out of Scope), not through any `docs/` path. The Mechanics
Bible formulas involved (`docs/mechanics/05_world_evolution.md`) were checked and found accurate —
they describe intended formulas, not real-world reachability, and this assessment found no formula
divergence. No `docs/parity_ledger/*.yaml` entry requires a status change either — see Parity Ledger
Overlap below.

## Parity Ledger Overlap

Checked `docs/parity_ledger/world_dynamics.yaml` for every entry mentioning `trauma`/`calamity`:
`WORLD-105` (P1, `verified`, calamity propagation formula,
`tests/unit/world/test_calamity_pressure_propagator.py`), `WORLD-106` (P1, `verified`, trauma-concern
bridge), `WORLD-118` (P2, `verified`, creature maturity scales with trauma), `WORLD-121` (P2,
`verified`, calamity magical/demonic reproduction), `WORLD-123` (P1, `verified`, population-pressure/
calamity fold-in). All are formula-level, unit-test-backed, and remain accurate — none asserts or
depends on real-corpus reachability of the producer, so none is contradicted by this ticket's
finding. `docs/parity_ledger/progression.yaml`'s `PROG-030` already carries the 2026-09-28 dated
evidence for the `aging_death`/`succession` fix (added by the now-closed
`TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`), confirmed current and unchanged by this
assessment. **No P0 parity entry in the trauma/calamity family requires a new or updated
`test_path`** — the P0 entries checked in this family (`WORLD-024`–`WORLD-097`) are unrelated
hazard/ecology formulas, pre-existing and unaffected. Confirms the ticket's own Assumptions
("no SCP change is required") and extends the same conclusion to the parity ledger: no change is
required there either.

## Prior Work

- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (open, adopted as J1) — original composition
  gap finding plus its own 2026-09-20 zero-callers addendum, re-verified here.
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (open, adopted as J2) — the moon_cave spatial-
  isolation finding, re-verified here.
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` (done, merged `5d4e4a237`/PR#254) — the landed
  fix J3 is assessed against; its own registry addenda, parity ledger update, and regression tests are
  the direct evidentiary basis for J3's Level 1/3 findings here.
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` (open, `tickets/todos/`) — the follow-up split
  off the dual-writer-race fix for the still-silent starvation/sleep-debt death path; adjacent to but
  distinct from J3's OLD_AGE-only scope here.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §4/§6 — performed the
  `calamities_boss_spawns` → `calamity_intensity` + `world_boss_spawn` split and the
  `regional_trauma_hazards_sovereignty` → `regional_trauma` + `regional_sovereignty` split that
  produced today's registry rows; both splits' own reasoning already anticipated the exit claims
  reached here.
- `docs/plans/world_composition_precondition_gap_finding.md` — durable record naming J1 and J2 as
  confirmed instances 1 and 2 of the "mechanics whose preconditions depend on unvalidated world
  composition" pattern, and `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (instance 4) as the
  checked, disconfirmed exception — directly relevant to the shared-root-cause question below.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (open, `tickets/todos/`) — owns
  `calamity_intensity`'s registry `state`/label write; J1's exit claim is routed there as a
  recommendation only.

## Risks and Open Questions

- **Shared-root-cause hypothesis (checked, not confirmed).** J2's root symptom ("a region recording
  zero combat deaths") does **not** also explain the out-of-scope
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`. That ticket was already checked directly
  (`docs/plans/world_composition_precondition_gap_finding.md`, instance 4, "the exception") and found
  to have a distinct, single-cause classification divergence: `world_dynamics.py`'s trauma block
  detects every real death via `alive_set is False`, but `resolve_lifecycle()`'s own separate death
  filter only checked `outcome_kind in ("KILL", "PERMADEATH")` — missing `"DEFEAT"`, which real combat
  resolution also sets `alive_set=False` for (confirmed empirically: 20/20 sampled real deaths were
  `"DEFEAT"`, zero `"KILL"`). Entities in that ticket's own sampled region *are* correctly co-located
  and deaths *do* genuinely occur — the opposite of J2's spatial-isolation cause. **Stated here per
  the ticket's own instruction; not absorbed into this ticket's scope.**
- J1's compound finding (zero callers *and* an unreachable trigger condition even if wired) means a
  single "condition" or "defect" label undersells the real complexity — recorded as DEFECT
  (recommendation only) because the wiring gap is the more fundamental blocker, but the composition
  gap is real and independent, and would still need addressing even after any wiring fix.
- J3's Level-2 claim is explicitly bounded to default settings and the current corpus, per the
  ticket's own Scope — a modified lifespan config, or a purpose-built long-horizon harness, could
  produce a different answer. Not tested here; stated as a limit, not resolved.
- Whether AI-driven wandering could later route a hero into a hazard region during a real run
  (partially closing J1's composition gap) was never traced by the adopted ticket, and is not traced
  here.
- Whether any entity ever paths into `moon_cave` for non-combat reasons (quest content) was flagged as
  unresolved by the adopted J2 ticket's own Implementation Notes and remains open here.

## Anti-Drift Hazards

- Do not fix any of the three mechanisms as part of closing this ticket — Out of Scope is explicit
  and absolute; a confirmed defect routes to separate work.
- Do not write `calamity_intensity`'s registry label here — it routes to
  `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` as a recommendation only.
- Do not expand into `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` or
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, even though the shared-root-cause check directly
  touches the latter's territory — state the finding and stop, per the ticket's own instruction.
- Do not treat J3's Level-2 "not reachable within real corpus horizon" as a defect — the mechanism is
  correctly built and verified via staged-scenario technique; the horizon gap is a reachability
  condition, not broken code, and the registry already records this accurately.
- Do not conflate `STARVED` (Axis C: code correct, wired, data-starved — J2's and J3's shape) with
  `orphan`/dead-code (J1's deeper, 2026-09-20 zero-callers finding) — the registry's own note already
  distinguishes these two severities; collapsing them would misrepresent J1's compound finding.
- Do not pick up `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`'s starvation/sleep-debt
  detection gap here — it is a distinct, already-filed follow-up, not part of J3's OLD_AGE-only scope.
