---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
artifact_type: investigation
tags: [world, determinism, observability, architecture, root-cause]
---

# Investigation — sovereignty ownership-writer consolidation

The ticket body carries the verified 2026-09-24 two-writer comparison table. **This file does not
restate it.** It records what changed since that table was written, resolves the ticket's single
`UNVERIFIED` open question, and names two findings the ticket does not contain.

Base: branch `sovereignty-ownership-writer`, cut from `origin/main` `6d630250d`.

---

## 1. The ticket's own priority assessment is stale, and the reason is datable

The ticket states the P1 consistency hazard is resolved and classes itself `P2 / refactor`. That
assessment is **dated 2026-09-25**. `#276` landed **2026-10-01**, six days later (`786f9ee9b`).

`#276` widened what reaches `recent_deaths` to include `DEFEAT`, `HAZARD` **and** passive deaths
(`src/systems/lifecycle_systems/lifecycle.py:215-234`). Writer 2 is gated on `if recent_deaths:`, so
it now fires on materially more ticks than when the ticket was written. The ticket could not have
accounted for this.

**This does not by itself establish a hard bug.** "Fires more often" is not "holds two conflicting
live values"; the two writers run sequentially within one tick (writer 1 at phase `world_dynamics`,
writer 2 later at `lifecycle`), so the later write simply wins. Whether they ever *disagree*, and
whether writer 2 ever writes ownership at all, is a runtime question — see §5.

## 2. Line anchors in the ticket have drifted; the structure has not

Re-verified at `6d630250d`. Structural claims **all hold**: shared `±50` constants, no `HERO_GUILD`
branch in writer 2, `world_dynamics` (`pipeline.py:348`) before `lifecycle` (`pipeline.py:414`).

One anchor moved: the call site is **`lifecycle.py:298`**, behind the gate at **`294`** — not the
`272` the ticket cites. Cite 298/294 from here on.

## 3. The decisive open question resolves: NOT ADDRESSED, and unobstructed

The ticket marks this `UNVERIFIED` and says it "may decide the whole ticket": is moving the
ownership-settlement sweep to a phase position after `lifecycle` permissible under the Sliding State
ordering rule and the pipeline contracts?

**Answer: no document addresses it, and nothing in the code blocks it.**

- **Sliding State is not a general phase-ordering law.** Its sole authoritative statement is
  `docs/engine/authoritative_pipeline.md:79`, scoped to the `action_routing` phase and describing
  intra-phase actor-queue visibility of combat kills. Every other occurrence in the repo is a
  derivative restatement. It says nothing about cross-phase placement of a settlement step.
- **The 39-phase order is not frozen.** `authoritative_pipeline.md:11` states only the Singular
  Bottleneck Law (a routing law); line 17 declares the doc *derived from* `pipeline.py:refine()`.
  `tests/integration/pipeline/test_phase_order_contract.py::test_phase_order_frozen` pins only the
  **7 kernel `TickPhase` enum members** and never mentions `world_dynamics` or `lifecycle`.
  `src/engine/phase_graph.py:36-70` carries skip-policy metadata with **no ordering edges at all**.
- **No phase between `world_dynamics` (348) and `lifecycle` (414) reads `owner_faction_id`.** All 13
  intervening phases were enumerated from source and none reads it. Every actual reader is either
  earlier (`town_resolution.py` at phase `pipeline.py:339`; `faction_decision.py:203` at `:230`),
  post-`refine()` (`apply_plan.py`, `metrics.py`, `fingerprint.py`, the presenters, the two
  observability extractors), a docstring only (`military_conflict.py:163-166`), or dead
  (`src/world/regional_sovereignty.py` — zero callers; `quest_generator.py`/`quest_engine.py` —
  reachable only via unimported re-export shims).
- **Stronger structural reason the position is safe:** phases read `state.regions`, the frozen
  pre-tick snapshot (`src/core/state.py:288`). `owner_faction_id_set` lives on `WorldUpdate` and is
  invisible until apply. So the phase position of the ownership *write* is unobservable to every
  in-tick reader; only the end-of-tick applied value can differ.
- **In-repo precedent for exactly this design:** `src/engine/pipeline.py:430-435`, the
  `faction_sentiment` phase — "Runs last among the real per-tick phases so it sees every
  SocialBondUpdate produced this tick". Placing a settlement step late so it sees every contribution
  is already an established, comment-documented pattern here. `belief_staleness_decay`
  (`pipeline.py:400-407`) is a second precedent.
- **No same-tick `SOVEREIGNTY_SHIFT` consumer exists.** Events flush into `recent_world_events` at
  apply (`src/engine/apply.py:367-370`) and are visible only from the **next** tick; `pipeline.py:141-144`
  and `:234` state the one-tick lag is inherent. `WorldEmergencePhase`, `town_resolution.py:51` and
  `faction_decision.py:214,261` all read the lagged window. `tests/unit/world/test_sovereignty_events.py`
  calls `resolve_dynamics` directly and is phase-position-agnostic. There is **no HardLawMonitor
  invariant** on sovereignty.

**Residual consequence, not a blocker:** `world_events_add` is an ordered list truncated to the last
500 at `apply.py:370`. Moving the sweep later moves its events later in that list (more likely to
survive truncation) and inverts their order relative to the vacancy events appended at
`lifecycle.py:318`. No consumer was found that depends on intra-list order. This is
fingerprint-visible and belongs in the divergence entry.

## 4. Finding the ticket does not contain: writer 2's flips are invisible to observability

`WORLD-107` (`docs/parity_ledger/world_dynamics.yaml:1374-1388`) is `status: verified`,
`priority: P1`. Its text asserts that on a ±50 crossing a `SOVEREIGNTY_SHIFT` `WorldEvent` is emitted
and flushed, "making sovereignty shifts observable in `WorldEmergencePhase.execute()` subsequent
ticks".

Writer 2 (`process_influence_shift`) **emits no `SOVEREIGNTY_SHIFT`** — confirmed in the ticket's own
verified table and re-checked here. Therefore **any ownership flip performed by writer 2 is invisible
to `WorldEmergencePhase` and to agent observability**, while `WORLD-107` asserts such shifts are
observable.

This is a conditional defect, and the condition is measurable: it is live if and only if writer 2
ever actually writes ownership in production (§5). If it does, `WORLD-107`'s `verified` status is
false today and this ticket carries a parity correction, not merely an architecture tidy-up.

## 5. The one question still open, and why it is a measurement

Writer 2's two conditions are narrow — conquest requires `owner_faction_id is None` **and**
`influence <= -50`; liberation requires an invader owner **and** `influence >= +50`. Writer 1 runs
first in the same tick and settles ownership against the same `±50` constants. So writer 2 may be
**effectively dead for ownership purposes**, its conditions already discharged by writer 1 earlier in
the tick.

Which it is decides the ticket's shape:

- **Writer 2 never flips** → it is dead code for ownership. Consolidation is low-risk cleanup, the
  §4 observability gap is latent rather than live, and `WORLD-107` stays honest by accident.
- **Writer 2 does flip** → §4 is a live P1 parity defect, and the handover's "one durable fact held
  with two conflicting live values" framing is earned rather than asserted.

A multi-thousand-tick instrumented run is in progress to settle this, with a positive control — a
zero result could mean "cannot happen" or "the instrument never fired", and those must not be
confused. **This section is deliberately unresolved until that lands.** Do not plan against either
branch before then.

### 5a. A second runtime claim, flagged and pending

`src/world/influence.py:62` is the **only** producer of `WorldUpdate.influence_delta` in `src/`
(verified by exhaustive grep: the other hits are a local dict at `:37,54,57`, the merge at
`core/updates.py:881`, the apply at `apply_plan.py:118`, and the consumer at `world_dynamics.py:89`).
That producer runs at `lifecycle`, 13 phases **after** its consumer.

If no production path populates `influence_delta` before `world_dynamics` executes, then writer 1's
"unconditional sweep against settled influence" in fact always settles against **last tick's**
influence, never this tick's — and moving it after `lifecycle` would be the first time it sees
in-tick influence. `tests/integration/world/test_regional_sovereignty.py:63-71` proves the field *can*
be populated from outside the pipeline (it injects one directly, and `TrustBoundaryPhase` does not
strip `WorldUpdate`), so whether anything in **production** does is the open part. Being measured
alongside §5; **inference only until then.**

## 6. Adjacent precedent worth following

- `docs/guidelines/intentional_divergences.md` §2.58 (`RATIFIED`, class **Unified**) settled the ±50
  threshold and at lines 1943-1947 **explicitly deferred this ticket**, flagging but not prejudging
  the phase question.
- §2.59 (`TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`) is the **same shape of problem** — two
  writers of one field disagreeing by one tick — resolved by declaring one sole authority
  (`resolve_lifecycle`), class **Bug Fix**, and notes it closed the gap "without any kernel
  phase-ordering change". Closest available template.
- §2.52 characterises `refine()`'s order as "already-certified" — the nearest thing in the corpus to
  treating sub-phase order as contractual, but it is an incidental phrase used to justify *relying
  on* the order, not to forbid changing it. Worth naming so nobody later reads it as a prohibition.
- `docs/world/regional_sovereignty_runtime_contract.md:36-55` records the two writers as a scoped
  documented decision and states the one-tick consolidation risk. It records the status quo and
  imposes no prohibition.

## 7. Out-of-scope drift found while investigating

Recorded so it is not lost; **not** to be fixed under this ticket unless it blocks the change.

1. **`authoritative_pipeline.md` is out of parity with the code.** The doc says "39 phases"
   (`:11`); `src/engine/pipeline.py` has **44** `update = run_phase(...)` call sites. At least
   `belief_staleness_decay` (`:408`), `clan_lifecycle` (`:418`) and `faction_sentiment` (`:441`) are
   absent from the doc table. The only test touching the number asserts the literal string
   `"39 phases"` appears in the doc
   (`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:18`), so the count is
   pinned as text while the code has moved. Both verified directly.
2. **Two `combat-mechanics` SKILL.md copies carry a stale phase number** for `action_routing`
   ("phase 12"; the doc table now numbers it 13) — `.claude/skills/combat-mechanics/SKILL.md:103`
   and `.agents/skills/combat-mechanics/SKILL.md:101`.
3. **A third, dead sovereignty path exists.** `src/world/regional_sovereignty.py::RegionalSovereigntyService`
   has zero callers — already tracked by `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`
   (still `todos/`, `hotfix`). No file overlap with this ticket; schedulable independently. Relevant
   only as context: any consolidation should note it is not the intended new home for settlement.

## 8. Verification state of every claim in this file

| Claim | Status |
|---|---|
| `#276` landed 2026-10-01, ticket written 2026-09-25 | **verified** (`git log`) |
| `recent_deaths` widened to DEFEAT/HAZARD/passive | **verified** (source read) |
| Call site at `lifecycle.py:298`, gate `294` | **verified** |
| Structural table still accurate at `6d630250d` | **verified** |
| Sliding State is `action_routing`-local | **verified** (sole doc occurrence) |
| 39-phase order not pinned by any test | **verified** |
| No intervening phase reads `owner_faction_id` | **verified** (enumerated + exhaustive grep) |
| No same-tick `SOVEREIGNTY_SHIFT` consumer | **verified** |
| Writer 2 emits no `SOVEREIGNTY_SHIFT` | **verified** |
| `influence.py:62` sole producer of `influence_delta` | **verified** (exhaustive grep) |
| Doc says 39 phases, code has 44 `run_phase` sites | **verified** (both counted) |
| Baseline: 10 tests pass incl. `test_regional_ownership_flip` and WORLD-107's `test_path` | **verified** (run) |
| Writer 2 ever flips ownership in production | **PENDING measurement (§5)** |
| `influence_delta` always zero at `world_dynamics` in production | **PENDING measurement (§5a)** |
| Replay fingerprint unchanged by a phase move | **NOT verified** — needs a determinism run |
| Whether only the 2.2 ownership block must move, vs the whole `world_dynamics` phase | **open design question** (2.1 trauma reads `combat.alive_set` from earlier phases; respawn/calamity sub-sections cadence-gated and wired to `EntityGenerator` at `pipeline.py:346-348`) |
