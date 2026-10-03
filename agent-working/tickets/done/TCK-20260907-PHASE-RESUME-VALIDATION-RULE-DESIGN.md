---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN
phase: done
date: 2026-09-07
tags: [ai, workflows, agent-monitoring]
---

# TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN

## Title
Design/decision doc: resolve the phase-level workflow-resume checkpoint validation rule (roadmap item 15)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Roadmap item 15 (`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`, Bucket B —
Experiment, H1) and `workflow_reliability_epic.md`'s M3 milestone require a **written
design/decision document**, not implementation code, resolving the resume-semantics validation
rule the freeze pass (§76 of `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3) required before
any phase-level resume logic can be written for `.claude/workflows/implement-ticket.js`. The
epic doc's own proposed minimum sufficient set is: a checkpoint is reusable only if
`workflow_version` matches, the input a phase consumed is unchanged (`input_hash`), and every
artifact that phase produced still exists on disk — with `source_revision`/`phase_version` added
only if this design work finds them materially necessary (not by default). The invariant to state
and hold once implemented: `checkpoint exists + checkpoint still valid = safe to reuse` — never
`checkpoint exists = skip phase`; on any validation failure the workflow restarts from the earliest
invalidated phase, not a blind skip.

This deliverable is analogous in shape and rigor to `docs/ai/shadow_promotion_gate_thresholds_decision.md`
and its owning ticket `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` — a decision-document-only,
hotfix-tier ticket producing a reviewable `docs/ai/*_decision.md` doc grounded in real, freshly
re-checked evidence, with zero `src/`/workflow code changes.

**Critical distinction confirmed during scoping (do not re-litigate):** this ticket is about
resuming a stalled/crashed `implement-ticket.js` **ticket-workflow pipeline run** (Scope →
Investigate → Plan → ... → Finalize), not the simulation engine's own tick-state checkpointing.
`graphify query "workflow resume checkpoint validation"` traversed `src/engine/checkpoint.py`
(`CanonicalStateHasher`, `CanonicalHashScheduler`, `BudgetedCanonicalHasher`,
`ScenarioCheckpointer`) and confirmed it is a completely separate, unrelated subsystem
(simulation-tick state checkpointing/hashing for the game engine and scenario runtime) with no
architectural relationship to ticket-workflow phase resume. This ticket must not touch, reference
as a model, or conflate with `src/engine/checkpoint.py`.

## Scope
- Author a new `docs/ai/phase_resume_validation_rule_decision.md`, matching the shape of
  `docs/ai/shadow_promotion_gate_thresholds_decision.md` / `docs/ai/default_packet_scenarios_decision.md`
  (frontmatter, "decides and evidences" framing, numbered sections, closing Resolution section).
- Confirm and state, citing direct investigation of `.claude/workflows/implement-ticket.js` and
  `.claude/skills/implement-ticket/SKILL.md`, exactly what "resume" means in this repo **today**:
  passing `ticket_id` re-loads the existing ticket at the Scope phase (skips ticket *creation*
  only) and then re-runs every subsequent phase (Investigate/Plan/Review/Implement/...) from
  scratch — there is no phase-level checkpoint, no skip-if-already-done logic, and no validation of
  prior-phase output validity anywhere in the pipeline today. State this plainly as the greenfield
  baseline the design work starts from.
- Evaluate the epic's proposed minimum sufficient validation-field set
  (`workflow_version` + `input_hash` + per-phase-artifact-existence) against real investigation
  findings, and explicitly conclude whether it is sufficient or whether `source_revision`/
  `phase_version` are materially necessary — grounded in evidence, not assumed either way in
  advance. In particular, investigate and address the real precedent already found during scoping:
  `agent-orchestration/workflows/implement-ticket.yaml` already has a `workflow_version` top-level
  field, consumed today by `tools/agent_codex_runtime_shadow/matrix.py`'s
  `_VERIFIED_AGAINST_WORKFLOW_VERSION` staleness check (a different consumer, same field) — the
  doc must state whether this existing field can be reused as-is for the resume validation rule's
  `workflow_version` check, or why a distinct field is needed instead.
- Ground the design in `docs/agent-monitoring/schema.md`'s actually-recorded per-phase data
  (`runs`/`events`/`tools` JSONL fields — `run_id`, `seq`, `phase`, `agent`, `status`, `ts`,
  `tool_call_count`, etc.) — identify which validation-rule fields already have a natural home in
  existing recorded data and which would need new, not-yet-recorded fields, rather than inventing a
  new schema wholesale without checking what already exists.
- State the invariant verbatim (`checkpoint exists + checkpoint still valid = safe to reuse` —
  never `checkpoint exists = skip phase`) and the required fallback behavior on validation failure
  (restart from the earliest invalidated phase, per §76 of the frozen proposal), including how
  "earliest invalidated phase" would be determined given the pipeline's linear phase ordering.
- Explicitly flag, per §76's own governance-table framing ("Auto-with-audit, gated by the
  validation rule"), what audit trail a resume decision would need to leave in
  `agent-monitoring/` (e.g., a new `events.jsonl` status/reason-code value analogous to existing
  gate-outcome values) so a resumed run's checkpoint-reuse decision is inspectable after the fact —
  as a stated design requirement for the future implementation ticket, not something this ticket
  builds.
- Update `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`'s
  M3 section to reflect that the design/validation-rule resolution is complete, pointing to the new
  decision doc, and note that M3 is now eligible to move from Bucket B into a future Bucket-A
  ticket (not yet that ticket itself) — mirroring the "mark RESOLVED with a pointer" convention
  `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` used for its own epic ticket.
- Cross-reference this ticket back into `tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md`'s
  `## Related Tickets` (or equivalent), per that epic ticket's own Acceptance Criterion 2
  ("a future session that picks up any one of these items links its resulting ... ticket back to
  this epic").

## Out of Scope
- Writing any phase-level resume implementation code in `.claude/workflows/implement-ticket.js` —
  that is explicitly future Bucket-A work, contingent on this design resolving first, not part of
  this ticket.
- Any change to `src/engine/checkpoint.py`, `CanonicalStateHasher`, `CanonicalHashScheduler`, or any
  other simulation-engine checkpointing code — unrelated subsystem, confirmed via graph traversal;
  do not conflate with or model this design on it.
- Building the actual audit-trail schema addition (new `events.jsonl` field/reason-code value) —
  this ticket states the requirement for a future ticket to build, it does not implement it.
- M2 (ticket-claim detection logging) and any other Bucket-B/C roadmap item — out of scope, tracked
  separately by their own future tickets/Experiment Specifications.
- Promoting this Bucket-B item into the future Bucket-A implementation ticket itself — this ticket
  only produces the design doc that makes that future ticket eligible to be scoped.
- Any change to `roadmap.md`'s own item-15 table row — the epic doc (`workflow_reliability_epic.md`)
  is the owning document for M3's status; `roadmap.md` is not touched by this ticket.

## Acceptance Criteria
- [x] `docs/ai/phase_resume_validation_rule_decision.md` exists, with valid frontmatter
      (`python3 tools/validate_frontmatter.py docs/ai/phase_resume_validation_rule_decision.md`
      passes), matching the numbered-section/"decides and evidences"/Resolution-section shape of
      `docs/ai/shadow_promotion_gate_thresholds_decision.md`.
- [x] The doc explicitly states, citing direct investigation of `.claude/workflows/implement-ticket.js`,
      that today's "resume" is ticket-ID re-invocation from Scope (re-runs every subsequent phase),
      not phase-level checkpoint restoration — and explicitly distinguishes this from
      `src/engine/checkpoint.py`'s unrelated simulation-tick checkpointing.
- [x] The doc evaluates the minimum sufficient set (`workflow_version`, `input_hash`,
      per-phase-artifact-existence) against real evidence and states a concrete conclusion on
      whether `source_revision`/`phase_version` are materially necessary, including an explicit
      finding on whether `agent-orchestration/workflows/implement-ticket.yaml`'s existing
      `workflow_version` field can be reused.
- [x] The doc states the invariant verbatim (`checkpoint exists + checkpoint still valid = safe to
      reuse` — never `checkpoint exists = skip phase`) and the restart-from-earliest-invalidated-
      phase fallback behavior.
- [x] The doc identifies, per validation-rule field, whether the needed data already has a home in
      `docs/agent-monitoring/schema.md`'s recorded `runs`/`events`/`tools` fields or would require a
      new field — citing the schema doc directly, not asserted from memory.
- [x] The doc states the audit-trail requirement (what a resume decision must leave inspectable in
      `agent-monitoring/`) as a requirement for the future implementation ticket.
- [x] `workflow_reliability_epic.md`'s M3 section is updated to reflect resolution, pointing to the
      new decision doc, and states M3 is now eligible to move to Bucket A (not yet that ticket).
- [x] `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` is updated to cross-reference this ticket
      under item 15 per its own Acceptance Criterion 2.
- [x] No `src/` file and no `.claude/workflows/*.js` file is created or modified — `Files Changed`
      lists only the new doc plus the two ticket/epic-doc edits above.

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (in progress) — the Bucket B/C tracking epic this
  ticket's item 15 belongs to; must be cross-referenced back per its own AC2.
- `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` (done) — the direct precedent this ticket's shape,
  tier, and rigor are modeled on (decision-doc-only, hotfix tier).
- `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` (done) — related context only, non-blocking:
  fixed a `seq`-numbering collision when a ticket's monitoring run is paused/resumed under the same
  `run_id`. This is a monitoring-attribution fix, not a phase-checkpoint-validity mechanism — it
  does not pre-empt or overlap this ticket's scope, but the design doc should note it as prior art
  in the "resume" problem space so a future implementer knows it already exists and is unrelated to
  the validation rule being designed here.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` / `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done) —
  related context only: the `.claude/current_run` sidecar this epic's M1 finished migrating already
  records `run_id`/`seq`/`phase`/`agent`/`execution_id`/`provider` per in-flight phase, which is
  relevant background for what state already exists mid-run, though it is not itself a durable
  checkpoint record.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` (M3 —
  the source spec this ticket implements; will be edited to mark M3 resolved).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (item 15 — read-only,
  confirms Bucket B / H1 / M3 mapping; not edited by this ticket).
- `docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html` (§76
  "Resume semantics, not just resume mechanics", §77 "Detection before prevention", the Automation
  boundary analysis "Phase-level resume" row, and the explicit note that an earlier revision's
  "read the sidecar and skip completed phases" framing undersold the problem).
- `docs/ai/shadow_promotion_gate_thresholds_decision.md` / `docs/ai/default_packet_scenarios_decision.md`
  — shape/rigor precedent for the new decision doc.
- `docs/agent-monitoring/schema.md` — the source of truth for what per-phase data is already
  recorded (`runs`, `events`, `tools` JSONL) that the validation rule should be grounded in.
- `.claude/skills/implement-ticket/SKILL.md` — documents today's `ticket_id`-resume behavior
  ("Scope phase re-loads it and skips creation").
- `tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` — the tracking epic to be
  cross-referenced.

## Related Stored Artifacts
None found covering phase-level workflow-resume validation-rule design. `stored_artifacts/`
searched via `search_docs`/grep for "resume-semantics"/"phase-level" — no prior investigation or
plan artifact exists for this specific design question.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (read-only investigation target — confirms today's
  ticket-ID-resume behavior; not modified by this ticket).
- `agent-orchestration/workflows/implement-ticket.yaml` (existing `workflow_version` field — real
  precedent to evaluate for reuse).
- `tools/agent_codex_runtime_shadow/matrix.py` (`_VERIFIED_AGAINST_WORKFLOW_VERSION`,
  `load_workflow_version_pair` — existing consumer of `workflow_version`, informs whether the field
  can be shared or must be forked for resume-validation purposes).
- `docs/agent-monitoring/schema.md` (per-phase recorded-data reference for grounding the rule).
- **Explicitly not** `src/engine/checkpoint.py` or any `src/engine/` file — unrelated subsystem,
  confirmed via `graphify query`.

## Assumptions / Open Questions
- Assumes the epic's own framing of the minimum sufficient field set
  (`workflow_version`/`input_hash`/artifact-existence) is the correct starting hypothesis to
  evaluate, not something to redesign from zero — if this design work's investigation finds that
  hypothesis fundamentally wrong (not just incomplete), that finding itself would invalidate this
  ticket's scope and should be raised rather than silently overridden.
- Assumes a hotfix-tier, decision-doc-only ticket is the correct vehicle for this Bucket-B design
  item (mirroring `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`'s precedent) rather than a formal
  "Experiment Specification" (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria) — the M3
  section's own text ("resolve the resume-semantics validation rule... This is design-resolution
  work, not implementation — it produces the validation rule") does not use Experiment-Specification
  language the way M2's section explicitly does, so this asymmetry is treated as intentional, not
  an oversight. If wrong, the deliverable shape would need to change to an Experiment Specification
  instead of a decision doc.
- `layer: ai` was chosen over `architecture` or `workflows`-as-layer (not a registered layer value)
  because `ai` is this repo's registered layer for "Claude agent/orchestration tooling," which is
  the closest fit among the 21 registered layers (`python3 tools/layer_registry.py list`); no new
  layer was registered since `ai` genuinely fits.
- Whether `source_revision`/`phase_version` end up materially necessary is explicitly left as the
  open question this ticket's own deliverable must answer — not pre-decided here in either
  direction, per the epic doc's own instruction not to add them by default.

## Implementation Notes

Context scan followed CLAUDE.md's mandatory order: `mcp__knowledge-search__search_docs` for
"phase-level workflow resume validation checkpoint" first (surfaced `docs/audits/D23_architecture_resilience.md`'s
existing "two genuinely distinct multi-step workflows" framing, corroborating the ticket's own
scoping note), then `graphify query "workflow resume checkpoint validation"` (BFS depth=2, 111
nodes, all rooted in `src/engine/checkpoint.py`/`scenario_checkpoint.py`/`scenario_runtime.py` —
confirms zero graph edges to any `implement-ticket.js`/agent-monitoring node, independently
corroborating the ticket's own pre-scoping finding that this is a fully separate subsystem).

Direct source investigation (not assumed from ticket prose) before writing the decision doc:
- `.claude/workflows/implement-ticket.js`: confirmed via `grep` for `existsSync`/skip-logic that no
  phase-skip-if-artifact-exists conditional exists anywhere tied to phase execution; the only
  resume-aware logic is Scope's ticket lookup (`tickets/inprogress/`, `tickets/done/`,
  `tickets/todos/**/`) and `seqOffset` monitoring-attribution continuity
  (`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`).
- `.claude/skills/implement-ticket/SKILL.md`: confirmed the one-line documented behavior ("Scope
  phase re-loads it and skips creation").
- `agent-orchestration/workflows/implement-ticket.yaml` + `tools/agent_codex_runtime_shadow/matrix.py`:
  read `workflow_version: 2`'s real consumer (`_VERIFIED_AGAINST_WORKFLOW_VERSION`,
  `load_workflow_version_pair`) and its docstring's explicit rationale for staying decoupled from
  per-artifact/per-fixture versioning (`TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION`).
- `docs/architecture/agent_orchestration_contract.md`'s Versioning section: independently confirms
  `workflow_version`/`hook_schema_version` is this repo's established whole-contract-level
  versioning convention, with no per-phase variant named anywhere.
- `docs/agent-monitoring/schema.md`: read the full `runs`/`events`/`tools` field tables to determine,
  per validation-rule field, whether a home already exists (see the doc's §4 table).

Conclusion reached (grounded in the above, not assumed in advance): the epic's proposed minimum
field set (`workflow_version` + `input_hash` + per-phase-artifact-existence) is sufficient;
`source_revision`/`phase_version` are not materially necessary (both subsumed by a correctly-scoped
`input_hash`, or lacking real evidence of a gap `workflow_version` leaves open). `workflow_version`
can be reused as-is from `implement-ticket.yaml` — same coarse whole-workflow semantics
`matrix.py` already relies on, no need to fork a distinct field. No conflict was found with the
epic's own hypothesis (the Gate Integrity condition in this ticket's own instructions — "if
fundamentally wrong, report honestly" — did not trigger; the hypothesis held up under evidence).

Deviation from the ticket's own Related Docs framing: none of substance. One precision fix beyond
the ticket's literal instructions — `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md`'s item 15
bullet already existed (added by a concurrent sibling-ticket session before this session started,
per that file's own note about a "concurrent-edit race"), but pointed to `tickets/todos/`, which
was already stale by the time this session started (the ticket had already moved to
`tickets/inprogress/` for implementation). Updated that bullet's location note and added the
decision-doc pointer without disturbing the surrounding items-13/14 bullets, rather than leaving a
now-inaccurate path in place.

Noted, not acted on: a duplicate ticket file exists at `tickets/todos/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md`
(the pre-scoping copy) alongside the in-progress copy this session worked from at
`tickets/inprogress/`. Per this repo's known hand-orchestration pattern, deleting that
`tickets/todos/` duplicate is Finalize/close-phase housekeeping, not implementer-phase work — flagged
here so a future Finalize/close pass does not miss it.

## Test Summary

Docs-only ticket per its own Testing section — no `pytest` run. Validation performed:
`python3 tools/validate_frontmatter.py docs/ai/phase_resume_validation_rule_decision.md` → OK (0
violations). `python3 tools/validate_frontmatter.py --content-type ticket
tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` → OK. `python3
tools/validate_frontmatter.py --content-type ticket
tickets/inprogress/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md` → OK. `git status
--porcelain` confirmed no `src/` path and no `.claude/workflows/*.js` path among this session's own
changes (the working tree has other, unrelated concurrent-session changes present — per CLAUDE.md's
shared-worktree Hard Rule, those are left untouched and unclaimed by this ticket).

## Files Changed
- `docs/ai/phase_resume_validation_rule_decision.md` (new) — the decision document.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` (modified)
  — M3 section marked RESOLVED with a pointer to the new doc and a summary of its findings; M3's
  row in the "Acceptance signal for this epic" section marked met; M3's decision doc added to
  References.
- `tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` (modified) — item 15's
  `## Related Tickets` bullet corrected (stale `tickets/todos/` path → `tickets/inprogress/`) and
  the decision-doc pointer added.
- `tickets/inprogress/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md` (this file, modified) —
  Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary.
- `docs/agent-monitoring/schema.md` (modified, Doc-Update phase) — added a `workflow_version`/
  `input_hash` entry to the "What is not recorded" section, pointing to
  `docs/ai/phase_resume_validation_rule_decision.md` as the design work that identified this
  recording gap; no schema field was actually added (that remains future implementation work).

Not this ticket's own edit, pre-existing in this shared worktree from the just-Finalized sibling
ticket `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`'s own Finalize regeneration step,
left staged/uncommitted per this batch's own convention of accumulating commits until the batch
closes: `docs/REGISTRY.yaml`.

No `src/` file and no `.claude/workflows/*.js` file was created or modified.

## Completion Summary

Produced `docs/ai/phase_resume_validation_rule_decision.md`, resolving the resume-semantics
validation-rule design question `workflow_reliability_epic.md`'s M3 required before any
phase-level resume implementation can be written for `implement-ticket.js`. The doc confirms
today's baseline has no phase-level checkpoint anywhere (resume is ticket-ID re-invocation from
Scope only), explicitly distinguishes this from `src/engine/checkpoint.py`'s unrelated
simulation-tick checkpointing (confirmed via graph traversal), evaluates and confirms the epic's
proposed minimum validation-field set (`workflow_version` + `input_hash` +
per-phase-artifact-existence) as sufficient with `source_revision`/`phase_version` found not
materially necessary, confirms `implement-ticket.yaml`'s existing `workflow_version` field can be
reused as-is, grounds each field in `docs/agent-monitoring/schema.md`'s real recorded shape
(identifying which need new fields), states the invariant and earliest-invalidated-phase restart
fallback verbatim, and states the future audit-trail requirement without building it. Both
required cross-references landed: `workflow_reliability_epic.md`'s M3 section and
`TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md`'s item 15 bullet. No `src/` or
`.claude/workflows/*.js` file was touched.
