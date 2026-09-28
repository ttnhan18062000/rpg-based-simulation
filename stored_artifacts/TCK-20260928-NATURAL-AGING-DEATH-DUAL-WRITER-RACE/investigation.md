---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE
artifact_type: investigation
tags: [bug, lifecycle, engine, determinism]
---

# Investigation — TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE

## Current Behavior

### The two writers (both re-verified directly against current `origin/main` source, 2026-09-28)

**Writer 1 — `ApplyPath._compute_entity_changes`** (`src/engine/apply.py:94-110`, inside the
`is_life_due` block):
```python
new_age = life.age_ticks + 1
...
changes["lifecycle"] = replace(life,
    age_ticks=new_age,
    active=(new_hp > 0 and new_age < life.max_age_ticks)
)
```
Runs unconditionally for every `active` (or `is_life_due`-cadence-gated) entity, every tick that
`is_life_due` fires, as part of the passive/biological decay branch — no `EntityUpdate` involved,
this write lands directly in the `changes` dict that becomes the next `AuthoritativeState`
generation (`src/engine/apply_plan.py:325`, the sole call site of `_compute_entity_changes`, no
worker-parallel duplicate).

**Writer 2 — `LifecycleSystem.resolve_lifecycle`** (`src/systems/lifecycle_systems/lifecycle.py:
146-218`): loop guard `if not entity.lifecycle.active: continue` (`:147-148`) skips already-inactive
entities entirely; OLD_AGE check `entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks`
(`:193-195`) against `state` — the frozen pre-tick snapshot passed into `resolve_lifecycle`, i.e.
age **before** this tick's increment. On death it writes `active=False` via `EntityUpdate.active`
(`:211-212`), which — confirmed by tracing `src/engine/patches.py:69-73` (`LifecyclePatch.apply`,
reads `changes.get("lifecycle", entity.lifecycle)` then overwrites `.active`) and
`src/engine/patches.py:762-763` (`extract_patches`, `update.lifecycle is not None or update.active
is not None`) — commits into the **same** `entity.lifecycle.active` field Writer 1 writes. Both
writers target one field, not two related-but-distinct ones.

### Why the race is deterministic, not probabilistic (confirmed via kernel phase order)

`Kernel._tick_once_inner` (`src/engine/kernel.py:387-454`) runs, in order:
`_phase_scheduling` → `_phase_collection` → **`_phase_resolution`** (`:424`, which calls
`AuthoritativeApplyPipeline.refine()`, whose `"lifecycle"` phase at `src/engine/pipeline.py:414`
invokes `LifecycleSystem.resolve_lifecycle(state, u)` against the **pre-tick** `state`) →
`_phase_cleanup` → **`_phase_advancement`** (`:434`, which calls `ApplyPath.apply_generation()` →
`ApplyPlanBuilder.build_plan()` → `_compute_entity_changes`, `src/engine/kernel.py:824-843`,
committing the passive age increment).

So on the tick where `age_ticks` first reaches `max_age_ticks`:
1. Resolution phase runs first, reads the *not-yet-incremented* age (still one below max) →
   `resolve_lifecycle`'s OLD_AGE check is False → no `EntityUpdate.active`/`death_reason` produced
   for this entity this tick.
2. Advancement phase then commits Writer 1's write: `age_ticks` becomes `max_age_ticks`,
   `active=(new_hp>0 and new_age<max_age_ticks)` evaluates False → entity is now
   `active=False, death_reason=None, is_permadeath=False`.
3. Next tick, `resolve_lifecycle`'s own loop guard (`:147-148`) sees `active=False` and `continue`s
   — this entity can never reach the OLD_AGE branch again. Terminal silent state, exactly as the
   ticket describes.

### Empirical reproduction (this investigation, not inspection-only)

Ran a fresh natural-aging scenario through real `Kernel.tick_once()` (not staged past max) against
current `origin/main`-equivalent code in this worktree:
- `age_ticks=0, max_age_ticks=3`: subject dies silently — `active=False, death_reason=None` from
  tick 3 onward, never recovers, heir never receives inventory.
- Also ran the unreviewed WIP branch's own regression file
  (`git show 30c9fa9e8:tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py`) unmodified
  against this tree: **3/3 fail**, confirming the ticket's own "failed 3/3 against current code"
  claim independently (not merely trusted from the ticket text).
- Starvation/sleep-debt path (AC7), separate probe: entity built with `hunger=95.0, sleep_debt=98.0,
  hp=1, max_age_ticks=100000` (age nowhere near max). One `tick_once()` call:
  `hp=0, alive=False, active=False, death_reason=None, death_tick=None`. **Confirmed empirically
  affected — same silent signature.** Root cause is distinct from the age race, though: it is not a
  race at all. `LifecycleSystem.resolve_lifecycle` has **no branch that ever checks combat HP/alive
  state from passive decay** — its only two death triggers are `age_ticks >= max_age_ticks`
  (`:193-195`, "OLD_AGE") and `ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH")` (`:202-204`,
  "COMBAT"), confirmed by a repo-wide grep of `death_reason =` assignments (only these two string
  literals exist anywhere in `src/`). A passive starvation/exhaustion death writes
  `combat.hp=0, combat.alive=False, lifecycle.active=False` directly inside
  `_compute_entity_changes` (`apply.py:104-110`) with **no corresponding `EntityUpdate`** for
  `resolve_lifecycle` to ever see — there is no `"STARVATION"`/`"EXHAUSTION"` death_reason anywhere
  in the codebase. This is a missing detection branch, not a timing race; fixing Writer 1/Writer 2
  precedence for age alone will not fix this on its own — `resolve_lifecycle` needs a new
  HP/alive-based detection branch (or an equivalent), which is a real additional scope item AC7
  implies but the ticket's Scope section does not explicitly call out as a code change (only as
  "determine empirically... if it is silent, fix it here or split it out with a written reason").

### `initial_active=False` spawns (Q3) — confirmed dormant, not currently exercised in production

`ArchetypeEntityFactory.build_entity` (`src/entities/archetype_factory.py:129-131`) sets
`entity.lifecycle.active=False` at construction when `spawn.initial_active` is False. Under
**current** (buggy) code, such an entity can still be flipped to `active=True` later purely as a
side effect of Writer 1's own formula (`active=(new_hp > 0 and new_age < life.max_age_ticks)` — this
has no dependency on the entity's own prior `active` value, so a surviving, non-aged-out inactive
spawn gets activated the next time `is_life_due` fires for it). This is almost certainly an
accidental side effect, not a designed "spawn dormant, wake up later" mechanism — no doc anywhere
describes it, and `is_life_due` is a **global** cadence gate (`should_run(tick, None,
cadence.lifecycle)`), not an entity-specific wake condition.

Grepped all of `src/` and `tests/` for callers: **`initial_active=False` currently has exactly one
caller anywhere in the repository** — `tests/unit/entities/test_archetype_entity_factory.py:165`,
a construction-only unit test that never runs a tick. **No production spawn path passes
`initial_active=False` today** (`src/worldassembly/entity_spawner.py:71` hardcodes
`initial_active=True`). This lowers the ticket's own-stated risk (Q3 cannot break anything live
today, by direct code search, not inference), but the field remains part of `EntitySpawnContext`'s
public contract, so the theoretical hazard is real for any future caller.

The unreviewed WIP branch's candidate fix for Q1 (`active=(new_hp > 0 and life.active)`, see below)
would **remove** the only mechanism — accidental or not — that could ever flip such a spawn back to
active, since the expression now ANDs against the entity's own already-`False` `active` value
instead of computing a fresh value from age/hp. The WIP branch's own commit message discloses this
exact gap ("side effect on spawns with initial_active=False not yet evaluated") and its regression
test file does not cover it. **Q3 is not answered by adopting the WIP branch as-is** — per the
ticket's own Assumptions, this decision should not be defaulted here; it is a real design choice
(does an `initial_active=False` spawn require an explicit, intentional activation path, and if so
where does it live?) that should return to the systemic-world roadmap unless the implementer can
show a production caller exists that requires an answer now.

### WIP branch (`natural-aging-old-age-dispatch-fix-unreviewed` @ `30c9fa9e8`) evaluated as a Q1 candidate

`src/engine/apply.py` diff: changes Writer 1's `active=` expression from
`(new_hp > 0 and new_age < life.max_age_ticks)` to `(new_hp > 0 and life.active)`. This makes Writer
1 **never independently deactivate an entity for age** — once `life.active` is `False` (only ever
set by Writer 2, or by construction-time `initial_active=False`), it stays `False`; while `True`, it
stays `True` unless `new_hp <= 0` (still, correctly, an immediate deactivation on passive HP-loss —
this is the same `new_hp > 0` gate that also produces the starvation silent-death signature above,
untouched by this candidate fix). Its own bundled regression scenario
(`tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py`, inspected via `git show`, not
merged) exercises exactly the ordinary-per-tick-progression path AC6 requires and fails 3/3 against
current code (independently re-confirmed above) — useful as a starting shape for the real fix's own
regression test, not as an approved implementation. It does not touch `resolve_lifecycle` at all,
so it relies entirely on Writer 2 remaining the sole place `age_ticks >= max_age_ticks` is
evaluated — which, since resolution runs a tick before advancement, means the death is recorded on
the tick **after** `age_ticks` reaches `max_age_ticks` (the WIP test's own
`test_old_age_death_happens_on_the_first_tick_age_reaches_max_age` encodes and pins exactly this:
the subject is still `active=True` at `age_ticks==MAX_AGE`, and death fires the following tick).
This is the AC2/AC4 "does the correction shift the recorded death tick" answer for this specific
candidate: **yes, by exactly one tick relative to the current (broken) tick the passive branch
writes `active=False` on** — consistent with the ticket's own "Likely yes, by one" note. This
finding is offered as evidence for the plan phase, not as the decision itself; Q1 is explicitly not
pre-decided by this investigation.

### `initial_active`/spawn-activation aside: no other runtime writer of `lifecycle.active` exists

Grepped `src/` for every `active=True`/`active_set=True`/`.active = True` touching
`lifecycle`/`life`/`LifecycleComponent` — only construction-time builder calls
(`src/worldbuilding/compiler.py:665`, `src/perf/scenarios.py` ×6) and the `V2EntityBuilder`
default (`True`). No system reactivates an entity at runtime. This confirms the dual-writer
diagnosis is complete: exactly two runtime writers of `entity.lifecycle.active`, Writer 1 and
Writer 2, nothing else.

## Mechanics / Engine Constraints

- **`docs/engine/authoritative_mutation_pipeline_contract.md`** §1 ("Proposal → Refine → Apply"):
  states Refine "consolidates deltas and tie-breaks conflicts" and Apply "commits the consolidated
  delta." As currently implemented, Writer 1 (inside Apply, via the passive branch) makes an
  independent authoritative decision about `lifecycle.active` that Refine (Writer 2) never gets a
  chance to tie-break, because Writer 1's decision is made **after** Refine has already run for
  that tick, against a snapshot Refine did evaluate correctly. The two-writer race is a direct
  instance of the pipeline law's own "tie-break conflicts" responsibility not being honored for
  this specific field.
- **`docs/core/state.md`** "Frozen Lifecycle Law": `AuthoritativeState.apply(update)` is meant to
  be the single transition point per tick; this holds at the state-container level (one new
  generation is produced) but not at the field level for `lifecycle.active`, since two independent
  code paths compute it without either reading the other's output.
- **`docs/simulation/lifecycle_systems_contract.md`** (P1, authoritative source for lifecycle death
  triggers) currently documents `resolve_lifecycle()`'s two death triggers as the entirety of how an
  entity can die (its own death-trigger table, "Old age" / "Combat death"), and separately documents
  the passive branch's HP-loss-from-starvation/exhaustion condition — but never connects the two:
  it does not disclose that the passive branch's HP-loss can itself deactivate an entity (for either
  age or starvation) without ever passing through the death-trigger table. This doc is currently
  incomplete about real runtime behavior, independent of which fix direction is chosen.
- **`docs/world_rules/life-body/lifecycle.md`** LIFE-01's own "Repository evidence" paragraph
  asserts "`combat.alive` is set `False` at `new_hp <= 0` uniformly... `is_permadeath_set`... The
  two fields are never conflated in the same write" — this claim is **currently false** for both the
  age race and the starvation gap (an entity reaches `active=False` with `is_permadeath_set` staying
  `False` and no `death_reason`, which is neither "alive" nor "confirmed permanently dead" — a third,
  undocumented state LIFE-01 does not account for). If AC3 is satisfied as scoped (no tick exists
  where `active=False` with `death_reason=None` is terminal), this claim becomes true again and the
  doc would not need a correction; if the declared authority chosen leaves any code path where
  `active` can still go `False` without a `resolve_lifecycle` pass in the same or a bounded number
  of ticks, this doc's evidence claim needs revisiting (see Risks).
- **Determinism**: CLAUDE.md hard rule "Do not break determinism." Both writers are already fully
  deterministic (no RNG, no wall-clock); the fix must preserve bit-identical determinism, only
  change *which* writer's decision persists and *which tick* the OLD_AGE death lands on — the tick
  shift itself must be pinned by a test (AC4), not silently absorbed.

## Docs Requiring Update

- `docs/simulation/lifecycle_systems_contract.md`: the death-trigger table (lines ~36-39) and the
  "Biological" section (lines ~67-104) must be reconciled to state which writer is now the sole
  authority for `lifecycle.active`, document the resolution rule when the two branches would
  disagree, and (if AC7's starvation/sleep-debt gap is fixed in this ticket rather than split out)
  add the new death trigger row and its `death_reason` string to the table. This is the most
  directly on-point doc for AC5's "single declared authority... documented" requirement — it is the
  P1 contract doc whose own "Source:" line already cites both `lifecycle.py` and
  `apply.py::ApplyPath._compute_entity_changes` (passive branch) as joint sources.
- `docs/guidelines/intentional_divergences.md`: AC4 requires the death-tick shift (if any) to be
  "stated and justified, not absorbed silently — this is a determinism-visible change." This is
  exactly the shape of every other entry in this file (most recently §2.58, the sovereignty
  dual-writer ticket's own entry, immediately preceding this one numerically) — add a new
  `§2.59`-shaped entry with a `Bug Fix` (or equivalent) rationale class, citing the old vs. new tick
  and the regression test that pins it.
- `docs/parity_ledger/progression.yaml`: `PROG-030` (`text: '`test_aging_and_death`: Aging and
  death.'`, `priority: P0`, `status: legacy_verified`, `test_path: null`) is the parity-ledger entry
  for exactly this behavior. Per CLAUDE.md's Authoritative Mechanics Rule ("When a behavior
  changes: find the relevant parity ledger entry and update `status` and `v2_evidence`... P0
  entries require a passing `test_path`"), this entry must be updated with the new `v2_evidence`
  and given a real `test_path` pointing at the new ordinary-per-tick-progression regression test
  this ticket adds (AC6/AC9) — it currently has none, which is itself a pre-existing P0 gap this
  ticket is well-positioned to close as a side effect.

The following were considered and are **not** required to change as part of this ticket:

`docs/mechanics/01_entity_anatomy.md` (path: `docs/mechanics/01_entity_anatomy.md`) — its §4
"Biological Laws" table documents the hunger/sleep-debt accrual rates and HP-damage thresholds
(bit-identical parity, unaffected by this ticket, which does not touch the accrual formula or
thresholds themselves). It does not claim anything about which system owns old-age or starvation
*death detection*, so there is nothing in it to correct or contradict. If AC7's starvation gap is
fixed here by adding a new `resolve_lifecycle` branch, the Mechanics Bible chapter still does not
need a change — the death-*trigger* ownership contract lives in `docs/simulation/
lifecycle_systems_contract.md` (listed above), not in this chapter, matching the existing division
of labor between the two docs elsewhere in the codebase.

`docs/core/state.md` (path: `docs/core/state.md`) — generic state-container architecture doc (the
"Frozen Lifecycle Law," immutability, component composition). It does not make any per-field
authority claim about `lifecycle.active` specifically that this ticket's fix would falsify or
require correcting; the pipeline-law violation this ticket addresses is more precisely described by
`authoritative_mutation_pipeline_contract.md`'s own §1 (also not required to change — see next).

`docs/engine/authoritative_mutation_pipeline_contract.md` (path:
`docs/engine/authoritative_mutation_pipeline_contract.md`) — states the general Proposal → Refine →
Apply law at a high level and does not name `lifecycle.active` or any other specific field; the
ticket's fix brings actual behavior into compliance with this doc's existing law rather than
requiring the doc's own text to change.

`docs/world_rules/life-body/lifecycle.md` (path: `docs/world_rules/life-body/lifecycle.md`) — its
LIFE-01 "Repository evidence" claim is presently inaccurate (see Mechanics/Engine Constraints
above), but becomes accurate again once AC3 is satisfied as scoped, so no textual change is
strictly required by this ticket **if and only if** the chosen fix genuinely closes every silent
`active=False`/`death_reason=None` path AC3 names (age race and, if in scope here, the starvation
gap). Flagged as conditional in Risks below — if the implementer scopes the starvation fix out
("split it out with a written reason," per the ticket's own Scope text) rather than fixing it here,
this doc's evidence claim would remain falsified by a known, disclosed, still-open gap, and would
then need either a correction or an explicit forward-reference to the follow-up ticket.

`docs/plans/systemic_world/first_wave_plan.md`, `docs/plans/systemic_world/
ticket_planner_handoff.md`, `docs/plans/systemic_world/roadmap.md` — the ticket's own Related Docs
and Assumptions name these (the first_wave_plan's §3 scheduling-gate row should reportedly be
updated to reflect this ticket now being scheduled). **These files do not exist anywhere in this
working tree** (`docs/plans/systemic_world/` is entirely absent from `HEAD` on this branch); they
exist only inside the unmerged `systemic-world-roadmap-proposal` branch (PR #249). This ticket
cannot literally edit them from this worktree without first pulling that branch's content in —
flagged as a blocking gap in Risks, not silently dropped from scope.

## Parity Ledger Overlap

- `docs/parity_ledger/progression.yaml::PROG-030` — `test_aging_and_death`, **P0**,
  `status: legacy_verified`, `test_path: null`. Directly on point; requires update per Docs
  Requiring Update above. Being P0, it requires a passing `test_path` once updated (CLAUDE.md
  parity rule) — the new AC6 regression test satisfies this.
- `docs/parity_ledger/social_narrative.yaml::SOC-245` (default-heir assignment,
  `test_path: tests/unit/progression/test_lifecycle.py::test_default_heir_tie_break_deterministic`)
  and `::SOC-269` (inherited-nemesis feud transfer,
  `test_path: tests/unit/progression/test_lifecycle.py::test_inherited_nemesis_blocker_is_weakened_relative_to_original`)
  — both test `resolve_lifecycle`'s lineage-dispatch logic directly via staged already-dead state
  (not through ordinary per-tick progression), so they exercise logic downstream of death detection,
  not the detection race itself. Unaffected by this ticket if AC8's "pass unmodified" holds, since
  neither writer's fix changes what happens *after* `is_dead` is already True. No update needed
  unless the implementer's fix changes dispatch ordering/timing, which is out of this ticket's
  scope.
- No P0 entry anywhere in the ledger currently exercises the exact ordinary-per-tick-progression
  path this ticket's AC6 test requires — confirmed by grep across all `docs/parity_ledger/*.yaml`
  for `aging`/`OLD_AGE`/`lifecycle`/`death_reason`/`succession`/`resolve_lifecycle`; only PROG-030
  (above) and the SOC entries above are on point, none with a staged-vs-ordinary distinction
  recorded.

## Prior Work

- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` (#247, `stored_artifacts/
  TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/`) — same defect *class* (two systems
  writing one durable field with no declared precedence), closed 2026-09-27. Its resolution shape
  was **narrower** than this ticket's own AC5: it kept both writers and only synchronized the
  numeric threshold between them (a shared-constant "Unified" divergence), rather than declaring one
  writer the sole authority. This ticket's own scope (AC5: "a single declared authority... with the
  resolution rule when the two writers disagree") is the stronger form of fix — do not assume the
  sovereignty precedent's "just share a constant" shape transfers directly; `lifecycle.active` has
  no meaningful "shared constant" to synchronize, since the two writers disagree about *whether to
  write at all*, not about a threshold value.
- `registries/mechanisms.yaml::aging_death` entry (lines 634-706) already flags, as of its
  2026-09-20 note, "`src/engine/apply.py::ApplyPath._compute_entity_changes` also computes `new_age
  < life.max_age_ticks` for an entity's own `active` flag — a second real code path touching the
  same concept, not investigated further here... flagging in case it represents unintended
  duplication." This ticket is the direct follow-through on that flag. The same entry's own
  verification evidence (`tests/mechanic_scenarios/test_aging_death_value_differential.py`) is
  explicitly staged (`age_ticks=1000` fixed, not incremented per-tick) "avoiding the same cadence
  trap Program A hit on `goal_hierarchy`" — i.e. the mechanism's own "verified: observed" evidence
  was deliberately constructed in a way that happens to never exercise the exact defect this ticket
  fixes. Not a flaw in that entry's own scope (it was answering a different question, per §5.1's
  null-result-horizon rule), but worth naming so the dated evidence note this ticket's AC9 requires
  doesn't read as duplicating already-settled verification.
- `TCK-20260904-LINEAGE-DEATH-DISPATCH` — added the heir/feud-transfer/dying-wish dispatch logic
  inside `resolve_lifecycle` this ticket depends on reaching (AC2). Confirmed unaffected by either
  writer-precedence fix, since it only runs after `is_dead` is already True.
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (source of
  `tests/unit/engine/test_dirty_set_passive_decay_consumers.py`) — directly exercises Writer 1's own
  `active=` write formula in a real-pipeline test, on a different edge case (an already
  combat-dead entity, `hp=0` at construction) where `new_hp > 0` is already False regardless of the
  second `and` operand. Confirmed by hand-tracing both the current formula and the WIP branch's
  candidate replacement (`active=(new_hp > 0 and life.active)`) against this test's fixture: both
  produce `active=False` (the `new_hp > 0` term alone is decisive here), so this specific test is
  not expected to break under that candidate fix — but it is the one existing test closest to the
  code being changed and must be re-run explicitly, not assumed safe by this reasoning alone.

## Risks and Open Questions

- **Q1 (which writer is authoritative) is not pre-decided here**, per the ticket's own framing. The
  WIP branch's candidate (Writer 2 sole authority for age; Writer 1 keeps only the `new_hp > 0`
  immediate-HP-death gate) is evaluated above as one option with real evidence for/against, not
  adopted. The plan phase must make this decision explicitly and document the resolution rule
  (AC5), not silently follow the WIP branch.
- **Q3 (`initial_active=False` spawn reactivation) is a real open question, not currently forcing a
  decision** — zero production callers today (confirmed by repo-wide grep), so no live behavior
  regresses if left unaddressed, but the WIP-style fix silently removes the only path (accidental or
  not) that could ever reactivate such a spawn. Per the ticket's own instruction, do not pick a
  default here — return it to the systemic-world roadmap, or explicitly document in the ticket's
  Implementation Notes that the accidental reactivation path is being intentionally removed with no
  replacement, since nothing today depends on it.
- **AC7 (starvation/sleep-debt path) is a distinct root cause from the age race**, not just a second
  instance of the same one-tick timing race — `resolve_lifecycle` has no HP/alive-based detection
  branch at all today. A pure Writer-1-vs-Writer-2 precedence fix for age will not, by itself,
  resolve AC7; it requires either a new `resolve_lifecycle` detection branch (with its own
  `death_reason`, e.g. `"STARVATION"`/`"BIOLOGICAL"`) or an explicit, justified split-out into a
  separate ticket. The ticket's own Scope text permits either ("fix it here or split it out with a
  written reason") — this is a real scope decision for the plan phase, not resolved by this
  investigation.
- **`docs/plans/systemic_world/*` do not exist in this working tree.** The ticket's Related Docs and
  Assumptions both reference edits to files that only exist on the unmerged
  `systemic-world-roadmap-proposal` branch. If the plan/implementation phases are expected to update
  `first_wave_plan.md` §3 as the Assumptions section states, that dependency needs to be resolved
  first (merge or cherry-pick that branch's plan docs in) or the requirement needs to be explicitly
  descoped with a stated reason — silently skipping it would leave the plan package's own
  truthfulness claim (the Assumptions section's own words) unmet.
- **Existing tests staging age past `max_age_ticks`** are not limited to the two files the ticket
  names (`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`,
  `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`). Also found:
  `tests/integration/optimization/test_force_full_scan_phase_compliance.py:242-252` (stages
  `age_ticks=1000==max_age_ticks` directly and asserts `refined.entity_updates[1].active is False`
  from `resolve_lifecycle` alone) and `tests/mechanic_scenarios/test_aging_death_value_differential.py`
  / `tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py` (same staged-age
  pattern). None of these should need changes under any Q1 resolution that keeps `resolve_lifecycle`
  as at least *a* valid OLD_AGE detector for already-past-max entities, but each is worth an explicit
  pass/fail check, not an assumption, since AC8 requires "pass unmodified" to be proven, not asserted.
- **Determinism/tick-shift interaction with downstream consumers**: if the fix shifts the death tick
  by one (as the WIP evidence suggests for one candidate), any consumer that currently reads
  `lifecycle.active` as a death signal one tick earlier than `resolve_lifecycle`'s own
  `death_tick`/`death_reason` (e.g. `src/economy/vacancy.py`'s vacancy check, which reads
  `lifecycle.active`/`combat.alive` directly, not `death_reason`) will now see the entity remain
  "occupying" its role for one additional tick before vacating. This is very likely benign (vacancy
  detection doesn't care about the *reason*, only the flag, and the flag still eventually goes
  False) but should be confirmed against `tests/unit/economy/test_vacancy.py` /
  `tests/integration/economy/test_economic_vacancy_signal.py` explicitly, not assumed, since AC8
  names "economy-vacancy tests" by name.

## Anti-Drift Hazards

- **Do not conflate the age race fix with the starvation/sleep-debt gap fix as though they share one
  root cause.** They produce the identical *symptom* (silent `active=False`/`death_reason=None`) but
  the age case is a genuine one-tick ordering race between two writers, while the starvation case is
  an outright missing detection branch in `resolve_lifecycle`. A fix that only reorders/consolidates
  the age-writer precedence will not touch the starvation gap at all — verify AC7 separately, with
  its own evidence, not as a side effect of the AC1-AC6 age fix.
- **Do not silently change the `new_hp > 0` immediate-HP-death gate inside `_compute_entity_changes`
  while fixing the age term.** That gate is a real, load-bearing check (combat-adjacent HP loss must
  still deactivate promptly) and is orthogonal to the age precedence question — any Q1 fix should
  leave it untouched unless AC7's starvation fix is also being done here, in which case the change
  needed is adding a `resolve_lifecycle` detection branch, not altering this gate's own condition.
- **Do not scope-creep into `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`'s territory.**
  That ticket is explicitly Out of Scope here and held for sequencing; nothing in this ticket's fix
  touches region/faction ownership fields, only `entity.lifecycle.active`/`death_reason`. Keep it
  that way even though both are "dual-writer" class defects being fixed by the same actor.
  Out-of-scope, per Related Docs — do not attempt to update it in the course of this ticket without
  first resolving the "these files don't exist in this tree" gap noted in Risks.
- **Do not treat the WIP branch's `active=(new_hp > 0 and life.active)` expression as pre-approved.**
  It is optional evidence for one candidate answer to Q1, explicitly not an approved fix per the
  ticket's own Assumptions — re-derive and justify whichever expression the plan actually adopts,
  including its interaction with `initial_active=False` spawns (Q3) and the starvation gate.
  Combat-triggered `active=False` writes elsewhere (`src/engine/combat.py`'s KILL/PERMADEATH path)
  are out of this ticket's scope per its own Out of Scope section (Related but "unverified... a risk
  to check, not a claim to rely on") — do not touch that path without first confirming it does not
  share this race (it routes through `resolve_lifecycle`'s `ent_upd.combat.outcome_kind` check, not
  the passive branch's age/hp gate, so on a static read it looks unaffected, but this was not proven
  by running a scenario, only by code trace).
