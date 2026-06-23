---
ticket_id: TCK-20260623-DEAD-CODE-REMOVAL
phase: investigation
date: 2026-06-23
revision: 2
---

# Investigation: D11 Audit Correction (TCK-20260623-DEAD-CODE-REMOVAL)

## Scope (Revised — doc-only, no src/ deletions)

The original D11 audit classified 9 `src/` directories as "zero importer" orphans
eligible for deletion. Import graph analysis in the prior run proved this classification
is incorrect for all directories: every directory has live production or test importers.

This ticket's scope is now **doc corrections and parity ledger updates only**. No
`src/` files will be deleted.

### What this ticket changes

1. `docs/audits/D11_dead_code.md` — add "Post-Audit Correction" section
2. `docs/plans/open_audit_findings_backlog.md` — Section 1E marked INVALID
3. `docs/guidelines/design_patterns.md` — remove dead `src/ai/states.py` references
4. `docs/parity_ledger/combat_movement.yaml` — COMB-093–099 → `legacy_verified`
5. `docs/parity_ledger/strategic_cognition.yaml` — STRAT-166–174 → `legacy_verified`
6. `docs/parity_ledger/social_narrative.yaml` — SOC-142 → `legacy_verified`

---

## Parity Ledger Entries — Confirmed State

All entries confirmed via direct YAML read (2026-06-23). The YAML files are
top-level lists (not `{entries: [...]}` dicts).

### combat_movement.yaml — COMB-093 through COMB-099

| ID | Current status | test_path |
|---|---|---|
| COMB-093 | verified | None |
| COMB-094 | verified | None |
| COMB-095 | verified | None |
| COMB-096 | verified | None |
| COMB-097 | verified | None |
| COMB-098 | verified | None |
| COMB-099 | verified | None |

All 7 entries have `v2_evidence: "Implementation proven via exhaustive checklist
audit Phase 1-11"` and `proof_type: null`. No named test functions exist in `tests/`
for any of these entries (grep confirmed zero matches for `test_ai_boredom_diversification`,
`test_boredom_modifier_applies_multipliers`, `test_life_stage_modifier_early_bracket`,
`test_motive_modifier_biases_explore`, `test_motive_modifier_biases_rest`,
`test_motive_modifier_biases_flee`, `test_goal_evaluator_uses_modifiers`).

**Action:** Set `status: legacy_verified` on all 7. Add `divergence_note` explaining
that the described behaviors live in the live `src/ai/score_modifiers.py` and
`src/ai/life_stage.py` (confirmed importers exist in production code), and that no
dedicated V2 unit tests cover these specific score-modifier behaviors.

### strategic_cognition.yaml — STRAT-166 through STRAT-174

| ID | Current status | test_path |
|---|---|---|
| STRAT-166 | verified | None |
| STRAT-167 | verified | None |
| STRAT-168 | verified | None |
| STRAT-169 | verified | None |
| STRAT-170 | verified | None |
| STRAT-171 | verified | None |
| STRAT-172 | verified | None |
| STRAT-173 | verified | None |
| STRAT-174 | verified | None |

All 9 entries have `test_path: null`. These cover trait-system behaviors
(trait definitions, assignment, stacking, unknown-trait handling, compatibility)
in `src/core/traits.py`. The association with `src/ai/` in the original D11 scope
was an artifact of the parity ID range, not a direct dependency.

**Action:** Set `status: legacy_verified` on all 9. Add `divergence_note` explaining
that `src/ai/personality.py` is live code (imported by
`src/systems/strategic_systems/intelligence.py`), no dedicated V2 test_path exists
for these trait-adjacent behaviors, and mapping to V2 trait tests is deferred.

### social_narrative.yaml — SOC-142

| ID | Current status | test_path |
|---|---|---|
| SOC-142 | verified | None |

Entry text: `` `test_bravery_modifiers`: bravery modifiers ``
`v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"`
`proof_type: null`

No test function named `test_bravery_modifiers` exists anywhere in `tests/`
(grep confirmed zero matches).

Note: `social_narrative.yaml` has a YAML parse error at line 2789 (a colon inside
an unquoted string value in a different entry). The SOC-142 entry itself at line
1502 is well-formed and safe to edit.

**Action:** Set `status: legacy_verified`. Add `divergence_note` explaining the same
rationale as COMB-093–099: behavior lives in live `src/ai/` code, no dedicated V2
test exists, and the "verified" claim was based on prose audit only.

---

## design_patterns.md — Dead References to src/ai/states.py

The file `src/ai/states.py` does not exist on disk. Confirmed by directory listing
of `src/ai/`: only `goals/__init__.py`, `goals/base.py`, `goals/scorers.py`,
`life_stage.py`, `personality.py`, `score_modifiers.py` are present.

### Lines referencing non-existent files

| Line | Content |
|---|---|
| 77 | `3. Add a \`StateHandler\` in \`ai/states.py\` for the new state.` |
| 203 | `## 5. AI State Machine — Strategy Pattern` (section heading) |
| 205 | `**Location:** \`src/ai/states.py\`` |
| 209 | Description of `StateHandler` subclass and `STATE_HANDLERS` dict |
| 211–219 | Code block showing `STATE_HANDLERS` dict (dead example) |
| 221–226 | "How to Add a New AI State" steps referencing `states.py` |
| 236 | Pattern Summary table row: `\| **Strategy** (State Handlers) \| \`ai/states.py\` \| ...` |
| 327 | File Map entry: `│   ├── brain.py              # AIBrain ...` (brain.py does not exist) |
| 328 | File Map entry: `│   ├── goal_evaluator.py     # Backward-compat shim` (does not exist) |

### What must be removed

- **Section 5 entirely** (lines 203–228 inclusive, from `## 5.` through the `---`
  separator): references only `src/ai/states.py` which does not exist.
- **Line 77**: the Step 3 instruction `Add a StateHandler in ai/states.py` must be
  removed or replaced with a note that this pattern is not currently implemented.
- **Section 6 Pattern Summary table row** (line 236): the `Strategy (State Handlers)`
  row references `ai/states.py` and must be removed.
- **Section 8 File Map** (lines 327–328): `brain.py` and `goal_evaluator.py` entries
  must be removed; `ai/goals/` entry (lines 329–333) is correct and stays.

### What must NOT be changed

Section 1 (`GoalScorer` plugin pattern) references `src/ai/goals/` — this directory
exists and is actively imported by live code. Section 1 is accurate and must not
be touched.

---

## D11 Audit Doc — Post-Audit Correction Section

File: `docs/audits/D11_dead_code.md`

The correction section must document:

1. **Claim being corrected:** The audit's "zero importer" characterization is
   incorrect for all 9 directories examined.

2. **Evidence per directory** (confirmed importers):
   - `src/ai/` — imported by `src/systems/strategic_systems/intelligence.py` (live AI)
   - `src/quests/` — top-level import in `src/engine/apply.py` (authoritative path)
   - `src/progression/` — top-level imports `LevelingService`, `VeterancyService`
     in `src/engine/apply.py`
   - `src/entities/` — top-level import in `src/worldassembly/entity_spawner.py`
   - `src/content_semantics/` — imported by 10+ live engine files; active infrastructure
   - `src/town/` — imported by `src/world/providers/requirements.py` + 8 test files
   - `src/actions/` — imported by 3 test files
   - `src/runtime/` — imported by 2 test files
   - `src/views/readiness.py` — imported by 1 test file

3. **Status correction:** audit status should read `corrected` (was `done`).

4. **Reference:** investigation findings in
   `stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md`.

---

## open_audit_findings_backlog.md — Section 1E

File: `docs/plans/open_audit_findings_backlog.md`

Section 1E currently contains the deletion plan for D11 orphan directories.
Replace the deletion plan with:

> **INVALID — All directories confirmed live (2026-06-23)**
> Investigation TCK-20260623-DEAD-CODE-REMOVAL proved every directory listed in D11
> has active production or test importers. No deletion is safe without a prior
> migration epic. See `stored_artifacts/TCK-20260623-DEAD-CODE-REMOVAL/investigation.md`
> for per-directory importer evidence.

---

## Risks and Blockers

None. All decisions were resolved in the prior run:

- No `src/` deletions → no regression risk
- Parity ledger changes are status-only (`verified` → `legacy_verified`) with
  `divergence_note` explaining the rationale
- design_patterns.md Section 5 removal is safe: the file it references (`states.py`)
  does not exist on disk; removing a dead reference cannot break any live code
- `social_narrative.yaml` parse error is in a different entry (line 2789); SOC-142
  (line 1502) is safely editable without touching the malformed region
