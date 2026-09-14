---
status: active
layer: mechanics
authority: P1
audience: developer
last_verified: 2026-09-14
---

# Faction War Drivers — Design Proposal (DRAFT, NOT CERTIFIED)

**This is a proposal, not yet-built mechanics. No code has been written against this document.**
Per explicit instruction: peer review required before any implementation. Once approved and built,
the verified formulas belong in `docs/systems/faction_contract.md` (the living, parity-ledger-backed
contract for this subsystem) — this file is the review artifact, not the destination.

Ticket: `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`. Full investigation evidence:
`stored_artifacts/TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION/investigation.md` (once
moved) / `staging_artifacts/.../investigation.md` (current).

## 1. Problem, restated

`DiplomaticStateMachine.compute_transitions()` is a real, wired, correctly-implemented 4-step
diplomatic state machine — but every precondition past the first rung is structurally unreachable:

1. `military_strength` never diverges from its `1.0` default before war (the only producer is a
   WAR-exhaustion drain that requires war to already exist).
2. `territory` can only be gained *by* a war (siege-won transfer requires an existing WAR).
3. `tension_level`'s only real runtime producer is gated on territory, so it's blocked by #2 too.

**The war system can only be entered from a state that only war produces.** User's decision: build
real pre-war drivers — militaries diverging and tension rising from actual world conditions, not
authored starting positions. This document proposes how, reusing existing live systems wherever a
real one exists, and states plainly where none does.

## 2. Reuse-before-invention: what already exists

### 2.1 Does faction→region ownership already exist? — Partially yes, with a real gap

`docs/mechanics/regional_sovereignty.md` (Certified) and `RegionState.owner_faction_id: Optional[int]`
are real and live: death-triggered influence deltas (`FactionInfluenceService.process_influence_shift()`,
`src/world/influence.py`) correctly classify the *specific* dying/killing entity's real faction via
`FactionSemanticsService.is_invader()`/`is_protector()`, which reads each catalog faction's own
`alignment_bucket` (`defender`/`invader`/`neutral`) — a genuine per-faction classification covering
all ~16 real factions, not just two.

**The gap**: the resulting ownership write collapses that specific-faction identity into the legacy
4-value `Faction` enum (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`) —
`owner_faction_id_set = Faction.MONSTER_HORDE`, always, regardless of which real catalog faction
(`orc_clan`, `goblin_warband`, `dragon_cult`, ...) actually caused the conquest. This is a **known,
already-documented limitation** — `docs/systems/faction_contract.md`'s own FAC-010 note: *"The
int/str type mismatch [between `RegionState.owner_faction_id: Optional[int]` and
`FactionState.faction_id: str`] is a known limitation."* Territory transfer (siege-won) already
writes to the correct place (`FactionState.territory`, string-keyed) — only the *influence-driven*
conquest path collapses identity.

**Taxation reuses the same collapsed identity** (`src/engine/town_resolution.py`): vault keys are
`f"faction_{Faction(fid).name.lower()}_gold"` — literally `faction_hero_guild_gold`,
`faction_monster_horde_gold`, etc. Confirmed only 4 buckets, never a real catalog faction id.

**Verified reachability, split by path**:
- **Static (compile-time) ownership is real, reachable, and already produces income.** In a real
  3000-tick run (`urban_political`, seed=42), `hometown`/`trading_hometown` were pre-authored at
  compile time with `owner_faction_id=Faction.HERO_GUILD`, `influence=100.0`. `faction_hero_guild_gold`
  grew from a 1000 baseline to `5708.00` over the run — real, live taxation income.
- **Dynamic (influence-driven) conquest/liberation is CONFIRMED unreachable, not just unverified.**
  §5's follow-up check ran the same probe across four real corpus worlds (`urban_political`,
  `frontier_living_world`, `dungeon_crawl`, `generated_frontier_3_42`), 3000 ticks each — 12,000
  combined real ticks. **`region.owner_faction_id` never changed once, for any region, in any of
  the four worlds.** Every unowned "wild" region (`goblin_camp`, `bandit_road`, `old_mine`, etc. —
  regions independently confirmed elsewhere this batch to have real combat, via `trauma_score`
  movement) showed `influence` staying at exactly `0.0` for the entire run, in all four worlds —
  not slow, not partial, exactly zero movement. The only nonzero influence anywhere was the two
  regions with compile-time-authored ownership, pinned at their starting `100.0` and never moving
  further either.

  Traced the classification path by hand to rule out an obvious cause: `EntityGenerator.spawn_monster()`
  sets `identity.faction=Faction.MONSTER_HORDE` (no `identity.properties["faction_id"]`), so
  `get_faction_id_str()` returns `"monster_horde"`; `FactionSemanticsService.get_alignment_bucket()`
  finds no catalog entry literally named `"monster_horde"`, falls back to
  `get_legacy_faction_bucket()`'s string-matching heuristic, and correctly resolves `"invader"` —
  classification *should* work for the death of an ordinary spawned monster. `recent_deaths`
  collection in `lifecycle.py::resolve_lifecycle()` has no role/kind filter that would exclude
  monsters either. The actual root cause was not chased further here (time-boxed — this is now a
  separate reachability defect from the one this ticket investigates, filed as its own follow-up:
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`). **This changes §3.2's confidence level from
  "unverified" to "known-broken prerequisite"** — see the updated table in §3.3.

### 2.2 What could make military strength diverge? — Vault gold is real; region-count is unverified

Reusing the taxation/vault system (§2.1) once specific-faction identity is fixed gives a real,
already-partially-live economic signal per faction. `FactionState.resources: Dict[str, int]` exists
on the dataclass but has **zero real producers** (confirmed via grep — not wired to anything;
`AuthoritativeState.global_resources` is the real, live vault, not this field). `RegionState.population_cohorts`
exists and is real per-region demographic data, but is not evaluated in this pass — flagged as a
possible future input, not proposed here, to avoid the exact failure mode peer warned about (a
formula built on entity/cohort-level data that turns out uniform across the real corpus, the way
the prior perceived-power draft found every entity at level 1). Region-count-controlled is
plausible in principle (more territory → more military weight) but its own real producer (§2.1's
dynamic conquest path) is now confirmed unreachable, not just unverified — proposing it as an input
would inherit that same confirmed-dead reachability, not a new open question.

### 2.3 Would fixing territory alone unblock tension? — Yes, no new mechanism needed

`FactionAwarenessService.compute_tension_updates()` (`src/engine/faction_decision.py:221-245`) is
already correct and complete: `+0.1` tension per `RESOURCE_DEPLETED` WorldEvent inside
`fs.territory`. It is blocked *only* by `territory` always being empty. **Fixing §2.1's identity
gap so factions actually receive `FactionState.territory` entries makes this producer start working
with zero new code.** This is the cleanest win in this whole proposal — a real, already-correct
mechanism currently starved of its one input.

## 3. Proposed design

### 3.1 Close the identity gap (breaks loop #2 territory, and #3 tension for free)

Add a new field carrying the *specific* catalog faction id alongside the existing legacy int field
— **do not change `RegionState.owner_faction_id`'s type**, given its wide consumer surface
(`town_resolution.py`, `quest_engine.py`, `quest_generator.py`, `metrics.py`,
`state_presenter.py`, `replay/fingerprint.py`, `event_extractor.py`/`event_shapers.py` — all
confirmed via grep). A parallel field keeps every existing consumer's behavior byte-identical and
scopes the new behavior to exactly the code that needs specific-faction identity.

Proposed: `RegionState.owner_faction_id_str: Optional[str] = None`, populated in
`FactionInfluenceService.process_influence_shift()` from the same `get_faction_id_str(entity)` call
already made on each death event (currently used only to classify protector/invader, then
discarded) — no new classification logic, purely recording what's already computed.

A new, small reconciliation step (run once per tick, or on `owner_faction_id_str` change) derives
`FactionState.territory` for the owning faction: add the region to the new owner's `territory`,
remove it from any prior owner's. This is additive to the existing siege-transfer path
(`FactionUpdate.territory_add`/`territory_remove`), not a replacement — both paths write to the
same authoritative field.

**This one change is sufficient to make `shared_territory` (loop #2) reachable, and — because
`compute_tension_updates()` already reads `fs.territory` correctly — simultaneously unblocks organic
tension growth (loop #3) with no separate mechanism.**

### 3.2 Military strength driver (breaks loop #1) — provisional formula, needs review

Reusing §2.1's now-fixed per-faction vault gold (`faction_{faction_id}_gold` in
`global_resources`, once §3.1's identity fix also extends to the taxation key — a small, same-shape
change to `town_resolution.py`'s `faction_keys` construction):

```
military_strength = clamp(0.2, 3.0, 1.0 + LOG_SCALE * log10(max(1.0, vault_gold / BASELINE_GOLD)))
```

Sketch only — `LOG_SCALE`/`BASELINE_GOLD` are placeholders, not proposed values; a log scale is
suggested so a faction with 10x the gold isn't 10x the military strength, matching the format of
other real multiplier tables in this codebase (e.g. `DIFFICULTY_TIERS`'s own sub-linear growth).
**This needs real-run calibration once vault gold is confirmed to actually diverge meaningfully
between multiple factions** — with `owner_faction_id_str` wired, at minimum two real factions (not
just the legacy Hero Guild/Monster Horde pair) need to hold territory and generate divergent income
for this formula to produce a real, non-degenerate `military_strength` spread. That is unverified
until §3.1 lands and a real run is measured against it — flagged explicitly rather than assumed.

### 3.3 Which loop each driver breaks

| Driver | Loop broken | Confidence |
|---|---|---|
| §3.1 identity fix → `FactionState.territory` derivation | #2 (`shared_territory`) | High — reuses a fully-live classification path; only the write-side collapse is new work |
| §3.1 (same fix, free) → tension accrual unblocked | #3 (`tension_level`) | High — the consuming mechanism is already correct and complete, purely input-starved |
| §3.2 vault-gold-driven `military_strength` | #1 (`military_strength` imbalance) | **Low, pending a separate fix.** §2.1's dynamic-conquest path is now confirmed unreachable (12,000 real ticks across 4 worlds, zero ownership changes) — `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` must land first, or this driver has no real per-faction signal to read beyond the two legacy Hero Guild/Monster Horde buckets that happen to be statically pre-owned in most worlds |

### 3.4 What stays circular / open, stated plainly

- **Dynamic (influence-driven) conquest is now confirmed to never fire for any faction in a real
  run** (§2.1, §5) — this is no longer an open question but a second, separate reachability defect
  sitting directly underneath §3.2's proposed driver. Filed as its own ticket
  (`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`) rather than folded into this design, since
  it's a distinct mechanism (`FactionInfluenceService.process_influence_shift()`) with its own root
  cause still to be found. **§3.2 should not be built until that ticket resolves** — building a
  military-strength formula on top of a per-faction signal that structurally cannot diverge (since
  only the two legacy Hero Guild/Monster Horde vaults ever move, via static pre-authored ownership,
  never any of the other ~14 factions) would reproduce this exact ticket's own root problem one
  layer down.
- **Vault-gold divergence between the ~14 non-Hero/Monster factions specifically has never been
  measured, and per the above, currently cannot be** — the one real growth observed in this
  investigation (`faction_hero_guild_gold`: 1000→5708) came entirely from compile-time-authored
  static ownership, not any dynamic path.
- This proposal does not address `EntityGenerator.spawn_stronghold()`'s own maturity-scaled stat
  term (flagged in the sibling maturity-gate ticket, D-05) — out of scope here, unrelated mechanism.

## 4. "War actually works end-to-end" — the acceptance bar, stated before any code lands

Per the lesson carried forward from the maturity-gate ticket: a declared WAR is not the finish
line. Sieges, territory transfer, and `EXPAND_TERRITORY` (`src/engine/military_conflict.py`) are
all downstream, live, wired code that has — per D-06's own original finding — **never actually run
in a real corpus episode**, because no WAR has ever been declared. Once war becomes reachable,
treat that code as unverified, not proven, exactly as the maturity-gate ticket found real defects
(tier-5 stat fallback, unregistered loot) waiting behind a gate nobody had ever opened.

**The real acceptance bar for this design, once built**: one real, unmodified corpus-world run
where all of the following are observed, not just constructed in isolation://
1. At least one real faction pair's `military_strength` diverges meaningfully from the `1.0`
   default via the new driver (not hand-set).
2. At least one real faction pair reaches `WAR` via `DiplomaticStateMachine.compute_transitions()`
   under real, unmodified thresholds — not a threshold change, since none is proposed here.
3. A siege actually starts, progresses, and completes (`MilitaryConflictPhase.execute()`) with a
   real territory transfer and a real `TERRITORY_TRANSFERRED` WorldEvent.
4. `EXPAND_TERRITORY` (if it depends on the transferred territory) is checked for whether it
   actually fires correctly with genuinely-transferred territory, not just idle code.
5. The eventual `WAR → NEUTRAL` exhaustion transition is observed to fire correctly too, closing
   the loop, not just the opening half.

Declaring victory at step 2 alone repeats the exact mistake this arc has spent all week correcting.

## 5. Verification done before sign-off (was: "immediate next step")

Checked whether `RegionState.owner_faction_id` (dynamic path) ever flips for a non-pre-authored
region, for any faction, in a real corpus world. Ran the same instrumented probe across four real,
unmodified worlds — `urban_political`, `frontier_living_world`, `dungeon_crawl`,
`generated_frontier_3_42` — 3000 ticks each, 12,000 combined real ticks.

**Result: zero ownership changes, in any world, for any region, ever.** Every "wild" region
(confirmed elsewhere this batch to have real combat via `trauma_score` movement — e.g.
`goblin_camp`) showed `influence` frozen at exactly `0.0` the entire run in all four worlds. The
only nonzero influence anywhere came from two regions with compile-time-authored starting
ownership, and even those never moved past their starting `100.0`.

This is not "the design needs different values" — `FactionInfluenceService.process_influence_shift()`
appears, on a code-level trace, like it should fire (see §2.1's classification trace), but
empirically does not, for a reason not yet found. That is now `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`,
filed separately. **§3.2 (the military-strength driver) is downgraded from "provisional formula" to
"blocked pending that ticket"** — §3.1 (territory/tension) is unaffected, since it derives from
whatever ownership *does* exist (static or dynamic) rather than depending on the dynamic path
specifically.
