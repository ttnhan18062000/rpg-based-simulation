---
ticket_id: TCK-20260626-FIX-DESIGN-PATTERNS
phase: plan
date: 2026-06-26
---

# Implementation Plan — TCK-20260626-FIX-DESIGN-PATTERNS

## Objective

Rewrite `docs/guidelines/design_patterns.md` from V1-only content to V2-primary content, archive V1
in a clearly-marked legacy section, add an anti-drift test, add a parity ledger entry, and
update the stale README blurb.

---

## Dependency Map

```
Step 1 (rewrite doc)
  └─► Step 2 (README blurb — references the doc by description)
  └─► Step 3 (anti-drift test — reads the doc; must pass after step 1 is done)
  └─► Step 4 (parity ledger entry — cites the rewritten doc as v2_evidence)

Step 3 (test file created)
  └─► Step 5 (knowledge-index-update — triggered by docs/ changes in steps 1, 2, 4)

Step 1 + Step 2 + Step 4 → Step 5 (make knowledge-index-update)
Step 1 through Step 5 → Step 6 (ticket update — records all files changed)
```

Steps 1–4 are independently writable but Step 3 should be verified after Step 1 is complete.
Step 5 must run after Steps 1, 2, and 4 are all done. Step 6 is always last.

---

## Scope Guards (What NOT to Touch)

- **No source code changes.** `src/` is read-only for this ticket. All changes are in `docs/`,
  `tests/docs/`, and `docs/parity_ledger/`.
- **Do not remove `src/ai/goals/`.** That is D11's scope.
- **Do not delete the V1 section.** Archive it inline under `## Legacy Patterns (V1 — do not use
  in new code)`.
- **Do not modify `docs/plans/open_audit_findings_backlog.md`**, `docs/audits/D11_dead_code.md`,
  or `docs/audits/D12_pattern_consistency.md` — those are historical audit records, not guidance
  docs.
- **Do not modify `docs/engine/manifest.json`.** `design_patterns.md` is not and should not be
  added to the manifest (it is a guidelines doc, not an engine contract).
- **Do not touch `docs/REGISTRY.yaml`** unless the doc's frontmatter fields (`layer`, `audience`,
  `authority`) change from their current values — they do not; the rewrite preserves the same
  frontmatter.
- **Do not alter any existing parity ledger entries.** Only append INFRA-220.

---

## Step 1 — Rewrite `docs/guidelines/design_patterns.md`

### Files changed
- `docs/guidelines/design_patterns.md` (full rewrite of body; frontmatter preserved verbatim)

### What to do

Preserve the existing frontmatter block exactly:
```yaml
---
status: active
layer: guidelines
authority: P1
audience: developer
---
```

Replace the entire body (everything after the frontmatter closing `---`) with the following
structure. Exact prose is at the implementer's discretion; the structure and all named symbols
below are mandatory.

#### Required document structure

```
# Design Patterns & Extension Guide

[One-paragraph intro: this doc describes V2 extension points. V1 patterns are archived below.]

---

## Overview

[Table: 4 V2 patterns, brief purpose, primary file(s)]

---

## Pattern 1 — Domain Phase Class

### When to use
### Structure
  - Signature: `XPhase.apply(state: AuthoritativeState, ...) -> StateUpdate`
  - Must not mutate AuthoritativeState
  - Wire into src/engine/pipeline.py
### Reference implementations (table: all 8 domain phases, file, typed return)
  Must include: AdventureDecisionPhase (src/domains/adventure/phase.py → StateUpdate)
               ProgressionPhase, CooperationPhase, CombatEngagementPhase,
               InformationPhase (partially typed), WorldEmergencePhase (P2 gap),
               PerceptionPhase (P2 gap), MemoryPhase (P2 gap)
### Engine constraints
  - Cite docs/engine/kernel.md (6-phase loop), governance_logic.md (should_run cadence)
  - Cite INFRA-206/207/208 (phase domain permissions in src/engine/phase_domain_permissions.py)
### How to add a new domain phase

---

## Pattern 2 — Decision/Mutation Separation via Typed Update Records

### When to use
### Structure
  - Domain phases return typed records; never write entity fields directly
  - ApplyPath in src/engine/apply.py is the only commit point
### Key types (table: StateUpdate, EntityUpdate, StrategicUpdate, StaminaUpdate,
                      NavigationUpdate, EquipmentUpdate, RejectionEvent — all in src/core/updates.py)
### Engine constraints
  - Cite docs/engine/authoritative_pipeline.md (17-phase, phases 13-17)
  - Cite docs/engine/authoritative_mutation_pipeline_contract.md
  - Cite INFRA-204 (AuthoritativeState does not import from src/engine/)
  - Cite compliance IDs PERF-017 and RES-202 on ApplyPath
### How to add a new update record

---

## Pattern 3 — Presenter / Read-Model Separation

### When to use
### Structure
  - All API responses shaped by presenters in src/api/presenters/
  - Presenters must not import AuthoritativeState outside TYPE_CHECKING
  - Methods are @staticmethod or @classmethod; return plain dicts or Pydantic models
### Key classes (table: StatePresenter, DecisionPresenter, ScenarioPresenter,
                       CampaignHistoryResponse/NarrativeLedgerEntryPresenter,
                       ReadModelService, ReadModelCache — with files)
### Engine constraints
  - Cite INFRA-210 (parity ledger)
  - Cite tests/architecture/test_api_read_model_guard.py (enforced at import level)
### How to add a new presenter

---

## Pattern 4 — Feature Pack Registration (Opportunity Extension)

### When to use
### Structure
  - Declare manifest.yaml under content/packs/<name>/
  - FeaturePackLoader loads packs filtered by RuntimeProfile.active_pack_names
  - FeatureRegistry.list_all() returns enum + pack-registered values
### Key classes/files
  - FeatureRegistry: src/domains/feature_packs/registry.py
  - FeaturePackLoader: src/domains/feature_packs/loader.py
  - Example pack: content/packs/demo_escort_pack/manifest.yaml (registers ESCORT_DIGNITARY)
### Engine constraints
  - Cite INFRA-PACK-001, INFRA-PACK-002, INFRA-PACK-003
### How to add a new feature pack

---

## Pattern 5 — Combat Extension (Strategy Pattern, Partially Live)

[Short section — DamageCalculator in src/actions/damage.py is partially live via the
actions layer. Not a primary V2 extension point but documented to avoid confusion.
Kept brief: what it is, where it lives, when to use vs. when to use Domain Phase instead.]

---

## Legacy Patterns (V1 — do not use in new code)

> **Historical archive.** The patterns below were used in V1 and are preserved here because
> the source files (`src/ai/goals/`, `src/core/entity_builder.py`) still exist for compliance
> reasons. They are not exercised by the V2 tick path. Do not add new code following these patterns.
> See `docs/plans/open_audit_findings_backlog.md` §2 for the D11/D12 findings that deprecated them.

### V1 Pattern A — Goal Evaluation (GoalScorer Plugin)
[Retain existing §1 content verbatim or condensed: GoalScorer, GoalEvaluator, GOAL_REGISTRY,
src/ai/goals/ — clearly noted as deprecated]

### V1 Pattern B — Entity Construction (EntityBuilder)
[Retain §3 content verbatim or condensed: EntityBuilder, src/core/entity_builder.py — clearly noted;
WorldAssemblyResolver is the V2 equivalent]

### V1 Pattern C — Trait Aggregation (UtilityBonus)
[Retain §4 content verbatim or condensed: UtilityBonus, TraitStatModifiers — clearly noted as
V1 goal-scoring scaffolding; UtilityBonus is mypy-excluded]
```

### Mandatory content requirements (acceptance-mapped)

| Requirement | Acceptance criterion it satisfies |
|---|---|
| `GoalScorer`, `GoalEvaluator`, `GOAL_REGISTRY`, `src/ai/goals/` appear ONLY under `## Legacy Patterns` | AC: V1 no longer primary extension model |
| At least 3 V2 patterns documented with real class names and file paths | AC: ≥3 V2 patterns |
| `## Legacy Patterns (V1 — do not use in new code)` header present | AC: V1 section clearly marked |
| `Domain Phase`, `StateUpdate`, `StatePresenter` terms present in primary sections | test_v2_extension_patterns_documented |
| `src/domains/`, `src/core/updates.py`, `src/api/presenters/` cited in primary sections | test_v2_file_paths_cited |
| All `` `src/*.py` `` paths cited in backticks exist on disk | test_no_broken_src_links_in_doc |
| Frontmatter preserved: `status: active`, `layer: guidelines`, `authority: P1`, `audience: developer` | test_add_frontmatter_live.py |
| Section numbering is clean (no §5-to-§7 jump) | Investigation §6 |

### Verification command
```bash
pytest tests/docs/test_design_patterns_currency.py -v
pytest tests/tools/test_add_frontmatter_live.py -v -k "design_patterns"
```

---

## Step 2 — Update `docs/guidelines/README.md` stale blurb

### Files changed
- `docs/guidelines/README.md` (line 14 only)

### What to do

Current line 14:
```
- **[Design Patterns](design_patterns.md)**: Architectural spines (Aspects, Systems, Presenters).
```

Replace with a description that accurately reflects V2 content. Target phrasing (exact wording
may vary; meaning must match):
```
- **[Design Patterns](design_patterns.md)**: V2 extension patterns — Domain Phase, typed update records, presenter/read-model layer, and feature pack registration.
```

The blurb must not mention "Aspects" or "GoalScorer" — those are V1 terms that no longer appear
in the primary doc.

### Dependency
Depends on Step 1 (must know final doc structure to write an accurate blurb).

### Verification
Read the file and confirm line 14 no longer says "Architectural spines (Aspects, Systems, Presenters)."

---

## Step 3 — Add `tests/docs/test_design_patterns_currency.py`

### Files changed
- `tests/docs/test_design_patterns_currency.py` (new file)

### What to do

Create the file with exactly the five test functions from `test_plan.md §2.1`:

| Test function | What it asserts |
|---|---|
| `test_v1_symbols_not_in_primary_sections` | `GoalScorer`, `GoalEvaluator`, `GOAL_REGISTRY`, `src/ai/goals/` absent before the `Legacy Patterns` header |
| `test_v2_extension_patterns_documented` | `Domain Phase`, `StateUpdate`, `StatePresenter` all present in content |
| `test_v2_file_paths_cited` | `src/domains/`, `src/core/updates.py`, `src/api/presenters/` all present in content |
| `test_legacy_section_clearly_marked` | `Legacy Patterns` header present AND V1 symbols appear in the section after it |
| `test_no_broken_src_links_in_doc` | All `` `src/*.py` `` backtick-quoted paths exist on disk via `os.path.exists()` |

The test file uses `DOC_PATH = "docs/guidelines/design_patterns.md"` (relative path — tests must be
run from the repo root, which is standard for this project).

### Dependency
Step 3 can be written concurrently with Step 1, but must be verified (pytest run) only after
Step 1 is complete.

### Verification command
```bash
pytest tests/docs/test_design_patterns_currency.py -v
```

All five tests must pass (PASSED, not xfail or skip).

---

## Step 4 — Add INFRA-220 to `docs/parity_ledger/infrastructure.yaml`

### Files changed
- `docs/parity_ledger/infrastructure.yaml` (append after INFRA-219 block, before INFRA-PACK-001)

### What to do

Insert the following YAML block between the end of the INFRA-219 entry (after its `support_boundary:
null` line, around file line 2533) and the start of INFRA-PACK-001 (currently line 2535). The
format matches adjacent INFRA-21x entries exactly.

```yaml
- id: INFRA-220
  text: >
    docs/guidelines/design_patterns.md documents V2 extension patterns (Domain Phase
    class, typed update records via src/core/updates.py, presenter/read-model layer
    via src/api/presenters/, feature pack registration) as the authoritative extension
    model for new code. V1 patterns (GoalScorer, src/ai/goals/) are archived in a
    clearly-marked Legacy section and not presented as active extension points.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    docs/guidelines/design_patterns.md (rewritten TCK-20260626-FIX-DESIGN-PATTERNS)
  proof_type: null
  test_path: tests/docs/test_design_patterns_currency.py
  divergence_note: null
  support_boundary: "Doc tooling only — no simulation behavior involved."
```

### Format constraints
- Use the block scalar style (`>`) for `text` and `v2_evidence` — consistent with INFRA-TYPE-001.
- `null` for `legacy_evidence`, `proof_type`, `divergence_note`.
- `support_boundary` as a quoted string (matches INFRA-219 style).

### Dependency
Independent of Steps 1–3; can be done concurrently. Does not depend on Step 3 existing, but
the `test_path` field must match the file created in Step 3.

### Verification
```bash
python3 -c "import yaml; entries = yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml')); ids = [e['id'] for e in entries]; assert 'INFRA-220' in ids, 'INFRA-220 missing'; print('INFRA-220 present')"
```

---

## Step 5 — Run `make knowledge-index-update`

### Files changed
- None directly (updates search index artifacts under `graphify-out/` or knowledge index store)

### What to do

```bash
make knowledge-index-update
```

This is required because Steps 1, 2, and 4 all modify files under `docs/`. Per CLAUDE.md:
"If any files under `docs/` were created or modified: run `make knowledge-index-update` to keep
the agent context search index current."

### Dependency
Must run after Steps 1, 2, and 4 are complete (all docs/ changes must be finalized first).

### Verification
Command exits 0. If the command fails or is unavailable, record the failure in the ticket
Implementation Notes — do not block the commit.

---

## Step 6 — Update ticket Implementation Notes

### Files changed
- `tickets/inprogress/TCK-20260626-FIX-DESIGN-PATTERNS.md`

### What to do

Fill in the following ticket sections with actuals:

**Implementation Notes** — summarize the decisions made:
- V1 archive approach chosen (inline `## Legacy Patterns` section)
- DamageCalculator documented as Pattern 5 (secondary / partially-live), not primary tier-1
- Section numbering: 5 primary patterns + 1 legacy archive section (clean numbering)
- Frontmatter preserved unchanged
- `docs/REGISTRY.yaml` not modified (frontmatter fields unchanged)

**Test Summary** — list the 5 new test functions and which passing commands were run.

**Files Changed** — list all files modified/created:
- `docs/guidelines/design_patterns.md` (rewritten)
- `docs/guidelines/README.md` (line 14 updated)
- `tests/docs/test_design_patterns_currency.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-220 appended)

**Completion Summary** — one paragraph confirming all acceptance criteria met.

### Dependency
Must be the final step (after all changes are verified).

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Step(s) |
|---|---|
| `design_patterns.md` no longer presents `GoalScorer`, `src/ai/goals/`, or `GOAL_REGISTRY` as the primary extension model | Step 1 (doc rewrite) + Step 3 (test_v1_symbols_not_in_primary_sections) |
| At least 3 V2 extension patterns documented with real class names and file paths | Step 1 (Patterns 1–4) + Step 3 (test_v2_extension_patterns_documented, test_v2_file_paths_cited) |
| V1 section retained but clearly marked as legacy/historical | Step 1 (`## Legacy Patterns (V1 — do not use in new code)` section) + Step 3 (test_legacy_section_clearly_marked) |
| `tests/docs/test_doc_integrity.py` passes (no broken links) | Step 3 implicitly; Step 1 must not introduce broken src/ links (test_no_broken_src_links_in_doc enforces this) |
| Parity ledger entry in `infrastructure.yaml` references this doc | Step 4 (INFRA-220) |
| README.md blurb is no longer V1-era | Step 2 |
| Knowledge search index current | Step 5 |
| Ticket complete and moved to done/ | Step 6 (precondition for finalize phase) |

---

## Unresolved Questions

None. All open questions from the ticket were resolved during investigation:

| Question | Resolution |
|---|---|
| Archive inline vs. remove V1 section? | Archive inline under `## Legacy Patterns (V1 — do not use in new code)` — files still exist, compliance IDs reference them (investigation §6) |
| Which V2 patterns to document? | Four primary: Domain Phase, Decision/Mutation Separation, Presenter/Read-Model, Feature Pack. Plus DamageCalculator as a secondary Pattern 5. (investigation §2) |
| Does DamageCalculator belong as a primary V2 pattern? | No — secondary section only; it is partially live but not the V2 extension model for new domain logic (investigation §6) |
| Does `docs/REGISTRY.yaml` need updating? | No — frontmatter fields (`layer`, `audience`, `authority`) are unchanged (verified in step 1 scope guard) |
