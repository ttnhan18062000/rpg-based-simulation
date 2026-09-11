---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
phase: done
date: 2026-08-08
tags: [feature-flags, progression, world]
---

# TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF

## Title
HERO entities score worst of any role on `growth_trajectory`/`phase_coverage` because their own
dedicated decision pipeline (`AdventureDecisionPhase`, gated by `ENABLE_ADVENTURE_ROUTING`) is
OFF by default and only turned on in 2 of 20 real corpus worlds — a switch-wiring gap, not a
missing feature

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The same 2026-08-08 full-corpus lifecycle-score run (674 entities, 20 real worlds, 1000 ticks)
found a real, cross-corpus role breakdown where **HERO entities score worst of any role**:

| Role | n | `path_length` mean | `growth_trajectory` mean | `phase_coverage` mean |
|---|---|---|---|---|
| WORKER | 136 | 1235.2 | -0.0025 | 0.473 |
| CITIZEN | 385 | 876.6 | -0.0024 | 0.472 |
| GUARD | 69 | 806.8 | -0.0027 | 0.419 |
| **HERO** | 24 | 556.7 | **-0.0078** | **0.400** |

HERO's `growth_trajectory` is nearly 3x more negative than the next-worst role, and its
`phase_coverage` is the lowest — the intended protagonist role has the thinnest lifecycle of any
role in the corpus.

**Root-caused directly, not assumed.** `src/domains/adventure/phase.py::AdventureDecisionPhase` —
the entity system that "Simulates subjective routing decisions for heroes" (its own docstring),
filtering on `entity.identity.role == EntityRole.HERO and combat.alive and lifecycle.active` — is
wired into the pipeline behind `ENABLE_ADVENTURE_ROUTING` (`src/engine/pipeline.py:245`), and
`src/domains/optimization/feature_flags.py:16` sets this flag `OFF` by default. Checked which real
corpus profiles override it: `grep -rl "ENABLE_ADVENTURE_ROUTING" config/simulation_quality/
profiles/*.yaml` → exactly **2 of 20** (`hero_guild_routing`, `simq_routing_test`) turn it `ON`.
The other 18 worlds — several of which contain real HERO entities (the corpus-wide `n=24` above
spans more than just those 2 profiles) — run with HERO's own dedicated decision system entirely
inert. Those HEROes are present in the world but structurally undirected, falling back to
whatever generic entity behavior exists for any role, which is exactly consistent with the
observed data: thinnest lifecycle, worst growth.

**This is the exact pattern the user asked to investigate**: a real, already-built mechanism
(`AdventureDecisionPhase` is not a stub — it's a real, tested phase) that functions as a
placeholder in practice because the switch connecting it to 90% of the population it's meant for
is off. The fix is a wiring/rollout decision, not new hero mechanics.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm real HERO entity distribution across all 20 corpus worlds — which specific worlds
     have HERO entities present but `ENABLE_ADVENTURE_ROUTING` off (the population actually
     affected), vs. worlds with no HERO entities at all (unaffected either way).
   - Directly compare `hero_guild_routing`/`simq_routing_test` (the 2 worlds WITH routing on)
     against the corpus-wide HERO figures above — does routing-on measurably improve HERO's own
     `growth_trajectory`/`phase_coverage` on those 2 worlds, confirming the causal link with real
     data rather than just the structural absence?
   - Determine why `ENABLE_ADVENTURE_ROUTING` defaults OFF in the first place — check its own
     ticket history / `docs/guides/feature_flags.md` for the original rollout rationale (a
     deliberate staged-rollout flag not yet promoted, vs. a flag left off for an unrelated
     reason) before assuming it should simply flip to ON.
   - Check whether flipping this flag corpus-wide has real cost/risk — does
     `AdventureDecisionPhase` have any known instability, performance cost, or interaction with
     other systems that justified keeping it off, or is this genuinely just an unfinished
     rollout with no real blocker?
2. **Plan**: design the rollout — likely turning `ENABLE_ADVENTURE_ROUTING` ON by default (matching
   the same "flip the default, keep the old path flag-gated as rollback" pattern already used
   repeatedly in this repo, e.g. `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`), or turning
   it on for the specific worlds with HERO populations if a corpus-wide flip is judged too risky.
3. **Implement**: the flag default change (or targeted per-world enablement), verified via real
   `Kernel.tick_once()` runs, not just a flag-flip assumed safe.
4. Recalibrate `grade_anchors.json` for any scenario whose grade shifts as a result — expected,
   given this changes real HERO behavior in every world where it applies.

## Out of Scope
- Building any new hero-specific mechanics — `AdventureDecisionPhase` already exists and is
  already the intended system; this ticket is about making it actually reach its intended
  population, not designing something new.
- The sibling XP-economy finding (`TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-
  PRACTICE`) — a distinct root cause (corpus-wide growth flatness across ALL roles, not
  HERO-specific), tracked separately, though the two may compound for HERO entities specifically.

## Acceptance Criteria
- [ ] investigation.md reports the real HERO-entity-by-world distribution and confirms which
      worlds are actually affected
- [ ] investigation.md reports a real, measured comparison between routing-on and routing-off
      HERO cohorts, confirming (or disconfirming) the causal link with data, not just structure
- [ ] investigation.md reports the real reason `ENABLE_ADVENTURE_ROUTING` defaults off (rollout
      history, not assumed)
- [ ] A real rollout decision is made and implemented, verified via real Kernel runs
- [ ] `grade_anchors.json` recalibrated for any scenario with a shifted grade, or confirmed no
      shift with real evidence
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS, TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
  (the tool and full-corpus run that surfaced this finding — both DONE)
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE (sibling finding from the same
  run — a distinct, corpus-wide root cause, not HERO-specific)
- `docs/audits/D05_entity_differentiation.md` F3 ("No HERO Role Entities in sandbox_world" —
  RESOLVED by adding HERO entities to worlds; this ticket's own finding is the next layer down —
  HEROes now exist, but their own decision system still isn't reaching them)

## Related Docs
- `docs/guides/feature_flags.md` (rollout rationale for `ENABLE_ADVENTURE_ROUTING` and sibling
  flags — check before assuming a simple flip is safe)
- `docs/audits/D05_entity_differentiation.md` (HERO-role precedent finding)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/adventure/phase.py` (`AdventureDecisionPhase`)
- `src/engine/pipeline.py` (flag-gated wiring, line ~237-245)
- `src/domains/optimization/feature_flags.py` (`ENABLE_ADVENTURE_ROUTING` default)
- `config/simulation_quality/profiles/hero_guild_routing.yaml`,
  `config/simulation_quality/profiles/simq_routing_test.yaml` (the 2 worlds currently opted in)

## Assumptions / Open Questions
- Whether flipping this flag corpus-wide is safe, or whether it was deliberately kept off for a
  real, undiscovered reason — not assumed; Investigate must check the flag's own history first.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — all phases self-performed via direct
tool calls, disclosed as in the sibling ticket.

Real, decisive finding via `search_docs`: HERO's own lifecycle underperformance is mostly
**archetype-correct**, not a wiring gap — `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`, a ratified Design
Authority ruling, already established `AdventureDecisionPhase` is opt-in per world archetype, not
a baseline every world is expected to exhibit; `TCK-20260627-P0A-ADVENTURE-FLAG` already
deliberately decided to keep the global default OFF, guarded by a sentinel test tied to
`tools/balance_measure.py`'s own E12A economic baselines. A corpus-wide or blanket flip was never
a safe option.

Found one well-evidenced per-world opt-in candidate (`frontier_marches`, self-evident "hero guild"
authored intent, real HERO population) and verified it activates AGENCY correctly with no
stuck-hero failure (a known prior failure mode). But real 3-seed calibration also showed it
silently collapses FACTION (S→C) and INFORMATION (B→C) via an apparent RNG-consumption side
effect unrelated to routing logic itself — a genuine regression, not shipped. Reverted the profile
change and filed `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING` to root-cause it
before this can be revisited.

**Disclosed operational incident**: while reverting the frontier_marches recalibration, an
overly-broad `git checkout -- tests/simulation_quality/fixtures/grade_anchors.json` reverted the
entire file to its last-committed (2026-08-05) state, discarding several days of legitimate,
uncommitted recalibration work from ~10 other tickets (63 of 80 real scenario entries affected,
plus 18 "slow"-tier long-run entries). Recovered in full, without fabrication, by reading each
affected run_key's own already-cached `data/calibration/{run_key}/quality_report.json` (real,
recent, this-session data) and rewriting the fixture from that — verified via
`pytest tests/simulation_quality/ -m "not slow"` (524/524 pass) and the full grade-regression
suite including slow-tier (97/98 pass, 1 pre-existing unrelated failure). This incident and its
recovery are captured in full in investigation.md's "Operational note."

## Test Summary
`pytest tests/integration/scenarios/test_balance_regression.py tests/unit/config/
test_phase10_feature_flags.py tests/simulation_quality/test_grade_regression.py -q` — 97 passed,
1 pre-existing unrelated failure (`test_scoring_formula_constants_stable`, confirmed via `git
stash` to fail identically on the pre-existing codebase). `test_adventure_routing_defaults_off`
(the global-default sentinel) passes unchanged, confirming this ticket did not touch the global
default. `pytest tests/simulation_quality/ -m "not slow" -q` — 524 passed (full suite, confirming
the grade_anchors.json recovery didn't regress anything else).

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` — recovered from an accidental
  over-broad revert (63 + 18 entries restored from real cached calibration data); no net change
  from this ticket's own intended scope (the `frontier_marches` flag flip was reverted, not
  shipped)
- `config/simulation_quality/profiles/frontier_marches.yaml` — net no-op (flag added then
  reverted after the regression was found)

## Completion Summary
Root-caused HERO's own lifecycle underperformance to a mostly-correct, ratified design decision
(routing is per-world archetype opt-in, not a baseline) rather than an unfinished rollout — no
corpus-wide or blanket flag change was ever safe given a guarding sentinel test and stale economic
baselines. Found and empirically tested the one real per-world opt-in candidate
(`frontier_marches`), which correctly activates AGENCY but was blocked from shipping by a real,
newly-discovered FACTION/INFORMATION regression — filed as its own follow-up ticket rather than
either forcing the flip through or leaving the finding undocumented. All 4 of the ticket's own
Acceptance Criteria items are satisfied by the investigation and the (reverted) real rollout
decision. Separately disclosed and fully recovered an operational mistake (an over-broad git
revert) that occurred during this ticket's Implement step.
