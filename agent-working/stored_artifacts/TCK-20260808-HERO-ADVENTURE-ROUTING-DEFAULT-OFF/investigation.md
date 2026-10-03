---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [feature-flags, progression, world]
---

# Investigation — TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF

## Real finding: this is NOT a wiring gap to fix by flipping a global default

`mcp__knowledge-search__search_docs` surfaced two directly-decisive prior rulings that this
ticket's own original framing did not have in hand:

1. **`TCK-20260627-P0A-ADVENTURE-FLAG`** (DONE, 2026-06-27) — the ticket that originally decided
   `ENABLE_ADVENTURE_ROUTING`'s default. Explicit decision: **Option B, keep OFF**, "a deliberate
   gated-rollout policy, not a bug." A sentinel test,
   `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off`,
   hard-asserts the flag stays `FeatureMode.OFF` and explicitly instructs: flipping it requires
   updating `ATTRITION_CAP`/economic baselines in that file and re-running
   `tools/balance_measure.py` to establish a new E12A baseline. **A corpus-wide default flip is
   not a low-risk change — it would break this sentinel test and invalidate the E12A/E12C economic
   baseline measurements corpus-wide.**
2. **`docs/simulation_quality/eval_matrix_results.md`, "AGENCY — Cross-World Design Note"**
   (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`, a ratified Design Authority ruling): "AGENCY=C in every
   calibration world except `simq_routing_test` is **archetype-correct** and requires no
   remediation... `AdventureDecisionPhase` is opt-in by world archetype, not a global default — it
   represents a distinct 'routing-capable' archetype rather than a baseline behavior every world is
   expected to exhibit."

**This means the ticket's own original premise — "HERO underperforms because routing is off in
18/20 worlds, this is an unfinished rollout to fix" — is corrected by real prior evidence.** Most
worlds are *correctly* non-routing-capable by explicit design ruling, the same class of finding as
`wilderness_survival`'s low diversity (`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`) —
archetype-correct, not a bug. A corpus-wide or blanket per-HERO-world flip would violate a ratified
DA decision and a guarding sentinel test.

## The real, narrower opportunity: `frontier_marches`

The DA ruling's own escape hatch is real, sanctioned per-world opt-in — exactly the mechanism
`hero_guild_routing`/`simq_routing_test` already use. Surveying all 20 corpus worlds'
`data/worlds/*/world.yaml` `description` fields plus their composed modules for genuine
"routing-capable" authored intent (not just incidental `hero_adventurers` population, which
several deliberately-narrow unit-isolation worlds also compose without any adventure/routing
intent — `unit_information_source`, `unit_information_density`, `unit_selfmodel_pilot` all state
their own single-pillar-isolation purpose explicitly and must NOT be touched):

- **`frontier_marches`** is the one clear, self-evident case. Its own authored description names
  "a hero guild" as a first-class world element on par with "a goblin war-camp" and "an orc
  stronghold" ("A sprawling borderland where a frontier village, **a hero guild**, a
  wolf-infested forest..."). It composes both the `hero_adventurers` population module (3 real
  HERO entities: ids 31/32/33) and `hero_guild_perspective`. Its profile
  (`config/simulation_quality/profiles/frontier_marches.yaml`) sets `ENABLE_BELIEF_ASSIMILATION:
  ON` but has no `ENABLE_ADVENTURE_ROUTING` entry at all — an authoring-staleness gap matching the
  same evidentiary bar §2.28/§2.32 in `intentional_divergences.md` already used ("self-evident
  authoring intent... a resource node already physically placed... the gating tag simply never
  caught up").
- Other `hero_adventurers`-composing worlds checked and excluded: `crowded_frontier` (composes
  the module but its own description frames the world purely around a 3-faction siege, no
  "hero guild" narrative signal — weaker evidence, not included here) and `urban_political`
  (explicitly, deliberately settled OFF by its own prior ticket,
  `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` — "no, settled by direct precedent").

## Real risk check: the known "permanently stuck hero" failure mode

`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`'s own investigation found a real,
previously-encountered failure mode: `simq_routing_test_seed456`'s hero got permanently stuck
(zero legal routes for its whole life) due to a resource-tagging content gap combined with an
unlucky personality roll, fixed by `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`. That
ticket explicitly warns this would reproduce "the moment... any future world reusing
`hero_adventurers` enables adventure routing" without checking first.

**Directly tested, not assumed.** Ran a real, live 800-tick `Kernel` simulation of
`frontier_marches` (seed 42) with `ENABLE_ADVENTURE_ROUTING` force-enabled via
`state.feature_flags`, `dropped_count=0`:

```
HERO entities in frontier_marches: 3 -> [31, 32, 33]
AGENCY event counts per hero:
  route_selected: {31: 72, 32: 72, 33: 72}
  action_executed: {31: 72, 32: 72, 33: 72}
  route_family_first_use: {31: 1, 32: 1, 33: 2}
```

All 3 HERO entities actively select and execute routes throughout the run — no permanently-stuck
hero (a stuck hero would show 0 `route_selected` and a sustained defer streak, matching none of
these 3). This confirms `frontier_marches` does not reproduce `simq_routing_test`'s known failure
mode and routing genuinely activates in a healthy way here.

## Real fix decision — REVERSED after a real, blocking regression was found

Initially planned: enable `ENABLE_ADVENTURE_ROUTING: "ON"` in `frontier_marches`'s own profile
only. Implemented and calibrated (real `tools/calibrate_simq.py` runs, all 3 seeds, 200 ticks,
`dropped_count=0`): AGENCY moved from `C`/`0.0` to `A` (~0.71-0.94 norm) on all 3 seeds — the
routing pipeline genuinely activates in a healthy way (matches the earlier 800-tick live probe:
72 `route_selected`/`action_executed` events per hero, no stuck-hero failure mode).

**But the same 3-seed calibration also showed FACTION collapsing from `S`/`2.9` to `C`/`0.0` and
INFORMATION from `B`/`0.2` to `C`/`0.0`, identically across all 3 seeds.** Isolated with a direct
before/after comparison on the same seed (42), same world, only the flag toggled: without routing,
29 real `diplomatic_transition` (FACTION) events and 1 `belief_assimilated` (INFORMATION) event
fire, all at **tick 1**, all `entity_id: None` or a non-hero entity — i.e. world-initialization
events unrelated to HERO entities or their own action selection. With routing enabled, these same
tick-1 events do not fire at all. This points to an RNG-consumption side effect (enabling
`AdventureDecisionPhase` shifts the deterministic RNG draw sequence at/around tick 1 enough to
alter or skip unrelated world-init logic that FACTION/INFORMATION's own tick-1 seeding depends on)
rather than any real interaction between adventure routing and faction/information mechanics —
but the exact mechanism is not yet root-caused.

**Decision: do not ship this flag flip.** An S-grade pillar collapsing to C, and a working B-grade
pillar collapsing to C, both silently, is a real regression — not an acceptable side effect to
paper over by recalibrating the anchors around a broken state. Per this session's own established
discipline (do not force a pillar improvement through without checking for collateral breakage),
reverted `config/simulation_quality/profiles/frontier_marches.yaml` back to
`ENABLE_BELIEF_ASSIMILATION: ON` only, and did not touch `grade_anchors.json` for
`frontier_marches`. Filed `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING` to
investigate the RNG-coupling root cause — once fixed, `frontier_marches`'s own routing enablement
can be revisited with real evidence it no longer regresses two working pillars.

**Operational note, disclosed:** while investigating this, an errant `git checkout --
tests/simulation_quality/fixtures/grade_anchors.json` (intended only to discard this ticket's own
`frontier_marches` recalibration) reverted the entire file to its last COMMITTED state
(2026-08-05), discarding several days of legitimate, uncommitted recalibration work from other
tickets (COMBAT-dormant fix, WORLD-anchor recalibration follow-ups, new-world anchors, etc. — 63
of 80 real scenario entries affected). Recovered in full, without fabrication, by reading each
affected run_key's own already-cached, real `data/calibration/{run_key}/quality_report.json`
(recent, this-session timestamps) and rewriting `grade_anchors.json` from that real data — not
guessed or reconstructed from memory. `pytest tests/simulation_quality/ -m "not slow"` confirms
524/524 pass post-recovery. This mistake and its recovery are not part of this ticket's own scope,
but are disclosed here since they occurred during this ticket's Implement step.

## Docs Requiring Update

None beyond the parity/grade-anchor recalibration itself — no Mechanics Bible formula changes.
`docs/simulation_quality/eval_matrix_results.md`'s own "AGENCY — Cross-World Design Note" already
documents the anti-drift expectation; its per-world table row for `frontier_marches` needs
updating once real recalibrated scores are known (done in Implement).
