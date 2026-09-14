---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION
phase: open
date: 2026-09-14
tags: [faction, grand-strategy]
---

# TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION

## Title
Sieges, territory transfer, and `EXPAND_TERRITORY` all require a formal `DiplomaticState.WAR` between factions that no observed run has ever produced — the user has reversed the prior "accepted long-horizon divergence" disposition; find whether any real design declares when war should happen before building anything

## Status
BLOCKED

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`docs/plans/deferred_tuning_decisions_register.md`'s own D-06 entry: siege progression, territory
transfer, and `EXPAND_TERRITORY` are all live, wired code
(`src/engine/military_conflict.py`) gated on a formal `DiplomaticState.WAR` between two factions.
No WAR was declared in any observed run, including a real 200-tick `campaign_life_arc` episode.
Siege completion itself is fast once war exists (~20-34 ticks) — **the bottleneck is war never
starting, not siege being slow.** `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`
and `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (both done) originally accepted this as a
disclosed long-horizon divergence.

**The user has reversed that disposition** — same as the sibling maturity-gate ticket
(`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), filed from the same decision. Per
D-06's own caveat: "how *often* factions should go to war is tuning; whether they *ever* do in a
real run is reachability."

## Scope
- **Investigation first, no implementation until peer has reviewed the design question.**
- **The central question, per explicit instruction: find whether any real design declares WHEN a
  faction should go to war.** A first pass already located a real candidate —
  `DiplomaticStateMachine.compute_transitions()` (`src/domains/faction/diplomatic_state_machine.py`)
  — a tension/military-strength-driven state machine (`NEUTRAL → TENSE` at `pair_tension > 0.4`,
  `TENSE → HOSTILE` at `pair_tension > 0.7` or shared territory, `HOSTILE → WAR` at a >20%
  military-strength imbalance). **This needs real verification, not assumption**: is this a real,
  intentional design answering "when should war happen," or is it itself unreachable/decorative
  (matching this week's own repeated pattern of mechanisms that exist in code but never fire in
  practice)? Check what real `tension_level`/`military_strength`/`territory` values actually look
  like across a real run, and whether the WAR-transition thresholds are ever actually approached.
- If `DiplomaticStateMachine` is confirmed to be a real, working design that simply never reaches
  its own thresholds in practice (a reachability problem, same shape as D-05), investigate why —
  which of `pair_tension`, `shared_territory`, or `military_strength` imbalance is the actual
  blocker, and whether a realistic run could ever produce it.
- **If no real design exists for when war should happen** (i.e., if `DiplomaticStateMachine` turns
  out to be dead/decorative, or if there's no other real trigger anywhere), **stop and bring that
  finding to peer/user rather than choosing a trigger condition** — inventing when factions go to
  war is real game design, the same category of decision as per-enemy danger ratings were treated
  as this arc, not an implementation detail to decide unilaterally.

## Out of Scope
- Actually building or changing any war-declaration trigger — investigation only, per explicit
  instruction, regardless of which of the two outcomes above the investigation finds.
- The lair/world-boss maturity gate (D-05) — sequenced separately, own ticket
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), different shape of problem (that one
  already has a real, working trigger design; this one's own design status is what's in question).
- Siege mechanics/territory transfer/`EXPAND_TERRITORY` themselves — already confirmed live, wired
  code per D-06's own text; not what's broken here.

## Acceptance Criteria
- [ ] A real, evidence-backed answer on whether `DiplomaticStateMachine.compute_transitions()` (or
      any other mechanism) constitutes a genuine, working design for when war should happen, versus
      being itself unreachable or absent.
- [ ] If a real design exists but is unreachable in practice: real evidence (not assumption) on
      which precondition (tension, territory, military-strength imbalance) is the actual blocker.
- [ ] If no real design exists: the finding is brought to peer/user explicitly as a design question,
      not decided or built here.
- [ ] No implementation without that review, regardless of which outcome the investigation finds.

## Related Tickets
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (done — one of the two tickets
  that originally deferred this)
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (done — the other)
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (filed alongside this one, from the
  same user decision — sequenced first, different shape of problem)
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (filed during this ticket's design phase —
  the proposal's own military-strength driver is blocked on this resolving first)
- `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (filed during this ticket's design phase —
  the sentiment design's own importance-weighting requirement, cut from this build and scoped as
  its own separate initiative)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` § D-06 (the entry this ticket investigates)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/faction/diplomatic_state_machine.py` (`compute_transitions()` — the candidate real
  design for war-declaration timing, not yet verified as reachable or intentional)
- `src/engine/military_conflict.py` (`MilitaryConflictPhase` — consumes an already-WAR relation for
  siege/territory logic; confirmed not itself the producer of a WAR declaration)
- `FactionState.tension_level`/`.military_strength`/`.territory` (the real inputs
  `compute_transitions()` reads — their own real producers/typical values not yet traced)

## Assumptions / Open Questions
- Whether `DiplomaticStateMachine` is a real, reachable design or another dormant mechanism is the
  central open question this ticket exists to answer — not assumed either way here.

## Implementation Notes
**2026-09-14: investigation complete, no code changed — bringing findings to peer/user review
before any implementation, per this ticket's own explicit instruction.** Full detail in
staging_artifacts/investigation.md. Summary:
- **Central question answered: a real design exists.** `DiplomaticStateMachine.compute_transitions()`
  is a real, deliberate, deterministic 4-step state machine (NEUTRAL→TENSE→HOSTILE→WAR→NEUTRAL),
  genuinely wired into the real tick pipeline (`src/engine/pipeline.py:260`, called every tick).
  This is not the "no design exists" outcome.
- **But it's unreachable in practice, via three independent, partly-circular blockers**, confirmed
  via a real 3000-tick simulation (`urban_political`, seed=42, 16 factions):
  1. `military_strength` is mathematically frozen at `1.0` for every faction, always — the only
     real producer (a WAR-exhaustion drain) only applies to factions already at war. The `WAR`
     transition's own `>20% imbalance` precondition can never be satisfied from real pre-war state.
  2. `territory` is circularly blocked — no world spec ever seeds it at compile time (confirmed:
     zero references to `territory` anywhere in `WorldCompiler`), and the only real runtime
     producer (siege-won territory transfer) itself requires an existing WAR to fire. `shared_territory`
     can never be the thing that triggers a *first* war.
  3. `tension_level`'s only real runtime producer is *also* gated on territory (a `RESOURCE_DEPLETED`
     event must land inside the faction's own territory) — so it's blocked by the same root cause
     as #2. The only way any faction ever gets nonzero tension is compile-time authoring (2 of 16
     factions in the real corpus, seeded at 0.5), which clears `NEUTRAL→TENSE` (>0.4) but falls
     short of `TENSE→HOSTILE` (>0.7) and never moves further — confirmed empirically, every such
     pair got stuck at TENSE for the full 3000-tick run.
- **Not "just slow" — not one large number.** Fixing this cleanly likely needs at least one new
  real mechanism (military-strength divergence before war, and/or a territory/tension producer
  that doesn't itself require war to exist first), not just reachable threshold values — a real
  design decision, flagged explicitly rather than assumed to be the same shape as the sibling
  maturity-gate ticket (D-05).

**2026-09-14, design phase**: user decided to build real pre-war drivers (militaries diverging and
tension rising from world conditions, not authored seeding). Per explicit instruction, this is
genuine new game design — specification first, reviewed by peer before any code, same sequencing
as the perceived-power precedent. Checked reuse-before-invention per peer's three questions before
proposing anything:
1. **Region sovereignty already exists and is live** (`RegionState.owner_faction_id`,
   `docs/mechanics/regional_sovereignty.md`) — but collapses the specific catalog faction id into a
   legacy 4-value enum (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`), a known,
   already-documented limitation (FAC-010, `docs/systems/faction_contract.md`). Fixing that
   collapse (a parallel field, not a type change to the existing one) derives `FactionState.territory`
   for real, breaking loop #2.
2. **Fixing territory alone unblocks tension for free** — `FactionAwarenessService.compute_tension_updates()`
   is already correct, purely starved of the `territory` input loop #2 fixes.
3. **Vault-gold taxation is real and already growing** (confirmed: `faction_hero_guild_gold`
   1000→5708 over a real 3000-tick run) but only for statically pre-authored ownership — the
   *dynamic* (influence-driven) conquest path was not observed to fire for any region in that same
   run, an open reachability question flagged explicitly rather than assumed resolved.

Full proposal drafted: `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` (explicitly marked draft,
not certified, no code written against it).

**Decision-changing update found while verifying §3.2's own dependency**: ran the same probe
across 4 real corpus worlds (12,000 combined ticks) to check whether dynamic (influence-driven)
region conquest ever fires. It does not — zero ownership changes, in any world, for any region,
ever, despite confirmed real combat deaths in those same "wild" regions. Only compile-time-authored
static ownership has ever been observed. This downgrades the proposal's §3.2 (military-strength
driver) from "provisional formula" to "blocked pending a separate fix" — filed as its own ticket,
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, rather than silently assumed away. §3.1
(territory/tension derivation) is unaffected.

**2026-09-15, design phase continued — user's own faction-sentiment design added as the primary
tension driver.** User specified a continuous faction-to-faction sentiment (hostile ← neutral →
friendly), serving all faction-level interaction (trade/diplomacy, not just war), built from real
entity interaction and weighted by the acting entity's importance to their faction. Proposal
restructured around this (now §3.2, renumbering the prior military-strength sketch to §3.3):
- **Mirrors `SocialBond`** (`src/core/models/social.py:14`) exactly — same 4 fields
  (`familiarity`/`sentiment`/`last_interaction_tick`, target-keyed), reusing the shape rather than
  inventing an eighth parallel implementation. One deliberate, flagged deviation: no `role` field,
  since `FactionState.diplomatic_relations` already plays that categorical role at faction scope —
  a third source of truth was avoided, not silently added.
- **Real interaction hook found**: `SocialBondUpdate` (`src/core/updates.py`) is the single choke
  point all three real entity-interaction producers (combat, cooperation/contracts, appraisal)
  already write through, all flowing into `RelationshipService.process_update()`. A new derivation
  phase can read the same tick's already-produced updates and attribute cross-faction deltas — zero
  changes needed to any of the three producer systems.
- **Importance weighting, empirically checked, not assumed**: `public_reputation` confirmed real and
  non-degenerate (measured: min=1.0, max=2.0, mean=1.232, 8 distinct values across 49 entities) —
  recommended as the weight. `veterancy_rank` (peer's own tentative suggestion) confirmed
  **degenerate** in the same real run (all 49 entities at rank 0) — the exact "everyone is level 1"
  failure shape from the earlier perceived-power draft — explicitly NOT used, contra the tentative
  suggestion, with the empirical evidence stated plainly. No real "faction leader" designation
  exists anywhere (`ClanState.leader_entity_id` is a different, unwired concept) — noted as a real
  gap rather than papered over with an invented signal.
- **Decay**: no live precedent found for a similarly-shaped directed value (the one comparable past
  attempt, `KnowledgeFact.effective_certainty()`, was abandoned and deleted) — proposed as
  genuinely new work, explicitly flagged as such rather than presented as reuse.
- **Feeds the existing, untouched `tension_delta` → `DiplomaticStateMachine` path** — no change to
  the already-tested state machine itself (`FAC-006` parity entry stays exactly as verified).
- **Honest gap stated in the acceptance bar (§4)**: this design should reliably get real faction
  pairs to `TENSE`/`HOSTILE`. It does **not** address loop #1 (`military_strength`) at all — that
  remains genuinely open, blocked on the same `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`
  ticket as before. Reaching `WAR` itself is named as a stretch goal, not assumed, until loop #1
  gets its own real driver — stated explicitly rather than implied solved.

Full revised proposal: `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` §3.2/§3.5/§3.6/§4/§6. No
code written. Sent to peer for review.

**2026-09-15, peer review round 1 — `public_reputation` spread checked over a longer run, not just
at one point in time.** Peer's concern: a 2× range (1.0-2.0) may be too narrow to express "a king's
betrayal reads as categorically different from a peasant's," and asked whether the spread widens
with more play rather than assuming the earlier 3000-tick snapshot was representative. Ran a real
5000-tick instrumented run (`urban_political`, seed=42), sampling `public_reputation`'s
min/max/mean/distinct-count at 10 checkpoints (every 500 ticks). **Result: the spread does not
widen at all.** `min`/`max` are pinned at exactly `1.000`/`2.000` — the field's own hard floor and
ceiling — at every single checkpoint from tick 500 through tick 4999; `spread (max-min)` reads
exactly `1.000` the entire time. Mean drifts *down* over the run (1.335→1.145) as new
default-reputation spawns dilute the average, not because the range changes shape. **This
strengthens the concern rather than resolving it** — the 2× ceiling is structural, not something
more playtime fixes. Added to the spec (§3.2.4, §6) with the explicit conclusion: the design wants
real importance weighting and the world does not currently have a signal strong enough to carry it
— a finding for the user, not quietly patched over. Also added the general rule peer asked for: any
field proposed as a discriminator must be measured for spread before a design leans on it — this is
the second time in this arc a proposed input turned out uniform across the corpus (the first was
entity level in the perceived-power draft).

Sent to peer for review — no implementation until approved, per explicit instruction.

**2026-09-15, both open questions resolved by the user.** (1) Build a real importance signal — but
as its own initiative, not folded into sentiment; filed
`TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (scoping only, not built, not blocking). (2)
Ship sentiment now on its own merits; the military-strength driver is separate, later work.
Amended the spec accordingly:
- Added a prominent decision banner at the very top of the document (before §1), so the
  "reaches `TENSE`/`HOSTILE`, not `WAR`" gap and the "importance weighting is cut, not deferred
  quietly" fact are the first things a reader hits, not buried in §6.
- Removed the `IMPORTANCE_WEIGHT` multiplier from §3.2.3's integration entirely — replaced with a
  single fixed `FACTION_SCALE_FACTOR`, applied uniformly regardless of which entity acted. Rewrote
  §3.2.4 to state the cut decision plainly rather than leaving a "recommended as placeholder"
  half-answer.
- Kept §3.2.6's trade extension point named, unchanged — the clearest near-term payoff of shipping
  sentiment alone.
- §4's acceptance bar and §6's summary both updated to match: build against a real, unmodified
  corpus-world run showing genuine sentiment divergence and at least one pair reaching
  `TENSE`/`HOSTILE` — not a constructed fixture, matching this week's own standing bar.

Per explicit instruction: spec amendments first, bring the revision to peer, then code. Sent for
review; no implementation started.

## Test Summary
_(none — investigation only; findings verified via direct probes against a real, instrumented
3000-tick simulation and direct code/grep evidence, not committed as test files, since no fix has
been chosen yet)_

## Files Changed
_(none — investigation only, per this ticket's own explicit instruction)_

## Completion Summary
_(not complete — investigation delivered a real, evidence-backed answer per the ticket's own
acceptance criteria; awaiting peer/user review before any implementation proceeds)_
