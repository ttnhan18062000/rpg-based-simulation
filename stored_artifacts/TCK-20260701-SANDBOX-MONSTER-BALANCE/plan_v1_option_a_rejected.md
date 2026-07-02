---
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: plan
date: 2026-07-01
---

# Plan: sandbox_world monster stat differentiation

## Approach

Content-only fix, one file's core change (`data/worlds/sandbox_world/world.yaml`), plus a
regression test, plus regenerated compile/calibration artifacts. No `src/` logic is touched —
confirmed in investigation.md that the resolver chain (`_resolve_entity_stats`,
`RoleSemanticsService`, `EntityArchetypeResolver`) is correct; the bug is that
`role: monster` in sandbox_world's population entry is not a catalog-registered role ID and
silently falls to global defaults.

**Reuse decision**: `data/content/social/roles.yaml` already registers monster-family roles
with `legacy_engine_role: MONSTER` (`predator_hunter`, `alpha`, `raider`, `leader`, `sentinel`,
`brute`, `dragon_champion`), each pointing at an existing `stat_profiles.yaml` entry, and each
already consumed elsewhere in the catalog via `entity_archetypes.yaml` (e.g. `hungry_wolf` uses
`role: predator_hunter` / `stat_profile: wolf_predator_base`, used in the `wolf_pack_small`
population recipe). Fix: point sandbox_world's monster population at one of these **existing**
registered roles instead of inventing anything new. No new catalog content is required.

Initial pick: **`predator_hunter`** (→ `wolf_predator_base`: hp=45, atk=12, def=3) — the
catalog's baseline "generic wilderness monster" role (same role the `hungry_wolf` archetype
uses). This is a reuse of the closest semantic match to an undifferentiated "monster"
population, not a new invention. Because sandbox_world's `worldtemplate.v1` schema only
propagates the `role` field through to stat resolution (see investigation.md, Current Behavior
step 2 — `stats_profile` on the population recipe is dropped by `WorldTemplateExpander` and
never reaches `PopulationSpec`), `role:` is the only lever available without touching engine
code, and is sufficient on its own.

## Ordered Steps

**Step 1 — Change the monster population's role in sandbox_world.**
- File: `data/worlds/sandbox_world/world.yaml`
- Change L39: `role: monster` → `role: predator_hunter`
- Independently verifiable: `python3 -c "from src.worldbuilding.recipe import ...; ..."` or
  `make world-validate WORLD=sandbox_world` succeeds; `role_semantics.get_default_stats_profile
  ("predator_hunter")` returns `"wolf_predator_base"` (can be checked directly against
  `data/content/social/roles.yaml`).

**Step 2 — Add a regression test guarding the stat-differentiation property.**
- File: `tests/unit/worldbuilding/test_sandbox_world_monster_stats.py` (new)
- Compile `data/worlds/sandbox_world/world.yaml` via `WorldCompiler.compile()`; assert every
  monster-faction entity's resolved `(hp, atk, def)` differs from the flat default
  `(100, 10, 0)` (do not pin to `wolf_predator_base`'s exact numbers — see test_plan.md
  Anti-Drift Test Guards, this must survive later stat-profile retuning in Step 5).
- Depends on: Step 1 (test would fail against the old `role: monster` value — this is
  intentional; run it once before Step 1 to confirm it currently fails, proving it exercises
  the bug).

**Step 3 — Recompile sandbox_world and regenerate the committed compile report.**
- File: `data/worlds/sandbox_world/world_compile_report.json` (regenerated, not hand-edited)
- Command: `make world-compile WORLD=sandbox_world`
- Confirms `entity_count` unchanged (23), `state_hash` changed (expected per ticket AC),
  `warnings` empty.
- Depends on: Step 1.

**Step 4 — Run the scoped regression suite (fast tests).**
- Commands: see test_plan.md "Scoped Pytest Commands" (unit/content_semantics,
  unit/worldbuilding, cli/test_world_cli.py, integration/scenarios/test_entity_differentiation.py)
- Confirms no other world/test was accidentally affected (isolation check).
- Depends on: Steps 1-3.

**Step 5 — Empirically verify the tick-8 wipe no longer occurs (seed 42 + seed 137, 200 ticks).**
- Re-run the exact D20 audit scenario: `tools/calibrate_simq.py` (or the underlying run harness
  it wraps) against `sandbox_world`, seed 42 and seed 137, 200 ticks.
- Inspect emitted `entity_killed` events for ticks 0-8. Acceptance: NOT all 5 monster entities
  die within tick 8 (per ticket AC — "some attrition is acceptable; total wipe is not").
- **Iteration loop (not a new unresolved question — a normal verify-then-adjust step):** if the
  `predator_hunter` pick (Step 1) still produces a full 5-entity wipe by tick 8, escalate to a
  tougher already-registered monster role in this order and repeat Steps 1, 3, 5:
  `alpha` (alpha_predator_base: hp=75/atk=16/def=4) → `leader` (warlord_base:
  hp=120/atk=24/def=8) → `brute` (troll_brute_base: hp=260/atk=28/def=8). Do not invent a new
  stat profile at any point in this loop — all four candidates are pre-existing catalog roles.
- Depends on: Steps 1, 3 (needs a compiled world to run); may loop back to Step 1.

**Step 6 — Regenerate simulation-quality calibration data and update grade anchors.**
- Files: `data/calibration/sandbox_world_seed42_200t/`, `sandbox_world_seed137_200t/`,
  `sandbox_world_seed999_200t/`, `sandbox_world_seed42_1000t/` (regenerated calibration
  reports/jsonl), `tests/simulation_quality/fixtures/grade_anchors.json` (updated grades for
  the four `sandbox_world_*` keys if any pillar shifted beyond current anchor, per
  `test_grade_regression.py`'s own docstring procedure).
- Command: `make calibrate` (or the sandbox_world-scoped equivalent) then
  `pytest tests/simulation_quality/test_grade_regression.py -v -k "not slow"` (+ `-m slow` for
  the 1000t anchor once, per test_plan.md).
- Depends on: Step 5 (need the final chosen role/profile settled first — recalibrating against
  an interim choice that gets escalated in Step 5's loop would be wasted work).

**Step 7 — Update `docs/audits/D20_simq_integration.md` P2 row to resolved.**
- File: `docs/audits/D20_simq_integration.md` (Actionable Next Steps table, current P2 row:
  "Investigate `early_extinction` penalty at tick 8 — sandbox_world entities 16–20 are weak").
  Update rationale/status column to reference this ticket ID and the resolution (role changed
  from unregistered `monster` string to registered `predator_hunter`/escalated role; verified
  via Step 5).
- Depends on: Step 5 (need the final verified outcome to describe accurately).

**Step 8 — Divergence-doc decision (resolved now, no entry needed).**
- Ticket AC references `docs/guidelines/v2_intentional_divergences.md`; the actual file is
  `docs/guidelines/intentional_divergences.md` (confirmed in investigation.md). That doc's
  scope is explicitly "intentional behavior shifts in `src` compared to original `src`" — this
  fix touches zero `src/` code, only `data/worlds/sandbox_world/world.yaml` content, and
  corrects an authoring bug rather than diverging from any documented legacy engine behavior.
  **Decision: no new entry required.** Note this determination explicitly in the ticket's
  Implementation Notes so the AC is demonstrably addressed ("considered, not applicable")
  rather than silently skipped.
- Depends on: none (can be done any time; listed last for narrative completeness alongside
  Step 7's doc update).

## Files to Change (summary)

| File | Change type | Step |
|---|---|---|
| `data/worlds/sandbox_world/world.yaml` | Edit — 1 field (`role: monster` → registered role) | 1 |
| `tests/unit/worldbuilding/test_sandbox_world_monster_stats.py` | New — regression test | 2 |
| `data/worlds/sandbox_world/world_compile_report.json` | Regenerated (new `state_hash`) | 3 |
| `data/calibration/sandbox_world_seed42_200t/*`, `sandbox_world_seed137_200t/*`, `sandbox_world_seed999_200t/*`, `sandbox_world_seed42_1000t/*` | Regenerated calibration reports | 6 |
| `tests/simulation_quality/fixtures/grade_anchors.json` | Edit — updated grades for `sandbox_world_*` keys, if any pillar moved beyond current anchor | 6 |
| `docs/audits/D20_simq_integration.md` | Edit — P2 row → resolved | 7 |
| `tickets/inprogress/TCK-20260701-SANDBOX-MONSTER-BALANCE.md` | Edit — Implementation Notes documenting the divergence-doc "no entry needed" decision | 8 |

## Scope Guards (what NOT to touch)

- Do NOT modify `src/simulation_quality/scorers/combat.py` or
  `config/simulation_quality/detection_params.yaml` (`early_extinction` logic/threshold —
  confirmed correct, explicitly out of scope).
- Do NOT modify `src/worldassembly/resolver.py` (`CompileProfileResolver`,
  `_resolve_entity_stats`) or `src/content/resolver.py` (`EntityArchetypeResolver`,
  `RoleSemanticsService`) — resolution logic is correct; only sandbox_world's content was wrong.
- Do NOT modify `src/worldbuilding/recipe.py` (`WorldTemplateExpander`) to propagate
  `stats_profile`/`inventory_profile`/`cognition_profile` — real gap, but an engine/schema
  change affecting every `worldtemplate.v1` world; out of this ticket's content-layer scope.
- Do NOT modify any world other than `sandbox_world` (`dungeon_crawl`, `wilderness_survival`,
  `urban_political`, etc. are reference-only) — explicit ticket Out of Scope.
- Do NOT add a new role or stat profile to `data/content/social/roles.yaml` /
  `data/content/entities/stat_profiles.yaml` — an adequate registered monster role already
  exists; adding a new one would be the "invent a new archetype system" the ticket warns
  against.
- Do NOT change combat formulas in `docs/mechanics/02_combat_laws.md` or any engine damage/
  defense calculation — explicit ticket Out of Scope.
- Do NOT weaken `test_grade_regression.py`'s ±1 band tolerance to force a pass instead of
  properly regenerating calibration data (see test_plan.md Anti-Drift Test Guards).
- Do NOT hand-edit `data/worlds/sandbox_world/world_compile_report.json` or any
  `data/calibration/*/quality_report.json` — always regenerate via the compile/calibrate
  commands so `state_hash` and derived metrics stay internally consistent.

## Dependency Map

```
Step 1 (edit role) ──┬──> Step 2 (new test) ──> Step 4 (regression suite)
                      ├──> Step 3 (recompile) ──> Step 4
                      └──> Step 5 (empirical 200t verify) ──(loop back to Step 1 if wipe persists)
                                     │
                                     v
                           Step 6 (recalibrate + anchors)
                                     │
                                     v
                           Step 7 (D20 audit doc update)

Step 8 (divergence-doc decision) — independent, no upstream dependency
```

## Acceptance Criteria → Steps

| Ticket AC | Satisfied by |
|---|---|
| Root cause confirmed: which resolver/catalog path assigns sandbox_world monster stats | investigation.md (Current Behavior) — pre-implementation, no code step needed |
| Monsters no longer die as an entire cohort within the first 10 ticks (some attrition OK) | Steps 1, 5 (with escalation loop) |
| Final state hash changes are expected and documented | Step 3 (regeneration) + Implementation Notes / Completion Summary at finalize |
| `docs/guidelines/intentional_divergences.md` updated if this counts as a divergence | Step 8 (decision: not applicable, documented) |
| D20 audit P2 row updated to resolved | Step 7 |
| No regression in existing sandbox_world / world-compile tests | Step 4 (+ Step 6 for calibration-anchor tests specifically) |

## Unresolved Questions

**None.** Both candidate ambiguities were resolved during investigation, not left open:
- *Which catalog pattern to reuse* — resolved: registered monster-family roles in
  `roles.yaml` (`predator_hunter` et al.) already exist and are used elsewhere
  (`entity_archetypes.yaml` → `populations.yaml` → module worlds like `dungeon_crawl`). This
  is a straightforward "reuse existing role X" decision, not a real open question.
- *Whether to add a full kernel-tick integration test (10-tick survival assertion) as a
  stronger permanent CI guard* — decided against: the stat-differentiation unit test (Step 2)
  guards the direct cause, and the calibration-anchor tests (Step 6) already provide
  200-tick behavioral regression coverage across the exact 0-10 tick window via the COMBAT
  pillar's `early_extinction`/`attrition` scoring. Adding a redundant slow kernel-loop test
  would violate the project testing rule against superficial/duplicate coverage.

The only genuinely empirical unknown — *which specific registered role's stat profile actually
prevents the tick-8 wipe* — is not a "human decision" question; it is resolved by Step 5's
verify-and-iterate loop during implementation, using only pre-existing catalog roles.

## Deviations (recorded during implementation, 2026-07-01)

**Plan invalidated at Step 1 verification. Implementation stopped; no code/content changes
were kept. Status: DOD_BLOCKED.**

Investigation.md's root-cause trace (Current Behavior steps 2-4) followed
`CompileProfileResolver._resolve_entity_stats()` / `RoleSemanticsService.get_default_stats_profile()`
in `src/worldassembly/resolver.py`, assuming this is the code path that resolves
sandbox_world's entity combat stats. **This is factually wrong for `sandbox_world`'s actual
schema.** `sandbox_world/world.yaml` is `schema_version: worldtemplate.v1`. The CLI compile
entrypoint (`src/worldbuilding/cli.py`, `cmd_compile`, the `"worldtemplate" in schema_version`
branch) sets `context = None` unconditionally for this schema type before calling
`WorldCompiler.compile(spec, seed=seed, output_report_path=report_path, context=context)`.

`CompileProfileResolver` (and therefore `RoleSemanticsService.get_default_stats_profile`,
and therefore `data/content/social/roles.yaml`'s `default_stats_profile` field) is **only**
invoked by `WorldAssemblyResolver.resolve()` (`src/worldassembly/resolver.py:728`) — used for
`worldcomposition.v1` module-based worlds (e.g. `dungeon_crawl`) and the procedural generator
(`src/worldgeneration/generator.py:315`) — never for `worldtemplate.v1` template worlds like
`sandbox_world`.

Inside `WorldCompiler.compile()` itself (`src/worldbuilding/compiler.py:264-283`), combat
stats (`hp=100, max_hp=100, atk=10, def_stat=0, attack_range=1, readiness=100.0`) are
hardcoded local variables, only overridden by `context.entities[pop_key]` — and `context` is
always `None` for template worlds. **The `role:` field has no code path to combat stats for
`sandbox_world` at all**, regardless of which string it holds.

Empirically verified (scripted against `WorldTemplateExpander.expand()` +
`WorldCompiler.compile()`, the exact calls the CLI makes) across all four plan-specified
fallback roles — `predator_hunter`, `alpha`, `leader`, `brute` — every one resolved to the
identical flat default `(hp=100, atk=10, def=0)`. The role-escalation loop in Step 5 cannot
succeed at any point in the sequence; this is a structural fact of the compile path, not
per-role noise.

**Worse, the change is regressive, independent of the stats question.** `get_role_enum()`
(`src/worldbuilding/compiler.py:29-51`), called with `catalog_repo=None` on this path, buckets
`EntityRole` via a crude uppercase-substring heuristic (`"MONSTER" in role_str.upper()` →
`EntityRole.MONSTER`, else falls through to `EntityRole.CITIZEN`). The literal string
`"monster"` matches; none of `predator_hunter` / `alpha` / `leader` / `brute` (nor any other
registered catalog role ID) contain the substring `"MONSTER"`. Verified empirically: all four
candidates resolved `identity.role` to `EntityRole.CITIZEN` instead of `EntityRole.MONSTER`.
`EntityRole.MONSTER` is load-bearing elsewhere: `src/engine/legality.py:497` (combat legality
base score), `src/engine/combat_rewards.py:36-42` (XP reward classification),
`src/engine/occupancy_snapshot.py:35`, `src/world/camp.py:48`, `src/world/spawn.py:55`. Making
this change would have silently reclassified sandbox_world's monsters as citizens across all
of these systems, for zero stat benefit.

**Resolution:** Step 1's edit was applied, tested, and reverted (`git checkout --
data/worlds/sandbox_world/world.yaml data/worlds/sandbox_world/world_compile_report.json`).
Steps 2-8 were not performed — Step 2's regression test was written, used to prove the
negative result, then deleted (it would have asserted a property the fix cannot deliver).
No `src/` files were modified at any point (scope guard against touching `WorldCompiler`,
`CompileProfileResolver`, or `WorldTemplateExpander` was respected throughout — the finding
is that respecting those guards makes option (a), as specified, structurally impossible for
`worldtemplate.v1` worlds, not that any guard needed to be broken).

Ticket's own Scope section names an untried alternative — option (b), "adjust spawn
placement/distance so monsters aren't immediately adjacent to 18 hostile entities at tick
0-8" — which remains content-only and in-scope, but requires fresh investigation (engagement
radius, movement speed, region distance dynamics) not covered by this plan or its
investigation.md. That investigation was not started; re-scoping to option (b) is a decision
for the next planning pass, not a silent pivot taken here.
