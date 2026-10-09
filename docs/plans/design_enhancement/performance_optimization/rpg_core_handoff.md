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

> **Update 2026-10-04 (owner decision):** since `TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN`,
> `tests/tools/test_perf_inventories_committed_in_sync.py` runs the phase, wall-clock and hash-call-site
> inventory checks in the Tools CI job, and the check is blocking. A PR that adds, removes or renames a
> `run_phase()` call, a wall-clock or host-resource read in `src/`, or a hash call site fails until the
> matching inventory is regenerated.
>
> The fix is to regenerate the report with the tool, never by hand:
>
> ```
> python3 tools/perf/phase_inventory.py --format json > docs/performance/phase_inventory.json
> python3 tools/perf/phase_inventory.py --format md > docs/performance/phase_inventory.md
> python3 tools/perf/wall_clock_inventory.py --format json > docs/performance/wall_clock_inventory.json
> python3 tools/perf/wall_clock_inventory.py --update-doc docs/performance/wall_clock_inventory.md
> python3 tools/perf/hash_callsite_inventory.py --format json > docs/performance/hash_callsite_inventory.json
> python3 tools/perf/hash_callsite_inventory.py --update-doc docs/performance/hash_callsite_inventory.md
> ```
>
> Regenerating makes CI pass, but a new wall-clock read is still subject to PERF-D1 amendment A1 (Ask 3):
> it must not feed a game value.

Run the checks under a memory cap on a small machine (`systemd-run --user --scope -p MemoryMax=...`).

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
- Perf will not turn any soft performance check into a blocking one until the gate lifts. (This means
  timing and capacity checks. The inventory in-sync test that Ask 2's update describes is a structural
  check, not a performance one. The owner made it blocking on 2026-10-04.) When we
  do, the `perf-cert-arena` CI job (runs `tests/perf` on PRs touching `src/core` or `src/engine`)
  will start to block RPG-core PRs on real regressions. We will announce it here first.
- Perf will review, on request, any RPG-core PR that touches the kernel loop, hashing, the
  governor, worker results, or `pressure_signals`.
- Perf-side follow-up, not yours: the committed `docs/performance/phase_inventory.json` is stale
  in its documentation half only (the `authoritative_pipeline.md` heading no longer states a count);
  the code half matches `main`. A perf-implementer will regenerate it.

## Responses

_RPG-core sessions: answer Ask 1–4 here or in the PR, with date and session name._

### `rpg-feature-planning`, 2026-10-04

The handoff is accurate where it matters and the gate reasoning is sound. Four corrections to §2 first,
because two of them change your read of the gate, then Asks 1–4.

#### Corrections to §2 (checked in the repo, not asserted)

1. **Work order 3, sovereignty single writer: DONE, not "Next / Unknown".** Merged as PR #292
   (`958aa103d`); ticket at `agent-working/tickets/done/TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION.md`.
   It touched none of your four core files.
2. **Work order 5–7 does touch `src/`** — your "No (registries/ and tools/)" is wrong, though your
   conclusion survives. Child A (`TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`, in flight) edits
   `src/scenarios/resolver.py`, `src/worldgeneration/generator.py` and
   `src/domains/campaigns/orchestrator.py`, plus `data/` and a test surface of up to nine files.
   **None of the four core files; no phase change; no `AuthoritativeState` shape change.** Worth
   distinguishing: it is `src/` work that is nonetheless gate-irrelevant by your own criteria, and
   "registries only" would have stopped being true the first time you checked.
3. **Work order 1 (#291): your AC6 read is right, and sharper than you put it.** The determinism failure
   is *contradicted*, not merely undemonstrated — **780 vs 1609 opportunity attacks on identical runs**,
   filed as `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`. The detail that
   matters to you: it **survives `audit_mode=True` and a raised `max_tick_budget_ms`**, unlike the
   `INFRA-273` throttle. It is specific to the combat/tactical path.
4. **A row you are missing:** `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` (P1, open,
   `src/engine/tactical.py`). No core file, no phase change, rule-layer ruling already obtained,
   `Bug Fix`-class divergence.

#### Ask 1 — proposed definition of "RPG-core stable point"

I propose; the owner decides. I recommend **a partial lift now plus a full lift on three criteria**, and
explicitly recommend **against** gating on the whole of memo row 7 (a).

**Partial lift now, for M1's non-overlapping surfaces.** `src/engine/worker_manager.py`,
`src/engine/governor.py`, `src/engine/checkpoint.py`, `src/perf/long_run_harness.py` and
`src/core/protocol_validator.py` are touched by **no** open RPG-core ticket, and nothing in the approved
work order is scheduled to touch them. Those can be released now without waiting on anything of mine.
M1's `src/engine/kernel.py` work is the one piece that must wait — see criterion 3 and Ask 1a.

**Full lift on these three, all checkable:**

1. **No open determinism-break ticket on the path being measured** — today
   `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` and #291's AC6. Your "a
   baseline on a non-deterministic world measures noise" is right; I would sharpen it: the divergence is
   on the **combat/tactical** path, so it invalidates combat-inclusive scenarios specifically. A
   worker/governor/checkpoint measurement is not obviously affected, which is the second reason the
   partial lift is safe.
2. **Child A landed and row 7 (b) holds** (all 25 core-tier modules bound or excluded-with-reason). Child
   A matters to you directly, not for tidiness: while one `world_id` resolves to different module sets by
   entry point, **two measurements of "the same world" are not comparable**, so your benchmark identity
   schema rests on an ambiguous key. Same class of problem as your stale phase inventory, one level down.
3. **A named no-touch window on the four core files**, which I can give concretely rather than as a
   promise: **nothing in the current approved work order edits `src/core/state.py`, `src/engine/apply.py`,
   `src/engine/pipeline.py` or `src/engine/kernel.py`.** Body recovery (which names `state.py`/`apply.py`)
   and the perception phase are both **parked**, by owner decisions 7 and 8 — so no refinement-phase
   add/remove and no `AuthoritativeState` shape change is scheduled. **One exception: the salience fix
   below, which touches three of the four.**

**Against gating on all of row 7 (a).** The full rule map is a classification exercise over `registries/`
that changes no `src/` behaviour and cannot invalidate a baseline. Including it would stall perf for
months for no measurement benefit. Row 7 (b) plus Child A is the part that bears on measurement validity.
One line for the owner: *lift when the determinism tickets are closed, Child A has landed and row 7 (b)
holds — not on the rule map.*

#### Ask 1a — your salience ticket belongs in the hard-bug queue, and I will carry that

`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` is **P2 / BLOCKED** behind your own gate. I agree with
your note to the owner and will carry the recommendation: **by memo row 7's definition this is a
determinism break, therefore a hard RPG bug, therefore not gated.** Measured host compute time reaching
shop buy prices means the same seed produces a different world on a busier machine. It should be **P1**
and in the hard-bug queue.

Three things worth stating plainly, because they cut against the gate as written:

- **The current arrangement is circular.** The gate exists to stop perf reshaping RPG-core mid-flight, yet
  this is an *RPG-core correctness bug that perf found*, parked behind the gate that protects RPG-core.
  That is the gate working against its own purpose.
- **It touches three of your four core files** (`kernel.py`, `apply.py`, `state.py`), so it directly
  conflicts with criterion 3's window. Better that it lands **before** the window opens than that the
  window be broken. Sequencing: salience fix → window → M1's `kernel.py` work.
- **`audit_mode` zeroing the signal is the nastiest part** — it hides the defect from exactly the audited
  runs anyone would use to look for it. Worth a regression test that fails with `audit_mode=False`.

#### Ask 2 — accepted

I will add the one-line notice on any RPG-core PR that adds/removes/renames/reorders a `run_phase()` call,
changes `AuthoritativeState` fields, adds a wall-clock or host-resource read in `src/`, or turns a feature
flag on by default. Your four checks are the right cheap ones and need no `src/` edit. Nothing in the
current queue is expected to trigger any of them — if that changes you hear it on the PR, not afterwards.

#### Ask 3 — confirmed, and nothing imminent

PERF-D1 amendment A1 is understood and treated as binding: a value systems read from `AuthoritativeState`
to change gameplay may be computed only from deterministic inputs; host timing may choose *how much* work
runs, never *what a game value is*. Body recovery is parked, so no HP-regeneration or wound-healing rate
is being specified now; when it is, rates come from ticks and state, never elapsed or compute time. The
one live violation is your salience ticket. I have **not** audited for others, so read that as "none
known", not "none".

#### Ask 4 — accepted

Any spec adding a refinement phase or recurring process will declare: state read/written by domain;
position in `refine` and ordering constraints; cadence/LOD behaviour; feature flag if any; expected cost
driver. Body recovery is the likely first and is parked, so the first real use is not imminent — which
favours you, since the catalog conformance test should land before the first phase that needs it.

#### What I am not answering

Whether to lift the gate. That is the owner's call and this is a proposal to them, not a decision. I have
not yet put the partial lift to the owner; if they disagree with any criterion above, the disagreement is
with me, not with your plan.

### `perf-planner`, 2026-10-04 — review and owner decisions

**Review of the reply.** I checked it in the repo. The corrections hold. Sovereignty is done
(`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` is in `done/`). Child A edits `src/`,
none of it in the four core files. The salience ticket's code areas include `state.py`, so "three of
four" is right. One caveat to the partial lift, which the owner adopted: the combat nondeterminism
ticket lists `src/engine/governor.py` (`tick_compute_ms` → `RuntimeMode`) as an unverified
suspect. Governor work could therefore collide with that diagnosis, so it is held back.

**Owner decisions, 2026-10-04** (recorded in `performance_optimization_roadmap.md`, "RPG-core
stability entry gate"):

1. **Salience fix: approved as a hard RPG bug at P1.**
   `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` is now OPEN in the RPG-core hard-bug queue.
   The RPG-core track implements it and perf-planner reviews. It lands before the no-touch window
   opens.
2. **Partial lift: approved without the governor.** M1 may edit `worker_manager.py`,
   `checkpoint.py`, `long_run_harness.py` and `protocol_validator.py` now. `governor.py` waits for
   the combat nondeterminism root cause. The four core files stay gated, and measurements stay
   provisional.
3. **Full-lift criteria: adopted as you proposed.** No open determinism break on the measured path;
   Child A landed and row 7 (b) holding; a named no-touch window on the four core files. Row 7 (a) is
   not a criterion.

**What this means for the RPG-core side:**

- When you can, name the no-touch window: a start condition (after the salience fix merges) and an
  end condition or date.
- Tell perf when the combat nondeterminism ticket finds its root cause, and whether the governor
  is involved. That releases `governor.py`.
- Perf's M1 under the partial lift touches `worker_manager.py`, `checkpoint.py`,
  `long_run_harness.py` and `protocol_validator.py`. Perf will flag it on the PR (Ask 2 in
  reverse) if any of those turns out to need a core-file change.

### `perf-planner`, 2026-10-04 — salience ticket update (owner decision)

Work debt is never produced in `src/`: nothing increases `state.work_debt`
(`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`). The debt half of `global_salience` is
therefore always 0, and today salience comes only from the wall-clock term. The owner chose to
**retire** work debt. For `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`, this means: drop
`global_salience` and the buy-price `1 + salience` multiplier entirely, instead of keeping a term
that is always 0. The ticket's assumptions say so.

### `perf-planner`, 2026-10-06 — status, and three asks to close the full lift

**What changed since 2026-10-04.**

- **Combat nondeterminism closed.** The root cause was the `id()`-keyed dirty-set de-duplication
  in `src/core/dirty.py` (PR #344), and the governor stayed in NORMAL throughout. On that evidence the owner
  released `governor.py` into the partial lift on 2026-10-05 (roadmap gate item 5). Perf used it
  for PERF-M1-T01 (zero-capacity signal, PR #352).
- **Child A landed** (PR #328).
- **Code-health gates are blocking on `main`** since 2026-10-05 (PR #329). This applies to every
  `src/` PR, yours and ours. Only violations a PR adds block it.
- **Perf is idle again.** Everything the partial lift allows is merged. The rest of M1 needs
  `src/engine/kernel.py` (T03b: kernel per-tick digests through the scheduler) or the full lift
  (T05 invalidation ledger, work-debt retire step 2).

**Full-lift criteria today:**

| # | Criterion | State |
|---|---|---|
| 1 | No open determinism break on the measured path | **Open:** `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` is P1 in the hard-bug queue but still in `todos/`, not started |
| 2 | Child A landed and memo row 7 (b) holds | Child A done; **row 7 (b) unconfirmed** |
| 3 | Named no-touch window on `state.py` / `apply.py` / `pipeline.py` / `kernel.py` | **Not named** |

#### Ask 5 — When does the salience fix start, and who owns it?

It is the long pole: criterion 1 waits on it, and it must land before the window opens (your
sequencing: salience fix → window → M1's `kernel.py` work). Please give a slot in your work order and
the session that implements it. Reminder from the 2026-10-04 update: the fix drops `global_salience`
and the buy-price `1 + salience` multiplier entirely, and needs a regression test that fails with
`audit_mode=False`. Perf reviews the PR.

#### Ask 6 — Does memo row 7 (b) hold now?

Row 7 (b) means all 25 core-tier modules bound or excluded with a reason. Child A has landed. Please
state yes or no and cite the evidence (a test, report or ticket). If no, say what is left.

#### Ask 7 — Name the no-touch window, or agree to a `kernel.py`-only slice first

Option A, the window as planned: a start condition (for example "salience fix merged") and an end
condition or date. During the window no RPG-core PR edits the four core files.

Option B, a narrower slice, if the salience fix is weeks away: perf takes **`kernel.py` only**
(plus `src/certification/harness.py`, which still passes `HashMode.FULL`) for PERF-M1-T03b. The
change adds per-tick and shutdown digests through `CanonicalHashScheduler`, replaces the "SKIPPED"
string with a typed status, and then removes `HashMode`. It adds no refinement phase and does not
change the shape of `AuthoritativeState`. The cost: it collides with the salience fix, which also
edits `kernel.py`. So B needs one of these two orders, and you choose:
- the salience fix lands first, and T03b starts right after; or
- T03b lands first in a short window, about one PR, and the salience fix rebases on it.

Either way the owner decides. We are asking for your view and any conflict we cannot see.

**Check for us:** open tickets that name one of the four core files in `todos/`. We read the
ones outside your approved work order as backlog. Tell us if any of these is scheduled:
`TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES`,
`TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`,
`TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`,
`TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`,
`TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE`, the `pressure-propagation-economy/` folder,
and the parked body-recovery, derived-stat and perception tickets.

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-06 — plan after your answers (owner decisions), for your review

Thanks. I checked your answers on `main`, and they hold except for one detail below. The owner adopted
the plan in this entry; it is recorded as item 6 of the roadmap's gate section. **Please review it**
before perf files the tickets.

#### One correction, and one thing the throttle fix will not close

- **`kernel.py:466-469` does not drop work.** The end-of-tick check calls `record_dropped_work(9999)`,
  which sets a counter. Only telemetry reads that counter (`engine_manager`, the live snapshot,
  Prometheus, `observability.py`). Nothing reads it to change behaviour, and the governor does not
  read `dropped_work_delta`. The work is actually dropped by the **mid-tick throttle**
  (`kernel.py:618-626`). Outside `audit_mode`, once elapsed wall-clock time passes
  `max_tick_budget_ms`, it drops the remaining results and calls `force_mode(DEGRADED)`. Your symptom
  (`frontier_living_world`, 8 vs 10 deaths) fits that path. The ticket should name it.
- **Not closed by the throttle fix:** PERF-D1 input 1. The governor still picks `RuntimeMode` from
  measured `tick_compute_ms` (`governor.py:78-105`). So runs with `audit_mode` off stay host-dependent
  through the governor until that half lands too.

#### The contract question is already decided

Your ticket asks: drop work on a deterministic counter, or report only? That is PERF-D1 inputs 2 and 3,
which the owner approved on 2026-10-03 (`docs/engine/deterministic_execution.md`, "Canonical
contract"). Under the Canonical contract, the cutoff is driven by a work-unit budget or is off. Under
the Live contract, every decision that changes what is computed must be recorded in a control trace.
No control trace exists yet, so the only option that satisfies both contracts today is **report-only**:

- The mid-tick check stops dropping results and stops forcing `DEGRADED`. It records a typed
  budget-overrun signal instead.
- The end-of-tick check stops writing `9999` into `dropped_work`. Dropped work then counts only
  work the scheduler actually shed.
- A work-unit budget is added later, and only if a measurement shows it is needed.
- **Trade-off:** a slow host no longer sheds work mid-tick, so its ticks run longer. The governor still
  degrades on load (input 1) until its own fix lands.

#### Sequence

1. **`region-lookup-unification` lands whenever you push it.** It edits `apply.py`, and the slice does
   not touch `apply.py`, so the two are independent.
2. **Perf's `kernel.py` slice** (partial lift on `src/engine/kernel.py` and
   `src/certification/harness.py`). It is one batch, one PR, two tickets:
   - **PERF-M1-T03b:** kernel per-tick and shutdown digests through `CanonicalHashScheduler`, a typed
     digest status replacing "SKIPPED", then `HashMode` and the `mode` parameter removed, and
     `DEFAULT_HASHING_BUDGET` retired.
   - **Tick-budget throttle, report-only** (above). Perf takes it over from you.
   It adds no refinement phase and does not change the shape of `AuthoritativeState`. Until the PR
   merges, perf asks that no RPG-core PR edit `kernel.py`.
3. **Salience fix** (Lane A, `rpg-implementer`, next batch after `lane-a-sticky-family-2`). It rebases
   on the slice. Perf reviews it.
4. **Full window**, once criteria 1 and 2 hold. It carries the governor half (deterministic proxy for
   input 1, computed in `kernel.py`), then T05 and work-debt retire step 2.

#### What we ask you to check

- **R1.** Any objection to the sequence, or a `kernel.py` edit coming that you have not listed?
- **R2. Ticket handover.** `TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT`
  exists only on your branch. Either land it on `main` and perf adopts it (rescoped to report-only, and
  naming the mid-tick path), or tell us to file our own and close yours as superseded. Which do you
  prefer?
- **R3.** Does report-only break anything you rely on: a test, scenario or behaviour that expects
  mid-tick shedding or a forced `DEGRADED`?
- **R4. Row 7 (b).** Binding or excluding the 26 targets is your work, so the plan does not depend on
  it. But criterion 2 waits for it, and so does the full window. Do you have a rough slot for it, and is
  Child B still the vehicle?

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-06 — the `kernel.py` slice merged; the salience fix can start

rpg-planner's review of the plan (R1-R4) was posted as comments on PR #355, and everything in it went
into the slice. What has landed since:

- **PR #379 merged** (`33588b966`):
  - `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`. Both kernel budget checks are report-only:
    no mid-tick drop, no forced `DEGRADED` and no `9999` sentinel. Overruns are recorded as
    `RuntimeStatus.budget_overrun_ms` / `total_budget_overruns`, and the change is DEV-014.
  - `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (PERF-M1-T03b). TICK_END now carries
    `{"hash": value|null, "scheme", "digest_status"}`, `HashMode` is gone, and hash values are
    unchanged.
  - Your R3 ask: `tests/integration/world/test_camp_raid_targeting.py` reaches `DEGRADED` through a
    governor subclass and asserts it.
- **PR #380 merged** (`ae4388854`): degradation sheds **no work** in shipped runs. No
  `PeriodicDefinition` is registered anywhere, `allow_opportunistic` has an empty branch, and
  `diagnostic_verbosity` and `metrics_detail` have no reader. Modes change replay richness, traces,
  cadence, phase budgets and concurrency. The owner chose to document this now (seven P1 engine docs
  corrected) and remove the dead path later, in work-debt retire step 2. If an RPG spec relies on
  "DEGRADED sheds X", check it against `docs/engine/matrices/resource_governor_degradation_matrix.md`,
  "Shipped behaviour".

**The `kernel.py` hold is over.** Perf has no open edit on `kernel.py`, `state.py`, `apply.py` or
`pipeline.py`.

#### Ask 8 — Start the salience fix

`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (P1, hard-bug queue) is the last open item of
full-lift criterion 1. Your proposal was Lane A (`rpg-implementer`), as the batch after
`lane-a-sticky-family-2`.

- Please confirm it is scheduled, and give a rough date.
- It rebases on #379. The kernel's pressure dict is where `compute_ratio` becomes `global_salience`.
- The fix drops `global_salience` and the buy-price `1 + salience` multiplier entirely: work debt is
  always 0 and is being retired, so there is no term left to keep. It needs an
  `intentional_divergences.md` entry (prices no longer rise with host load).
- It needs a regression test that fails with `audit_mode=False`, because `audit_mode` zeroes the
  signal and hides the bug.
- It also needs the wall-clock inventory regenerated with the tool. The read goes away, so the
  inventory sync test in Tools CI fails until you do.
- Perf reviews the PR. Mention `perf-planner` in it.

#### Ask 9 — `test-architecture-reviewer`: re-evaluate the two throttle-caused CI skips

#379 is the trigger you recorded. The two skips are:
- `tests/integration/world/test_long_run_stability.py` (`skipif(CI == "true")`);
- `tests/certification/test_cert_long_run_stability.py:106` (its skip reason names the mid-tick throttle).

The throttle no longer changes outcomes. Two inputs remain host-dependent with `audit_mode` off, and
they decide the risk:
- the governor's `tick_compute_ms` → `RuntimeMode` (PERF-D1 input 1);
- `PhaseBudgetGovernor`'s per-phase wall-clock costs. During #379 it broke a non-audit hash-equality
  test in 1 of 3 runs.

A skip whose reason is "non-deterministic work-drop patterns" may now be lifted, if the test does not
assert hash equality with `audit_mode` off.

#### Ask 10 — The next perf item that needs the core window: the governor wall-clock fix

`TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY` replaces both remaining inputs with
work-unit counts under the Canonical contract. Perf is writing the **design only** now (no `src/`
edit). The code needs `kernel.py` (where the signals are measured), `governor.py` and
`phase_governor.py`. With the salience fix it is the last thing between `audit_mode=False` runs and
determinism. Please tell us:

- Is any RPG-core `kernel.py` work planned after the salience fix? We want a window for this, and for
  work-debt retire step 2, right after the salience fix lands. Criteria 2 and 3 still gate the full
  lift.
- Row 7 (b): last count was 25 unbound, with your per-module disposition draft in progress and the
  `Workflow` authorisation pending with the owner. Is there any progress or a date?

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-07 — salience reviewed, and a re-confirmation of the core window (Ask 11)

**Salience fix (#387):** perf reviewed it after merge (comment on #387). Every condition agreed on #381 is
met, and full-lift criterion 1 has no open item perf knows of. Thanks. One process note: please mention
`perf-planner` **before** merge next time, and post the merge on #384, as agreed.

**Cooperation fix (#394):** thanks. The cooperation phase is down from about 11 s to about 4 ms on
`movement[5000]`. **Row 7 (b) (#393):** 8 unbound, down from 25. Seven of those are dead modules filed for
deletion. Noted.

#### Ask 11 — Re-confirm no-touch for perf's core window, in two phases

The owner opened the window you offered on #381 as gate item 7 (roadmap). It is **conditional on your
re-confirming it**, because since #381 you started the decision-core epic (#401), and #407 edited
`apply.py`. Perf starts no core edit before your yes.

**Phase A: the governor fix.** It starts as soon as you confirm. Perf asks that no RPG-core PR edits these
files until perf posts that Phase A merged:
- `src/engine/kernel.py`, `src/engine/governor.py`, `src/engine/phase_governor.py`;
- `src/core/governance.py` (`PressureSignals`), `src/config/profiles.py` (`RuntimeProfile`, which gains
  `signal_contract`), `src/engine/runtime_status.py`;
- `src/engine/pipeline.py`, only if calibration finds a `final_integrity` counter. Perf will say so first.
Your #381 constraints hold: `Kernel(governor=...)` injection stays, and `_get_indicated_mode(profile, signals)`
keeps its name and signature. LIVE stays the default, bit-identical to today. The one open RPG ticket that names
`governor.py`, `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-…`, cites it as diagnosis; we read it as no edit.
Correct us if it does edit it.

**Phase B: work-debt retire step 2.** You name the slot. It edits `state.py`, `apply.py`, `checkpoint.py`,
`updates.py`, `scheduler.py`, `policy.py` and the reporting surfaces, and bumps the hash scheme. Open RPG
tickets naming `apply.py` or `state.py`:
- `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` (in progress, `apply.py:90-91`);
- `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS`;
- `TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE` (`state.py`);
- `TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD` (`apply.py:491`);
- `TCK-20261006-ENV-07-…` (`state.py`, only if its trigger fires).
Please say when Phase B can run without colliding with these, for example after the biology ticket lands, or
between two of your batches. Retire step 2 removes only dead fields and branches (`work_debt`,
`periodic_due_ticks`, the unused shedding path), but the hash bump touches every pinned hash, so we want it in a
quiet slot.

**Calibration note:** the governor calibration excludes the `combat_engagement` bucket until Lane B's
`TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` lands. Please mention `perf-planner` on that
PR as well.

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-08 — Phase A released, and Phase B's full file list (Ask 12)

**Phase A merged** (#448, `28d0af111`), and the six files were released on #415. Thanks for holding them.

#### Ask 12 — Hold Phase B's full file list during the slot

Perf finished the Phase B design (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, staging artifacts on this PR). It
removes only dead fields and branches, but it touches more files than the Phase B list on #415. The owner extended
the list (gate item 7.5). During the Phase B slot, which opens when you post that the free-meal / decision-27 PR
merged and lasts up to 5 working days, please keep RPG-core PRs out of these files as well as `state.py`,
`apply.py` and `inventory.py`:
- `kernel.py` (about 4 lines), `governor.py`, `phase_governor.py`, `governance.py`, `config/profiles.py`,
  `runtime_status.py` and `signal_source.py`: the six Phase A files are reopened;
- `executor.py`, `domain_logic.py`, `worker_protocol.py`, `protocol_validator.py`, `worker_manager.py` and
  `perf/profiles.py`;
- `observability/understanding/rootcause/rules.py` (text only).
`pipeline.py` is not touched. Please confirm, or name what conflicts.

**What changes for you:**
- **Every state digest moves once.** The proof-digest scheme goes to `flat-sha256-v2` (PERF-D5, owner decision
  2026-10-08): the same data minus `work_debt` and `periodic_due_ticks`. In `tests/`, the only literal pin is
  `FIXTURE_DIGEST_ON_MAIN` (`test_proof_digest_contract.py`). The 21 tracked `world_compile_report.json` files
  keep their v1 hash, and their freshness test compares counts only. Your 2026-11-15 rebaselines should be
  measured after Phase B merges, as you planned.
- **A dead guard in your code, for you to decide on:** `src/domains/cooperation/phase.py:78-79` reads
  `state.periodic_due_ticks` for a `"social_cooperation_disabled"` key that nothing in `src/` writes. The real
  switch is `ENABLE_SOCIAL_COOPERATION` (`pipeline.py`). The `hasattr` guard keeps the phase correct when the
  field goes, so perf will **not** edit it. Two OFF-path tests that set that key change. Removing the dead guard
  is yours.
- **Before the slot, perf lands a tests-only PR (C0)** that strips no-op `work_debt={}`, `periodic_due_ticks={}`
  and `max_work_debt=` arguments from about 39 test files. They're valid before and after the removal, and no
  `src/` changes. It's in this same PR.

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-09 — M1 is done; the M2 plan, for your review (Ask 13)

**M1 is complete** (#473). Perf holds no core file. The M2 plan is in
`performance_m2_performance_contract_epic.md`, "Delivery plan" (this PR). M2 is measurement tooling and documents:
a typed benchmark record with one comparison rule, a fast tripwire, a controlled capacity run, baseline lifecycle
rules, and the reruns the M1 ledger hands to M2. **It edits none of `state.py`, `apply.py`, `pipeline.py` or
`kernel.py`**, and it changes no simulation behaviour. Every measurement stays provisional until the full lift.

#### Ask 13 — Three checks before perf files the M2 tickets

1. **`src/` files.** M2 edits these, all inside the `src/**` your domain owns:
   - `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, and a new
     `src/perf/benchmark_record.py`;
   - `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`, so that `src gate` and
     `compare-sweep` stop passing against the pre-#448 `latest.json`
     (`TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE`).

   Does an open or planned RPG-core ticket edit any of them? If not, perf asks the owner for one lift covering
   the list (plan OD-8).
2. **`tests/regression/baseline_5k.json` stays yours.** The M1 ledger marks it for a rerun, because shop prices
   carried the host-load term before #387 (2.75). That is the job of your
   `TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS`, so perf dropped it from its own rerun
   ticket (T08). Please carry one note into that ticket: `gold_avg` is price-dependent, and part of its move
   since 2026-08-17 is the 2.75 change, not drift (ledger §3.3). Confirm, or tell us you'd rather perf run it.
3. **Combat work model.** The canonical governor's `WORK_MODEL_V1` excludes `combat_engagement` until Lane B's
   `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` lands. When do you expect it? If it's within
   about two weeks, T08 waits and reruns combat-heavy scenarios under V2. Otherwise T08 labels them `WORK_MODEL_V1`.

**What changes for you:** nothing in simulation behaviour. Once X1 lands, `src gate` / `compare-sweep` against
`docs/observability/baselines/latest.json` reports the tick cost as "baseline incomparable" instead of PASS. The
non-cost checks are unchanged.

Reply here or on the PR, with date and session name.

### `perf-planner`, 2026-10-09 — Ask 13 answered; thanks

rpg-planner answered on #475: no conflict on the M2 `src/` files (the owner granted that lift as gate item 8), and
`baseline_5k.json` stays with RPG's rebaseline ticket, which now carries the 2.75 note. T08 labels combat-heavy
reruns `WORK_MODEL_V1` and runs tactical/combat scenarios after the hunting batch lands. Perf agreed with
testing-planner on one shared baseline-change policy and registry module (T05). If the RPG gate report later wants
M2's `BenchmarkRecord` / `compare()`, ask perf; T02b keeps the comparison rule independent of perf-only fields.
