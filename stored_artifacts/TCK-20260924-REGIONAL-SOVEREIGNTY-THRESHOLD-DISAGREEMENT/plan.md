---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT
artifact_type: plan
tags: [world, documentation, determinism]
---

# Implementation Plan — TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT

## Summary

Implements the ticket's own `## Decision Revision (2026-09-24)` (R1/R3/R4) exactly as settled by
the user, plus the added `_COMPARISON_TEXT` scope item from PR #245's review. **This plan makes no
new design decisions** — three prior investigation/escalation rounds already resolved every real
question (threshold value, writer-consolidation deferral, HERO_GUILD preservation). It only
translates the already-settled decision into concrete file:line edits.

**Net effect, smaller than any of the three original decision drafts:**
- `src/world/influence.py`: **zero changes.** `CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` are
  already `-50.0`/`50.0` and stay exactly as they are (R1).
- `src/engine/world_dynamics.py`: the ownership block **is not deleted, not moved, not rewritten**
  (R4/void-R2). Its only change is importing and using the same two constants instead of
  hardcoded `100.0`/`-100.0` literals — same comparisons, same guards, same event emission, new
  magnitude only.
- `docs/mechanics/regional_sovereignty.md`: threshold lines corrected to ±50 (R1).
- `docs/world/regional_sovereignty_runtime_contract.md`: **no threshold change** (already ±50); a
  new short section documents the two writers and points to the deferred consolidation ticket
  (AC3/R4).
- `docs/world/threat_and_consequences_contract.md`, `docs/mechanics/05_world_evolution.md`: **no
  change** — both already state ±50.
- `tools/semantic_control_plane/generate_territory_control_view.py`: `_COMPARISON_TEXT`'s counts
  become computed from the registries instead of hardcoded (added scope, AC8).
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-107`): updated in place (R3/AC6).
- `docs/guidelines/intentional_divergences.md`: one new entry, rationale class **Unified** — this
  ticket is explicitly **not** behavior-neutral (R4's own instruction: do not describe it as pure
  alignment).

**One existing test breaks under the new threshold and must be fixed as part of this ticket, not
treated as an incidental regression:** `tests/unit/world/test_sovereignty_events.py::test_no_sovereignty_event_when_influence_below_threshold`
uses `influence=50.0` as its "below threshold, no event" fixture. Under the old ±100 threshold this
was safely below; under the new ±50 threshold `50.0 >= 50.0` is true and the test's own assertion
(`sv_events == []`) would fail. `tests/unit/world/test_influence.py::test_conquest_and_liberation_thresholds`
and `tests/unit/world/test_stronghold.py` need **no** changes — confirmed by direct read, since
neither hardcodes the ±100 value and `FactionInfluenceService` is not touched by this plan.

## Steps

### Step 1 — `docs/mechanics/regional_sovereignty.md` §1.2: correct thresholds to ±50 (R1, AC1/AC2)

**Files:** `docs/mechanics/regional_sovereignty.md`

**Change:** In §1.2 "Ownership Thresholds":
- `**Hero Guild Control**: Influence > 100.0.` → `**Hero Guild Control**: Influence >= 50.0.`
- `**Monster Horde Control**: Influence < -100.0.` → `**Monster Horde Control**: Influence <= -50.0.`
- `**Contested**: Between -50.0 and 50.0.` — **do not change**. Per R1, this line is already
  correct once ±50 is the ownership boundary (the original decision's "fold into Contested" item
  is void — there is no 50-100 band to fold).

Update `last_verified` frontmatter to today's date.

**Do NOT touch:** §1.1 "Influence Dynamics" (the +1.0/+50.0 accrual-rate figures) — a separate,
pre-existing discrepancy against `influence.py`'s real `DEATH_INFLUENCE_SHIFT = 5.0`, explicitly
Out of Scope ("Any other sovereignty behavior: influence accrual rates").

**Verify:** Read back §1.2; confirm the comparison operators (`>=`/`<=`) match the real code's own
operators exactly (Step 2).

---

### Step 2 — `src/engine/world_dynamics.py`: import shared threshold constants (R4/AC3a)

**Files:** `src/engine/world_dynamics.py`

**Change:** In the existing inline import at the top of the "2.2 Ownership & Calamity Progression"
block:
```python
from src.world.influence import _region_owner_faction_id_str, FactionInfluenceService
```
(add `FactionInfluenceService` to the existing import). Then replace the two hardcoded literals:
```python
if current_influence >= 100.0 and (owner_fid is None or not _sem.is_protector(owner_fid)):
```
→
```python
if current_influence >= FactionInfluenceService.LIBERATION_THRESHOLD and (owner_fid is None or not _sem.is_protector(owner_fid)):
```
and
```python
elif current_influence <= -100.0 and (owner_fid is None or not _sem.is_invader(owner_fid)):
```
→
```python
elif current_influence <= FactionInfluenceService.CONQUEST_THRESHOLD and (owner_fid is None or not _sem.is_invader(owner_fid)):
```
Update the comment directly above (`# Ownership Law: Threshold of 100/-100 for control`) to read
`# Ownership Law: shared threshold with FactionInfluenceService (src/world/influence.py) — see
TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`.

**Do NOT touch:** The `is_protector`/`is_invader` guards, the `new_owner`/`changed` assignment
logic, the `SOVEREIGNTY_SHIFT` event-emission block (lines ~91-100), the hazard-scaling block
after it, or anything in `2.2b Flush sovereignty events`. All of R4's own findings (the
unconditional per-tick sweep, the phase-ordering dependency, the one-tick-latency risk of moving
this elsewhere) apply specifically *because* this code stays exactly where it is — do not refactor
around it.

**Verify:** `grep -n "100.0" src/engine/world_dynamics.py` shows zero remaining ownership-threshold
literals (the hazard block's own unrelated `50.0` trauma threshold at a different line is not
touched and is expected to remain).

---

### Step 3 — Fix the one breaking test (`test_sovereignty_events.py`)

**Files:** `tests/unit/world/test_sovereignty_events.py`

**Change:**
- `test_no_sovereignty_event_when_influence_below_threshold`: change the fixture's
  `influence=50.0` to `influence=30.0` — still comfortably below the new ±50 threshold, preserving
  the test's own intent ("below threshold → no event") rather than accidentally asserting on the
  boundary value itself.
- Module docstring: `"When a region's influence crosses ±100, ..."` → `"When a region's influence
  crosses ±50, ..."` (comment-only, matches the real, now-shared threshold).

**Do NOT touch:** `test_sovereignty_shift_event_emitted_on_hero_takeover` (influence=110.0),
`test_sovereignty_shift_event_emitted_on_monster_takeover` (influence=-110.0),
`test_sovereignty_event_payload_contains_influence` (influence=120.0) — all three use values
comfortably beyond ±50 already and need no change; confirmed by direct read.

**Verify:** `pytest tests/unit/world/test_sovereignty_events.py -v` — all 5 tests green.

---

### Step 4 — Add the shared-constant regression test (AC5)

**Files:** `tests/unit/world/test_sovereignty_events.py` (extend) or a new small test in
`tests/unit/world/test_world_dynamics.py` if that file already covers `WorldDynamicsSystem`'s own
ownership logic more directly (implementer's call — check both files' existing scope first; prefer
`test_sovereignty_events.py` since it already has the `_run_step22` harness this needs).

**Change:** Add two tests:
1. `test_world_dynamics_ownership_threshold_uses_shared_constants` — a source-level guard:
   read `src/engine/world_dynamics.py`'s own source text and assert no bare `100.0`/`-100.0`
   literal appears in the ownership-threshold comparison lines (e.g. assert
   `"FactionInfluenceService.LIBERATION_THRESHOLD"` and
   `"FactionInfluenceService.CONQUEST_THRESHOLD"` both appear in the file, and that the literal
   string `"100.0"` does not appear immediately after `current_influence >=`/`current_influence <=
   -` — a direct, permanent guard against the two paths silently drifting apart numerically again,
   which is the entire point of AC3a).
2. `test_world_dynamics_flips_ownership_at_shared_threshold_boundary` — a behavioral proof: run
   `WorldDynamicsSystem.resolve_dynamics` (via the existing `_run_step22` harness) at
   `influence=50.0` (unowned region) and assert a `HERO_GUILD` flip occurs (mirrors
   `FactionInfluenceService`'s own `>= LIBERATION_THRESHOLD` semantics exactly at the boundary);
   and at `influence=-50.0` assert a `MONSTER_HORDE` flip. This is the direct behavioral proof that
   both paths now agree at the boundary value, not just that the source text references the same
   name.

**Do NOT touch:** `tests/unit/world/test_influence.py`, `tests/unit/world/test_stronghold.py` —
confirmed unaffected, no edits.

**Verify:** `pytest tests/unit/world/test_sovereignty_events.py -v` — both new tests green.

---

### Step 5 — `docs/world/regional_sovereignty_runtime_contract.md`: document the two writers (R4/AC3)

**Files:** `docs/world/regional_sovereignty_runtime_contract.md`

**Change:** Add a new section immediately after "## What sovereignty means at runtime" (before
"## Taxation — `regional_sovereignty.py`"):

```markdown
---

## Two independent ownership writers (deliberate, deferred consolidation)

`owner_faction_id` is written by two separate code paths, not one:

- `FactionInfluenceService.process_influence_shift()` (`src/world/influence.py`) — triggered only
  when a death occurred this tick (`src/systems/lifecycle_systems/lifecycle.py:272`, gated on
  `if recent_deaths:`).
- `WorldDynamicsSystem.resolve_dynamics()`'s own ownership block (`src/engine/world_dynamics.py`)
  — an unconditional sweep over every region, every tick, against final settled influence
  regardless of cause, running earlier in the same tick's pipeline
  (`world_dynamics` phase precedes `lifecycle`).

As of `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`, both paths read the same
`CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` constants from `src/world/influence.py`, so they can no
longer disagree numerically. **Consolidating onto one writer was investigated and deliberately
deferred** — the two paths differ in trigger and phase position, not just implementation, and
naively consolidating would delay death-driven flips by one tick (a determinism/ordering change
requiring its own investigation). Tracked separately:
`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`. Do not assume this is an oversight —
it is a scoped, documented decision.

---
```

**Do NOT touch:** Any other section of this doc — it is already correct at ±50 throughout.

**Verify:** Read back; confirm the new section names both real code paths and the consolidation
ticket ID correctly.

---

### Step 6 — `docs/parity_ledger/world_dynamics.yaml` (`WORLD-107`): update in place (R3/AC6)

**Files:** `docs/parity_ledger/world_dynamics.yaml`

**Change:** Update the `WORLD-107` entry:
- `text`: change `"crosses +100 (HERO_GUILD takeover) or -100 (MONSTER_HORDE takeover)"` to
  `"crosses +50 (HERO_GUILD takeover) or -50 (MONSTER_HORDE takeover)"`. Leave the rest of the
  description (event shape, payload, flush mechanism) unchanged — none of that changed.
- `v2_evidence`: append a sentence: `"TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT:
  threshold literals replaced with FactionInfluenceService.LIBERATION_THRESHOLD/CONQUEST_THRESHOLD
  imports, resolving a prior ±50/±100 disagreement against src/world/influence.py; event emission
  and flush mechanism unchanged."`
- `test_path`: change to
  `tests/unit/world/test_sovereignty_events.py::test_world_dynamics_flips_ownership_at_shared_threshold_boundary`
  (Step 4's new behavioral test — the direct proof of the corrected, now-shared threshold; the
  existing `test_sovereignty_shift_event_emitted_on_hero_takeover` remains valid but no longer
  exercises the exact boundary this ticket fixed).
- `status`: stays `verified` (the mechanic itself is unchanged and still verified; only the
  threshold value it was verified against moved).

**Do NOT touch:** Any other entry in this file. Do not add a second, duplicate entry — per R3, this
is the one real entry to update, not a new one.

**Verify:** `python3 tools/parity_ledger_writer.py --validate` (or whatever this repo's own
sanctioned validator/writer entry point is — confirm exact command by checking
`docs/parity_ledger/schema.json`'s own tooling references before running) shows the file still
schema-valid. Never hand-edit past what a plain YAML value change requires; if a dedicated writer
script exists for this file, prefer it per this project's own "big diff via sanctioned writer is
safe, via raw Edit is corruption risk" precedent — but a two-field, one-entry value edit like this
is the same shape M1's own plan already made directly via `Edit` on `rule_classifications.yaml`
without incident, so a direct, narrow `Edit` is acceptable here too as long as the diff is scoped
to exactly these three fields on this one entry.

---

### Step 7 — `docs/guidelines/intentional_divergences.md`: new entry (R4/AC7, rationale class Unified)

**Files:** `docs/guidelines/intentional_divergences.md`

**Change:** Add a new numbered entry (next available number in §2's sequence) immediately after
the most recent existing entry, matching the established format exactly:

```markdown
### 2.NN Regional Sovereignty Ownership Threshold Unified to ±50; `WorldDynamicsSystem`'s Independent ±100 Retired (TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT)
- **Subsystem**: World Evolution / Regional Sovereignty
- **Old Behavior**: Two live, independent ownership-transfer paths disagreed on threshold —
  `FactionInfluenceService.process_influence_shift()` (death-gated) flipped ownership at ±50;
  `WorldDynamicsSystem.resolve_dynamics()`'s own unconditional per-tick sweep flipped ownership at
  ±100. `docs/mechanics/regional_sovereignty.md` (the Mechanics Bible chapter) stated ±100 as
  canonical — itself an unreachable comparison (`> 100.0` against the `[-100, 100]` clamp at
  `influence.py:59`) — while a second, newer Bible chapter (`05_world_evolution.md`, dated
  2026-09-02) explicitly rebutted ±100 as merely the clamp bound, not a real trigger tier, and both
  `docs/world/regional_sovereignty_runtime_contract.md` and
  `docs/world/threat_and_consequences_contract.md` already stated ±50. The Bible was split against
  itself, and the observable rule a region actually followed depended on which of the two live
  code paths reached it first in a given tick.
- **New Behavior**: `WorldDynamicsSystem`'s ownership block now imports and compares against the
  same `FactionInfluenceService.CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` constants (`-50.0`/
  `50.0`) instead of its own hardcoded `±100.0` literals. `docs/mechanics/regional_sovereignty.md`
  corrected to ±50 with reachable comparisons. Both writers remain (see the runtime contract doc's
  new "Two independent ownership writers" section) — the fix resolves the *numeric* disagreement,
  not the plurality of writers, which is deliberately deferred to
  `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`.
- **This is not behavior-neutral.** `WorldDynamicsSystem`'s own unconditional per-tick sweep now
  triggers at half its former magnitude — ownership flips via that path occur sooner and more
  often than before, for both conquest and liberation. This was unavoidable: any single direction
  that made all four sources agree necessarily changed at least one live path's actual threshold.
- **Rationale**: **Unified** — reconciling two independently-evolved, disagreeing thresholds into
  one, following the newer, code-cited, deliberately-corrective Mechanics Bible chapter
  (`05_world_evolution.md`, 2026-09-02) over the older, unreachable one
  (`regional_sovereignty.md`, 2026-05-18, from "Resource V2 Implementation").
- **Verification**: `tests/unit/world/test_sovereignty_events.py::test_world_dynamics_ownership_threshold_uses_shared_constants`
  and `::test_world_dynamics_flips_ownership_at_shared_threshold_boundary` (new, Step 4).
  `tests/unit/world/test_influence.py::test_conquest_and_liberation_thresholds` (existing,
  confirmed unaffected — `FactionInfluenceService` itself was never touched).
- **Deferred, not fixed here**: consolidating onto a single ownership writer
  (`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`) — the two paths differ in trigger and
  phase position, and naive consolidation risks a one-tick determinism/ordering change that needs
  its own investigation.
- **Status**: RATIFIED
```

**Do NOT touch:** Any other entry. Insert only, do not renumber or edit existing entries.

**Verify:** Read back; confirm the entry number is genuinely the next unused one in §2's sequence
(re-check immediately before this step, in case a concurrent session added an entry in the
meantime).

---

### Step 8 — `generate_territory_control_view.py`: compute `_COMPARISON_TEXT`'s counts (added scope, AC8)

**Prerequisite, blocking, confirmed by direct check (not assumed):** `_COMPARISON_TEXT`,
`render_cross_domain()`, and `build_cross_domain_view()` **do not exist anywhere in this branch's
working tree or on `origin/main`** — confirmed via `grep` across all `.py` files (zero hits) and
`git merge-base --is-ancestor 42fff7d52 HEAD`/`...origin/main` (both false). They exist only in
commit `42fff7d52` on branch `semantic-control-plane-m4`, PR #245, which is still **open, unmerged**
(confirmed via `gh pr view 245 --json state,mergedAt`). This branch (`sovereignty-threshold-decision`)
was cut from `origin/main` before M4 merged. **Steps 8-9 cannot run until PR #245 merges to `main`
and this branch is rebased/merged onto the post-#245 `main`.** Steps 1-7 have no such dependency —
they touch `src/engine/world_dynamics.py`, `src/world/influence.py`-adjacent docs, the parity
ledger, and `intentional_divergences.md`, none of which PR #245 touches — and should proceed now,
independently. Re-check PR #245's merge status immediately before starting Step 8, not just at
plan-write time — it may have landed by then.

**Files:** `tools/semantic_control_plane/generate_territory_control_view.py`

**Change:** `_COMPARISON_TEXT` is currently a static string with hardcoded counts (`0/4`, `10/10`,
classification breakdowns). Refactor:
- Remove the static `_COMPARISON_TEXT` module-level constant.
- Add a new function `_render_comparison(view: dict) -> str` taking the already-computed
  `view` dict from `build_cross_domain_view()` (which `render_cross_domain()` already has in
  scope) and building the counts line(s) from `view["territory"]`/`view["combat"]`'s own
  `mapped`/`unmapped`/`verified`/`unverified`/`classification_counts` fields — the exact same
  values the banner and per-domain sections already render, computed once, not duplicated as a
  second hardcoded literal.
- Keep the qualitative, judgment-call prose (the "inconvenient part, stated plainly" paragraph and
  the closing "neither domain came out cleaner" paragraph) as static text **inside** this function
  — those are not counts and are explicitly out of this step's scope to make "computed" (AC8's own
  scope guard: "the counts in `_COMPARISON_TEXT` only").
- Update `render_cross_domain()`'s call from `lines.append(_COMPARISON_TEXT)` to
  `lines.append(_render_comparison(view))`.

**Do NOT touch:** The qualitative prose's own wording, `render()`'s Territory-only path, or any
other function. Do not broaden `mapping_drift_check.py`'s drift classes — a "generated prose vs.
computed banner" drift class is a real, separate finding to report, not to build here.

**Verify:** `make cross-domain-management-view` re-run; the regenerated
`docs/brainstorm/cross_domain_management_view.md`'s `## Comparison` section shows the same real
counts as before (since the underlying registry data has not changed), now sourced from
computation rather than a literal.

---

### Step 9 — Add the anti-drift test for the comparison counts (AC8's own "real assertion" requirement)

**Files:** `tests/unit/tools/test_cross_domain_management_view.py`

**Change:** Add `test_comparison_counts_match_the_computed_banner` — independently re-derive the
Territory and Combat mapped/unmapped/verified/unverified counts and classification breakdowns
directly from the real registries (the same way `test_combat_mixed_realization_is_not_smoothed_into_a_clean_result`
already does), then assert those exact numbers appear in `_render_comparison(view)`'s own output
string. This is the test that would have caught the original hardcoded-`_COMPARISON_TEXT` drift
class — `test_real_cross_domain_view_is_up_to_date` (existing) cannot, since it regenerates from
the same source and stale-but-self-consistent prose reproduces byte-for-byte.

**Do NOT touch:** The existing four tests in this file.

**Verify:** `pytest tests/unit/tools/test_cross_domain_management_view.py -v` — 5/5 green.

---

### Step 10 — Full scoped regression run

**Files:** none changed (verification-only)

**Change:**
```
pytest tests/unit/world/test_sovereignty_events.py \
       tests/unit/world/test_influence.py \
       tests/unit/world/test_stronghold.py \
       tests/integration/world/test_regional_sovereignty.py \
       tests/unit/tools/test_cross_domain_management_view.py \
       tests/unit/tools/test_territory_control_view.py \
       -v
```
Never `pytest tests/` unscoped.

**Verify:** All files green, including `test_regional_ownership_flip` (Step 2's guards/comparisons
still produce the same real-world flip this integration test proves, now at the corrected
magnitude — the test itself asserts `influence >= 100.0` region state reaching `HERO_GUILD`, which
still holds trivially since 109.5 also clears the new, lower ≥50.0 bound).

---

### Step 11 — Close the ticket

**Files:** `tickets/inprogress/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT.md`
(`## Implementation Notes`, `## Test Summary`, `## Files Changed`, `## Completion Summary`)

**Change:** Record the three escalation rounds' outcomes (already written into the ticket's own
Decision Revision section — do not re-derive), every test run and result, the full file list, and
a completion summary. Then run `done-checker` (or `tools/gate_checks/done_checker_static.py`),
move to `tickets/done/`, migrate staging artifacts to `stored_artifacts/`, record hand-orchestrated
monitoring coverage.

**Verify:** `done-checker`'s post-Finalize conditions pass.

## Scope Guards

- No change to `src/world/influence.py` — `FactionInfluenceService`'s constants and logic are
  untouched (R4).
- No deletion, move, or rewrite of `WorldDynamicsSystem`'s ownership block — same file, same phase
  position, same guards, same event emission (R4/void-R2).
- No third `intentional_divergences.md` entry for a capability loss — none occurred; HERO_GUILD was
  never at risk once R2 was voided.
- No touching `docs/world/threat_and_consequences_contract.md` or `docs/mechanics/05_world_evolution.md`
  — both already state ±50, confirmed by direct read.
- No re-classifying `TERR-02` in `registries/rule_classifications.yaml` — Out of Scope, unchanged
  by this ticket regardless of what the eventual reclassification review finds.
- No broadening `mapping_drift_check.py`'s drift classes to cover generated-prose-vs-banner drift
  — that's a separate finding to report, not build (Step 8's own scope guard).
- No starting `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — filed, deliberately not
  this ticket's job.
- No influence-accrual-rate changes (the `+1.0`/`+5.0` discrepancy in `regional_sovereignty.md`
  §1.1 vs. `influence.py`'s `DEATH_INFLUENCE_SHIFT`) — pre-existing, separate, Out of Scope.

## Dependency Map

- Step 1 (Bible doc fix) is independent of Steps 2-4; can run in any order relative to them.
- Step 2 (`world_dynamics.py` constants) has no dependency; must run before Steps 3-4 (both
  depend on the corrected threshold to know what "below threshold" and "boundary" mean).
- Step 3 (fix breaking test) depends on Step 2.
- Step 4 (new regression tests) depends on Step 2.
- Step 5 (runtime contract doc) is independent of Steps 1-4; can run any time.
- Step 6 (parity ledger) depends on Step 4's test existing (names it in `test_path`).
- Step 7 (`intentional_divergences.md`) depends on Steps 2 and 4 (cites the real fix and its
  verification path).
- Step 8 (`_COMPARISON_TEXT` computation) and Step 9 (its test) are independent of Steps 1-7 in
  terms of *content* (separate file, separate concern), but **hard-blocked** on PR #245
  (`semantic-control-plane-m4`) merging to `main` first — the target code does not exist on this
  branch yet. Steps 1-7 are not blocked and should land first/independently.
- Step 10 (full regression) depends on every test-touching step (3, 4, 9) — if Step 8/9 are still
  blocked when Steps 1-7 are otherwise ready, run Step 10's regression scoped to Steps 1-7's own
  tests first, and re-run the full scope (including Step 9's test) once 8/9 land.
- Step 11 (closing) depends on every prior step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — canonical threshold chosen, rationale recorded | Ticket's own Decision Revision (R1); Step 7 records it in `intentional_divergences.md` | Read-back |
| AC2 — all four sources state that threshold | Steps 1, 2 (docs already correct per R1 need no edit) | `test_world_dynamics_ownership_threshold_uses_shared_constants` |
| AC3 — authority relationship explicit (revised: documented + deferred, not removed) | Step 5 | Read-back |
| AC3a — both paths read the same constants | Step 2 | `test_world_dynamics_ownership_threshold_uses_shared_constants` |
| AC4 — strict-inequality/clamp reachability | Step 1 (`>=`/`<=`, matching the real code) | Read-back; Step 2's code already used `>=`/`<=` |
| AC5 — regression test for both paths, fails on drift | Step 4 | Both new tests in Step 4 |
| AC6 — parity ledger updated | Step 6 | N/A (data update; validated by ledger's own schema check) |
| AC7 — `intentional_divergences.md` entry if behavior changes (it does) | Step 7 | Cites Step 4's tests |
| AC8 — `_COMPARISON_TEXT` computed, real assertion against drift | Steps 8, 9 | `test_comparison_counts_match_the_computed_banner` |

## Anti-Drift Notes

- **Do not re-open R1 (±50 vs ±100) or R4 (defer vs. consolidate).** Both are settled by the user
  after three independent verification rounds; this plan only implements them.
- **Do not add a HERO_GUILD branch to `FactionInfluenceService`.** R2 is explicitly void — the
  capability was never at risk once `WorldDynamicsSystem`'s block is confirmed to survive
  untouched.
- **Do not delete, move, or refactor `WorldDynamicsSystem`'s ownership block** even though it now
  looks like an obvious "duplicate" of `FactionInfluenceService`'s own logic — R4's own finding
  (unconditional sweep vs. death-gated, different phase position, one-tick-latency risk) is why
  the two must stay separate for now.
- **`docs/world/threat_and_consequences_contract.md` and `05_world_evolution.md` need zero edits.**
  Confirmed already correct; do not "helpfully" touch them.
- **The `_COMPARISON_TEXT` fix is about computation, not content.** Do not change what the
  qualitative prose says — only make the numbers it cites derive from the registries instead of
  being typed twice.

## Unresolved Questions

None. Every open item from the investigation, the three escalation rounds, and this plan's own
fact-verification pass (exact file:line edits, the one breaking test, the shared-constant test
design, the parity ledger update, the `_COMPARISON_TEXT` refactor shape) has been resolved as a
concrete decision above.
