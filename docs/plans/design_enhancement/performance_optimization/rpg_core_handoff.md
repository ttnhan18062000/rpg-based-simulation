---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, determinism, engine, planning]
---

# Handoff — Performance track to the RPG-core sessions

**From:** `perf-planner`, 2026-10-04, at `origin/main` `82088824d`.
**To:** the session(s) planning and implementing RPG-core work (the systemic-world track:
`docs/plans/systemic_world/roadmap.md` §8 work order, owner decision memo rows 7 and 8).
**Reply:** comment on the PR that adds this file, or commit an answer under "Responses" at the
bottom. The perf sessions run on a different machine and do not see your handover notes.

Nothing here asks you to change your work order. It asks for one definition, a few notifications,
and one rule you already follow. Everything else is information so our two tracks do not collide.

## 1. Where the performance track stands

- **Idle by design.** Every piece of perf work that the RPG-core stability entry gate allows is merged (PRs #287, #296, #306,
  #308, #311): M0 governance closed, decisions PERF-D1 (+ amendment A1), D2, D4, D5 and D6 approved by
  the owner, evidence inventories under `docs/performance/`, a provisional benchmark identity
  schema, and the tooling honesty fixes.
- **What blocks us is your track.** `performance_optimization_roadmap.md`, "RPG-core stability
  entry gate": no baseline, capacity number or SimQ/Arena comparison counts as evidence, and no
  perf ticket edits `src/`, until the owner states the RPG-core foundation has reached a stable
  point. The Python Code Craft `src/` freeze also applies. The owner re-confirmed both on
  2026-10-04.
- **Next when the gate lifts:** M1 (correctness prerequisites,
  `performance_m1_correctness_prerequisites_epic.md`), then M2-T03/T04/T05 (tripwire, capacity
  run, baseline lifecycle). M1's primary surfaces are `src/engine/worker_manager.py`,
  `src/engine/governor.py`, `src/engine/checkpoint.py`, `src/engine/kernel.py`,
  `src/perf/long_run_harness.py`, `src/core/protocol_validator.py`.

## 2. What we understand you are doing (check us)

From the repository on 2026-10-04. Correct anything that is wrong.

| Item | Status as we read it | Touches `state.py` / `apply.py` / `pipeline.py` / `kernel.py`? | Adds or removes a refinement phase / changes `AuthoritativeState` shape? |
|---|---|---|---|
| Work order 1: goal-dispatch fix + scorer hostility (`TCK-20261002-GOAL-WINNER-...`, PR #291) | In progress; PR held (AC2/AC3 unmet, AC6 determinism fails on `frontier_living_world`) | No | No |
| Work order 2: faction-hostility sweep (`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`) | In progress | Not that we can see | No |
| Work order 3: sovereignty single writer | Next | Unknown | Unknown |
| Work order 5–7: semantic foundation (`TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION`) | Epic scoped | No (registries/ and tools/) | No |
| Body recovery / survivable defeat epic | Epic scoped, spec-first | Names `state.py` and `apply.py` | Possibly: a recovery process could be a new phase or state |
| Derived-stat authority (`TCK-20261001-SPAWN-AND-DERIVATION-...`) | Parked by decision 7 | `state.py`, `apply.py` (values, not shape) | Possibly later (`stat_profile_id`, noted as not in scope) |
| Perception phase (`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`) | Blocked; decision 8: current perception is authoritative, designed phase parked | No | No |

Our reading: the near-term work order is mostly AI/strategy and registry work and does not reshape
the engine core. That is good news for the gate. Body recovery is the first item likely to add a
phase or state.

## 3. Asks

### Ask 1 — Propose what "RPG-core stable point" means (most important)

**Why:** the gate lifts only on an owner statement, and nothing defines when to make it. No
document links the gate to a milestone. Without a definition, the perf track has no way to see the
gate coming, and the owner has nothing to check.

**What:** propose criteria to the owner, in your own terms. A starting point from perf's side,
which you should replace with something that fits your plan:

1. Memo row 7 (a) and (b) hold (the "complete" semantic foundation), or a named slice of it.
2. No open hard-bug ticket is a **determinism break** (row 7's own list includes it). Today that
   includes PR #291's AC6 failure and `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`.
   A baseline taken on a non-deterministic world measures noise.
3. For the four core files (`src/core/state.py`, `src/engine/apply.py`, `src/engine/pipeline.py`,
   `src/engine/kernel.py`): either no open RPG-core ticket edits them, or you name a window in
   which you will not touch them.
4. You expect no refinement-phase add/remove and no `AuthoritativeState` shape change for some
   stated period, or you list the ones still coming (for example body recovery).

It does not need to be a freeze. Perf measurements are labelled with a commit and the phase inventory, so a later
RPG-core change invalidates baselines in a known way. A partial lift is also an option (for
example M1 on `worker_manager.py`, `governor.py` and `checkpoint.py` only, which you do not touch).

**Who decides:** the owner. You propose; perf can review the proposal.

### Ask 2 — Tell us when a merge changes the engine's shape

Add one line to the PR description (or the closing ticket) when an RPG-core PR does any of these:

| Change | Why perf cares | Cheap check you can run (tools only, no `src/` edit) |
|---|---|---|
| Adds, removes, renames or reorders a `run_phase()` call in `AuthoritativeApplyPipeline.refine` | Phase inventory and the PERF-D6 catalog are keyed on it | `python3 tools/perf/phase_inventory.py --format md` and compare with `docs/performance/phase_inventory.md` |
| Changes `AuthoritativeState` fields | Canonical hash cost and benchmark identity | none; just say so |
| Adds any wall-clock or host-resource read in `src/` (`time.*`, `perf_counter`, `psutil`, ...) | PERF-D1 determinism contract | `python3 tools/perf/wall_clock_inventory.py --check docs/performance/wall_clock_inventory.json` (exit 1 = new read) |
| Turns a feature flag on by default | Roadmap rule: such a change carries an on/off phase-attribution table | `python3 tools/perf/flag_attribution.py --flag <FLAG> --scenario mixed` (small entity count; label the result provisional) |

None of these checks runs in CI yet. We are not asking you to add them as gates. Run under a memory cap on a
small machine (`systemd-run --user --scope -p MemoryMax=...`).

### Ask 3 — Keep game-facing values deterministic (PERF-D1 amendment A1)

Owner-approved 2026-10-03, binding in both the Canonical and Live contracts: **a value that
systems read from `AuthoritativeState` to change gameplay may be computed only from deterministic
inputs.** Host timing and resources may choose how much work runs (cadence, LOD, budgets), never
what a game value is. This matters most for the new mechanics on your list:

- body recovery: HP regeneration, wound healing and defeat recovery rates must come from ticks and
  state, not from elapsed time or tick compute time;
- anything that reads `AuthoritativeState.pressure_signals`.

Known violation, filed by perf: `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (measured tick
compute time → `global_salience` → shop buy prices). The owner placed it behind the entry gate on
2026-10-03. Note for the owner: by memo row 7's definition it is a determinism break, which is a
hard RPG bug. If the owner moves it into your hard-bug queue, the ticket is ready (standard tier,
touches `kernel.py`, `apply.py`, `economy.py`), and perf will review.

### Ask 4 — New phases declare their footprint

The approved PERF-D6 phase catalog does not exist in code yet (it waits for the gate). Until it
does, when a spec adds a refinement phase or a recurring process (body recovery is the likely
first), write these down in the spec. This follows rule 7 of "Stable structure across every milestone" in
`performance_optimization_roadmap.md`:

- state it reads and writes (domains);
- position in `refine` and ordering constraints;
- cadence / LOD behaviour (every tick? dirty-set gated?);
- feature flag, if any;
- expected cost driver (per entity, per region, per event).

When the catalog lands it will add a conformance test that fails if a `run_phase()` call has no
catalog entry. Having this in your specs makes that a copy, not an investigation.

## 4. What perf will do, and will not do

- Perf will not edit the four core files while RPG-core tickets are open against them, and will
  not edit `src/` at all until the gate and the freeze lift.
- Perf will not turn any soft performance check into a blocking one until the gate lifts. When we
  do, the `perf-cert-arena` CI job (runs `tests/perf` on PRs touching `src/core` or `src/engine`)
  will start to block RPG-core PRs on real regressions. We will announce it here first.
- Perf will review, on request, any RPG-core PR that touches the kernel loop, hashing, the
  governor, worker results, or `pressure_signals`.
- Perf-side follow-up, not yours: the committed `docs/performance/phase_inventory.json` is stale
  in its documentation half only (the `authoritative_pipeline.md` heading no longer states a count);
  the code half matches `main`. A perf-implementer will regenerate it.

## Responses

_RPG-core sessions: answer Ask 1–4 here or in the PR, with date and session name._
