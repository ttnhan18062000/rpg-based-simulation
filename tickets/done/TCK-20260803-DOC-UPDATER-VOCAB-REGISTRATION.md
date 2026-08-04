---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION
phase: done
date: 2026-08-03
tags: [agent-monitoring, workflows, process-improvement]
---

# TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION

## Title
doc-updater Document-Update phase — monitoring vocabulary and glossary registration

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Second of three child tickets under `TCK-20260803-DOC-UPDATER-EPIC` (scope-only epic, tracking).
Note (corrected 2026-08-03 at Implement close): the sibling `TCK-20260803-DOC-UPDATER-CORE-WIRING`
referenced below as "in progress" throughout this ticket's original scoping text is now **DONE**
(closed 2026-08-03, moved to `tickets/done/`) — its phase/agent literals were already live in
`.claude/workflows/implement-ticket.js` by the time this ticket's Investigate/Plan artifacts ran,
and both were independently re-confirmed byte-for-byte before this ticket's Implement step edited
`vocabulary.py`.
Implements exactly sub-items 1, 2, and 4 of the design doc's (`docs/architecture/doc_updater_agent.md`)
"## Consequences" → "Monitoring/retro/dashboard registration" bullet: (1) registering the new
`Document-Update` phase and `doc-updater` agent literal in
`tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` dicts for the
`implement-ticket` workflow; (2) adding one new `category: "phase"` entry for `"Document-Update"` to
`registries/glossary_registry.jsonl`; (4) re-running (not modifying)
`tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced` to confirm
no divergence was introduced. Sub-item 3 (`dashboard-frontend/src/lib/phasePalette.ts` +
`phasePalette.test.ts`) is a separate, not-yet-created sibling child ticket. Sub-item 5
(`docs/agent-monitoring/schema.md`) needs no action — `vocabulary.py`'s own module docstring already
documents that file's prose tables as stale/non-authoritative and not read by any tooling.

**Hard dependency**: this ticket's changes are inert on their own. `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`
only gain meaning once the `Document-Update` phase and `doc-updater` agent actually exist and emit
real `pushEvent(...)` calls — that is entirely the sibling ticket `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s
scope (creating `.claude/agents/doc-updater.md` and wiring the phase into
`.claude/workflows/implement-ticket.js`). Landing this ticket before the sibling produces two
literals in `vocabulary.py`/`glossary_registry.jsonl` that nothing emits yet — harmless (the warn-only
check and drift report only ever *shrink* their false-positive surface by having them registered
early) but meaningless until the sibling lands. Landing the sibling before this ticket produces real
`Document-Update`/`doc-updater` events that render as unrecognized vocabulary drift in
`generate_retro.py`'s report and `validate.py`'s drift report until this ticket lands. Either
ordering is safe; neither ticket blocks the other's implementation, but both must land for the
combined behavior (real events, correctly recognized) to exist.

## Scope
1. `tools/agent-monitoring/vocabulary.py`: add the literal `"Document-Update"` to
   `WORKFLOW_PHASES["implement-ticket"]` (currently an 11-entry set: `Scope`, `Investigate`, `Plan`,
   `Review`, `Implement`, `Architecture-Verify`, `Test`, `Parity`, `Security-Review`, `Verify`,
   `Finalize`) and the literal `"doc-updater"` to `WORKFLOW_AGENTS["implement-ticket"]` (currently an
   11-entry set: `ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`, `implementer`,
   `test-scoper`, `parity-updater`, `security-reviewer`, `done-checker`, `finalizer`,
   `implement-ticket-orchestrator`). Both sets become 12 entries. No other module code changes —
   `record_events.py` (`from vocabulary import WORKFLOW_PHASES, infer_workflow, is_known_agent`),
   `validate.py` (`from vocabulary import CANONICAL_TIERS, WORKFLOW_PHASES, infer_workflow,
   is_known_agent`), and `generate_retro.py` (`from vocabulary import WORKFLOW_AGENTS,
   WORKFLOW_PHASES, infer_workflow`) all import the dicts directly and pick up the new literals with
   zero code changes on their side.
2. `registries/glossary_registry.jsonl`: append one new line via
   `python3 tools/glossary_registry.py add "Document-Update" --category phase --description "..."`
   (or a manually appended line matching the same JSON shape) — `category: "phase"`, `term:
   "Document-Update"`, one-sentence description matching the tone/length of the existing 11
   `implement-ticket` phase entries (e.g. the `"Parity"` entry: "Parity-updater agent updates the
   relevant docs/parity_ledger entry so documentation and source code stay in sync after a behavior
   change."). Description should describe what the phase does once the sibling ticket implements it:
   doc-updater agent updates the docs flagged by Investigate's `## Docs Requiring Update` section (or,
   for hotfix tier, judged against the ticket's own Scope), specializing documentation edits the way
   parity-updater specializes parity-ledger edits.
3. Re-run `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced`
   after the `vocabulary.py` edit and confirm it still passes unmodified — it is an object-identity
   assertion (`record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES` /
   `record_events.infer_workflow is validate.infer_workflow`), not a count-based assertion, so adding
   two literals to existing dict values cannot break it; this step exists to confirm that fact holds
   in practice, not to change the test.
4. Run the full `tests/tools/test_validate_agent_monitoring.py`,
   `tests/tools/test_record_events.py`, and `tests/tools/test_glossary_registry.py` suites (test-scoper
   to confirm exact scope at implementation time) to catch any other latent count-based assertion
   against `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` or `glossary_registry.jsonl`'s entry count.

## Out of Scope
- Creating `.claude/agents/doc-updater.md` or wiring the `Document-Update` `phase(...)` block into
  `.claude/workflows/implement-ticket.js` — entirely `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s scope
  (sibling ticket, already in progress).
- `dashboard-frontend/src/lib/phasePalette.ts` (`WorkflowPhase` union, `PHASE_FAMILY`,
  `PHASE_PALETTE` hex value) and `dashboard-frontend/src/test/phasePalette.test.ts`'s completeness
  assertion — separate, not-yet-created sibling child ticket 3 (dashboard phase-palette
  registration) per the epic.
- Any change to `docs/agent-monitoring/schema.md` — its prose tables are documented (in
  `vocabulary.py`'s own module docstring) as already-stale and not read by any tooling; sub-item 5
  of the design doc's Consequences bullet explicitly says no action is needed here.
- Any change to `docs/ai/workflows.md`'s phase table or `docs/ai/system_overview.md`'s hotfix
  pipeline summary — those are `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s deliverables (items 5 in its
  own Scope), not this ticket's.
- Adding a `doc-updater` agent-role glossary entry — not needed per the design doc's own analysis:
  `src/api/agent_ops_dashboard/ingest.py`'s `_load_agent_role_descriptions()` (~line 422) reads every
  `.claude/agents/*.md` file's own `description:` frontmatter directly at request time, so
  `doc-updater.md`'s frontmatter (written by the sibling ticket) is self-sufficient.
- Modifying `record_events.py`, `validate.py`, or `generate_retro.py` themselves — they already
  import `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` from `vocabulary.py` and need no code change to pick up
  the two new literals.
- Modifying `WORKFLOW_AGENT_PREFIXES` or `infer_workflow()` — the new agent/phase are fixed literals
  in an existing workflow, not a new workflow or a prefix-family case.
- Modifying `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced`
  itself — confirmed to be an object-identity check, expected to pass unchanged; only touch it if it
  unexpectedly fails.

## Acceptance Criteria
- [x] `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES["implement-ticket"]` contains
      `"Document-Update"` (12 entries total, up from 11) — verified by direct read of the file.
- [x] `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` contains
      `"doc-updater"` (12 entries total, up from 11) — verified by direct read of the file.
- [x] `registries/glossary_registry.jsonl` contains exactly one new line with
      `"category": "phase"` and `"term": "Document-Update"`, matching the existing entries' JSON key
      shape (`added_date`, `category`, `description`, `term`) — verified by
      `python3 tools/glossary_registry.py list` or direct grep of the file.
- [x] `pytest tests/tools/test_validate_agent_monitoring.py -k test_canonical_vocabulary_single_sourced`
      passes with the file unmodified.
- [x] `pytest tests/tools/test_glossary_registry.py` passes (covers `add_term`'s append-only /
      duplicate-rejection / category-validation behavior against the new entry).
- [x] `pytest tests/tools/test_record_events.py` passes (covers `warn_vocabulary_drift`'s use of the
      updated `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` sets).
- [x] No other file under `tools/agent-monitoring/`, `src/api/agent_ops_dashboard/`, or
      `dashboard-frontend/` is modified by this ticket — confirmed via `git diff --stat` at Verify
      time.

## Related Tickets
- TCK-20260803-DOC-UPDATER-EPIC (in progress, epic, parent) — scope-only epic tracking this and two
  sibling child tickets.
- TCK-20260803-DOC-UPDATER-CORE-WIRING (DONE, closed 2026-08-03, sibling/dependency) — created
  `.claude/agents/doc-updater.md` and wired the `Document-Update` phase into
  `.claude/workflows/implement-ticket.js`. Already landed by the time this ticket's Implement step
  ran; this ticket's registration makes `vocabulary.py`/`glossary_registry.jsonl` recognize the
  real `Document-Update`/`doc-updater` events that wiring now emits.
- (sibling, not yet created) Dashboard phase-palette registration child ticket —
  `dashboard-frontend/src/lib/phasePalette.ts` + `dashboard-frontend/src/test/phasePalette.test.ts`.
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT (done) — established `vocabulary.py` as the
  single source of truth and `test_canonical_vocabulary_single_sourced` as its identity guard; this
  ticket extends the vocabulary, not the guard mechanism.
- TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS (done) — authored the original 21 phase-glossary
  descriptions this ticket's new entry must match in tone/length.
- TCK-20260718-GLOSSARY-REGISTRY (done) — built `tools/glossary_registry.py`'s append-only
  `add_term()`/category-validation mechanism this ticket uses.

## Related Docs
- `docs/architecture/doc_updater_agent.md` — authoritative design doc; this ticket implements
  sub-items 1, 2, and 4 of its "## Consequences" → "Monitoring/retro/dashboard registration" bullet
  (sub-item 3 is the dashboard sibling ticket; sub-item 5 needs no action).
- `docs/agent-monitoring/schema.md` — read to confirm (per the design doc's own claim and
  `vocabulary.py`'s module docstring) that no update is needed here; its prose tables are documented
  as already-stale and not a source of truth for any tooling.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS/` — prior work establishing the phase
  glossary category's description style/tone this ticket's new entry must match.
- `stored_artifacts/TCK-20260718-GLOSSARY-REGISTRY/` — prior work building the
  `glossary_registry.jsonl` append-only mechanism this ticket uses unchanged.
- None found specifically covering `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` extension
  for a not-yet-implemented phase.

## Related Code Areas
- `tools/agent-monitoring/vocabulary.py` [modified — add `"Document-Update"` /
  `"doc-updater"` literals]
- `registries/glossary_registry.jsonl` [modified — one new `category: "phase"` line]
- `tests/tools/test_validate_agent_monitoring.py` [read/re-run only, not modified unless it
  unexpectedly fails]
- `tools/agent-monitoring/record_events.py` [read-only reference — confirms import/usage of
  `WORKFLOW_PHASES`/`is_known_agent`, no code change]
- `tools/agent-monitoring/validate.py` [read-only reference — confirms import/usage of
  `WORKFLOW_PHASES`/`is_known_agent`, no code change]
- `tools/agent-monitoring/generate_retro.py` [read-only reference — confirms import/usage of
  `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` for phase/agent normalization, no code change]

## Assumptions / Open Questions
- **This ticket's changes are meaningless/inert in isolation** until `TCK-20260803-DOC-UPDATER-CORE-WIRING`
  lands and the `Document-Update` phase / `doc-updater` agent actually emit `pushEvent(...)` calls —
  documented above in Request Summary and Related Tickets. Landing order between this ticket and the
  sibling is not constrained (either can land first; see Request Summary for the two safe-but-inert
  intermediate states).
- `layer: observability` chosen over `layer: ai` (used by the parent epic and sibling core-wiring
  ticket) because this ticket's actual file changes are entirely within
  `tools/agent-monitoring/`/`registries/glossary_registry.jsonl` — the registered `observability`
  layer's note ("Agent monitoring, dashboards, event bus, telemetry") is a more precise fit than
  `ai`'s ("Claude agent/orchestration tooling") for this specific ticket's scope, even though the
  parent epic used `ai` for its own broader scope.
- Tags (`agent-monitoring`, `workflows`, `process-improvement`) chosen from the already-registered
  set (`python3 tools/tag_registry.py list`); `documentation` (used by the epic and sibling
  core-wiring ticket) was deliberately not carried over here — this ticket touches no `docs/` prose,
  only `tools/`-tree Python and a `registries/*.jsonl` data file. No new tag registration needed.
- No `docs/parity_ledger/*.yaml` overlap found — grepped `docs/parity_ledger/` for
  `doc-updater`/`Document-Update`/`WORKFLOW_PHASES`/`glossary_registry` references; the only hits
  (`docs/parity_ledger/infrastructure.yaml` INFRA-289/290/291) cover the unrelated SQLite
  derived-index migration (`query.py`/`validate.py`/`generate_retro.py` read-path), not vocabulary
  registration. This is agent-orchestration tooling, not a simulation-mechanics change, so no ledger
  entry applies.
- Assumes the 11-entry counts for `WORKFLOW_PHASES["implement-ticket"]` and
  `WORKFLOW_AGENTS["implement-ticket"]` cited in this ticket (confirmed by direct read of
  `tools/agent-monitoring/vocabulary.py` on 2026-08-03 during scoping) have not drifted by
  implementation time — Investigate should re-confirm the current sets before editing, in case
  unrelated intervening work added or removed a literal.

## Implementation Notes
Followed `staging_artifacts/TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION/plan.md`'s 3 steps exactly,
no deviations.

**Step 1 (`tools/agent-monitoring/vocabulary.py` + `registries/glossary_registry.jsonl`, landed
together):** Re-confirmed the pre-edit 11-entry counts for both `WORKFLOW_PHASES["implement-ticket"]`
and `WORKFLOW_AGENTS["implement-ticket"]` by direct read (no intervening drift since scoping). Added
the literal `"Document-Update"` to `WORKFLOW_PHASES["implement-ticket"]` (line 23) and the literal
`"doc-updater"` to `WORKFLOW_AGENTS["implement-ticket"]` (line 42) — both sets now 12 entries. Ran
`python3 tools/glossary_registry.py add "Document-Update" --category phase --description "..."` (the
real CLI, not a hand-written JSON line) to append the matching `category: "phase"` glossary entry;
`added_date` (`2026-08-03`) and key-sorting were produced by the real `add_term()` code path. Ran the
Step 1 verify command immediately after both edits landed — all 69 tests in
`test_validate_agent_monitoring.py` + `test_record_events.py` + `test_glossary_registry.py` passed,
including `test_real_seeded_registry_covers_every_workflow_phase` (the test that hard-fails on
partial state) and `test_canonical_vocabulary_single_sourced` (unmodified, still an object-identity
check).

**Step 2 (`docs/parity_ledger/infrastructure.yaml`):** Confirmed `INFRA-315` was still the highest
existing ID (no intervening entry claimed 316). Appended `INFRA-316`, matching `INFRA-287`/
`INFRA-315`'s schema shape (`id`, `text`, `status: verified`, `priority: P2`,
`legacy_evidence: null`, `v2_evidence`, `proof_type: regression`,
`test_path: tests/tools/test_glossary_registry.py`, `divergence_note: null`, `support_boundary`).
`text`/`v2_evidence` explicitly frame this as a minimal, routine one-entry extension of the `phase`
glossary category `INFRA-287` established, not a second category-creation event; `INFRA-287`'s own
existing text was not touched. `v2_evidence` cites the actual post-edit line numbers
(`vocabulary.py:23`, `vocabulary.py:42`) and the new glossary line's `added_date`. Verified the YAML
parses cleanly (`yaml.safe_load`) and that `python3 tools/parity_index.py build --db-path <scratch>`
against a scratch DB path (never the real repo `parity-index/parity.db`) indexes the new entry with
zero health findings and `status: ok` (1947 total entries, `INFRA-316` present exactly once,
`entry_order: 320`).

**Step 3 (verification only, no files changed):** Re-ran the full Step 1 verify command — still 69
passed, no other latent count-based assertion broke. Also ran the plan's optional sibling spot-check
(`test_doc_updater_agent_file.py`, `test_document_update_phase_wiring.py`,
`test_workflow_meta_conformance.py`) — 23 passed, 1 pre-existing xfail (not a regression), confirming
no cross-ticket interaction with the already-landed `TCK-20260803-DOC-UPDATER-CORE-WIRING` sibling.

`git status`/`git diff --stat` confirmed this ticket's own edits touched exactly the three files the
plan scoped: `tools/agent-monitoring/vocabulary.py`, `registries/glossary_registry.jsonl`,
`docs/parity_ledger/infrastructure.yaml`. All other pending working-tree changes visible in
`git status` predate this session (already-uncommitted sibling-ticket work) and were left untouched.

Per the plan's Anti-Drift Notes, also corrected this ticket file's own Request Summary and Related
Tickets framing that described `TCK-20260803-DOC-UPDATER-CORE-WIRING` as still "in progress" — it is
DONE (closed 2026-08-03, in `tickets/done/`).

**Deviation, discovered at Test phase (see `plan.md`'s Deviations section for full detail):** a
second, separate vocabulary-declaration site exists at
`agent-orchestration/workflows/implement-ticket.yaml` (the provider-neutral orchestration contract),
"bootstrap-initialized once" from `vocabulary.py`'s sets per its own header comment and
`agent-orchestration/README.md`. Neither this ticket's nor `CORE-WIRING`'s Investigate phase
surfaced it — a genuine investigation gap. Step 1's `vocabulary.py` edit correctly caused
`tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` to fail (a real Test-gate
failure), since the contract file was never re-derived. Fixed with a narrow, additive, one-time
correction (matches the contract file's own explicitly stated design — "generated FROM it once,"
not an ongoing sync): added `Document-Update` to the contract's `phases:` list and `doc-updater` to
its `agents:` list, positioned/tiered to match the real `implement-ticket.js` behavior. No
`roles/*.yaml` file was added (confirmed no test or loader cross-references `agents:` membership
against role-file existence). This surfaced 4 further stale literal assertions in
`tests/agent_orchestration_claude_adapter/` — 2 direct, mechanical consequences of the contract edit
(a phase-count list and a `len() == 11→12` assertion), and 2 line-number staleness from
`CORE-WIRING`'s own earlier edit shifting `implement-ticket.js`'s later lines down (`1380,1392` →
real current `1450,1462`, confirmed via direct grep, not guessed). All 4 fixed as deterministic
literal corrections — no test logic weakened or altered. Files touched by this deviation:
`agent-orchestration/workflows/implement-ticket.yaml`,
`tests/agent_orchestration/test_contract_structure.py`,
`tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py`,
`tests/agent_orchestration_claude_adapter/test_generator_containment.py`,
`tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`,
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`. Full 124-test
suite across `tests/agent_orchestration/`, `tests/agent_orchestration_claude_adapter/`,
`tests/agent_orchestration_codex_adapter/` passes (193 combined with this ticket's own original
3-file scope, 69 tests).

## Test Summary
```
python3 -m pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_glossary_registry.py -v
```
69 passed (0 failed). Includes `test_real_seeded_registry_covers_every_workflow_phase`,
`test_canonical_vocabulary_single_sourced`, `test_real_seeded_registry_every_entry_has_non_blank_description`,
`test_real_seeded_registry_every_entry_has_valid_category`, `test_add_term_rejects_duplicate_term`,
`test_load_registry_raises_on_duplicate_term`, `test_vocabulary_warning_never_raises_or_exits` — all
named explicitly in the plan's Step 1 Verify section — all passed.

Optional sibling spot-check (`test_doc_updater_agent_file.py`,
`test_document_update_phase_wiring.py`, `test_workflow_meta_conformance.py`): 23 passed, 1 xfailed
(pre-existing expected xfail, not caused by this ticket's changes).

Parity-ledger YAML validated via `yaml.safe_load` (clean parse) and
`python3 tools/parity_index.py build --db-path <scratch>` (status `ok`, `INFRA-316` indexed with zero
health findings, run against a throwaway scratch DB path, never the real repo
`parity-index/parity.db`).

**Deviation-fix test run** (see Implementation Notes): first attempt at the full Test phase found
`tests/agent_orchestration/test_bootstrap_vocabulary_equality.py::test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`
failing (real, reproducible — `agent-orchestration/workflows/implement-ticket.yaml` never
re-derived after Step 1). After the deviation fix (contract YAML + 4 stale test literals corrected):
```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -q
```
**124 passed, 0 failed.** Combined with the original Step 1 3-file scope (69 passed):
```
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_glossary_registry.py tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -q
```
**193 passed, 0 failed** — independently re-confirmed by the orchestrator (not just self-reported).
Also re-ran the CORE-WIRING sibling spot-check (42 passed, 1 pre-existing xfail) to confirm no
cross-ticket regression — unchanged/still clean.

## Files Changed
- `tools/agent-monitoring/vocabulary.py` — added `"Document-Update"` to
  `WORKFLOW_PHASES["implement-ticket"]` and `"doc-updater"` to
  `WORKFLOW_AGENTS["implement-ticket"]`.
- `registries/glossary_registry.jsonl` — appended one new `category: "phase"`, `term:
  "Document-Update"` entry via `tools/glossary_registry.py add`.
- `docs/parity_ledger/infrastructure.yaml` — appended new `INFRA-316` entry.
- `tickets/inprogress/TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION.md` — this file (Status,
  Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion
  Summary, the CORE-WIRING "in progress" → "DONE" framing correction, and the deviation note).
- `agent-orchestration/workflows/implement-ticket.yaml` — **deviation, discovered at Test phase**:
  added `Document-Update` to `phases:` and `doc-updater` to `agents:`.
- `tests/agent_orchestration/test_contract_structure.py` — deviation: added
  `Document-Update` to `_EXPECTED_TIER_MATRIX`.
- `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` — deviation: renamed
  `test_live_phase_order_has_the_expected_11_phases` → `..._12_phases`, updated expected list.
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py` — deviation:
  `len(phase_order) == 11` → `== 12`.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` — deviation:
  `FINALIZE_INCOMPLETE` call-site line numbers `[1380, 1392]` → real current `[1450, 1462]`.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — deviation: same
  line-number correction.

## Completion Summary
Registered the `"Document-Update"` phase and `"doc-updater"` agent literals — already live in
`.claude/workflows/implement-ticket.js` since the sibling `TCK-20260803-DOC-UPDATER-CORE-WIRING`
landed — into `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`
dicts for the `implement-ticket` workflow, and added the matching `category: "phase"` glossary
entry `registries/glossary_registry.jsonl` requires to stay internally consistent
(`test_real_seeded_registry_covers_every_workflow_phase` hard-fails otherwise). Added a new
`INFRA-316` parity-ledger entry recording this as a routine one-entry extension of the `phase`
glossary category `INFRA-287` established. All 3 original plan steps completed with no deviation
from their own scope; a genuine investigation gap surfaced at Test time (a second vocabulary-
declaration site at `agent-orchestration/workflows/implement-ticket.yaml`, missed by both this
ticket's and the sibling CORE-WIRING ticket's Investigate phases), fixed as a narrow, deterministic,
additive correction plus 4 mechanically-derived stale-literal test fixes — documented in full in
`plan.md`'s Deviations section per CLAUDE.md's "never silently deviate" rule. Final state: all
scoped tests pass (69/69 core suite, 124/124 across the full agent-orchestration test surface after
the deviation fix — 193/193 combined — plus 42/43 CORE-WIRING sibling spot-check with 1 pre-existing
xfail); the 3 original
plan-scoped files plus the 6 deviation-fix files listed above are the complete Files Changed set —
no file beyond those was touched. This ticket's own registration was previously inert
(no matching phase/agent literal existed to register against); with the sibling already landed,
this closes the loop — `validate.py`'s drift report and `generate_retro.py` will now correctly
recognize real `Document-Update`/`doc-updater` events instead of flagging them as vocabulary
drift.
