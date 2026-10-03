---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260902-ASPECT-TERM-CLEANUP
phase: done
date: 2026-09-02
tags: [documentation]
---

# TCK-20260902-ASPECT-TERM-CLEANUP

## Title
Fix remaining live doc references to the fictional Aspect model (IdentityAspect/MindAspect/CombatAspect) missed by TCK-20260902-ENTITIES-DOC-REWRITE

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
TCK-20260902-ENTITIES-DOC-REWRITE rewrote `docs/core/entities.md` to replace a fictional
"Aspect-Oriented Model" (`IdentityAspect`/`CombatAspect`/`MindAspect` — classes that do not exist
in the current codebase; the real architecture is the Component system in `src/core/state.py`,
e.g. `IdentityComponent`, `CombatComponent`, `StrategicComponent`) with accurate content. That
ticket's Document-Update phase found 4 more live, non-archived docs still using the same stale
terminology and correctly left them out of its own scope (different doc families/rigor, larger
blast radius). This ticket closes those 4 stragglers, plus one directly-tied parity-ledger entry
discovered during this ticket's own mandatory parity-ledger check.

## Scope
1. `docs/systems/strategic_cognition.md:71` — "Strategic state is stored in the `StrategicState`
   model within the `MindAspect`." → `MindAspect` becomes `StrategicComponent`
   (`src/core/strategic.py:382-416`), matching `docs/core/entities.md`'s Component Composition
   table.
2. `docs/architecture/macro_interest_constraints.md` — State Ownership Grid (§2) and its
   downstream prose references (§3, §4):
   - `IdentityAspect` (line 28) → `IdentityComponent`.
   - `MindAspect` (lines 29, 40, 48) → `StrategicComponent`.
   - This is a table + prose fix, not pure word-substitution: verify the exact current field
     paths behind "`life_directive`" and "`MindAspect.narrative.memory_log`" against
     `src/core/state.py` (`IdentityComponent`), `src/core/strategic.py` (`StrategicComponent`),
     and `src/core/cognition.py` (`CognitionModel`, which owns a `memory` sub-component per
     `docs/core/entities.md`'s component table) before finalizing the wording — the nesting
     (`.narrative.memory_log`) may now live under `cognition` rather than `strategic`. Do not
     guess; confirm against source before editing this line.
3. `docs/mechanics/damage_formula_contract.md:258` — regression-test table row "COMB-072 ...
   Wound penalties apply to `CombatAspect`" → `CombatComponent`. Confirmed during scoping: this
   is a pure terminology correction in a test-description cell; the damage formula, worked
   example, and Source Areas table above/around it require no change.
4. `docs/parity_ledger/combat_movement.yaml` — `COMB-072` entry's `text` field (currently "...
   reduce properties in CombatAspect..") → `CombatComponent`. Discovered during this ticket's
   mandatory parity-ledger check (triggered by item 3, a Mechanics Bible P0 chapter). Must be
   updated via `tools/parity_ledger_writer.py`, never a raw file edit (full-file YAML rewrites by
   hand risk corrupting this schema-validated ledger).
5. `docs/compliance/checklist.md` — confirmed a living/current tracking doc (`status: active`,
   not archived), so corrected in place, not preserved as history:
   - Line 738 (`SOC-052`): "Verify Entity and `IdentityAspect` absorb new fields." →
     `IdentityComponent`.
   - Line 1067 (`SUB-051`): "AOA Stabilization: Test `CombatAspect` invariants (formerly
     Stats)." → correct only the class-name reference to `CombatComponent`; preserve the "AOA
     Stabilization" phase label itself, since it names a real historical ticket/era
     (`TCK-20260330-CORE-STABILIZATION`), not a current-state architecture claim.
   - Line 1231 (`COMB-072`, the checklist's own mirrored copy of the parity-ledger row in item
     4): "Verify that wounds correctly reduce properties in `CombatAspect`." →
     `CombatComponent`.

## Out of Scope
- `docs/core/entities.md` and `docs/core/state.md` — already accurate (rewritten/verified by
  TCK-20260902-ENTITIES-DOC-REWRITE); reference only, do not edit.
- Any `src/` file — this is a documentation/parity-ledger terminology fix, not a code change.
- Any other "Aspect"-referencing string found elsewhere in `docs/parity_ledger/` during this
  ticket's scan but not named above — specifically `combat_movement.yaml` lines 815/836-837/847
  (`test_aspect_model_purity`, `test_mandatory_aspect_naming`, and a `model_fields`/"Aspects"
  mention) and `substrate.yaml` line 375 (`test_aspect_model_rebuild_integrity`). These appear to
  be literal historical test **function names**, not prose claims about current architecture —
  correcting them would require verifying/renaming actual test code in `src`/`tests`, which is
  out of this docs-only ticket's scope. See Related Tickets for a suggested follow-up.
- Any file under `tickets/done/` or `tickets/working_log.csv` referencing AOA/Aspect history
  (e.g. `TCK-20260330-AOA-COMPOSITION-COMPLETED`, `TCK-20260410-PH1-STG2-ASPECT-INTEGRATION`) —
  these are closed tickets recording real historical events and must not be altered.
- `docs/guidelines/intentional_divergences.md` — not touched; this is a terminology correction,
  not a behavior divergence, so no new divergence entry is warranted (verify this assumption
  still holds at implementation time; do not add an entry unless the source review in item 2/3
  above surfaces an actual behavior mismatch, not just a naming one).
- Re-litigating whether the Aspect model ever existed historically — `stored_artifacts/
  TCK-20260405-DOCS/investigation.md` (historical, `status: historical`) describes an April 2026
  "AOA Pivot" where an Aspect-Oriented Architecture effort was apparently underway at that time,
  referencing since-removed paths (`src/core/aspects/`, `src/core/entities/entity.py`). This
  ticket does not need to resolve whether that effort fully landed and was later reverted, or was
  abandoned mid-flight — TCK-20260902-ENTITIES-DOC-REWRITE already confirmed the *current* source
  of truth is the Component system in `src/core/state.py`, and that is the only fact this ticket
  depends on.

## Acceptance Criteria
- [x] `grep -rn "MindAspect\|IdentityAspect\|CombatAspect" docs/systems/strategic_cognition.md
  docs/architecture/macro_interest_constraints.md docs/mechanics/damage_formula_contract.md
  docs/compliance/checklist.md` returns zero matches after the fix.
- [x] `docs/parity_ledger/combat_movement.yaml`'s `COMB-072` entry `text` field no longer contains
  `CombatAspect`, and the file still validates against `docs/parity_ledger/schema.json` after
  being written via `tools/parity_ledger_writer.py` (not a raw edit).
- [x] `docs/architecture/macro_interest_constraints.md`'s State Ownership Grid and all three prose
  cross-references consistently use `IdentityComponent`/`StrategicComponent`, with the
  `life_directive` and `memory_log` field-path references verified against the actual field
  locations in `src/core/state.py` / `src/core/strategic.py` / `src/core/cognition.py` (not just
  a mechanical class-name swap).
- [x] `docs/mechanics/damage_formula_contract.md`'s worked formula example and Source Areas table are
  byte-identical to before except the single `CombatAspect` → `CombatComponent` terminology swap
  on the COMB-072 regression-test row.
- [x] `python3 tools/validate_frontmatter.py` (or the project's equivalent frontmatter check) passes
  on all 4 touched docs — frontmatter itself is unchanged, only body content.
- [x] `make knowledge-index-update` is run and `docs/REGISTRY.yaml` reflects the updated docs, per
  the project's After Work rule for any `docs/` change (registry regeneration itself deferred to
  Finalize's post-migration self-check per project convention; the knowledge-search index was
  incrementally rebuilt now, re-embedding the 4 changed docs).

## Related Tickets
- TCK-20260902-ENTITIES-DOC-REWRITE — parent/originating ticket; rewrote `docs/core/entities.md`
  and identified these 4 stragglers as explicitly out of its own scope.
- TCK-20260405-DOCS (`tickets/done/`, historical) — an earlier, unrelated "Documentation
  Out-of-Sync (AOA Pivot)" investigation from April 2026 covering different files
  (`architecture.md`, `entities_and_factions.md`, `ai_system.md`, `api_reference.md`, none of
  which are this ticket's 4 targets); surfaced here as historical context only, not overlapping
  in-flight work.
- Suggested follow-up (not filed by this ticket): a separate pass to verify whether the
  parity-ledger test-name references flagged in Out of Scope
  (`test_aspect_model_purity`, `test_mandatory_aspect_naming`,
  `test_aspect_model_rebuild_integrity`) still match real test function names in `tests/`, and
  correct them (with matching source renames) if they've drifted.

## Related Docs
- `docs/core/state.md` — canonical Component Composition Pattern description (reference only).
- `docs/core/entities.md` — canonical, already-corrected Component table (reference only).
- `docs/parity_ledger/combat_movement.yaml` — `COMB-072` entry, edited via `tools/
  parity_ledger_writer.py` as part of this ticket.
- `docs/parity_ledger/schema.json` — parity ledger entry schema, for validation.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/` (`investigation.md`, `plan.md`,
  `test_plan.md`) — prior investigation confirming Component system is the real architecture.
- `stored_artifacts/TCK-20260405-DOCS/investigation.md` (historical) — earlier AOA-pivot
  doc-sync investigation; different files, non-overlapping, informational only.

## Related Code Areas
- `src/core/strategic.py` (`StrategicComponent`, `state.py:382-416`) — read-only reference for
  correct terminology/field names.
- `src/core/state.py` (`IdentityComponent`, `CombatComponent`) — read-only reference for correct
  terminology/field names.
- `src/core/cognition.py` (`CognitionModel`) — read-only reference, to verify the
  `memory_log`/`narrative` field path for item 2's `macro_interest_constraints.md` fix.

## Assumptions / Open Questions
- Assumes `layer: guidelines` is the right single-value layer for a cross-doc terminology
  cleanup spanning `systems`, `architecture`, `mechanics`, and `compliance` doc families — none
  of the existing per-family layers (`systems`, `architecture`, `mechanics`, `compliance`) fit
  the ticket as a whole since the change touches all four; `guidelines` was specified in the
  originating request as the closest fit for a cross-cutting doc-process ticket. Flagged, not
  re-litigated, since it was explicitly directed.
- Assumes the exact current field path behind `macro_interest_constraints.md`'s
  "`MindAspect.narrative.memory_log`" (whether it now lives on `StrategicComponent` or on the
  separate `cognition` component's `CognitionModel.memory`) needs implementer-time source
  verification — this ticket does not resolve it in advance per the project's Uncertainty Rule
  ("vague leads stay vague until evidence narrows them").
- Assumes `docs/compliance/checklist.md`'s `COMB-072`/`SOC-052`/`SUB-051` row IDs are purely
  coincidentally identical in spelling to the parity-ledger IDs of the same name (both trace back
  to the same underlying regression tests) — if implementation finds they are meant to be kept
  in lockstep by tooling, the checklist and ledger edits should be verified consistent with each
  other, not just each individually correct.
- Assumes no `docs/guidelines/intentional_divergences.md` entry is needed, since nothing about
  actual behavior changes — only terminology. If item 2 or 3's source verification surfaces an
  actual mismatch between documented and implemented behavior (not just naming), that would be a
  new finding requiring its own follow-up ticket, not silently folded into this one.

## Implementation Notes
Implemented exactly the 5 scoped locations, no more:

1. `docs/systems/strategic_cognition.md:71` — `MindAspect` → `StrategicComponent`.
2. `docs/architecture/macro_interest_constraints.md` — State Ownership Grid (§2, lines 28-29) and
   two prose cross-references (§3 line 40, §4 line 48):
   - Line 28: `IdentityAspect` → `IdentityComponent` (mechanical class-name swap; content
     unchanged — no better-fitting owner exists in source for the row's `life_directive`/OCEAN
     wording, and this design doc reads as forward-looking/aspirational for the "Macro-Interest
     Redesign" rather than a literal 1:1 current-state mapping, consistent with
     `TCK-20260902-ENTITIES-DOC-REWRITE`'s finding that the Aspect naming itself is stale but this
     doc's non-Aspect content was out of that ticket's scope too).
   - Line 29: `MindAspect` → `StrategicComponent` (verified: `beliefs` dict field and `directives`
     dict both live directly on `StrategicComponent`, `src/core/strategic.py:390-400` — matches
     the row's "Active Motives, Perceptual Beliefs, and Current Goal selection" content, no
     further wording change needed).
   - Line 40 (§3): `MindAspect` → `StrategicComponent` (verified: `TurningPointState` /
     `turning_points` field lives on `StrategicComponent`, `src/core/strategic.py:399`, matching
     the "records a `TurningPoint`" claim).
   - Line 48 (§4, Memory Cap): did NOT do a mechanical word swap. Investigated source per the
     ticket's explicit flag: no `narrative`/`memory_log` field exists anywhere under
     `StrategicComponent`. `src/core/strategic.py`'s only capped list-like field is
     `turning_points` (`max_turning_points: int = 20`), which does not match the doc's stated cap
     of **50 entries**. `src/core/cognition.py`'s `MemoryModel.experience` (`ExperienceMemory`,
     `capacity: int = 50`) is the literal match for both the "50 entries" cap and the
     weighted-salience pruning language, and it is owned by `CognitionModel`
     (`src/core/cognition.py:319-336`, aggregated under the `cognition` component per
     `docs/core/entities.md`'s Component Composition table, not `strategic`). Corrected the line
     to `CognitionModel.memory.experience` (owned by the `cognition` component) rather than
     `StrategicComponent`, per the ticket's own hint that ".narrative.memory_log" may live under
     cognition. This is a doc-accuracy improvement beyond a pure terminology swap, but stays
     within item 2's explicit "not pure word-substitution... confirm against source" instruction.
3. `docs/mechanics/damage_formula_contract.md:258` — `CombatAspect` → `CombatComponent` on the
   COMB-072 regression-test table row only; the formula, worked example, and Source Areas table
   above/around it are untouched (verified via targeted `Edit` on the single line).
4. `docs/parity_ledger/combat_movement.yaml` — `COMB-072.text` field: `CombatAspect` →
   `CombatComponent`. Written exclusively via `tools/parity_ledger_writer.py`'s `write_entry()`
   (loaded the full existing entry via `yaml.safe_load`, mutated only the `text` field, called
   `write_entry("combat_movement.yaml", entry)`), never a raw `Edit` against the YAML. The writer
   validated the entry and rebuilt the derived parity SQLite index in-process. Resulting diff is a
   single-line change (`git diff --stat`: `1 file changed, 1 insertion(+), 1 deletion(-)`); all
   other COMB-072 fields (`status`, `priority`, `v2_evidence`, `test_path`, `proof_type`,
   `divergence_note`, `support_boundary`) are byte-identical to before.
5. `docs/compliance/checklist.md` — 3 in-place corrections, exactly as scoped:
   - Line 738 (SOC-052): `IdentityAspect` → `IdentityComponent`.
   - Line 1067 (SUB-051): `CombatAspect` → `CombatComponent`; the "AOA Stabilization" historical
     phase label was preserved verbatim (not touched), per the ticket's explicit instruction since
     it names the real historical `TCK-20260330-CORE-STABILIZATION` ticket/era.
   - Line 1231 (COMB-072 mirror row): `CombatAspect` → `CombatComponent`, matching the
     parity-ledger fix in item 4.

Confirmed the ticket's `## Assumptions` about the checklist row IDs held: `SOC-052`, `SUB-051`,
and `COMB-072` in `docs/compliance/checklist.md` are a manually-maintained mirrored list, not
tooling-synced to the parity ledger — no additional consistency mechanism needed beyond making
both individually correct.

No `docs/guidelines/intentional_divergences.md` entry was needed — source verification for items
2 and 3 surfaced only naming/ownership corrections, not an actual behavior mismatch between
documented and implemented mechanics. No `src/` file was touched. `docs/core/entities.md` and
`docs/core/state.md` were read only, for reference, never edited.

## Test Summary
- `python3 tools/validate_frontmatter.py <file>` run individually against all 4 touched docs
  (`docs/systems/strategic_cognition.md`, `docs/architecture/macro_interest_constraints.md`,
  `docs/mechanics/damage_formula_contract.md`, `docs/compliance/checklist.md`) — all 4:
  `OK: 1 file(s) checked — no violations`.
- `grep -n "MindAspect\|IdentityAspect\|CombatAspect" <all 4 docs>` — zero matches after the fix
  (confirmed via a combined `grep -n` invocation, exit code 1 / no output).
- `docs/parity_ledger/combat_movement.yaml`: `tools/parity_ledger_writer.validate_entry()` run
  directly against the post-write `COMB-072` entry — passes. Full-file `jsonschema.validate()`
  against `docs/parity_ledger/schema.json` surfaced one pre-existing violation (`COMB-007`,
  `test_path: null` on a `status: verified`/`priority: P0` entry) — confirmed via `git stash`
  that this violation exists identically on the pre-change file (unrelated to this ticket,
  consistent with the writer's own docstring noting 1320 pre-existing `missing_test_path` findings
  ledger-wide). `COMB-072` itself has no such issue.
- `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/docs/ -m "not slow" -q`
  → `45 passed, 1 skipped, 1 xfailed` (baseline sanity check, per ticket instructions).
- `.venv/bin/python3 -m pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py -q`
  → `59 passed` (direct coverage of the writer path used for item 4).
- `.venv/bin/python3 -m pytest tests/tools/test_parity_index_baseline.py -q` → `15 passed` — no
  baseline-count drift from the `COMB-072` text-only edit (this repo has a documented history of
  parity-ledger edits shifting `missing_test_path_count` baselines; confirmed not triggered here
  since `test_path` on `COMB-072` was not touched).
- `grep -rln` across `tests/` for references to the 4 touched docs or `COMB-072` found no test
  that asserts on the literal body text changed here (`tests/tools/test_cognition_strategy_skill_content.py`,
  `test_add_frontmatter_live.py`, `test_done_checker_static.py` reference either a different file
  — `docs/mechanics/04_strategic_cognition.md`, not `docs/systems/strategic_cognition.md` — or only
  frontmatter fields, not body content).
- `make knowledge-index-update` — `Incremental update complete: 10298 chunks total (4 files
  re-embedded, 3223 from cache, 0 deleted)`, matching the 4 edited docs.
- Note: `.venv/bin/python3` is not present inside this worktree checkout — resolved via the
  Makefile's own `PYTHON3` search order (`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`,
  the shared main-repo venv) for both the pytest runs above and `make knowledge-index-update`.

## Files Changed
- `docs/systems/strategic_cognition.md` (edited — item 1)
- `docs/architecture/macro_interest_constraints.md` (edited — item 2)
- `docs/mechanics/damage_formula_contract.md` (edited — item 3)
- `docs/compliance/checklist.md` (edited — item 5)
- `docs/parity_ledger/combat_movement.yaml` (edited via `tools/parity_ledger_writer.py` — item 4)
- `docs/parity_ledger/social_narrative.yaml` (Parity phase — `SOC-052.text` field's `IdentityAspect`
  reference corrected to `IdentityComponent`, mirroring `checklist.md`'s already-fixed row for the
  same entry ID; edited exclusively via `tools/parity_ledger_writer.py`)
- `tickets/inprogress/TCK-20260902-ASPECT-TERM-CLEANUP.md` (this ticket — Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `agent-monitoring/tools.jsonl` (auto-updated by the monitoring hook on tool calls this run; to
  be staged alongside the above at commit time per project convention)
- No `staging_artifacts/` were created or modified — hotfix tier does not require them, and none
  existed for this ticket.

## Completion Summary
Corrected all 5 scoped locations that still referenced the fictional Aspect-Oriented Model
(`IdentityAspect`/`MindAspect`/`CombatAspect`) to the real Component system
(`IdentityComponent`/`StrategicComponent`/`CombatComponent`, `src/core/state.py` and
`src/core/strategic.py`): `docs/systems/strategic_cognition.md`,
`docs/architecture/macro_interest_constraints.md` (including a source-verified field-ownership fix
remapping the "50-entry memory cap" line from `StrategicComponent` to `CognitionModel.memory.experience`,
since no matching field exists under `StrategicComponent`),
`docs/mechanics/damage_formula_contract.md`'s COMB-072 regression-test row,
`docs/compliance/checklist.md`'s three mirrored rows (preserving the historical "AOA
Stabilization" phase label), and `docs/parity_ledger/combat_movement.yaml`'s `COMB-072.text` field
(written exclusively via `tools/parity_ledger_writer.py`, never a raw edit). No source code,
formulas, or `docs/core/entities.md`/`state.md` were touched; this is a pure terminology and
doc-accuracy correction with no behavior change.

**Document-Update's independent verification** found two further parity-ledger entries mirroring
the exact same stale terminology as the `checklist.md` rows already fixed above: `SOC-052`
(`docs/parity_ledger/social_narrative.yaml`) and `SUB-051` (`docs/parity_ledger/substrate.yaml`).
The Parity phase fixed `SOC-052` via `tools/parity_ledger_writer.py` (text-only change, all other
fields byte-identical). **`SUB-051` remains unfixed** — `write_entry()` rejected it because the
entry already carries a pre-existing, unrelated schema violation (`status: verified`,
`priority: P0`, but `test_path: null`, which `schema.json`'s P0 rule forbids). Per this project's
Gate Integrity rule, the terminology fix was not force-written around that violation, and
`status`/`priority` were not altered to route around it. `docs/parity_ledger/substrate.yaml:548`
still reads `CombatAspect` as of this ticket's close. This is a genuine, disclosed, material gap —
not silently dropped — and is a separate pre-existing data-quality issue (a P0 entry missing its
required test_path) unrelated to this ticket's own scope; recommend a follow-up ticket to either
attach a real test to `SUB-051` or resolve its priority, after which the trivial terminology fix
can land in one line.
