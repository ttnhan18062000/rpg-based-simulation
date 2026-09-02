---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-PARITY-TEST-PATH-GAP
artifact_type: plan
tags: [testing]
---

# Implementation Plan — TCK-20260902-PARITY-TEST-PATH-GAP

## Summary
Three P0 parity ledger entries (`SUB-051`, `TOWN-027`, `TOWN-076`) violate
`docs/parity_ledger/schema.json`'s P0/`verified` `test_path` requirement, enforced at write time by
`tools/parity_ledger_writer.py:validate_entry()` (confirmed at `tools/parity_ledger_writer.py:73-87`
by direct read: lines 75-77 require `v2_evidence`+`test_path` for `status in {verified, divergent}`,
lines 86-87 separately require `test_path` for `priority == "P0"`). Two of the three
(`TOWN-027`, `TOWN-076`) already have a real, behavior-verified modern test and only need a
citation repoint. `SUB-051` has no real coverage anywhere and needs one genuinely new unit test
before it can be repointed — this also unblocks the `CombatAspect`→`CombatComponent` terminology
fix on that same entry that a prior ticket (`TCK-20260902-ASPECT-TERM-CLEANUP`) deferred for
exactly this reason. `docs/compliance/checklist.md`'s `TOWN-027`/`TOWN-076` rows cite two test
files confirmed deleted from the repo (`ls` returned "No such file or directory" for both
`tests/unit/systems/test_routine_v2.py` and `tests/unit/economy/test_loot_scaling.py`) and must be
updated to the same real paths used in the ledger. No `src/` behavior changes anywhere in this
plan. All ledger writes go through `tools/parity_ledger_writer.py`, never raw YAML edits.

## Steps

### Step 1 — Repoint TOWN-027 in the parity ledger
**Files:** `docs/parity_ledger/town_resource.yaml` (via `tools/parity_ledger_writer.py`, not raw
edit)
**Change:** The `TOWN-027` entry currently reads (confirmed by direct read,
`docs/parity_ledger/town_resource.yaml:303-314`): `status: verified`, `priority: P0`,
`legacy_evidence: null`, `v2_evidence: "Implementation proven via exhaustive checklist audit
Phase 1-11"`, `proof_type: null`, `test_path: null`, `divergence_note: null`,
`support_boundary: null`, `text` unchanged. Load the shard (`yaml.safe_load` on
`docs/parity_ledger/town_resource.yaml`), locate the `id: TOWN-027` dict, set only its
`test_path` field to
`tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`
(function confirmed present at `tests/unit/social/test_teach.py:117` by direct grep), leave every
other field byte-identical, and call `parity_ledger_writer.write_entry("town_resource.yaml",
entry)` — `write_entry` upserts by `id` (`tools/parity_ledger_writer.py:90-119`) and calls
`validate_entry()` before any file write, so a mistyped `test_path` or dropped field fails loudly
before touching disk, not silently. The test itself (read at
`tests/unit/social/test_teach.py:117-134` during investigation) builds a teacher/student pair,
gives the student a `BlockerState(id="c1", kind="capability", subject="STRIKE")`, calls
`CoreActions.execute_train(...)`, and asserts `updates[2].strategic.blockers_remove == ["c1"]` —
this is a direct proof of the entry's claimed text ("learning a skill emits a strategic
resolution for the corresponding capability blocker"), not a name-similarity guess.
**Other writers to this resource:** `docs/parity_ledger/town_resource.yaml` is also the write
target of the `parity-updater` agent role on any other ticket's Parity phase, and of
`tools/parity_index.py build`'s read (not write) path. `write_entry`'s upsert is a
read-whole-file/modify/write-whole-file operation with no locking — if another session/ticket
writes the same shard file concurrently, the loser's change would be silently dropped on
overwrite. Per this repo's documented multi-worktree-session pattern, run `git status` on this
file immediately before writing to confirm no other in-flight change is staged/modified in this
shard, and treat Steps 1, 2, and 4 (below) as sequential, not parallelizable with each other or
with any other ticket's ledger write in this session.
**Do NOT touch:** any other entry in `town_resource.yaml`; `proof_type`, `legacy_evidence`,
`v2_evidence`, `divergence_note`, `support_boundary`, or `text` on `TOWN-027` itself; any raw
`Read`/`Edit` tool call against this YAML.
**Verify:** `pytest tests/unit/social/test_teach.py -k
test_teach_resolves_target_capability_blocker_not_teacher -v` passes (test_plan.md's scoped
command #1). Then run `python3 tools/parity_index.py build` as a separate, visible Bash call —
required even though `write_entry` already rebuilds the index in-process
(`tools/parity_ledger_writer.py:22-24`), because the agent-monitoring retro's
`_is_parity_index_build_call` only recognizes a Bash call whose command text literally contains
`parity_index.py` and `build` (documented at `tools/parity_ledger_writer.py:26-31`) — an
in-process call inside another script is invisible to it.

### Step 2 — Repoint TOWN-076 in the parity ledger
**Files:** `docs/parity_ledger/town_resource.yaml` (via `tools/parity_ledger_writer.py`)
**Change:** Same mechanism as Step 1. `TOWN-076` currently reads (confirmed by direct read,
`docs/parity_ledger/town_resource.yaml:794-804`): identical shape to `TOWN-027`
(`status: verified`, `priority: P0`, generic `v2_evidence`, `test_path: null`, all other fields
`null`), `text: '`test_corpse_loot_convergence`: corpse loot convergence'`. Set only `test_path`
to `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`
(function confirmed present at `tests/unit/resource/test_loot_channeling.py:118` by direct grep).
The test (read at `tests/unit/resource/test_loot_channeling.py:118-158` during investigation)
builds a `CorpseState` with two distinct `ItemStack`s, drives `LootSystem.update` through the full
channel duration, runs the result through `AuthoritativeApplyPipeline.refine` +
`ApplyPath.apply_generation`, and asserts both stacks transfer, the corpse is removed from state,
and both items land in the looter's inventory — this matches `TOWN-076`'s claim exactly.
**Anti-collision note:** `docs/compliance/checklist.md:1309` has a separate, differently-ID'd row
(`COMB-090`) that also contains the string `test_corpse_loot_convergence` in its title text — do
not let a text search for that string land an edit on the wrong row; `TOWN-076` is the only ledger
ID this step touches.
**Other writers to this resource:** same as Step 1 — `town_resource.yaml` is a single shard shared
with any other ticket's `parity-updater` runs; treat this write as sequential with Steps 1 and 4,
not concurrent.
**Do NOT touch:** any other entry in `town_resource.yaml` (including `COMB-090` in
`checklist.md`, which lives in a different file and is out of scope regardless); any field on
`TOWN-076` besides `test_path`.
**Verify:** `pytest tests/unit/resource/test_loot_channeling.py -k
test_loot_corpse_completion_transfers_all_item_stacks -v` passes (test_plan.md's scoped command
#2). Then `python3 tools/parity_index.py build` as its own visible Bash call, same reasoning as
Step 1.

### Step 3 — Write the new SUB-051 test
**Files:** `tests/unit/core/test_rpg_math.py` (extend existing file — do not create a new file)
**Change:** No existing test anywhere covers `CombatComponent`/derived-stat numeric invariants as
a standalone claim (confirmed by investigation's full-tree grep and cross-check against the
archived checklist `docs/archive/logic_checklist_exhaustive.md:875`). Add one new test function,
named for what it asserts (e.g. `test_combat_stats_stay_within_bounds_after_normal_recalculation`
— do not force-fit the literal old name `test_stats_invariants`). Place it in
`tests/unit/core/test_rpg_math.py`, immediately after `test_stat_recalculation` (that function
spans lines 25-62 per direct read; it already imports everything needed —
`AttributeComponent`/`CombatComponent` from `src.core.state` at line 3-6, `LevelingService` from
`src.progression.leveling` at line 8, `SkillScalingService` from `src.engine.rpg_depth` at line
9 — so no new imports are required). This file is the more natural fit over
`tests/unit/core/test_rpg_depth.py` because it already co-locates `test_stat_recalculation`, the
direct sibling test for the exact function (`LevelingService.recalculate_combat_stats`) this new
test exercises, matching the ticket's "mirror the sibling tests' style" instruction.

Construct three `AttributeComponent` cases (mirroring `test_stat_recalculation`'s explicit-value
style, `tests/unit/core/test_rpg_math.py:25-40`):
1. Baseline/average: all nine attributes at the dataclass default (5 each, confirmed at
   `src/core/state.py:451-478` — frozen dataclass, no `__post_init__` validation, default 5).
2. Low-agility, near-floor: `agility=1`, other attributes at a normal in-range value (e.g. 5) —
   specifically to prove the `readiness_speed` floor engages (formula at
   `src/progression/leveling.py:104`, confirmed by direct read:
   `readiness_speed = max(1.0, 10.0 + (attributes.agility - 5) * 1.0)` — at `agility=1` this
   evaluates to `max(1.0, 6.0) = 6.0`, still above the floor; use `agility=1` regardless because
   it is the documented near-floor case the test plan calls for, not because the floor triggers
   at this exact value — the assertion is `>= 1.0`, which holds either way).
3. High-but-valid: attributes at 99 (the documented cap, `docs/mechanics/01_entity_anatomy.md`
   Section 1: "scale from 1 to 99").

For each case, call both:
- `LevelingService.recalculate_combat_stats(attrs)` directly (function signature confirmed at
  `src/progression/leveling.py:76-86`; returns a dict with keys `max_hp`, `atk`, `def_stat`,
  `evasion`, `range`, `move_cost`, `tactical_role`, `readiness_speed` per the `return` at
  `src/progression/leveling.py:177-186`), and
- `SkillScalingService.get_effective_stats(attrs)` (signature confirmed at
  `src/engine/rpg_depth.py:342-356`; calls `recalculate_combat_stats` internally then applies an
  unconditional evasion clamp at `src/engine/rpg_depth.py:390`:
  `base_stats["evasion"] = max(0.0, min(0.95, base_stats["evasion"]))`).

Assert, for every case, from both call paths:
- `stats["max_hp"] > 0` and `isinstance(stats["max_hp"], int)`.
- `stats["atk"] >= 1` and `stats["def_stat"] >= 1` — this holds unconditionally for in-range
  attributes even though the source code's own `max(1, ...)` floor for these two fields is only
  applied inside `if wounds:`/`if scars:` branches (`src/engine/rpg_depth.py:379-381`,
  `386-387`) — confirmed by direct read that the no-wounds/no-scars path returns
  `recalculate_combat_stats`'s raw arithmetic with no floor, but that arithmetic is provably
  positive for the in-range inputs this test uses (e.g. minimum case `atk = 10 + int(1*0.5) = 10`,
  `def_stat = 5 + int(1*0.3) = 5`), so this assertion tests the *class of inputs this ticket is
  scoped to*, not the code's own (partial) enforcement.
- `0.0 <= stats["evasion"] <= 0.95` — this one **is** unconditionally enforced by
  `rpg_depth.py:390` regardless of wounds/scars, for every case.
- `stats["readiness_speed"] >= 1.0` for every case, including the `agility=1` case explicitly.

Additionally construct one `CombatComponent` via normal explicit kwargs (or through
`recalculate_combat_stats`'s output fed into a `CombatComponent(hp=..., max_hp=...)` construction,
matching how the rest of the file builds state) and assert `0 <= hp <= max_hp` and `max_hp > 0` —
this proves the *constructed component's* invariant, since `CombatComponent` itself
(`src/core/state.py:305-329`, confirmed by direct read: frozen dataclass, plain fields, no
validation) enforces nothing on its own.

**Explicitly do NOT assert** anything about negative-attribute or >99-attribute inputs, or about
`AttributePatch.apply`'s delta-clamp behavior — see Scope Guards below.
**Do NOT touch:** `test_level_up_mechanics`, `test_stat_recalculation`, `test_encumbrance_scaling`,
`test_stamina_and_wounds` (the four existing functions in this file, confirmed by direct grep,
`tests/unit/core/test_rpg_math.py`) — add only the one new function, do not edit their bodies or
reorder them. Do not touch `tests/unit/core/test_rpg_depth.py`'s `TestAttributeCaps` or
`TestEffectiveStats` classes (test_plan.md's anti-drift guard: these must keep passing unmodified
and are not to be duplicated or subsumed).
**Verify:** `pytest tests/unit/core/test_rpg_math.py tests/unit/core/test_rpg_depth.py -v` — all
pre-existing tests in both files still pass, plus the new function (test_plan.md's scoped command
#3, run last per its own instruction, after this step).

### Step 4 — Repoint SUB-051 and fix its terminology in the same write
**Files:** `docs/parity_ledger/substrate.yaml` (via `tools/parity_ledger_writer.py`)
**Change:** `SUB-051` currently reads (confirmed by direct read,
`docs/parity_ledger/substrate.yaml:546-556`): `text: "...Test CombatAspect invariants (formerly
Stats).."`, `status: verified`, `priority: P0`, `legacy_evidence: null`, `v2_evidence:
"Implementation proven via exhaustive checklist audit Phase 1-11"`, `proof_type: null`,
`test_path: null`, `divergence_note: null`, `support_boundary: null`. This is the entry
`tools/parity_ledger_writer.py:validate_entry()` (`tools/parity_ledger_writer.py:86-87`) refused
to let `TCK-20260902-ASPECT-TERM-CLEANUP` touch at all, because it is P0 with `test_path: null` —
that block is the reason this ticket exists. In one single `write_entry` call (do not split into
two writes), set both:
- `test_path` to the new test's real `file::function` from Step 3 (e.g.
  `tests/unit/core/test_rpg_math.py::test_combat_stats_stay_within_bounds_after_normal_recalculation`
  — use the implementer's actual chosen name from Step 3), and
- `text` to `` "`test_stats_invariants`: Stats invariants — AOA Stabilization: Test
  CombatComponent invariants (formerly Stats).." `` — i.e. only the substring `CombatAspect` →
  `CombatComponent`, every other word/character in `text` unchanged (matches the correction
  `docs/compliance/checklist.md:1067` already carries: `"...Test CombatComponent invariants
  (formerly Stats)."`, confirmed identical wording by direct read).
Leave `status`, `priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `divergence_note`,
`support_boundary` byte-identical.
**Other writers to this resource:** same shared-shard hazard as Steps 1/2, but for
`substrate.yaml` instead of `town_resource.yaml` — check `git status` on this file before writing,
run sequentially, not in parallel with any other ticket's write to this shard.
**Do NOT touch:** any other entry in `substrate.yaml`, including the visually adjacent `SUB-050`
(line 540-545, also `test_path: null` but out of scope) and `SUB-052`/`SUB-053`/`SUB-054` (lines
557+, already correctly cited to other tests — out of scope, do not "helpfully" touch their
citations too).
**Verify:** Re-run `pytest tests/unit/core/test_rpg_math.py -k
<new_test_function_name> -v` to confirm the exact cited function passes standalone (subset of
test_plan.md's scoped command #3). Then `grep -c CombatAspect docs/parity_ledger/substrate.yaml`
returns `0` (this ticket's own AC). Then `python3 tools/parity_index.py build` as its own visible
Bash call, same reasoning as Steps 1-2.

### Step 5 — Fix the two stale TEST: citations in docs/compliance/checklist.md
**Files:** `docs/compliance/checklist.md`
**Change:** Two rows cite test files confirmed deleted from the repo (`ls` returned "No such file
or directory" for both during this planning pass):
- Line 453 (`TOWN-027`): comment tag currently reads `<!-- ID: TOWN-027 SOURCE:
  src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit
  -->` (confirmed by direct read). Change only the `TEST:` value to
  `tests/unit/social/test_teach.py`, matching the ledger's new `test_path` from Step 1's file
  (function name omitted here — this checklist convention cites file paths only, not
  `file::function`, consistent with every other row in the file, e.g. line 450-456's siblings).
- Line 1830 (`TOWN-076`): comment tag currently reads `<!-- ID: TOWN-076 SOURCE:
  src/engine/economy.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->`. Change
  only the `TEST:` value to `tests/unit/resource/test_loot_channeling.py`, matching Step 2.

**Resolved scope call — SOURCE: field left unchanged.** Both rows' `SOURCE:` files
(`src/systems/world_systems/routine.py`, `src/engine/economy.py`) still exist on disk (confirmed
by direct `ls` — neither was deleted, unlike the two `TEST:` targets), so there is no equivalent
"file no longer exists" trigger for them. A grep of `routine.py` found no remaining reference to
`execute_train`/class-hall logic, meaning the `SOURCE:` citation may itself be stale relative to
where the class-hall/train logic actually lives today
(`src/engine/domain/core_actions.py::CoreActions.execute_train`) — but this ticket's own Scope
item 6 text ("update those two rows' citations to the real modern paths **from Scope items 1-2**")
and its AC ("SOURCE/TEST paths updated **off the now-deleted pre-restructure files**") both key
specifically off the deleted-test-file problem this ticket exists to fix, and Scope items 1-2 only
ever supply replacement `test_path` values, never replacement source paths. Auditing/correcting
every checklist row's `SOURCE:` accuracy is the same class of "widespread pre-existing pattern"
this ticket's Out of Scope section already excludes for the ledger's "dozens more" null-test_path
entries — re-auditing `SOURCE:` citations project-wide is a separate, unscoped, follow-on
concern, not part of this ticket's narrow test_path-gap fix. No change to the `SUB-051` row (line
1067) — confirmed by direct read it already reads `"...Test CombatComponent invariants (formerly
Stats)."` correctly, with no `SOURCE:`/`TEST:` comment tag present at all to fix.
**Do NOT touch:** the `SOURCE:` value on either row (see above); line 1309's `COMB-090` row
(different ledger ID, same substring `test_corpse_loot_convergence` — confirmed distinct entry by
direct read, do not conflate); any other row in this ~1800+ line file.
**Verify:** `grep -n "TOWN-027\|TOWN-076" docs/compliance/checklist.md` shows both rows now citing
the modern test paths; `python3 tools/validate_frontmatter.py` still passes (this file's own
frontmatter, if any, is unaffected by an inline HTML-comment edit deep in the body).

### Step 6 — Final full verification pass
**Files:** none changed; verification only.
**Change:** Run all three test_plan.md scoped pytest commands together as a final confirmation,
in this order (matches test_plan.md's own stated ordering — run the third command last, after
Step 3/4 land):
```
pytest tests/unit/social/test_teach.py -k test_teach_resolves_target_capability_blocker_not_teacher -v
pytest tests/unit/resource/test_loot_channeling.py -k test_loot_corpse_completion_transfers_all_item_stacks -v
pytest tests/unit/core/test_rpg_math.py tests/unit/core/test_rpg_depth.py -v
```
Then confirm all three AC-named schema conditions: `grep -c CombatAspect
docs/parity_ledger/substrate.yaml` → `0`; spot-check (via `yaml.safe_load` in a throwaway Python
one-liner, not a persistent script) that `SUB-051`/`TOWN-027`/`TOWN-076` each now have a non-null
`test_path` and unchanged `status`/`priority`; run `python3 tools/validate_frontmatter.py`.
**Do NOT touch:** anything — this step is read-only verification.
**Verify:** All of the above pass with no failures.

## Scope Guards
- **Do NOT touch `src/engine/patches.py` or `src/engine/rpg_depth.py`.** The `AttributePatch.apply`
  clamp bug (upper bound 100 instead of documented `ATTRIBUTE_CAP=99`, no lower bound at all) is a
  real, confirmed `src/` behavior gap, but the ticket's own Out of Scope section explicitly
  forbids any `src/` behavior change in this ticket. See "Recommended Follow-Up" below.
- **Do NOT attempt to fix any other P0/`test_path: null` entry** beyond `SUB-051`, `TOWN-027`,
  `TOWN-076` — this includes `SUB-050` (visually adjacent to `SUB-051`), `COMB-078`, `COMB-079`,
  `SUB-035` in other shards, and "dozens more" across `town_resource.yaml` per the ticket's own
  text. This is a separate, wider, already-named-but-unfiled follow-up
  (`TCK-20260902-ASPECT-TERM-CLEANUP`'s deferred suggestion) — not this ticket's job.
- **Do NOT edit `docs/parity_ledger/*.yaml` with raw `Read`/`Edit`.** Every write in Steps 1, 2,
  4 goes through `tools/parity_ledger_writer.py:write_entry()`.
- **Do NOT touch `combat_movement.yaml`** — already corrected via `COMB-072` in
  `TCK-20260902-ASPECT-TERM-CLEANUP`.
- **Do NOT rename or repurpose any existing test** to fit a citation — `TOWN-027`/`TOWN-076` cite
  tests that already exist and already pass unmodified; `SUB-051`'s new test must be genuinely new
  and naturally named, not a forced rename.
- **Do NOT assert on `AttributePatch.apply`'s clamp behavior or on `enforce_attribute_caps` being
  wired into the apply path**, in the new SUB-051 test or anywhere else in this ticket — see
  Recommended Follow-Up.
- **Do NOT touch `docs/guidelines/intentional_divergences.md`** — no behavior change occurs in
  this ticket.
- **Do NOT edit `docs/compliance/checklist.md:1309`'s `COMB-090` row** while working `TOWN-076`
  (Step 2/5) despite the shared substring `test_corpse_loot_convergence`.

## Dependency Map
- Step 3 (write SUB-051's new test) must land and pass **before** Step 4 (SUB-051 ledger write),
  because `validate_entry()` refuses a P0 write with `test_path: null` — Step 4 needs a real
  `file::function` to cite.
- Steps 1, 2, and 3 are otherwise independent of each other and may be done in any order (this
  plan lists Steps 1-2 first only because they are the lower-risk citation-only changes).
- Step 5 (checklist.md) depends on Steps 1 and 2 having landed (needs their final `test_path`
  strings) but is independent of Steps 3/4 (SUB-051's checklist row needs no change).
- Step 6 depends on all prior steps.
- Steps 1, 2, and 4 must be **serialized against each other and against any other session's
  concurrent parity-ledger write** (see each step's "Other writers to this resource" note) — they
  are not safe to parallelize even though they touch different shard files in some cases
  (`town_resource.yaml` for 1/2, `substrate.yaml` for 4), because `write_entry`'s upsert is a
  whole-file read/modify/write with no locking, and a second concurrent write to the *same* shard
  (Steps 1 and 2 both touch `town_resource.yaml`) would silently drop one write if truly
  simultaneous. Run them as ordinary sequential tool calls within this one implementation session,
  which is safe.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `SUB-051` has non-null `test_path`; `text` says "CombatComponent" with no `CombatAspect` string; `grep -c CombatAspect substrate.yaml` == 0 | Step 3 (new test), Step 4 (ledger write) | `pytest tests/unit/core/test_rpg_math.py -k <new_test_name> -v`; `grep -c CombatAspect docs/parity_ledger/substrate.yaml` |
| `TOWN-027` `test_path` == `tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`, test passes | Step 1 | `pytest tests/unit/social/test_teach.py -k test_teach_resolves_target_capability_blocker_not_teacher -v` |
| `TOWN-076` `test_path` == `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`, test passes | Step 2 | `pytest tests/unit/resource/test_loot_channeling.py -k test_loot_corpse_completion_transfers_all_item_stacks -v` |
| New SUB-051 test exists, passes, genuinely asserts CombatComponent/stat invariants (not a repurposed unrelated test) | Step 3 | `pytest tests/unit/core/test_rpg_math.py tests/unit/core/test_rpg_depth.py -v` |
| All three ledger writes made via `tools/parity_ledger_writer.py`; `parity_index.py build` run after each; YAML still schema-valid | Steps 1, 2, 4 (writer calls + explicit `build` calls) | Each step's own `python3 tools/parity_index.py build` call; `write_entry`'s internal `validate_entry()` (raises on violation) |
| `checklist.md` rows consistent with ledger's corrected citations | Step 5 | `grep -n "TOWN-027\|TOWN-076" docs/compliance/checklist.md` |
| `python3 tools/validate_frontmatter.py` passes | Step 6 (and implicitly every step, since no frontmatter is touched until Step 5/6's verification) | `python3 tools/validate_frontmatter.py` |

## Recommended Follow-Up (not part of this ticket)
**Confirmed live bug — attribute bound enforcement.** `AttributePatch.apply`
(`src/engine/patches.py:579-594`), the actual authoritative path an `AttributeUpdate` travels
through, clamps only the **upper** bound, and to **100** rather than the documented
`ATTRIBUTE_CAP = 99` (`src/engine/rpg_depth.py:26`) — e.g. `strength=min(100, new_att.strength +
u_att.strength_delta)`, repeated for all nine attributes at lines 585-593. There is **no
lower-bound clamp anywhere in this function** — a sufficiently negative delta can drive any
attribute to 0 or negative through the real apply path with nothing correcting it.

A correctly-written fix already exists in the codebase but is disconnected: `enforce_attribute_caps`
(`src/engine/rpg_depth.py:31-44`) correctly computes deltas to bring any attribute back into
`[1, 99]`, and is already unit-tested directly (`tests/unit/core/test_rpg_depth.py:451-464`,
`TestAttributeCaps`, including the lower-bound case
`AttributeComponent(strength=150, agility=0)` → `deltas["agility_delta"] == 1`). But
`grep -rln enforce_attribute_caps src/` returns only `rpg_depth.py` itself — it has **zero
callers** anywhere in `src/`, including `AttributePatch.apply`, cleanup phase, or anywhere else in
the authoritative pipeline. It is dead code from the live pipeline's perspective.

A future hotfix-tier ticket could scope directly from this: wire `enforce_attribute_caps` into
`AttributePatch.apply` (or an adjacent cleanup-phase step) so the `[1, 99]` law
(`docs/mechanics/01_entity_anatomy.md` Section 1: "Every entity possesses nine core attributes
that scale from 1 to 99") is actually enforced end-to-end, and fix the 100-vs-99 off-by-one on the
upper bound. This ticket deliberately does not touch this — see Scope Guards.

## Anti-Drift Notes
- The ticket's own "Related Code Areas" section names `src/engine/rpg_depth.py` as the location of
  `LevelingService.recalculate_combat_stats` — this is imprecise. The method's real definition is
  `src/progression/leveling.py:76-186`; `rpg_depth.py`'s `SkillScalingService.get_effective_stats`
  (`src/engine/rpg_depth.py:342-392`) only calls it. Step 3 cites the correct location.
- The generic `v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"`
  string on all three entries is untouched by this plan — the ticket does not ask for it to
  change, only `test_path` (and, for `SUB-051` only, `text`).
- `docs/compliance/checklist.md:1309`'s `COMB-090` row shares the substring
  `test_corpse_loot_convergence` with `TOWN-076` but is a wholly different ledger ID — verified
  distinct by direct read; Step 2/5 must not touch it.
- The two repointed tests (`test_teach.py`, `test_loot_channeling.py`) were read in full during
  investigation and confirmed to assert exactly the claimed behavior, not matched on
  name-similarity alone — no further re-verification of *behavioral correctness* is needed before
  writing the ledger citation, only the mechanical write via the writer tool.

## Deviations

None from the ordered 6 steps. Implementation notes on execution details not fully specified by
the plan:

- **Test name chosen for SUB-051**: `test_combat_stats_stay_within_bounds_after_normal_recalculation`
  (the plan's own suggested example name, used verbatim — it was already the natural, non-forced
  name for what the test asserts, so no alternate name was needed).
- **Test placement**: inserted immediately after `test_stat_recalculation` in
  `tests/unit/core/test_rpg_math.py`, exactly as Step 3 specified — no new file created (an empty
  `tests/unit/core/test_rpg_math.py` did not need creating; it already existed with 4 tests).
- **Environment note (not a plan deviation, but needed for reproducibility)**: bare `python3` in
  this sandbox lacks `pydantic`, so every `pytest`/`tools/validate_frontmatter.py` invocation for
  Steps 1, 2, 3, 6 used the repo's venv interpreter directly
  (`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest ...`) instead of bare
  `python3 -m pytest ...`. `tools/parity_ledger_writer.py` and `tools/parity_index.py` do not
  import `src.core.registries`/`pydantic`, so those ran fine under bare `python3` as the plan
  assumed.
- Step 4's `text` field: yaml.safe_dump re-serialized the em dash character back into the
  file's existing `—` escape convention (matching how the rest of the shard already encodes
  it) rather than a literal UTF-8 em dash — confirmed byte-for-byte equivalent in YAML semantics,
  not a content change.
