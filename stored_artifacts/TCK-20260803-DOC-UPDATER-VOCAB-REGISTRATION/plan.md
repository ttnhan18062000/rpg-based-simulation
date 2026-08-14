---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION
artifact_type: plan
tags: [agent-monitoring, workflows, process-improvement]
---

# Implementation Plan — TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION

## Summary

This ticket registers two already-live literal strings — `"Document-Update"` (phase) and
`"doc-updater"` (agent) — into `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/
`WORKFLOW_AGENTS["implement-ticket"]` sets, and adds the matching `category: "phase"` glossary
entry these two dicts require to stay internally consistent. The sibling ticket
`TCK-20260803-DOC-UPDATER-CORE-WIRING` has **already landed** (status: DONE, closed 2026-08-03) and
confirmed both literals exact byte-for-byte against the live `.claude/workflows/implement-ticket.js`
call sites (`phase()` at line 779, `writeSidecar`/`pushEvent` at 814/832-837, `agentType` at 829).
The ticket file's own Request Summary and Related Tickets sections still describe CORE-WIRING as "in
progress" / "already in progress" — this is now stale; Implement should correct that framing when it
updates the ticket file's Implementation Notes, but it is not itself part of this plan's steps (no
code or registry change results from it).

The investigation surfaced a real, previously-unnamed hard-failure coupling:
`test_glossary_registry.py::test_real_seeded_registry_covers_every_workflow_phase` iterates the live
`WORKFLOW_PHASES` dict and asserts every phase has a matching glossary entry — so the `vocabulary.py`
edit and the `glossary_registry.jsonl` append must land together, verified by the same test run,
before either is considered done. This plan sequences them as one combined step (Step 1) rather than
two separate ones for that reason. It also resolves the flagged parity-ledger open question:
`docs/parity_ledger/infrastructure.yaml` already tracks this exact class of tooling change
(`INFRA-281`, `INFRA-287`, `INFRA-289`–`INFRA-291`, `INFRA-302`), and `INFRA-287` is a direct
structural precedent (added the `phase` glossary category + its first 21 entries). This plan adds a
new minimal `INFRA-316` entry for consistency with that precedent, scoped narrowly to acknowledge
this is a routine one-entry extension of an already-established mechanism, not a second
category-creation event.

## Steps

### Step 1 — Register the phase/agent literals and the matching glossary entry together
**Files:** `tools/agent-monitoring/vocabulary.py`, `registries/glossary_registry.jsonl`
**Change:**
1. In `tools/agent-monitoring/vocabulary.py`, add the literal `"Document-Update"` to the
   `WORKFLOW_PHASES["implement-ticket"]` set (currently 11 entries: `Scope`, `Investigate`, `Plan`,
   `Review`, `Implement`, `Architecture-Verify`, `Test`, `Parity`, `Security-Review`, `Verify`,
   `Finalize` — becomes 12). Add the literal `"doc-updater"` to the
   `WORKFLOW_AGENTS["implement-ticket"]` set (currently 11 entries: `ticket-scoper`, `investigator`,
   `planner`, `architecture-reviewer`, `implementer`, `test-scoper`, `parity-updater`,
   `security-reviewer`, `done-checker`, `finalizer`, `implement-ticket-orchestrator` — becomes 12).
   Re-confirm the current 11-entry counts by direct read before editing, per the investigation's own
   caveat that intervening drift is possible (none was found as of 2026-08-03, but Implement should
   re-check).
2. In the same commit/step, append one new line to `registries/glossary_registry.jsonl` via:
   ```
   python3 tools/glossary_registry.py add "Document-Update" --category phase --description "Doc-updater agent updates the docs flagged by Investigate's ## Docs Requiring Update section (or, for hotfix tier, judged against the ticket's own Scope), specializing documentation edits the way parity-updater specializes parity-ledger edits."
   ```
   (Description text may be lightly adjusted for exact phrasing but must match the `Parity`-entry's
   tone/length — agent-first, one sentence, ends on effect/purpose. Use the CLI, not a hand-written
   JSON line, so `added_date` and key-sorting are produced by the real `add_term()` code path.)
**Do NOT touch:** `WORKFLOW_AGENT_PREFIXES`, `infer_workflow()`, any other `WORKFLOW_PHASES`/
`WORKFLOW_AGENTS` workflow key besides `implement-ticket`, any existing line in
`glossary_registry.jsonl` (append-only — do not edit or reorder existing entries),
`record_events.py`, `validate.py`, `generate_retro.py` (all three import the dicts by reference, zero
code change needed), `.claude/agents/doc-updater.md`, `.claude/workflows/implement-ticket.js`,
`docs/agent-monitoring/schema.md`, or any `dashboard-frontend/` file.
**Verify:**
```
python3 -m pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_glossary_registry.py -v
```
Specifically confirm `test_glossary_registry.py::test_real_seeded_registry_covers_every_workflow_phase`
passes (this is the test that hard-fails if the two edits are not both present), plus
`test_canonical_vocabulary_single_sourced`, `test_real_seeded_registry_every_entry_has_non_blank_description`,
`test_real_seeded_registry_every_entry_has_valid_category`, `test_add_term_rejects_duplicate_term`,
`test_load_registry_raises_on_duplicate_term`, and `test_vocabulary_warning_never_raises_or_exits`.

### Step 2 — Add a minimal parity-ledger entry for the vocabulary/glossary extension
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry, `id: INFRA-316` (next available ID — confirmed highest existing ID
as of this plan is `INFRA-315`; Implement should re-confirm no intervening entry claimed 316 before
writing). Shape, matching the existing entry schema (`id`, `text`, `status`, `priority`,
`legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`, `support_boundary`):
- `text`: describes `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION` adding `"Document-Update"` to
  `WORKFLOW_PHASES["implement-ticket"]`, `"doc-updater"` to `WORKFLOW_AGENTS["implement-ticket"]`,
  and one new `category: "phase"` glossary entry — explicitly notes this is a routine one-entry
  extension of the `phase` glossary category `INFRA-287` established (not a second category-creation
  event, no dashboard wiring change, no new `GLOSSARY_CATEGORIES` member).
- `status: verified`, `priority: P2`, `legacy_evidence: null`.
- `v2_evidence`: cite `tools/agent-monitoring/vocabulary.py`'s two edited set literals and the new
  `registries/glossary_registry.jsonl` line (with its `added_date` stamp) once Step 1 lands —
  Implement fills in exact line numbers after editing.
- `proof_type: regression`, `test_path: tests/tools/test_glossary_registry.py`.
- `divergence_note: null`.
- `support_boundary`: state this is agent-orchestration/monitoring-pipeline tooling only, no
  simulation behavior involved, no `src/` file touched — matching the phrasing pattern used by
  `INFRA-315`'s `support_boundary`.
**Do NOT touch:** any existing `INFRA-*` entry (append-only ledger; do not renumber or edit
`INFRA-287`, `INFRA-289`–`INFRA-291`, `INFRA-302`, or any other entry). Do not touch any other
`docs/parity_ledger/*.yaml` file (`substrate.yaml`, `combat_movement.yaml`, etc.) — this change is
`infrastructure.yaml`-only, per the investigation's grep confirming zero other-file overlap.
**Verify:** `python3 tools/parity_index.py build --db <scratch-path>` (or equivalent parity-index
validation script, if one exists in this repo's tooling) against a scratch DB path, never the real
repo `parity-index/parity.db` — confirm the new YAML entry parses without schema error. If no
dedicated parity-ledger schema-validation script is found at implementation time, a direct
`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` parse
check is the minimum bar.

### Step 3 — Confirm no other latent count-based assertion broke
**Files:** none changed — verification-only step.
**Change:** None. Re-run the full scoped test command from the ticket's Scope item 4 / test_plan.md's
Scoped Pytest Commands to catch any other latent count-based assertion against
`WORKFLOW_PHASES`/`WORKFLOW_AGENTS` or `glossary_registry.jsonl`'s entry count that wasn't already
covered by Step 1's verification.
**Do NOT touch:** Any file. This step is pure confirmation; if it fails, the failure belongs to
whichever file it names, and Implement resolves it as a targeted fix within this ticket's already-
defined scope (do not expand scope to fix an unrelated failure).
**Verify:**
```
python3 -m pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_glossary_registry.py -v
```
Optional spot-check (sibling's own regression surface, confirms no cross-ticket interaction):
```
python3 -m pytest tests/tools/test_doc_updater_agent_file.py tests/tools/test_document_update_phase_wiring.py tests/tools/test_workflow_meta_conformance.py -v
```

## Scope Guards

Explicitly out of scope for this plan (from the ticket's Out of Scope section and the
investigation's Anti-Drift Hazards):

- `.claude/agents/doc-updater.md` — CORE-WIRING's territory, already landed; read-only reference
  only if needed to confirm literal strings.
- `.claude/workflows/implement-ticket.js` — CORE-WIRING's territory, already landed; read-only
  reference only.
- `dashboard-frontend/src/lib/phasePalette.ts`, `dashboard-frontend/src/test/phasePalette.test.ts`,
  or any other `dashboard-frontend/` file — separate, not-yet-created sibling child ticket 3
  (dashboard phase-palette registration).
- `docs/agent-monitoring/schema.md` — self-disclaimed as non-authoritative in its own text (line
  239) and in `vocabulary.py`'s module docstring; do not "fix" its stale 11-entry table.
- `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`,
  `docs/ai/agents.md` — all four already updated by CORE-WIRING; no further edit needed here.
- `record_events.py`, `validate.py`, `generate_retro.py` — import the dicts by reference, need zero
  code change to pick up the two new literals.
- `WORKFLOW_AGENT_PREFIXES` or `infer_workflow()` — `doc-updater` is a fixed literal in an existing
  workflow, not a new workflow or prefix-family case.
- `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced` itself —
  expected to pass unmodified (object-identity check, not count-based); only touch if it
  unexpectedly fails, and if so treat that as a blocking anomaly to report, not something to edit
  around.
- Any existing line in `registries/glossary_registry.jsonl` or any existing `INFRA-*` entry in
  `docs/parity_ledger/infrastructure.yaml` — both are append-only; only append new content, never
  edit/reorder/renumber existing entries.
- Any `docs/parity_ledger/*.yaml` file other than `infrastructure.yaml`.
- Adding a `doc-updater` agent-role glossary entry (`category: "agent"`) — not needed; `ingest.py`'s
  `_load_agent_role_descriptions()` reads `.claude/agents/*.md` frontmatter directly, already
  self-sufficient via CORE-WIRING's `doc-updater.md`.

## Dependency Map

- Step 1 has no dependency on Step 2 or Step 3 — it is the ticket's core deliverable and can be
  verified in isolation.
- Step 2 (parity-ledger entry) is logically independent of Step 1's mechanics but its `v2_evidence`
  field should cite Step 1's actual line numbers/registry line — write Step 2 after Step 1 lands so
  the citation is accurate, not stale/predicted.
- Step 3 depends on Step 1 (it re-runs the same test surface as a final confirmation) but not on
  Step 2 (the parity-ledger YAML is not part of any pytest suite this ticket's regression surface
  covers).
- No step depends on any not-yet-existing sibling ticket (dashboard phase-palette). CORE-WIRING, the
  one real dependency, has already landed in full.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `WORKFLOW_PHASES["implement-ticket"]` contains `"Document-Update"` (12 entries) | Step 1 | Direct file read + `test_real_seeded_registry_covers_every_workflow_phase` |
| `WORKFLOW_AGENTS["implement-ticket"]` contains `"doc-updater"` (12 entries) | Step 1 | Direct file read |
| `registries/glossary_registry.jsonl` contains exactly one new `category: "phase"`, `term: "Document-Update"` line | Step 1 | `python3 tools/glossary_registry.py list` / direct grep; `test_real_seeded_registry_every_entry_has_non_blank_description`, `test_real_seeded_registry_every_entry_has_valid_category` |
| `test_canonical_vocabulary_single_sourced` passes with file unmodified | Step 1, confirmed again in Step 3 | `pytest tests/tools/test_validate_agent_monitoring.py -k test_canonical_vocabulary_single_sourced` |
| `test_glossary_registry.py` passes | Step 1, Step 3 | `pytest tests/tools/test_glossary_registry.py` |
| `test_record_events.py` passes | Step 1, Step 3 | `pytest tests/tools/test_record_events.py` |
| No other file under `tools/agent-monitoring/`, `src/api/agent_ops_dashboard/`, or `dashboard-frontend/` modified | Scope Guards (all steps) | `git diff --stat` at Verify time |
| (Not an original ticket AC, but resolved by this plan) Parity-ledger precedent question | Step 2 | Direct read of `docs/parity_ledger/infrastructure.yaml`'s new `INFRA-316` entry; YAML parse check |

## Anti-Drift Notes

- `test_canonical_vocabulary_single_sourced` is an object-identity assertion
  (`record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES`), not count-based — do not add any
  new test that asserts a fixed `len(...)` on `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` or on
  `glossary_registry.jsonl`'s total line count; use membership assertions only
  (`"Document-Update" in WORKFLOW_PHASES["implement-ticket"]`) if a new explicit test is added (test
  plan's optional `test_document_update_phase_and_agent_registered_in_vocabulary` candidate — not
  required, but if added, must live in `tests/tools/test_validate_agent_monitoring.py` alongside
  `test_canonical_vocabulary_single_sourced`, same membership style).
- Step 1's two edits (`vocabulary.py` + `glossary_registry.jsonl`) must land and be verified
  together in the same commit — `test_real_seeded_registry_covers_every_workflow_phase` hard-fails
  on any partial state where one is present without the other. Do not stage/commit them separately.
- `registries/glossary_registry.jsonl` is append-only (`add_term()` raises `ValueError` on duplicate
  term) — use the CLI, not a hand-written JSON line, to get `added_date` and key-sorting correct and
  exercise the real code path.
- `docs/parity_ledger/infrastructure.yaml` is likewise append-only in practice (every existing entry
  is historical) — Step 2 only appends `INFRA-316`; never edit `INFRA-287`'s existing text even
  though it is the direct precedent being cited.
- Parity-ledger precedent resolution (settled, not left to Implement's judgment): `INFRA-287`
  (`TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`) added glossary entries for an entire batch of phases
  at once — a category-creation event. This ticket adds exactly one phase/agent pair to an
  already-established category, so Step 2's `INFRA-316` is scoped as a minimal, routine extension of
  that precedent, not a repeat of it. This is why a new entry is warranted here even though the
  investigation's own Assumptions section had initially concluded none was needed.
- CORE-WIRING has already landed — do not re-verify or re-derive its line numbers as if they were
  still provisional; the investigation already confirmed the exact literals (`'Document-Update'`,
  `'doc-updater'`) match byte-for-byte. Treat that confirmation as settled, not something to
  re-investigate.
- Zero real `Document-Update`/`doc-updater` events exist yet in `agent-monitoring/events.jsonl` as of
  this plan — this ticket is pre-emptive. Do not treat the absence of live drift symptoms as a
  reason to skip or de-prioritize the registration; the first ticket implemented via
  `implement-ticket.js` after CORE-WIRING landed (this one) will be the first real source of such
  events, and this ticket's own Document-Update phase run will be the first test of whether the
  registration works end-to-end.
- When Implement updates the ticket file's Implementation Notes / Status, it should also correct the
  Request Summary/Related Tickets framing that still describes CORE-WIRING as "in progress" — it is
  DONE. This is a text-accuracy fix bundled into the ticket-file update Implement already performs
  as part of closing out the ticket, not a separate plan step or file-scope item.

## Deviations

**Discovered during Test phase, not anticipated by Investigate/Plan/Review:** a second,
separate vocabulary-declaration site exists at `agent-orchestration/workflows/implement-ticket.yaml`
(the provider-neutral orchestration contract, per `docs/architecture/agent_orchestration_contract.md`
and `agent-orchestration/README.md`). Its `phases:`/`agents:` lists were "bootstrap-initialized once"
from `vocabulary.py`'s sets (per the file's own header comment and the README's "Bootstrap
vocabulary — one-time, not a permanent sync" section) but were never re-derived after this ticket's
Step 1 edit, causing `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`'s
value-equality snapshot check to fail — a real, reproducible Test-gate failure, not a false
positive.

Neither this ticket's own Investigate phase nor the sibling `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s
Investigate phase surfaced `agent-orchestration/` — a genuine investigation gap, since it's a
real vocabulary-declaration site (its own README states this explicitly) that any phase/agent
addition should have been checked against from the start.

Fix applied (narrow, additive, matches the file's own stated one-time-bootstrap-correction design —
confirmed via `agent-orchestration/README.md`'s explicit "Do not build a two-way sync... [but] this
contract was generated FROM it once" framing, which licenses a one-time manual correction, not an
ongoing coupling):
- `agent-orchestration/workflows/implement-ticket.yaml`: added `Document-Update` to `phases:`
  (positioned between `Implement` and `Architecture-Verify`, `tiers: {standard: full, hotfix: full}`,
  matching the real `implement-ticket.js` execution order and unconditional-per-tier behavior) and
  `doc-updater` to `agents:`.
- No `roles/*.yaml` file was added for `doc-updater` — confirmed via direct code read that no test
  or loader validation cross-references `agents:` list membership against `roles/*.yaml` file
  existence (`test_agent_orchestration_dir_has_required_files`'s hard-coded "exactly 10 role files"
  count is independent and unaffected). Adding a full role-contract file for `doc-updater` would be
  a materially larger, unreviewed architectural addition outside this ticket's scope — explicitly
  not done here.
- Fixing this surfaced 4 further stale literal assertions in `tests/agent_orchestration_claude_adapter/`,
  all deterministic and mechanically re-derivable from the real, current state — no judgment calls:
  - `test_contract_structure.py::_EXPECTED_TIER_MATRIX`: added `Document-Update` entry (mirrors the
    contract YAML edit exactly).
  - `test_phase_order_conformance.py::test_live_phase_order_has_the_expected_11_phases`: renamed to
    `..._12_phases`, list updated to include `Document-Update` in the correct position.
  - `test_generator_containment.py::test_generator_output_matches_representation_schema_shape`:
    `len(phase_order) == 11` → `== 12` (direct, mechanical consequence of the contract edit).
  - `test_terminal_status_extractor.py` and `test_terminal_status_conformance.py`: both hard-coded
    `FINALIZE_INCOMPLETE`'s call-site line numbers as `[1380, 1392]` — stale purely because
    `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s own earlier edit to `.claude/workflows/implement-ticket.js`
    shifted every later line down by inserting the ~80-line Document-Update phase block. Confirmed
    real current line numbers via direct grep (`1450`, `1462`) before updating either literal —
    not guessed.

All 124 tests across `tests/agent_orchestration/`, `tests/agent_orchestration_claude_adapter/`,
`tests/agent_orchestration_codex_adapter/` pass after these fixes (193 combined with this ticket's
own original 3-file scoped surface, 69 tests). No test assertion was weakened, deleted, or had its check logic altered —
every fix corrects a stale literal to match independently-verified real current state, the same
class of fix `TCK-20260803-DOC-UPDATER-CORE-WIRING` itself already made once
(`test_current_run_sidecar_orchestrator.py`'s 9→10 site-count correction).
