---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [planning, process-improvement, workflows, architecture]
---

# RPG Core — Two-Implementer Lane Split

**Decided by the owner, 2026-10-04:** RPG core is blocking other sessions and the remaining queue is
large (~60 loose tickets plus 16 epic folders), so the rpg domain runs **two implementer sessions
concurrently**. This document is the partition that keeps them from colliding. It exists because two
implementers are only faster than one if they almost never touch the same file.

Owner of this document: `rpg-planner` (the dispatching planner). The implementers do not re-draw their
own lanes.

## 1. The seam

The split follows the seam the codebase already has, which is also the seam the Mechanics Bible and the
parity ledger already use:

> **Lane A — Agents.** What entities perceive, decide, and do.
> **Lane B — World & Body.** What the world and the entities are made of.

That this one line partitions `src/`, the Bible chapters, and the parity-ledger files all at once is the
evidence it is a real seam and not an arbitrary cut. Anything that needs both lanes at once is a sign the
ticket is scoped wrong, or that it belongs in §3.

## 2. Lane ownership

### Lane A — Agents (currently `rpg-implementer`)

```
src/cognition/            src/strategy/            src/ai/
src/content_semantics/
src/domains/{perception,motivation,emotion,memory,information,belief_institution,
             commitment,cooperation,combat_engagement,faction,fame,culture,adventure}/
src/systems/{social_systems,strategic_systems}/
src/systems/{narrative,social_contract,social_memory,learning,routine,redirection}.py
src/engine/{combat,combat_rewards,cognition,legality,faction_decision,faction_constants,
            interaction,behavior_consumers,candidate_selector}.py
```

Bible chapters **02** (combat laws) and **04** (strategic cognition). Parity ledger
`combat_movement.yaml`, `strategic_cognition.yaml`, `social_narrative.yaml`.

### Lane B — World & Body (currently `rpg-implementer-2`)

```
src/worldbuilding/   src/worldassembly/   src/worldgeneration/   src/worldmodules/   src/world/
src/content/         src/entities/        src/progression/       src/economy/
src/town/            src/quests/          src/scenarios/
src/systems/{world_systems,lifecycle_systems,economy_systems}/
src/systems/{economy,crafting,market,harvest_system,loot_system,guild_system,quest*,
             chest_system,genetics,lifecycle,town_service}.py
src/domains/{demographics,progression,world_emergence,time,chronicle,campaigns,
             culture→A,fidelity,feature_packs}/
data/worlds/**       data/content/**
```

Bible chapters **01** (entity anatomy), **03** (economic laws), **05** (world evolution), **06**
(worldbuilding foundation). Parity ledger `substrate.yaml`, `town_resource.yaml`,
`world_dynamics.yaml`, `progression.yaml`.

*(`src/domains/culture/` is Lane A — listed above in both places only to flag the one directory whose
name suggests content but whose behaviour is appraisal-side. If a second such case appears, correct this
document rather than deciding ad hoc.)*

## 3. The contested surface — claim before editing

These paths are reachable from both lanes, so they are **not** owned by either. They are the entire
conflict risk, and they are governed by a claim, not by a boundary:

```
src/core/**                      (state, entities, registries, conservation)
src/engine/kernel.py             and the 7-phase loop contract
src/engine/{apply,apply_plan,executor,governor}.py   (the authoritative mutation path)
src/observability/**             src/api/**
docs/mechanics/**                docs/engine/**
tests/ shared conftest and fixtures
```

**Protocol.** An implementer that needs a contested path asks the planner before editing it. The planner
grants an exclusive hold for the life of that one ticket and records it in the dispatch note; the other
lane either waits or gets resequenced. No hold is implied by a lane boundary, and no hold outlives its
ticket. `tests/architecture/**` additionally routes to `testing-planner` — ask there, not here.

## 4. The rules that actually prevent the collisions

1. **Dispatch-time file-overlap check (the planner's job, every dispatch).** No two concurrently-open
   tickets may name the same file in `## Related Code Areas`. The planner keeps the in-flight file list
   and checks a candidate against it *before* dispatching, not after a merge conflict. This is the
   single highest-value rule here — a lane split without it just moves collisions later.
2. **One worktree and one branch per implementer, never shared.** One git writer per worktree. A planner
   sharing a worktree with an implementer stops running git in it entirely.
3. **One open PR per lane.** Fold follow-ups into the lane's open PR rather than stacking a second. Two
   PRs must never touch the same file — if that is unavoidable, the work was mis-laned.
4. **Merge `origin/main` after the other lane's PR lands, before continuing.** Divergence is what turns a
   small overlap into a painful conflict. Do it at the merge, not at the next PR.
5. **Shared machine resources stay serialised.** `clean_data_runs_early` is mtime-gated, not
   session-scoped, so it deletes the other implementer's run data — **one simulation pipeline at a time
   across both lanes**, coordinated through the planner. A PID check is not a fix; PIDs recycle. Each
   implementer stages its own `agent-working/agent-monitoring/` shard in every commit.
6. **A cross-lane need is reported, not taken.** Message the other implementer first. Small, confirmed
   non-overlapping exceptions are fine when granted explicitly and written down (see §5).

## 5. Standing exceptions

- `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT` (Lane B's batch) fixes one
  undefined name in `src/engine/kernel.py` (contested) and one in
  `src/systems/social_systems/party.py` (**Lane A's** territory). Granted as a cross-lane exception on
  2026-10-04: both are one-line fixes, and Lane A confirmed its own in-flight sweep touches neither
  file. Recorded here rather than waived silently.

## 6. Current state, 2026-10-04

| | Lane A — Agents | Lane B — World & Body |
|---|---|---|
| session | `rpg-implementer` | `rpg-implementer-2` |
| worktree | `/home/u24desktop/Working/rpg-wt-goal-dispatch` | `.claude/worktrees/m2-idea43-temporal-note` (shared with the planner; implementer is sole git writer) |
| branch | `hostility-sweep-batch` | `world-definition-correctness-batch` |
| in flight | hostility sweep (Test phase): `src/content_semantics/faction.py`, `src/engine/{combat,legality,cognition}.py`, `src/systems/world_systems/intake.py`, `src/systems/strategic_systems/intelligence.py`, `src/domains/cooperation/providers.py` | the three world-definition P1s (generator region-ID collision → inert June balance fix → two undefined names) |

Verified non-overlapping at dispatch: the two in-flight sets share no file, and Lane A's sweep does not
touch `src/engine/kernel.py`. Note `src/systems/world_systems/intake.py` is a **Lane B path being edited
by Lane A** under the sweep that predates this document — it closes before Lane B goes near it; no new
cross-lane work is dispatched into that file until it lands.

## 7. Candidate next work per lane

Foundation-first still governs (hard RPG bugs before features, per the owner's 2026-10-02 direction), so
these are bug clusters, not feature slices. Order within a lane is the planner's call at dispatch.

**Lane A:** combat objective fixed-point non-termination; combat gate downstream starvation; combat risk
evaluation 3× mismatch; cross-faction combat rarity; tactical path nondeterminism under audit mode;
tactical retreat hardcoded world origin; perception-update phase never instantiated; cognition-capacity
enforcement conditional; sensory filter on a legacy faction enum; appraisal reads reputation without a
knowledge gate; capability context region/enemy data always empty; motivation doctrine stale.

**Lane B:** calamity intensity producer never fires; calamity random-chance unused constant; lair region
trauma never accumulates; regional influence shift never fires; region-danger-seen dead preconditions;
worldbuilding dangling region reference; worldbuilding duplicate region id across modules; regional
sovereignty orphan taxation; no mechanism records per enemy-kind danger; XP level-up threshold vs corpus
combat volume; biological pressure accumulation uniform; demographic cohort net delta truncates to zero;
spawn/derivation incompatible derived-stat models.

**Needs the planner's own sequencing pass before it can be laned:**
`TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` Child B (registry bindings) + **B2**
(`TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`) — they run **together, before** any
rule-map slice, and registry bindings land in the contested `src/core/` surface. Epics are
all-or-nothing; never cherry-pick out of the folder.
