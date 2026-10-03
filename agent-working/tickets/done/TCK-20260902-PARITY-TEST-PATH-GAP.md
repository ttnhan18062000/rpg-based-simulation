---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-PARITY-TEST-PATH-GAP
phase: done
date: 2026-09-02
tags: [testing]
---

# TCK-20260902-PARITY-TEST-PATH-GAP

## Title
Resolve `test_path: null` schema violation on 3 named P0 parity ledger entries (SUB-051, TOWN-027, TOWN-076) and finish the CombatAspect terminology fix TCK-20260902-ASPECT-TERM-CLEANUP could not land

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/parity_ledger/schema.json`'s `allOf` rule requires any entry with `priority: P0` to carry a
non-null `test_path` (schema.json lines 68-78), and separately requires `status: verified` /
`divergent` entries to carry both `v2_evidence` and `test_path` (lines 44-56). Three named P0
entries currently violate this while `status: verified`, citing only the generic sentinel
`v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"` and
`test_path: null`:

1. `SUB-051` (`docs/parity_ledger/substrate.yaml`) — `test_stats_invariants`. `text` also still
   says `"Test CombatAspect invariants (formerly Stats)"` — stale terminology TCK-20260902-
   ASPECT-TERM-CLEANUP explicitly tried and failed to fix here, because `tools/
   parity_ledger_writer.py`'s `validate_entry()` refuses to write ANY change to a P0 entry
   (terminology-only or not) while `test_path` stays null (schema.json lines 68-78; mirrored at
   `tools/parity_ledger_writer.py` lines 74-87). That ticket's own "Out of Scope" section named
   this exact entry and deferred it.
2. `TOWN-027` (`docs/parity_ledger/town_resource.yaml`) — `test_visit_class_hall_resolution`.
3. `TOWN-076` (`docs/parity_ledger/town_resource.yaml`) — `test_corpse_loot_convergence`.

Investigation (this ticket's own mandatory scan, full `tests/` tree grep — no exact-name match
found for any of the three) established that none of these three literal function names exist
in the current test tree, but two of the three claims ARE genuinely covered today by a real test
under a different name (found by searching by claimed *behavior*, not old name — see Related
Code Areas). The third (SUB-051) has no real coverage anywhere under any name and needs a new
test written, not just a citation repoint — see Scope item 3 and Assumptions.

## Scope
1. **TOWN-076 — repoint only.** Set `test_path: tests/unit/resource/test_loot_channeling.py::
   test_loot_corpse_completion_transfers_all_item_stacks` (function at line 118, landed by
   TCK-20260902-HARVEST-LOOT-TEST-COVERAGE). Confirm the test's assertions actually match the
   entry's claimed behavior ("corpse loot convergence" — full item-stack transfer on corpse
   completion) before citing it; do not cite on name-similarity alone. Write via `tools/
   parity_ledger_writer.py`, not raw YAML edit.
2. **TOWN-027 — repoint only.** Set `test_path: tests/unit/social/test_teach.py::
   test_teach_resolves_target_capability_blocker_not_teacher` (function at line 117). Confirm its
   assertion (`updates[2].strategic.blockers_remove == ["c1"]` where the blocker is
   `kind="capability"`) genuinely matches the entry's claim ("learning a skill emits a strategic
   resolution for the corresponding capability blocker") before citing it. Write via `tools/
   parity_ledger_writer.py`.
3. **SUB-051 — write a new test, then cite it.** No existing test anywhere (old name, new name,
   or behavior-equivalent) covers "Stats/CombatComponent invariants" as a standalone numeric-
   bounds claim distinct from its siblings SUB-052 (`test_damage_calc_math`, already cited to
   `tests/integration/pipeline/test_combat_legality_matrix.py`), SUB-053
   (`test_recalc_level_consistency`, cited to `tests/unit/core/test_rpg_depth.py`), and SUB-054
   (`test_combat_damage_invariants`, same file as SUB-052) — confirmed by the archived exhaustive
   checklist (`docs/archive/logic_checklist_exhaustive.md:875`, `RPG-COMBAT-063`), where this
   specific line is the only one of the five siblings still `[ ]` unchecked with no SOURCE/TEST
   citation ever recorded, past or present. Write a new unit test asserting `CombatComponent`
   invariants hold (no NaN/negative/out-of-bounds `hp`, `max_hp`, `atk`, `def_stat`, `readiness`,
   etc. after normal state construction and derived-stat recalculation via
   `LevelingService.recalculate_combat_stats`, mirroring the sibling tests' style in
   `tests/unit/core/test_rpg_math.py` / `test_combat_legality_matrix.py`). Land the new test
   under a name that does NOT reuse `test_stats_invariants` verbatim unless that literal name is
   the natural, non-forced name for what it actually asserts (avoid renaming-to-fit-citation).
   Then set `test_path` to the new test's real `file::function`.
4. **SUB-051 terminology.** Once `test_path` is non-null, rewrite `text` to replace
   `"Test CombatAspect invariants (formerly Stats)"` with the accurate
   `"Test CombatComponent invariants (formerly Stats)"` (matching the correction
   `docs/compliance/checklist.md:1067` already carries — checklist.md itself was already fixed
   for this line, only the parity ledger YAML lagged). Do this in the same `parity_ledger_writer.py`
   write as the `test_path` fix, not a separate pass.
5. Run `python3 tools/parity_index.py build` after each ledger write per the writer's own
   docstring convention (keeps the derived SQLite index from going stale).
6. Re-verify `docs/compliance/checklist.md`'s SUB-051/TOWN-027/TOWN-076 rows already carry
   correct SOURCE/TEST citations consistent with the ledger fix (TOWN-027 and TOWN-076's
   checklist rows currently cite pre-restructure paths — `tests/unit/systems/test_routine_v2.py`
   and `tests/unit/economy/test_loot_scaling.py` respectively — that no longer exist in the repo;
   update those two rows' citations to the real modern paths from Scope items 1-2 in the same
   pass, since leaving the checklist internally inconsistent with the ledger it mirrors would
   recreate the same drift this ticket is fixing).

## Out of Scope
- The other P0 `verified`/null-`test_path` entries discovered incidentally during this scan
  (`COMB-078`/`test_aspect_model_purity`, `COMB-079`/`test_mandatory_aspect_naming` in
  `combat_movement.yaml`, `SUB-035`/`test_aspect_model_rebuild_integrity` in `substrate.yaml`,
  and dozens more across `town_resource.yaml` alone — this is a widespread pre-existing pattern,
  not isolated to the 3 named entries). TCK-20260902-ASPECT-TERM-CLEANUP already named the first
  three of these as a "suggested follow-up, not filed" — this ticket does not file or absorb
  that follow-up; it stays scoped to the 3 entries named in this request.
- Any entry in `docs/parity_ledger/` other than `SUB-051`, `TOWN-027`, `TOWN-076`.
- Any `combat_movement.yaml` edit (the terminology fix already landed there via COMB-072 in
  TCK-20260902-ASPECT-TERM-CLEANUP).
- Rewriting or renaming any *other* existing test beyond the one new test SUB-051 needs; TOWN-027
  and TOWN-076 get citation-only changes, no test-code edits.
- `docs/guidelines/intentional_divergences.md` — no behavior change, only citation/terminology
  and one net-new test; not a divergence.
- Re-litigating whether the historical "Aspect-Oriented Architecture" effort fully landed —
  already settled by TCK-20260902-ENTITIES-DOC-REWRITE / ASPECT-TERM-CLEANUP: current source of
  truth is the Component system in `src/core/state.py`.
- Any `src/` behavior change — this ticket only adds test coverage and corrects ledger/checklist
  citations; it does not change `CombatComponent`, `LevelingService`, teaching, or looting logic.

## Acceptance Criteria
- [x] `docs/parity_ledger/substrate.yaml`'s `SUB-051` entry has non-null `test_path` pointing to
  a real, passing test; `text` reads `"...Test CombatComponent invariants (formerly Stats).."`
  with no remaining `CombatAspect` string; `grep -c CombatAspect docs/parity_ledger/substrate.yaml`
  returns 0.
- [x] `docs/parity_ledger/town_resource.yaml`'s `TOWN-027` entry `test_path` is
  `tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`
  (or the exact real path confirmed at implementation time) and that test passes:
  `pytest tests/unit/social/test_teach.py -k test_teach_resolves_target_capability_blocker_not_teacher -v`.
- [x] `docs/parity_ledger/town_resource.yaml`'s `TOWN-076` entry `test_path` is
  `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`
  (or the exact real path confirmed at implementation time) and that test passes.
- [x] The new SUB-051 test exists, passes, and genuinely asserts `CombatComponent`/stat
  numeric-invariant behavior (not a rename of an unrelated existing test to fit the citation).
- [x] All three ledger writes were made through `tools/parity_ledger_writer.py` (not raw
  Read/Edit) and `python3 tools/parity_index.py build` was run after; the resulting YAML still
  validates against `docs/parity_ledger/schema.json`.
- [x] `docs/compliance/checklist.md`'s SUB-051/TOWN-027/TOWN-076 rows are consistent with the
  ledger's corrected citations (TOWN-027/TOWN-076 rows' SOURCE/TEST paths updated off the
  now-deleted pre-restructure files).
- [x] `python3 tools/validate_frontmatter.py` passes on this ticket and any touched docs.

## Related Tickets
- TCK-20260902-ASPECT-TERM-CLEANUP (done) — fixed the same `CombatAspect` terminology pattern in
  `combat_movement.yaml`'s `COMB-072` entry and explicitly named `SUB-051` in `substrate.yaml` as
  out of scope, deferred here, because its `test_path` was null and the validating writer refused
  the write. Also surfaced (as an unfiled suggested follow-up) the `COMB-078`/`COMB-079`/`SUB-035`
  entries this ticket deliberately excludes — see Out of Scope.
- TCK-20260902-HARVEST-LOOT-TEST-COVERAGE (done) — landed
  `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`,
  the real modern test this ticket cites for TOWN-076.
- TCK-20260831-TRUST-GATED-TEACHING (referenced by `tests/unit/social/test_teach.py`'s own
  docstring, not independently verified by this scoping pass) — introduced
  `test_teach_resolves_target_capability_blocker_not_teacher`, the real modern test this ticket
  cites for TOWN-027.

## Related Docs
- `docs/parity_ledger/schema.json` — the `allOf` P0/`test_path` and `verified`/`test_path`+
  `v2_evidence` rules this ticket brings the 3 entries into compliance with (lines 44-56, 68-78).
- `docs/compliance/checklist.md` — mirrored rows for all 3 entries (lines ~1067, ~453, ~1830);
  already partially corrected for SUB-051's terminology but not TOWN-027/TOWN-076's stale file
  citations.
- `docs/archive/logic_checklist_exhaustive.md` — historical/archived checklist; confirms
  SUB-051/`RPG-COMBAT-063` was never checked or cited, unlike its 4 siblings (line 875 vs.
  874/876-878).
- `docs/testing/how_to_add_requirement_tests.md` §6 "Verifying the Parity Ledger for P0 Laws" —
  the standard procedure this ticket follows.
- `docs/core/entities.md`, `docs/core/state.md` — canonical Component-system terminology
  (`CombatComponent`, not `CombatAspect`) reference for Scope item 4.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL/` — background on why
  `tools/parity_ledger_writer.py` exists and what it validates.
- `stored_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/` (if present) — confirmed the Component
  system, not a historical "Aspect" model, is current source of truth.

## Related Code Areas
- `docs/parity_ledger/substrate.yaml` (SUB-051 entry, ~line 546) and `town_resource.yaml`
  (TOWN-027 ~line 303, TOWN-076 ~line 794).
- `tools/parity_ledger_writer.py` — the only sanctioned write path for these edits.
- `tests/unit/social/test_teach.py:117` — `test_teach_resolves_target_capability_blocker_not_teacher`
  (candidate real citation for TOWN-027).
- `tests/unit/resource/test_loot_channeling.py:118` —
  `test_loot_corpse_completion_transfers_all_item_stacks` (candidate real citation for TOWN-076).
- `tests/unit/core/test_rpg_math.py`, `tests/integration/pipeline/test_combat_legality_matrix.py`
  — sibling-test style precedent for the new SUB-051 test.
- `src/core/state.py` (`CombatComponent`, `AttributeComponent`) — the real components SUB-051's
  new test exercises.
- `src/engine/rpg_depth.py` (`LevelingService.recalculate_combat_stats`) — derived-stat
  recalculation path likely exercised by the new SUB-051 test.

## Assumptions / Open Questions
- Assumes `layer: testing` (registered in `registries/layer_registry.jsonl`) is the right fit —
  this ticket's substantive work is test-coverage/citation hygiene on the parity ledger, not
  cross-cutting process/convention authoring, so `testing` fits more precisely than `guidelines`
  even though the latter was the default suggested in the originating request template.
- Assumes `tier: standard` (not `hotfix`) is correct because SUB-051 requires writing a genuinely
  new test (substantive), even though TOWN-027 and TOWN-076 are simple citation repoints that
  would individually qualify as hotfix-tier on their own. Bundling under one standard-tier ticket
  was chosen over splitting into a hotfix (TOWN-027/TOWN-076) + separate standard (SUB-051)
  because the originating request explicitly asked to resolve SUB-051's `test_path` gap and its
  terminology fix "together" in one pass, and all three share the same root cause and write path.
  If the implementer finds SUB-051's new-test authorship trivial in practice, this reasoning
  should be revisited but the ticket need not be re-split retroactively.
- Assumes the two "real test found under a different name" citations (TOWN-027 → `test_teach.py`,
  TOWN-076 → `test_loot_channeling.py`) are correct matches on behavior, not just plausible
  name/keyword similarity — flagged in Scope items 1-2 for the implementer to re-verify against
  each entry's exact claimed text before writing, since this scoping pass read the test bodies
  but did not run them.
- Assumes no real test anywhere covers SUB-051's specific claim (checked via full-tree grep for
  the old name, grep for `CombatComponent`/`AttributeComponent`-adjacent invariant tests, and the
  archived checklist's own citation history) — if a downstream investigation phase finds a
  legitimate existing match this scoping pass missed, prefer that over writing a new test.
- Assumes `docs/compliance/checklist.md`'s SUB-051/TOWN-027/TOWN-076 row IDs are the same
  underlying regression-test claims as the parity ledger IDs of the same name (not coincidentally
  identical spelling) — same assumption ASPECT-TERM-CLEANUP made for this exact set of rows.

## Implementation Notes

Followed plan.md's 6 ordered steps exactly, no architectural deviation.

1. **TOWN-027 repoint.** Read the current entry via `yaml`/grep first
   (`docs/parity_ledger/town_resource.yaml:303-314`), then called
   `tools.parity_ledger_writer.write_entry("town_resource.yaml", entry)` with only `test_path`
   changed to `tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`,
   every other field byte-identical. Followed with an explicit, separately-visible
   `python3 tools/parity_index.py build` Bash call (required for the agent-monitoring retro's
   `_is_parity_index_build_call` detector, which only recognizes a literal Bash call containing
   `parity_index.py` and `build`, not the writer's own in-process rebuild).
2. **TOWN-076 repoint.** Same mechanism, `test_path` set to
   `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`.
   Confirmed via direct read that `docs/compliance/checklist.md:1309`'s unrelated `COMB-090` row
   (shares the substring `test_corpse_loot_convergence`) was never touched.
3. **New SUB-051 test.** Added
   `test_combat_stats_stay_within_bounds_after_normal_recalculation` to
   `tests/unit/core/test_rpg_math.py`, immediately after `test_stat_recalculation`, using the
   plan's own suggested name verbatim (it was already the natural name for what the test
   asserts). Three `AttributeComponent` cases (defaults, `agility=1`, all-99), each run through
   both `LevelingService.recalculate_combat_stats` and `SkillScalingService.get_effective_stats`,
   asserting `max_hp > 0` (and `int`), `atk >= 1`, `def_stat >= 1`, `0.0 <= evasion <= 0.95`, and
   `readiness_speed >= 1.0`; plus one `CombatComponent` construction asserting
   `0 <= hp <= max_hp`. No out-of-range/adversarial attribute values asserted, per the plan's
   explicit scope guard around the separate `AttributePatch.apply` clamp bug. Full file plus
   `tests/unit/core/test_rpg_depth.py` re-run together: 64 passed, 0 failed — no pre-existing test
   touched or broken.
4. **SUB-051 repoint + terminology fix, single write.** Set `test_path` to the new test's real
   `file::function` and rewrote `text`'s `CombatAspect` substring to `CombatComponent` in one
   `write_entry` call — every other field (`status`, `priority`, `legacy_evidence`, `v2_evidence`,
   `proof_type`, `divergence_note`, `support_boundary`) left byte-identical. This is the write
   `validate_entry()` previously refused (P0 + `test_path: null`) that blocked
   `TCK-20260902-ASPECT-TERM-CLEANUP` from touching this entry at all.
5. **checklist.md citations.** Updated only the `TEST:` value on the `TOWN-027` (line 453) and
   `TOWN-076` (line 1830) HTML-comment tags to the two real modern paths above; left `SOURCE:` on
   both rows unchanged (per plan's explicit scope call — the `SOURCE:` staleness question is a
   separate, unscoped audit). `SUB-051`'s row (line 1067) needed no edit — already read
   "CombatComponent" correctly with no `SOURCE:`/`TEST:` tag present.
6. **Final verification.** All three scoped pytest commands pass; `grep -c CombatAspect
   docs/parity_ledger/substrate.yaml` returns `0`; a throwaway `yaml.safe_load` spot-check
   confirmed all three entries carry non-null `test_path` with `status`/`priority` unchanged;
   `tools/validate_frontmatter.py` passes on the ticket, the staging artifacts directory, and
   `docs/compliance/checklist.md`.

**Environment note**: bare `python3` in this sandbox lacks `pydantic` (breaks `tests/conftest.py`
import chain via `src/core/registries.py` → `src/content/repository.py`). All `pytest` and
`validate_frontmatter.py` calls used the repo's venv interpreter directly
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`). `tools/parity_ledger_writer.py`
and `tools/parity_index.py` do not import that chain, so those ran fine under bare `python3`.

**Recommended follow-up (out of scope here, flagging per this ticket's own Recommended
Follow-Up section and investigation.md's Risks section) — confirmed live bug, not touched:**
`AttributePatch.apply` (`src/engine/patches.py:579-594`) clamps attribute values only on the
upper bound, and to **100** rather than the documented/`ATTRIBUTE_CAP` value of **99**
(`src/engine/rpg_depth.py:26`) — e.g. `strength=min(100, new_att.strength + u_att.strength_delta)`,
repeated for all nine attributes at `patches.py:585-593`. There is **no lower-bound clamp at all**
in this function — a sufficiently negative `AttributeUpdate` delta can drive any attribute to 0 or
negative through the real, authoritative apply path with nothing correcting it. A correct fix
already exists but is disconnected: `enforce_attribute_caps` (`src/engine/rpg_depth.py:31-44`)
correctly computes deltas to bring any attribute back into `[1, 99]`, and is already directly unit
tested (`tests/unit/core/test_rpg_depth.py:451-464`, `TestAttributeCaps`, including the
lower-bound case `AttributeComponent(strength=150, agility=0)` → `deltas["agility_delta"] == 1`).
But `enforce_attribute_caps` has **zero callers anywhere in `src/`** outside its own definition —
it is never invoked from `AttributePatch.apply`, the cleanup phase, or anywhere in the
authoritative pipeline; it is dead code from the live pipeline's perspective. A future hotfix-tier
ticket could wire `enforce_attribute_caps` into `AttributePatch.apply` (or an adjacent
cleanup-phase step) and fix the 100-vs-99 upper-bound off-by-one, to make the `docs/mechanics/
01_entity_anatomy.md` Section 1 law ("scale from 1 to 99") actually enforced end-to-end. This
ticket's own Out of Scope/Scope Guards sections explicitly forbid touching `src/engine/patches.py`
or `src/engine/rpg_depth.py`, so it was reported, not patched.

## Test Summary
- `pytest tests/unit/social/test_teach.py -k test_teach_resolves_target_capability_blocker_not_teacher -v` — 1 passed.
- `pytest tests/unit/resource/test_loot_channeling.py -k test_loot_corpse_completion_transfers_all_item_stacks -v` — 1 passed.
- `pytest tests/unit/core/test_rpg_math.py tests/unit/core/test_rpg_depth.py -v` — 64 passed, 0 failed (includes the 1 new SUB-051 test plus all pre-existing tests in both files, none modified).
- `grep -c CombatAspect docs/parity_ledger/substrate.yaml` — `0`.
- `tools/validate_frontmatter.py` — OK on `tickets/inprogress/TCK-20260902-PARITY-TEST-PATH-GAP.md`, `staging_artifacts/TCK-20260902-PARITY-TEST-PATH-GAP/` (3 files), and `docs/compliance/checklist.md`.
- No `src/` behavior changed; this is pure test authoring plus parity-ledger/docs metadata correction.
- **Test-phase retry disclosure (corrected — a prior draft of this section incorrectly claimed no
  wider run was needed):** the real Test phase DID run a wider scoped sweep
  (`tests/unit/core/ tests/unit/social/test_teach.py tests/unit/resource/test_loot_channeling.py
  tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_ledger_schema.py
  tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py`), and its first run
  found 1 failure: `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
  — a hardcoded `live_missing` baseline literal that this ticket's own 3 `test_path` repoints
  legitimately drove from 1320 down to 1317. This was resolved via a separate hotfix ticket,
  `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (already committed to this
  same branch, commit `2a1c1688`), not by editing anything in this ticket's own scope. Test phase
  was then re-run with the identical scoped command and passed clean: **323/323, 0 failed**.

## Files Changed
- `docs/parity_ledger/town_resource.yaml` — `TOWN-027` and `TOWN-076` `test_path` repointed (via `tools/parity_ledger_writer.py`, no other fields touched).
- `docs/parity_ledger/substrate.yaml` — `SUB-051` `test_path` set and `text`'s `CombatAspect` → `CombatComponent` corrected in one write (via `tools/parity_ledger_writer.py`).
- `tests/unit/core/test_rpg_math.py` — added new test `test_combat_stats_stay_within_bounds_after_normal_recalculation`.
- `docs/compliance/checklist.md` — updated `TEST:` citations on the `TOWN-027` (line 453) and `TOWN-076` (line 1830) rows.
- `tickets/inprogress/TCK-20260902-PARITY-TEST-PATH-GAP.md` — this ticket file (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary sections).
- `staging_artifacts/TCK-20260902-PARITY-TEST-PATH-GAP/plan.md` — added "Deviations" section (none from the 6 steps; execution-detail notes only).
- `staging_artifacts/TCK-20260902-PARITY-TEST-PATH-GAP/investigation.md` — pre-existing from this run's own Investigate phase, unmodified by this Implement pass (no rewrite needed).
- `staging_artifacts/TCK-20260902-PARITY-TEST-PATH-GAP/test_plan.md` — pre-existing from this run's own Plan phase, unmodified by this Implement pass.
- `agent-monitoring/tools.jsonl` — auto-updated by the monitoring hook on tool calls made this session (not hand-edited).

## Completion Summary
Resolved the `test_path: null` P0 schema violation on all three named parity ledger entries.
`TOWN-027` and `TOWN-076` were citation-only repoints to real, already-passing tests
(`tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher` and
`tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`)
confirmed by reading their full bodies against each entry's claimed behavior, not name-similarity.
`SUB-051` required a genuinely new unit test
(`tests/unit/core/test_rpg_math.py::test_combat_stats_stay_within_bounds_after_normal_recalculation`)
asserting `CombatComponent`/derived-stat numeric invariants across baseline, near-floor-agility, and
attribute-cap (99) cases, which then unblocked the `CombatAspect`→`CombatComponent` terminology fix
on the same entry that `TCK-20260902-ASPECT-TERM-CLEANUP` had been forced to defer. All three ledger
writes went through `tools/parity_ledger_writer.py` exclusively, each followed by a visible
`python3 tools/parity_index.py build`. `docs/compliance/checklist.md`'s two stale `TEST:` citations
(pointing at deleted pre-restructure test files) were corrected to match. No `src/` behavior was
changed. A confirmed, separate, pre-existing bug (`AttributePatch.apply`'s attribute clamp is
upper-bound-only, off-by-one at 100 vs. documented 99, with no lower bound, while a correct fix
`enforce_attribute_caps` sits unwired) was deliberately left untouched per scope guards and is
flagged above as a recommended follow-up ticket candidate.
