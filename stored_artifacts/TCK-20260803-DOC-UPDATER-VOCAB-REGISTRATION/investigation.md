---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION
artifact_type: investigation
tags: [agent-monitoring, workflows, process-improvement]
---

# Investigation — TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION

## Current Behavior

**`tools/agent-monitoring/vocabulary.py` (full file read, 95 lines) — confirmed current, unchanged
by the sibling ticket:**

- `WORKFLOW_PHASES["implement-ticket"]` (lines 21-24) is still exactly the pre-CORE-WIRING
  11-entry set: `Scope`, `Investigate`, `Plan`, `Review`, `Implement`, `Architecture-Verify`,
  `Test`, `Parity`, `Security-Review`, `Verify`, `Finalize`. `"Document-Update"` is **not** a
  member.
- `WORKFLOW_AGENTS["implement-ticket"]` (lines 40-44) is still exactly the pre-CORE-WIRING
  11-entry set: `ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`,
  `implementer`, `test-scoper`, `parity-updater`, `security-reviewer`, `done-checker`,
  `finalizer`, `implement-ticket-orchestrator`. `"doc-updater"` is **not** a member.
- This confirms the ticket's own Assumptions claim: `TCK-20260803-DOC-UPDATER-CORE-WIRING` did not
  touch this file (it was explicitly out of scope for that ticket — see its own "Out of Scope"
  list, item 1).
- `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` are consumed by `record_events.py` (warn-only drift check at
  write time), `validate.py::compute_drift_report` (lines 107-111, via `phase not in
  WORKFLOW_PHASES.get(workflow, set())` and `not is_known_agent(workflow, agent)`), and
  `generate_retro.py` (phase/agent normalization) — all three import the dicts directly, confirmed
  by grep; none need code changes to pick up two new literals.

**`.claude/workflows/implement-ticket.js` — confirmed real, current call sites (this ticket's
sibling, TCK-20260803-DOC-UPDATER-CORE-WIRING, landed and closed on 2026-08-03):**

- Line 10: `meta.phases` entry `{ title: 'Document-Update', detail: '...' }`.
- Line 774-777: comment block "Phase 5a: Document-Update".
- Line 779: `phase('Document-Update')` — exact literal, matches the ticket's assumed string.
- Line 814: `await writeSidecar(events.length + 1 + seqOffset, 'Document-Update', 'doc-updater')` —
  both literals exact.
- Line 829: `{ label: 'doc-update', schema: DOC_UPDATE_SCHEMA, agentType: 'doc-updater' }` — agent
  type literal exact (note: the sidecar *label* is `'doc-update'`, lowercase-hyphenated, distinct
  from the phase name `'Document-Update'` and the agent name `'doc-updater'`; this is consistent
  with other phases, e.g. Parity's label is `'parity'` not `'Parity'`, and is not part of the
  vocabulary this ticket registers).
- Lines 832-837: `pushEvent('Document-Update', 'doc-updater', docUpdate.blocker ? 'failed' : 'ok',
  ..., docUpdateTs)` — both literals exact, matching `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` addition
  targets byte-for-byte.

Confirmed: the two literals this ticket must add (`"Document-Update"`, `"doc-updater"`) are
exactly what the live code emits — no casing/spelling drift between the ticket's plan and the
landed sibling implementation.

**`registries/glossary_registry.jsonl` — sampled `category: "phase"` entries for tone/length
match (lines 36-46, 11 `implement-ticket` phase entries confirmed present, `"Document-Update"`
confirmed absent):**

Representative entries (one-sentence, agent-name-first, ends with a clause on effect/purpose):
- `"Parity"` (line 43): "Parity-updater agent updates the relevant docs/parity_ledger entry so
  documentation and source code stay in sync after a behavior change."
- `"Implement"` (line 40): "Implementer agent writes the code changes described in the plan, or,
  in implement-epic, delegates one full implement-ticket run per child ticket."
- `"Verify"` (line 45): "Confirms the work is genuinely complete against its own
  Definition-of-Done conditions - a 13-condition check in implement-ticket, or a
  regression/anchor-coverage check in simq-audit."

A new `"Document-Update"` entry should follow the `Parity`-style shape: agent-first, one sentence,
describing what doc-updater does and why (specializing documentation the way parity-updater
specializes the parity ledger), matching the design doc's own phrasing in
`docs/architecture/doc_updater_agent.md`.

**`tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced`**
(lines 236-241) — confirmed to be a pure object-identity assertion:
```python
assert record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES
assert record_events.infer_workflow is validate.infer_workflow
```
No count or literal-membership assertion anywhere in this test. Adding two literals to existing
dict *values* (not replacing the dict objects) cannot break it — confirmed structurally, matches
the ticket's own claim.

**`docs/agent-monitoring/schema.md`** — confirmed still not needing any edit. Line 239 explicitly
states: "Canonical phase/agent values for all four workflows are enforced from
`tools/agent-monitoring/vocabulary.py` — the tables below are illustrative documentation, not the
source of truth; if they disagree with `vocabulary.py`, the module wins." Its own `### phase
values (implement-ticket workflow)` list (line 243) is the stale 11-entry set (missing
`Document-Update`) — this staleness is pre-acknowledged and self-disclaimed by the doc itself, so
it is not a doc this ticket (or any future ticket, per the doc's own design) needs to keep in
sync. Confirms the ticket's Out of Scope claim and design doc sub-item 5.

**`agent-monitoring/events.jsonl`** — grepped for literal `"phase":"Document-Update"` and
`"agent":"doc-updater"`: **zero matches** for either. The 6 substring hits for "Document-Update"
in the file are all prose mentions inside `summary` text of `Scope`/`Plan`/`Review`/`Implement`/
`Test` phase events belonging to the `TCK-20260803-DOC-UPDATER-EPIC`,
`TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE`, and `TCK-20260803-DOC-UPDATER-CORE-WIRING` runs
themselves (agents describing their own work), not real emitted `Document-Update`-phase events.
This means: **no vocabulary-drift symptom currently exists in the live corpus** for this exact
phase/agent pair — CORE-WIRING's own implementation run predates the phase's existence in the
running workflow script (the phase was added to the `.js` file as part of that ticket's own
Implement step, but that same run had already passed its own Implement phase before the file
change took effect, and no ticket has been implemented through the full pipeline since CORE-WIRING
landed). The first ticket to be implemented via `implement-ticket.js` *after* CORE-WIRING landed
will be the first real source of `Document-Update`/`doc-updater` events — and until this ticket's
vocabulary registration lands, `validate.py`'s drift report and `generate_retro.py` would flag
those as drift. This is the exact "inert until sibling lands, meaningless until this lands" gap
described in the ticket's own Request Summary.

## Mechanics / Engine Constraints

None. This is agent-orchestration tooling (`tools/agent-monitoring/`, `registries/`), not
simulation logic. No `docs/mechanics/` chapter or `docs/engine/` contract constrains this change.

## Docs Requiring Update

None.

## Parity Ledger Overlap

No entry in `docs/parity_ledger/` directly names `doc-updater`/`Document-Update`/this vocabulary
registration. Independently grepped all of `docs/parity_ledger/*.yaml` for
`doc-updater|Document-Update|WORKFLOW_PHASES|glossary_registry` — the only hits are in
`infrastructure.yaml`:
- `INFRA-287` — `TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`, the entry documenting the *original*
  21-entry phase-glossary seeding this ticket's new entry extends. Historical/closed, not
  overlapping this ticket's specific scope, but directly analogous precedent (see Risks below).
- `INFRA-302` — dashboard phase-palette/echarts work, adjacent to the not-yet-created dashboard
  sibling ticket, not this one.
- Various `INFRA-281`/`INFRA-289`–`INFRA-291` mentions of `glossary_registry.py`/`WORKFLOW_PHASES`
  as general architecture references within other entries' text, not entries about this specific
  change.

No P0 entries touched. This ticket's own Assumptions section concludes no ledger entry is needed
("agent-orchestration tooling, not a simulation-mechanics change"). See Risks and Open Questions —
this investigation flags a precedent-based counter-consideration rather than silently overriding
the ticket's own conclusion.

## Prior Work

- `TCK-20260803-DOC-UPDATER-CORE-WIRING` (done) — sibling this ticket depends on. Confirmed the
  `Document-Update` phase and `doc-updater` agent now exist in
  `.claude/workflows/implement-ticket.js` with exactly the literal strings this ticket must
  register. Its own Files Changed list confirms `tools/agent-monitoring/vocabulary.py` was not
  touched.
- `TCK-20260803-DOC-UPDATER-EPIC` (in progress/EPIC_SCOPED) — parent epic tracking this ticket and
  its two siblings (CORE-WIRING, done; dashboard-palette, in progress per
  `TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE` events observed in `agent-monitoring/events.jsonl`).
- `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` (done, referenced in `vocabulary.py`'s own
  docstring) — established `vocabulary.py` as single source of truth and
  `test_canonical_vocabulary_single_sourced` as the identity guard this ticket must not weaken.
- `TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS` (done, `INFRA-287`) — authored the original 21
  phase-glossary descriptions (11 of them for `implement-ticket`) this ticket's new
  `"Document-Update"` entry must match in tone/length. Confirmed by direct sample above.
- `TCK-20260718-GLOSSARY-REGISTRY` (done) — built `tools/glossary_registry.py`'s append-only
  `add_term()`/`GLOSSARY_CATEGORIES`-validation mechanism this ticket uses unchanged. Confirmed
  `add_term()` (lines 109-144) rejects invalid categories, blank descriptions, and duplicate terms
  — all relevant guardrails for this ticket's step 2.

## Risks and Open Questions

- **Why "Docs Requiring Update" is None (rationale).** This ticket's actual file-change scope
  (`vocabulary.py`, `glossary_registry.jsonl`) touches no `docs/` path. `vocabulary.py` is source
  code, not `docs/`, but is the single source of truth multiple docs/tools defer to — no `docs/`
  prose file needs a parallel edit as a result. `docs/agent-monitoring/schema.md` explicitly
  disclaims its own phase/agent tables as non-authoritative (confirmed by direct read) and does
  not require updating either.
- **Real coupling discovered, not previously named in the ticket's own scope text**:
  `tests/tools/test_glossary_registry.py::test_real_seeded_registry_covers_every_workflow_phase`
  (lines 197-217) iterates the *live* `WORKFLOW_PHASES` dict from `vocabulary.py` and asserts
  every phase literal has a `registries/glossary_registry.jsonl` entry with `category: "phase"`
  and a non-blank description. This means: if `vocabulary.py`'s edit (ticket step 1) lands without
  the `glossary_registry.jsonl` edit (ticket step 2) in the same commit, this specific test will
  **fail** (not just the vocabulary-drift warn-only check — a hard pytest failure). This is a
  stronger, more precise justification for "both edits must land together" than the ticket's own
  text states, and should be called out explicitly in Plan/Implement as the enforcement mechanism
  behind Acceptance Criterion 5 (`test_glossary_registry.py` passes). Not a blocker — the ticket's
  scope already does both edits — but worth flagging so Implement does not stage/commit the two
  file edits separately without running this test in between.
- **Open question (not blocking, flagged per instructions rather than assumed)**: should this
  ticket also add a `docs/parity_ledger/infrastructure.yaml` entry, mirroring the precedent set by
  `INFRA-287` (`TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`), which performed the structurally
  identical operation (add glossary-registry `phase`-category entries for new
  `vocabulary.py`-registered literals) and *did* get an infrastructure.yaml entry? The ticket's own
  Assumptions section concludes no entry is needed, reasoning this is "agent-orchestration
  tooling, not a simulation-mechanics change" — but `infrastructure.yaml` is explicitly the
  parity-ledger subsystem file for "Replay, telemetry, observability, workers" (per
  `CLAUDE.md`'s own table) and has repeatedly tracked exactly this class of change (`INFRA-281`,
  `INFRA-287`, `INFRA-289`–`INFRA-291`, `INFRA-302`). This is a genuine judgment call the ticket's
  own author already made a call on; this investigation surfaces the counter-evidence rather than
  silently agreeing or overriding it. Recommend Plan either affirms the ticket's "no entry needed"
  call explicitly (distinguishing this ticket's narrower scope from INFRA-287's, e.g. "INFRA-287
  covered the foundational 21-entry seed; this is routine incremental vocabulary growth of an
  already-established mechanism, not a new capability") or adds a minimal `infrastructure.yaml`
  entry for consistency. Does not block implementation either way — low stakes, P2 ticket,
  non-P0 subsystem — but should not be silently decided without a stated rationale in Plan.
- The ticket's own line-number/count assumptions (11-entry sets) were independently re-confirmed
  accurate as of this investigation (2026-08-03) — no drift since scoping.

## Anti-Drift Hazards

- `test_canonical_vocabulary_single_sourced` is object-identity based
  (`record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES`), not count-based. Any new test
  added by this ticket (if any) must follow the same structural pattern — assert membership
  (`"Document-Update" in WORKFLOW_PHASES["implement-ticket"]`) or identity, never a bare
  `len(...) == 12` assertion, which would need updating again on the next vocabulary addition
  (e.g. the not-yet-created dashboard-palette sibling does not touch `vocabulary.py`, but some
  future phase addition will, and a count-based test would silently rot).
- Do not add a new literal to `WORKFLOW_AGENT_PREFIXES` or modify `infer_workflow()` — `doc-updater`
  is a fixed literal for an existing workflow (`implement-ticket`), not a new workflow or a
  prefix-family case like `create-tickets`'s `investigate:${concern_id}`.
- Do not touch `docs/agent-monitoring/schema.md` — confirmed twice now (ticket's own claim, this
  investigation's independent re-check) that it is self-disclaimed as non-authoritative and stale
  by design; "fixing" its stale 11-entry table would be unrequested scope creep, not a fix.
- Do not modify `record_events.py`, `validate.py`, or `generate_retro.py` — all three already
  import the dicts by reference and need zero code change; touching them would be unrequested
  scope creep into the sibling's or unrelated tickets' territory.
- `registries/glossary_registry.jsonl` is append-only (`add_term()` raises `ValueError` on
  duplicate term) — do not hand-edit an existing line or attempt to "fix" the file's existing 11
  `implement-ticket` phase entries; only append the one new `"Document-Update"` line, preferably
  via the CLI (`python3 tools/glossary_registry.py add "Document-Update" --category phase
  --description "..."`) rather than a hand-written JSON line, to get `added_date` and key-sorting
  correct automatically and exercise the real code path.
