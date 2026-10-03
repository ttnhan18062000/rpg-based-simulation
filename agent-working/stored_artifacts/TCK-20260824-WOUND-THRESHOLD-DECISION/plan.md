---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-THRESHOLD-DECISION
artifact_type: plan
tags: [combat]
---

# Implementation Plan — TCK-20260824-WOUND-THRESHOLD-DECISION

## Summary

The orchestrator has already decided: **delete** the unreachable 40% branch
(`WoundService.should_inflict_wound()` / `WOUND_THRESHOLD_RATIO`) in
`src/engine/rpg_depth.py`. This plan removes that dead code and its dedicated test class, adds one
new negative-boundary test against the live 25% gate to replace the coverage lost by the deletion,
resolves the `WOUND_THRESHOLD_RATIO` identifier collision in `docs/mechanics/01_entity_anatomy.md`
by removing the now-unused pseudocode identifier name, and repoints two parity ledger entries
(COMB-290, named in ticket scope; COMB-102, a P0 entry that becomes mechanically dangling as a
deterministic side effect of deleting the test it currently points to) to real, currently-passing
tests via the sanctioned `tools/parity_ledger_writer.write_entry()` path. `docs/mechanics/02_combat_laws.md`
requires no change (confirmed by investigation — no stale value or identifier collision there).

## Steps

### Step 1 — Delete the dead 40% wound-threshold code
**Files:** `src/engine/rpg_depth.py`
**Change:** Remove the module-level constant `WOUND_THRESHOLD_RATIO = 0.40` at line 111 (with its
inline comment) and remove the `WoundService.should_inflict_wound()` static method at lines
116-122, confirmed read verbatim:
```python
WOUND_THRESHOLD_RATIO = 0.40  # 40% of max HP in a single hit triggers wound

class WoundService:
    """Generates wounds from massive hits and transitions them to scars."""

    @staticmethod
    def should_inflict_wound(damage: int, max_hp: int) -> bool:
        """Check if a single hit is massive enough to cause a wound."""
        # VERIFIED v2: wound_infliction_massive_hit
        if max_hp <= 0:
            return False
        return damage >= (max_hp * WOUND_THRESHOLD_RATIO)
```
(`src/engine/rpg_depth.py:111-122`, read in full during planning). Delete only these two symbols —
leave the `class WoundService:` declaration and docstring at line 113-114 in place, followed
immediately by `create_wound()` (line 124 today, becomes the first method after deletion).

**Other writers to this file/symbol:** `grep -rn "should_inflict_wound\|WOUND_THRESHOLD_RATIO" src/
tests/` (per investigation.md) shows the *only* other references anywhere are: (a) the test-file
import at `tests/unit/core/test_rpg_depth.py:40` (removed in Step 2), and (b) the three hardcoded
assertions in `tests/unit/core/test_rpg_depth.py:199-201` (removed in Step 2). No other module,
system, or registry writes to or reads this constant/method — `src/engine/combat.py:607`'s live gate
(`damage > defender.combat.max_hp * 0.25`) is an independent inline literal that never called
`should_inflict_wound()` (confirmed by investigation.md's read of `combat.py:604-618`). There is no
concurrency/ordering hazard: this is a same-file deletion of two unreferenced symbols, not a shared
mutable resource.
**Do NOT touch:** `WoundService.create_wound()` (lines 124-146), `get_wound_stat_penalties()`
(148-167), `get_scar_stat_penalties()` (169-183) — all three are live (confirmed callers:
`create_wound()` from `combat.py:611`; the other two from `rpg_depth.py:385` and `:392` inside
`SkillScalingService.get_effective_stats()`). Do NOT touch the live 25% inline literal in
`src/engine/combat.py:607`.
**Verify:** `pytest tests/unit/core/test_rpg_depth.py -v -m "not slow"` collects and passes cleanly
after Step 2's companion test-file edit (this step alone will break collection until Step 2 lands —
implement Steps 1 and 2 together in one commit-worthy unit before running tests).

### Step 2 — Remove the dead-code test class and its import; add the missing negative-boundary test
**Files:** `tests/unit/core/test_rpg_depth.py`, `tests/unit/combat/test_direct_combat_outcomes.py`
**Change:**
1. In `tests/unit/core/test_rpg_depth.py`, remove `WOUND_THRESHOLD_RATIO` from the import list at
   line 40 (currently: `from src.engine.rpg_depth import (StaminaService, WoundService,
   LeashService, TerrainCostService, TargetStickinessService, SkillScalingService, ATTRIBUTE_CAP,
   enforce_attribute_caps, WOUND_THRESHOLD_RATIO, LEASH_CHASE_MULTIPLIER, TARGET_SWITCH_MARGIN)`,
   read verbatim at `tests/unit/core/test_rpg_depth.py:37-42`) — leaving it in place after Step 1
   causes an `ImportError` at collection time, per investigation.md's explicit flag.
2. Remove only the `test_wound_infliction_massive_hit` method (lines 196-201, verified read: it
   calls `WoundService.should_inflict_wound(40, 100)` / `(60, 100)` / `(30, 100)` directly — the
   dead 40% branch, never the live 25% path) and its preceding `# Logic ID: COMB-102` comment line
   (line 194) from `TestWoundInfliction` (class starts line 193). **Keep the class itself and its
   other three methods unchanged**: `test_wound_stat_impact` (line 205, preceded by `# Logic ID:
   COMB-103` comment at line 203 — keep that comment too), `test_wound_cumulative_penalties` (214),
   `test_healed_wound_not_penalized` (222) — all three call `WoundService.create_wound()` /
   `get_wound_stat_penalties()` directly (confirmed live methods, read verbatim at
   `tests/unit/core/test_rpg_depth.py:205-228`), none exercise the deleted method. This
   satisfies test_plan.md's explicit instruction not to delete the whole class, only the one method.
3. Add one new test to `tests/unit/combat/test_direct_combat_outcomes.py`, named
   `test_wound_infliction_below_live_threshold_produces_no_wound`, placed near the existing
   `test_wound_penalties_scale_with_severity_through_live_combat_path` (defined at
   `tests/unit/combat/test_direct_combat_outcomes.py:74`, confirmed by direct read) and
   `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` (line 121) —
   follow the same pattern (drive `CombatResolutionSystem.resolve_attack()` end-to-end, not
   `_get_wound_infliction()` directly) but assert the **negative** case: with damage set at or
   below `defender.combat.max_hp * 0.25`, the resulting update's wound field is `None`/empty (assert
   against whatever field name the two existing sibling tests already use for the wound result —
   read their exact assertion syntax from lines 74-160 before writing this test, do not guess a new
   field name).
**Other writers to this file/resource:** `tests/unit/core/test_rpg_depth.py` is also read/collected
by `tests/unit/core/test_rpg_math.py` and other test modules only via pytest's independent
collection, not shared mutable state — no write-conflict risk. `tests/unit/combat/test_direct_combat_outcomes.py`
was last written to by the completed sibling `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`, which
added the two sibling tests this new test is patterned after; no other in-flight ticket is known to
be editing this file concurrently (confirmed via `Related Tickets` in the ticket body — no open
sibling remains).
**Do NOT touch:** `TestScarPermanence` (starts line 231, uses `create_wound()`/`get_scar_stat_penalties()`,
unrelated), `test_wound_penalties_scale_with_severity_through_live_combat_path` and
`test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` themselves — read
only, do not modify their bodies (test_plan.md requires them to pass byte-identically before and
after this ticket).
**Verify:** `pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_direct_combat_outcomes.py -v -m "not slow"`
— all pass, including the new negative-boundary test.

### Step 3 — Resolve the `WOUND_THRESHOLD_RATIO` identifier collision in the Mechanics Bible
**Files:** `docs/mechanics/01_entity_anatomy.md`
**Change:** Investigation confirmed (`docs/mechanics/01_entity_anatomy.md:144-152`, read verbatim
during planning) that Section 6 "Wound Infliction" already states the correct value and uses
`WOUND_THRESHOLD_RATIO = 0.25` only as a **pseudocode identifier name**, never as a citation to the
real Python symbol. Once Step 1 deletes the real `WOUND_THRESHOLD_RATIO` Python symbol from
`rpg_depth.py`, no live code defines that name any more, so a future grep for
`WOUND_THRESHOLD_RATIO` will surface only this one doc location — the collision is structurally
resolved by Step 1's deletion. Decided call (per this plan, not left TBD): additionally rename the
pseudocode identifier in this doc's fenced block from `WOUND_THRESHOLD_RATIO` to
`WOUND_INFLICTION_RATIO`, to make it unambiguous on sight that this is doc-local illustrative
pseudocode, not a citation to a real Python name — this guards against a *future* re-collision if
someone reintroduces a same-named constant in code later, and costs nothing since the doc doesn't
cite `rpg_depth.py` for this value at all (it has no code citation for the threshold check itself,
per investigation.md). Apply this rename to both lines of the fenced block (lines 149-151):
```python
WOUND_THRESHOLD_RATIO = 0.25
is_wound = damage > (max_hp * WOUND_THRESHOLD_RATIO)  # strict >, only if defender survives
```
→
```python
WOUND_INFLICTION_RATIO = 0.25
is_wound = damage > (max_hp * WOUND_INFLICTION_RATIO)  # strict >, only if defender survives
```
Do not change the surrounding prose, the 25% value, or the strict-`>` semantics — only the
identifier name in the two code lines.
**Other writers to this file:** No other in-flight ticket is touching `01_entity_anatomy.md`
Section 6 (confirmed via ticket's own `Related Tickets` and investigation.md's "Prior Work" —
`TCK-20260619-PARITY-P0-BUGS` already closed and already fixed the value; no other open ticket
references this section).
**Do NOT touch:** Any other section of `01_entity_anatomy.md`, or `docs/mechanics/02_combat_laws.md`
(investigation confirmed it already uses the raw literal `0.25`, never the colliding identifier
name at all — `docs/mechanics/02_combat_laws.md:70-92`, no change required, this is a deliberate
no-op per the ticket's own AC #2 "stay internally consistent," already satisfied).
**Verify:** Manual read-back of the two edited lines; no automated test covers Mechanics Bible
prose content directly, but `tests/tools/test_validate_frontmatter.py` must still pass (frontmatter
untouched, so this is a no-risk check).

### Step 4 — Repoint COMB-290's `test_path` and `v2_evidence` to ground truth
**Files:** `docs/parity_ledger/combat_movement.yaml` (via `tools/parity_ledger_writer.write_entry()`,
not raw Edit — per session precedent on parity ledger file risk)
**Change:** Confirmed by direct read (`docs/parity_ledger/combat_movement.yaml:3023-3041`), COMB-290
currently has `test_path: tests/unit/combat/test_combat_matrix.py` (confirmed zero wound-related
tests by investigation's grep) and `v2_evidence` citing `_get_wound_infliction() line 583` (stale —
function is now at `combat.py:604-618`). `tools/parity_ledger_writer.py` (read in full during
planning: `tools/parity_ledger_writer.py:88-113`) exposes no CLI — it is a plain Python function
`write_entry(shard_filename: str, entry: dict, ledger_dir=None, db_path=None) -> dict` that
validates the full entry dict via `validate_entry()` then upserts it by `id` into the named shard,
replacing the whole entry (not a partial patch — the implementer must construct the *complete*
COMB-290 entry dict with all existing fields preserved except the two being corrected). Invoke it
via a short inline `python3 -c` call (or a one-off script), e.g.:
```python
from tools.parity_ledger_writer import write_entry
write_entry("combat_movement.yaml", {
    "id": "COMB-290",
    "text": "Wound infliction threshold — damage > max_hp * 0.25 (strict greater-than, 25%) triggers a wound on a surviving defender. Applies only if defender is alive after the hit.",
    "status": "verified",
    "priority": "P1",
    "legacy_evidence": None,
    "v2_evidence": "src/engine/combat.py CombatResolutionSystem._get_wound_infliction() lines 604-618 — `damage > defender.combat.max_hp * 0.25 and alive`. docs/mechanics/01_entity_anatomy.md Section 6 updated to match (TCK-20260619-PARITY-P0-BUGS). docs/mechanics/02_combat_laws.md Section 5 added wound threshold (TCK-20260619-PARITY-P0-BUGS).\n",
    "proof_type": "parity",
    "test_path": "tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path",
    "divergence_note": "Previously divergent: Chapter 02 stated 40%, entity_anatomy stated 40%, code used 25%. Resolved in TCK-20260619-PARITY-P0-BUGS: docs corrected to match source-authoritative 25% value.\n",
    "support_boundary": None,
})
```
(exact `text`/`divergence_note` strings preserved verbatim from the existing entry per direct read
at `docs/parity_ledger/combat_movement.yaml:3023-3041` — only `v2_evidence` line number and
`test_path` change). After the call succeeds, run a second, **visible** Bash call:
`python3 tools/parity_index.py build` — required per `tools/parity_ledger_writer.py`'s own
docstring (lines ~19-25, read during planning), which explains that `write_entry()`'s in-process
index rebuild is invisible to the retro tooling's Bash-command-text matcher, so a second explicit
build call is needed for `agent-monitoring`'s `parity_write_safety` metric to register it.
**Other writers to this shard:** `docs/parity_ledger/combat_movement.yaml` is a single YAML file
shared by every combat-movement parity entry (COMB-001 through at least COMB-291+). Step 5 below
also writes to this same shard (COMB-102). Both steps use the same `write_entry()` upsert-by-`id`
function, which only ever replaces the one matching entry by `id` — sequential calls to
`write_entry()` for different `id`s do not collide or overwrite each other's entries, but **must
not be run concurrently** (each call does read-modify-write of the whole shard file). Run Step 4
and Step 5 sequentially, not in parallel. No other ticket is known to be concurrently editing
`combat_movement.yaml` (confirmed via ticket's `Related Tickets`).
**Do NOT touch:** Any other entry in `combat_movement.yaml` besides COMB-290 in this step (COMB-102
is Step 5's job, not this step's).
**Verify:** `pytest --collect-only tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
succeeds before committing; `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_scan.py -v` passes after the write.

### Step 5 — Repoint COMB-102's `test_path` (P0, mechanically dangling after Step 2's deletion)
**Files:** `docs/parity_ledger/combat_movement.yaml` (via `tools/parity_ledger_writer.write_entry()`)
**Change:** Confirmed by direct read (`docs/parity_ledger/combat_movement.yaml:1104-1115`), COMB-102
is `priority: P0`, `test_path: tests/unit/core/test_rpg_depth.py::TestWoundInfliction::test_wound_infliction_massive_hit`
— the exact test Step 2 deletes. Per the project's P0 rule (`test_path` required and must resolve
for any `verified`/`divergent` P0 entry), this must be repointed in the same unit of work that
deletes the test, not left dangling. COMB-102's existing `v2_evidence` (read verbatim: "`src/engine/combat.py
CombatResolutionSystem._get_wound_infliction() delegates to src/engine/rpg_depth.py
WoundService.create_wound(damage=int(damage), max_hp=defender.combat.max_hp, tick=tick,
wound_id=w_id) (fixed in TCK-20260824-WOUND-PENALTY-FORMULA-WIRING).`") already correctly describes
the live `create_wound()` delegation, not `should_inflict_wound()` — only `test_path` is wrong, no
other field needs to change. Repoint `test_path` to
`tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
(the same live-path test used for COMB-290 in Step 4 — this is the correct fit: it drives
`resolve_attack()` end-to-end through `_get_wound_infliction()` → `WoundService.create_wound()`,
directly proving COMB-102's `text` field, `'test_wound_infliction_massive_hit: wound infliction'`
— note the `text` field itself is *not* changed, since it is a historical logic-ID label, not a
live test-name citation; only `test_path` and, if needed, `v2_evidence`'s stale reference to the
old test name are corrected). Invoke identically to Step 4 (full entry dict, all fields preserved
except `test_path`), followed by the same visible `python3 tools/parity_index.py build` call.
**Other writers to this shard:** Same shard as Step 4 (`combat_movement.yaml`) — run sequentially
after Step 4, not concurrently, per Step 4's note. Also note `COMB-103` (`combat_movement.yaml:1116-1130`,
`test_wound_stat_impact` — untouched, correct, live) sits adjacent in the same file region; this
step must not alter it. `COMB-104` (`combat_movement.yaml:1131-1142`) has a pre-existing, unrelated
wrong-class `test_path` bug (`TestWoundInfliction::test_scar_permanence` when `test_scar_permanence`
is actually defined in `TestScarPermanence`, confirmed at `tests/unit/core/test_rpg_depth.py:231-234`)
— this predates this ticket and is explicitly out of scope; do not fix it here.
**Do NOT touch:** COMB-103, COMB-104, or any other entry in this shard.
**Verify:** `pytest --collect-only tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
succeeds (same test as Step 4, already verified there); `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_scan.py -v` passes.

### Step 6 — Confirm `02_combat_laws.md` requires no change (no-op verification)
**Files:** `docs/mechanics/02_combat_laws.md` (read-only for this step)
**Change:** None. Investigation directly read `docs/mechanics/02_combat_laws.md:70-92` and confirmed
its pseudocode already uses the raw literal `0.25` (never the colliding `WOUND_THRESHOLD_RATIO`
identifier name at all) and already cites `CombatResolutionSystem._get_wound_infliction()`
(`src/engine/combat.py:605-617`) as evidence — both already correct and unaffected by either the
delete decision or the identifier rename in Step 3. This step exists to make explicit, in the
implementer's Files Changed/Implementation Notes, that this file was checked and deliberately left
unmodified — not silently skipped.
**Other writers to this file:** None known in this ticket's scope.
**Do NOT touch:** Do not edit this file as part of this ticket.
**Verify:** No test required; implementer confirms via direct read that lines 70-92 still contain no
`WOUND_THRESHOLD_RATIO` string and the `0.25` value, and records "no change needed, confirmed" in
the ticket's Implementation Notes.

## Scope Guards

- Do NOT touch `WoundService.create_wound()`, `get_wound_stat_penalties()`, `get_scar_stat_penalties()`
  in `src/engine/rpg_depth.py` — all three are live and owned by the completed
  `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`.
- Do NOT touch the live 25% inline threshold literal in `src/engine/combat.py:607`
  (`damage > defender.combat.max_hp * 0.25`) — this ticket resolves the *dead* 40% branch only, not
  live gating behavior.
- Do NOT touch `heal_wound()` or `MedicalService` — both were already deleted by the completed
  sibling `TCK-20260824-WOUND-HEALING-DECISION` (DEV-005); they no longer exist in the tree.
- Do NOT touch `TestScarPermanence` in `tests/unit/core/test_rpg_depth.py` (starts line 231) or any
  of `TestWoundInfliction`'s other three methods (`test_wound_stat_impact`,
  `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`).
- Do NOT touch `tests/unit/combat/test_direct_combat_outcomes.py`'s existing two sibling tests
  (`test_wound_penalties_scale_with_severity_through_live_combat_path`,
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path`) — read-only
  reference for the new test's pattern, must pass byte-identically before and after.
- Do NOT fix COMB-104's pre-existing wrong-class `test_path` bug — explicitly out of scope,
  pre-existing, unrelated to this ticket.
- Do NOT touch `docs/mechanics/02_combat_laws.md` content (Step 6 is verification-only, no edit).
- Do NOT touch `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (unbuilt scar-formation mechanic) or
  `TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND` (filed, unimplemented) — both are
  unrelated sibling-surfaced follow-ups.
- Do NOT use raw `Edit`/ad-hoc scripts on `docs/parity_ledger/combat_movement.yaml` — use
  `tools/parity_ledger_writer.write_entry()` exclusively for both COMB-290 and COMB-102.
- Do NOT run Steps 4 and 5's `write_entry()` calls concurrently against the same shard file — run
  sequentially.

## Dependency Map

- Step 1 and Step 2 must land together (same commit-worthy unit) — Step 1 alone breaks test
  collection (`ImportError` on `WOUND_THRESHOLD_RATIO`) until Step 2's import removal lands.
- Step 3 is independent of Steps 1/2/4/5 — it is a doc-only edit and can be done in any order, though
  logically it depends on the delete decision (already made) to justify the rename rationale.
- Step 4 and Step 5 both write to `docs/parity_ledger/combat_movement.yaml` via the same function —
  must run sequentially (Step 4 then Step 5, or reversed; order between them does not matter since
  they touch different `id`s, but they must not run in parallel).
- Step 5 is causally triggered by Step 2 (deleting `test_wound_infliction_massive_hit` is what makes
  COMB-102's `test_path` dangling) — Step 5 should be verified only after Step 2's deletion is
  confirmed committed, though the ledger write itself has no code dependency on Step 1/2's file state.
- Step 6 is independent, read-only, no dependency.
- All steps are independently verifiable via their own `Verify` command; the full scoped pytest run
  from `test_plan.md` should be run once after all steps land as a final integration check.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A single documented delete-vs-keep decision is recorded with rationale | Orchestrator decision (recorded in this plan's Summary and ticket's Implementation Notes at close) | N/A (documentation, not test-verified) |
| `01_entity_anatomy.md`, `02_combat_laws.md`, and COMB-290 stay internally consistent with the decision | Steps 3, 4, 6 | Manual read-back (Step 3, 6); `pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_scan.py -v` (Step 4) |
| If delete: `should_inflict_wound()`/`WOUND_THRESHOLD_RATIO` removed and `TestWoundInfliction` updated accordingly | Steps 1, 2 | `pytest tests/unit/core/test_rpg_depth.py -v -m "not slow"` |
| COMB-290's `v2_evidence` and `test_path` are corrected to reflect ground truth | Step 4 | `pytest --collect-only tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`; `pytest tests/tools/test_parity_ledger_schema.py -v` |
| (Deterministic consequence, folded into scope per orchestrator direction) COMB-102's `test_path` must not be left dangling | Step 5 | Same collect-only + schema test as above |

## Anti-Drift Notes

- `combat.py:607`'s live 25% gate is a raw inline literal, not a named constant, and never called
  `should_inflict_wound()` at any point — the two threshold implementations were always fully
  independent code paths. Deleting the dead one changes zero live behavior.
- The ticket's own Request Summary premise ("two Mechanics Bible docs cross-reference the stale
  value") is not literally true of the *value* — both docs already state 25% correctly since
  `TCK-20260619-PARITY-P0-BUGS`. The only real issue was the identifier-name collision, now resolved
  by Step 1 (deletion) + Step 3 (rename for future-proofing).
- COMB-102's `test_path` fix is a deterministic, mechanical consequence of deleting
  `test_wound_infliction_massive_hit` in Step 2 — not new, separately-scoped work and not a decision
  requiring further sign-off; it is included in this plan per the orchestrator's explicit direction
  and the project's P0 test_path rule (a P0 entry's `test_path` must resolve to a real, passing
  test).
- COMB-104's wrong-class `test_path` bug is real but pre-existing and unrelated — flagged in
  investigation.md for awareness only. Do not fix it under this ticket; if desired, it should become
  its own hotfix ticket.
- `tools/parity_ledger_writer.write_entry()` takes a **complete** entry dict and upserts by `id` —
  it is not a partial-field patch API. Any field omitted from the dict passed to `write_entry()`
  will be lost from the shard. Both Step 4 and Step 5 must pass every existing field of their
  respective entries, changing only the fields that actually need to change.
- The docstring in `tools/parity_ledger_writer.py` explicitly requires a second, visible
  `python3 tools/parity_index.py build` Bash call after each `write_entry()` call, because the
  retro tooling's `_is_parity_index_build_call` matcher only recognizes an explicit Bash command
  containing "parity_index.py" and "build" — the in-process rebuild inside `write_entry()` is
  invisible to it.

## Unresolved Questions

None.

## Deviations

- **Step 5 (COMB-102 `v2_evidence`)**: On the first `write_entry()` call the implementer appended
  an extra sentence to COMB-102's `v2_evidence` citing the new `test_path` and this ticket. The plan
  explicitly says only `test_path` and, "if needed," a *stale test-name reference inside*
  `v2_evidence` should change — and the original `v2_evidence` text contained no test-name reference
  at all (stale or otherwise), so no `v2_evidence` edit was actually warranted. Caught immediately
  and corrected with a second `write_entry()` call (+ a second visible `parity_index.py build`)
  restoring `v2_evidence` to the exact original string, changing only `test_path` as the plan
  specified. Net effect after both calls: COMB-102 matches the plan exactly (only `test_path`
  changed); the extra intermediate write is recorded here for traceability, not left silent.
- No other step deviated from the plan. All six steps, the scope guards, and the "do not touch"
  list were followed exactly as written, including running Steps 4 and 5 sequentially (never
  concurrently) against `docs/parity_ledger/combat_movement.yaml`, and issuing a separate visible
  `python3 tools/parity_index.py build` Bash call after each of the three `write_entry()` calls
  (two for COMB-290/COMB-102's final states, one extra for the COMB-102 correction above).
