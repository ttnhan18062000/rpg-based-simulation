---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-PARITY-TEST-PATH-GAP
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260902-PARITY-TEST-PATH-GAP

## Current Behavior

### TOWN-027 candidate repoint (`tests/unit/social/test_teach.py:117-134`)
`test_teach_resolves_target_capability_blocker_not_teacher` builds a teacher and a student, gives
the student a `BlockerState(id="c1", kind="capability", subject="STRIKE")`, establishes a trusting
bond, then calls `CoreActions.execute_train(teacher, {"skill_id": "STRIKE", "target_id": 2}, 5, [],
state)` and asserts `updates[2].strategic.blockers_remove == ["c1"]`. This directly proves
TOWN-027's claimed text — "learning a skill emits a strategic resolution for the corresponding
capability blocker" — the blocker removed is `kind="capability"` and removal is emitted as a
`strategic` update on the student (`updates[2]`), exactly matching the claim. Confirmed genuine,
not a name-similarity false match.

### TOWN-076 candidate repoint (`tests/unit/resource/test_loot_channeling.py:118-158`)
`test_loot_corpse_completion_transfers_all_item_stacks` builds a `CorpseState` with two distinct
`ItemStack`s, starts a loot action, advances `LootSystem.update` through the full channel duration,
then runs the final tick's `StateUpdate` through `AuthoritativeApplyPipeline.refine` and the
authoritative `ApplyPath.apply_generation`. It asserts both stacks transfer via
`resource_transfers[0].items_add`, the corpse is removed (`301 in refined.corpses_remove`, then
`301 not in state.corpses`), and both items land in the looter's inventory post-apply. This proves
TOWN-076's claim ("corpse loot convergence" — full item-stack transfer on corpse completion,
converging corpse removal + inventory credit through the authoritative pipeline). Confirmed
genuine.

### SUB-051 — no real coverage exists; real invariant-source code traced
`AttributeComponent` (`src/core/state.py:451-478`) is a frozen dataclass with nine plain `int`
attribute fields (default 5 each), no `__post_init__` validation of any kind — the class itself
enforces no range.

`CombatComponent` (`src/core/state.py:305-329`) is likewise a frozen dataclass with plain
`hp`/`max_hp`/`atk`/`def_stat`/`readiness`/etc. fields and no validation.

Derived-stat recalculation is `LevelingService.recalculate_combat_stats`
(`src/progression/leveling.py:76-186`, **not** `src/engine/rpg_depth.py` as the ticket's Related
Code Areas states — that file only re-exports/wraps it via `SkillScalingService.get_effective_stats`,
see below). Formulas (leveling.py:100-104): `max_hp = base_hp + vitality*2 + int(endurance*0.5)`,
`atk = base_atk + int(strength*0.5)`, `def_stat = base_def + int(vitality*0.3)`, `evasion =
base_evasion + agility*0.001`, `readiness_speed = max(1.0, 10.0 + (agility-5)*1.0)`. This function
returns `max_hp`, `atk`, `def_stat`, `evasion`, `range`, `move_cost`, `tactical_role`,
`readiness_speed` — it does **not** touch `hp` or `readiness` directly (both ticket text and Scope
item 3 loosely describe it as covering "hp...readiness" via this function; that's imprecise —
`hp`/`readiness` are separate `CombatComponent` fields set/clamped elsewhere, see below).

The real full-recalculation entry point used by the authoritative apply path is
`SkillScalingService.get_effective_stats` (`src/engine/rpg_depth.py:342-392`), which calls
`recalculate_combat_stats` then applies wound/scar penalties and an evasion clamp. Its own
docstring states the law: *"Law: Effective stats clamp to valid ranges (min 1 for atk/def, min 1
for HP)"* (`rpg_depth.py:360`). **The code only honors that law conditionally**:
`base_stats["atk"]`/`["def_stat"]`/`["max_hp"]` are floored to `max(1, ...)` only inside the
`if wounds:` / `if scars:` branches (`rpg_depth.py:379-387`); when an entity has no wounds and no
scars, `atk`/`def_stat`/`max_hp` are returned exactly as computed by `recalculate_combat_stats`
with **no floor applied at all**. Only `evasion` is unconditionally clamped (`max(0.0, min(0.95,
...))`, line 390).

Readiness itself (`CombatComponent.readiness`) is clamped in the apply path, not in the
recalculation: `src/engine/apply.py:128` (`min(100.0, comb.readiness + comb.readiness_speed)`) and
`:147` (`max(0.0, comb.readiness - 5.0)`). This one field's bound genuinely is enforced end-to-end.

**Attribute bound enforcement — confirmed live gap.** `AttributePatch.apply`
(`src/engine/patches.py:579-594`), the actual authoritative path an `AttributeUpdate` travels
through, clamps only the upper bound, and to **100**, not the documented cap of 99:
`strength=min(100, new_att.strength + u_att.strength_delta)` (repeated for all nine attributes,
lines 585-593). There is **no lower-bound clamp anywhere in this function** — a sufficiently
negative delta can drive any attribute to 0 or negative through the real apply path with nothing
correcting it.

A correctly-written clamp function already exists — `enforce_attribute_caps`
(`src/engine/rpg_depth.py:31-44`, using `ATTRIBUTE_CAP = 99` at line 26) — which computes deltas to
bring any attribute back into `[1, 99]` (`test_rpg_depth.py:451-464`'s `TestAttributeCaps` class
unit-tests this function directly, including the lower-bound case: `AttributeComponent(strength=150,
agility=0)` → `deltas["agility_delta"] == 1`). **But `enforce_attribute_caps` has zero callers
anywhere in `src/` outside its own definition** (`grep -rln enforce_attribute_caps src/` returns
only `rpg_depth.py` itself) — it is never invoked from `AttributePatch.apply`, the cleanup phase, or
anywhere in the authoritative pipeline. The function that would fully enforce the documented `[1,
99]` law exists but is dead code from the live pipeline's perspective.

Net effect for `AttributeComponent`: the [1, 99] range documented in
`docs/mechanics/01_entity_anatomy.md` Section 1 is enforced only partially and inconsistently by
live code — upper bound to 100 (off by one vs. the documented/`ATTRIBUTE_CAP` 99), no lower bound
at all. See Risks and Open Questions.

## Mechanics / Engine Constraints
- `docs/mechanics/01_entity_anatomy.md` Section 1 ("Core Attributes"): *"Every entity possesses
  nine core attributes that scale from **1 to 99**."* This is the textual source of the "1-99"
  invariant claim; it is accurate as documentation (matches `ATTRIBUTE_CAP = 99`) but is not fully
  enforced by the live apply path — see above.
- `docs/mechanics/01_entity_anatomy.md` Section 2 ("Derived Combat Stats") documents the exact
  formulas implemented in `LevelingService.recalculate_combat_stats` — `Max_HP`, `Attack`,
  `Defense`, `Evasion`, `Move_Cost` — verbatim-consistent with `leveling.py:100-155`. No invariant
  ("never negative", "clamped") language appears in this section of the doc itself; the "min 1"
  law is only stated in code (`rpg_depth.py:360` docstring), not in the Mechanics Bible.
- `docs/mechanics/02_combat_laws.md` documents minimum-damage (`>=1`), wound/scar thresholds, and
  readiness-speed floor (`floored at 1.0/tick`) laws but says nothing about attribute or base-stat
  numeric bounds directly — that invariant lives entirely in Chapter 1 and in code comments, not in
  Chapter 2.
- This ticket makes no behavior change, so no mechanics chapter's formulas or laws need editing;
  the new SUB-051 test must be consistent with the *documented* law (1-99, min-1 stats), not with
  whatever the code's partial/buggy enforcement currently does, when choosing what to assert for
  the in-scope "normal construction" case (see Test Plan).

## Docs Requiring Update
- `docs/compliance/checklist.md`: line 453 (`TOWN-027`) and line 1830 (`TOWN-076`) rows still cite
  pre-restructure test paths (`tests/unit/systems/test_routine_v2.py` and
  `tests/unit/economy/test_loot_scaling.py` respectively) that no longer exist in the repo; both
  rows' `TEST:` (and matching `SOURCE:`) comments must be updated to the real modern paths this
  ticket cites in the parity ledger (`tests/unit/social/test_teach.py` and
  `tests/unit/resource/test_loot_channeling.py`). The `SUB-051` row (line 1067) already reads
  `CombatComponent invariants` correctly and carries no `SOURCE:`/`TEST:` comment tag at all today
  — nothing to correct there terminology-wise, but once the new SUB-051 test exists it would be
  consistent (not currently required by schema/gates, but recommended) to add a `SOURCE:`/`TEST:`
  comment tag to that row mirroring its siblings (SUB-052/053/054 at lines 1068-1070, which also
  currently lack comment tags — this is a pre-existing pattern gap across all four sibling rows,
  not something this ticket introduces or is obligated to fix beyond SUB-051 itself).
- `docs/parity_ledger/substrate.yaml`: `SUB-051` entry (line 546) needs `test_path` set to the new
  test's real `file::function` and `text` corrected from `"...Test CombatAspect invariants
  (formerly Stats).."` to `"...Test CombatComponent invariants (formerly Stats).."` — via
  `tools/parity_ledger_writer.py`, not raw edit.
- `docs/parity_ledger/town_resource.yaml`: `TOWN-027` entry (line 303) and `TOWN-076` entry (line
  794) need `test_path` set to their confirmed real citations — via
  `tools/parity_ledger_writer.py`.

The `docs/mechanics/01_entity_anatomy.md` doc (path: `docs/mechanics/01_entity_anatomy.md`, under
`docs/`) does not need to change for this ticket: its "1 to 99" attribute-range claim and its
derived-stat formulas are already accurate as *documentation* of the intended law — the gap found
during this investigation (AttributePatch's missing lower-bound clamp and 99-vs-100 upper-bound
mismatch) is a code-vs-doc divergence in the *code*, not a doc inaccuracy, and this ticket is
explicitly forbidden from changing `src/` behavior (see Out of Scope in the ticket and Risks below).

The `docs/guidelines/intentional_divergences.md` doc (path: `docs/guidelines/intentional_divergences.md`)
is not required to change: this ticket adds test coverage and corrects stale citations only, with
no intentional behavior change, exactly as the ticket's own Out of Scope section states.

## Parity Ledger Overlap
- **SUB-051** (`docs/parity_ledger/substrate.yaml:546-556`) — `status: verified`, `priority: P0`,
  `test_path: null` (schema violation — P0 requires non-null `test_path` per `schema.json` lines
  68-78, and `verified` status separately requires it per lines 44-56). `text` still contains the
  stale `CombatAspect` string. No `divergence_note`/`support_boundary`. This is the entry requiring
  a genuinely new test (see Test Plan) — the only one of this ticket's three with no existing real
  coverage under any name.
- **TOWN-027** (`docs/parity_ledger/town_resource.yaml:303-314`) — same schema violation pattern
  (`verified`/P0, `test_path: null`). Confirmed real coverage exists at
  `tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher` —
  citation-only fix.
- **TOWN-076** (`docs/parity_ledger/town_resource.yaml:794-804`) — same schema violation pattern.
  Confirmed real coverage exists at
  `tests/unit/resource/test_loot_channeling.py::test_loot_corpse_completion_transfers_all_item_stacks`
  — citation-only fix. Note: `docs/compliance/checklist.md:1309` has an unrelated, differently-ID'd
  row (`COMB-090`) that also happens to use the string `test_corpse_loot_convergence` in its
  title — do not confuse this with `TOWN-076`; they are separate ledger IDs and this ticket touches
  only `TOWN-076`.

All three are P0 and currently in schema violation; fixing them is this ticket's entire reason to
exist. No other parity ledger entries are touched (see ticket's Out of Scope — the widespread
sibling pattern in `combat_movement.yaml`/`town_resource.yaml` is explicitly deferred).

## Prior Work
- `tickets/done/TCK-20260902-ASPECT-TERM-CLEANUP.md` — fixed the identical `CombatAspect` stale
  terminology pattern in `combat_movement.yaml`'s `COMB-072` entry, and explicitly named
  `SUB-051` as out of scope there because `tools/parity_ledger_writer.py`'s `validate_entry()`
  refuses any write to a P0 entry while `test_path` stays null — this ticket exists specifically to
  clear that blocker by writing the missing test first.
- `stored_artifacts/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE/` — landed
  `test_loot_corpse_completion_transfers_all_item_stacks`, confirmed above as the genuine TOWN-076
  citation.
- `stored_artifacts/TCK-20260831-TRUST-GATED-TEACHING/` — introduced
  `test_teach_resolves_target_capability_blocker_not_teacher` per that test's own docstring
  reference; confirmed above as the genuine TOWN-027 citation.
- `tests/unit/core/test_rpg_depth.py:451-464` (`TestAttributeCaps`) — closest existing analog to a
  "stats invariant" test, but it unit-tests the standalone `enforce_attribute_caps` helper function
  in isolation, not `CombatComponent`/derived-combat-stat invariants, and does not exercise the
  authoritative apply path at all. It does not satisfy SUB-051's claim and the ticket is correct
  that no existing test does.

## Risks and Open Questions
- **Confirmed real invariant gap, not just missing coverage (flagged per this ticket's own
  request).** `AttributePatch.apply` (`src/engine/patches.py:579-594`) clamps attribute upper
  bounds to 100 rather than the documented/`ATTRIBUTE_CAP` value of 99, and applies **no lower
  bound at all** — `enforce_attribute_caps` (`rpg_depth.py:31-44`), which would correctly enforce
  `[1, 99]`, is defined but never called anywhere in the live pipeline. Under **normal** attribute
  ranges (1-99, or even the off-by-one-tolerant 1-100 the code actually allows),
  `recalculate_combat_stats`'s `atk`/`def_stat`/`max_hp` formulas stay comfortably positive (e.g.
  minimum `atk = 10 + int(1*0.5) = 10`, minimum `def_stat = 5 + int(1*0.3) = 5`, minimum `max_hp =
  100 + 1*2 + int(1*0.5) = 102`), so a test scoped to the ticket's literal ask — "after **normal**
  state construction and derived-stat recalculation" (Scope item 3's own wording) — will pass. If
  the new test instead exercises adversarial/out-of-range attribute inputs (e.g. constructing
  `AttributeComponent(strength=-50)` directly, or driving an attribute negative via a real
  `AttributeUpdate`/`AttributePatch` delta), it would **legitimately fail**, correctly exposing this
  pre-existing gap. That gap is real but is a `src/` behavior fix, which this ticket's Out of Scope
  section explicitly forbids ("Any `src/` behavior change... this ticket does not change
  `CombatComponent`, `LevelingService`... logic"). **Recommendation for the planner**: scope the new
  SUB-051 test strictly to normal/in-range construction and typical level-up/recalculation flows
  (mirroring `test_rpg_math.py::test_stat_recalculation` and
  `test_rpg_depth.py::TestEffectiveStats` in style), so it passes against current code without
  requiring any src/ change, and separately flag the `AttributePatch`/`enforce_attribute_caps`
  wiring gap to the user as a candidate follow-up ticket (not filed by this investigation, per the
  project's "file tickets for workflow/behavior gaps rather than silently patch" convention) —
  **do not** let the SUB-051 test either (a) silently mask the gap by asserting something weaker
  than "invariant holds," or (b) fail the ticket by asserting the stricter/adversarial case and
  then getting "fixed" by loosening the assertion instead of being reported.
- The ticket's own Related Code Areas cites `src/engine/rpg_depth.py`
  (`LevelingService.recalculate_combat_stats`) — the method actually lives in
  `src/progression/leveling.py:76`; `rpg_depth.py` only calls it via
  `SkillScalingService.get_effective_stats`. Minor path inaccuracy for the planner/implementer to
  use the corrected location.
- TOWN-027/TOWN-076 repoints were confirmed by reading full test bodies in this investigation
  (matching the ticket's own instruction not to cite on name-similarity alone) — no open question
  remains on these two.

## Anti-Drift Hazards
- **Stay inside the 3 named entries.** The scan (both this investigation's and the ticket's own
  scoping pass) found the identical `test_path: null` + P0 schema-violation pattern on many more
  entries — `COMB-078`/`test_aspect_model_purity`, `COMB-079`/`test_mandatory_aspect_naming` in
  `combat_movement.yaml`, `SUB-035`/`test_aspect_model_rebuild_integrity` in `substrate.yaml`, and
  "dozens more" across `town_resource.yaml` per the ticket text. **Do not repoint, cite, or touch
  any of these while working this ticket** — they are explicitly Out of Scope and were already
  named as an "unfiled suggested follow-up" by the predecessor ticket
  (TCK-20260902-ASPECT-TERM-CLEANUP). Fixing them belongs to a future, separately-scoped ticket.
- **Do not fix the AttributePatch/`enforce_attribute_caps` wiring gap found above.** It's real, but
  it's a `src/` behavior change explicitly excluded by this ticket's Out of Scope; report it, don't
  patch it here even opportunistically "since we're already in the area."
- **Do not rename an existing unrelated test to fit the SUB-051 citation.** The ticket is explicit
  that this must be a genuinely new test, named naturally for what it asserts, not forced to match
  `test_stats_invariants` verbatim.
- **`docs/compliance/checklist.md:1309`'s `COMB-090` row** uses the same
  `test_corpse_loot_convergence` name string as `TOWN-076` but is a different ledger ID entirely —
  do not edit it while fixing TOWN-076; it is out of this ticket's scope.
- **Write path discipline**: all three parity ledger edits must go through
  `tools/parity_ledger_writer.py` (which enforces `validate_entry()` against `schema.json`), never
  raw `Read`/`Edit` on the YAML — consistent with the project's parity-ledger-safety pattern
  (`stored_artifacts/TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL/`) and the user's own standing
  guidance that ad-hoc full-file YAML rewrites on this ledger are a real corruption risk. Run
  `python3 tools/parity_index.py build` after each write.
