---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-EPIC
phase: done
date: 2026-08-03
tags: [workflows, documentation, agent-monitoring, dashboard, process-improvement]
---

# TCK-20260803-DOC-UPDATER-EPIC

## Title
Document-Update agent/phase epic — implement the doc-updater design in docs/architecture/doc_updater_agent.md

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/architecture/doc_updater_agent.md` (status: Proposed, already written and reviewed through a
3-iteration spec review loop, staged in git but not yet committed) specifies a new subagent,
`.claude/agents/doc-updater.md`, and a new `implement-ticket.js` pipeline phase, **Document-Update**,
that specializes documentation editing the way `parity-updater` already specializes
`docs/parity_ledger/*.yaml` edits. Today, doc edits are made by the generalist `implementer` agent,
which has zero doc-family-specific rules; the three existing enforcement layers (Investigate's
mandatory `## Docs Requiring Update` section, Implement-time `doc_staleness_check.py`, and Verify's
independent `check_docs_to_update_coverage` re-derivation) already catch missing doc updates but say
nothing about execution quality. This epic tracks the child tickets that will implement that design.
This epic itself is scope-only — tracking/sequencing, no direct implementation.

**Decision** (from the design doc): insert Document-Update between Implement's `agent()` call and
the existing `doc_staleness_check.py` bash() call (`implement-ticket.js` lines ~773-835), not after
that gate — the orchestrator must merge doc-updater's own `files_changed` into what
`doc_staleness_check.py` evaluates *before* that check runs, otherwise every ticket whose only
`docs/` change comes from doc-updater (not Implement's own diff) would be `DOC_STALENESS_BLOCKED`
before doc-updater ever ran. `doc_staleness_check.py`'s own internal pass/fail logic
(`check_doc_staleness()`) does not change. Runs for every tier, including hotfix.

**Scope boundary** (five rows, per the design doc): doc-updater owns `docs/` minus four exclusions —
`docs/parity_ledger/*.yaml` stays `parity-updater`'s; the ticket file, `working_log.csv`,
`docs/REGISTRY.yaml` regen, and `make knowledge-index-update` stay `finalizer`'s (Finalize);
`docs/archive/`, `docs/scenarios/`, `docs/entity/` are out-of-scope-for-everyone (matches
`generate_registry.py`'s `_SKIP_DOC_SUBDIRS`); `docs/audits/` is cite-only, never edited by this
pipeline (dated point-in-time snapshots, not living reference docs — this constraint was tested
directly during the design's own review, when a D17 finding was found already-fixed by unrelated
work). `planner`/`plan.md` are unchanged.

**Data flow**: the orchestrator computes "what" before spawning doc-updater — standard/epic tier
parses `investigation.md`'s `## Docs Requiring Update` bullets (path, reason); hotfix tier (no
`investigation.md`) passes the ticket's `## Scope` text plus `implementation.files_changed`, and
doc-updater makes a lighter-weight judgment call. "How" is static per-family rules baked into
`.claude/agents/doc-updater.md` (a `File | Subsystem`-shaped table covering `docs/mechanics/`,
`docs/engine/`, `docs/guides/`, `docs/guidelines/intentional_divergences.md`, `docs/plans/`,
`docs/audits/` (cite-only), and a catch-all for the other 17 general folders). Output contract
mirrors `parity-updater.md`: one-sentence summary, `docs_updated` (`{path, reason, what_changed}`),
`docs_skipped` (with justification — allowed, not a failure), `verified_by`.

**Error handling**: the Verify-time gate (`check_docs_to_update_coverage`) stays fully decoupled from
doc-updater's own self-report — it continues re-deriving ground truth from `investigation.md` + real
`git status` only, exactly as today ("never trust the self-report"). Standard/epic tier: a
doc-updater misjudgment that a flagged doc doesn't need touching is caught by Verify's existing gate
(`DOD_BLOCKED`); an outright doc-updater failure reports the blocker in structured output but does
not introduce a new blocking status — Verify's existing gate is the actual backstop. Hotfix tier has
no equivalent backstop: `check_docs_to_update_coverage` already returns `NA` unconditionally for
hotfix (no `investigation.md` to check against) — an accepted, pre-existing gap this design does not
worsen (the same gap exists today for the generalist implementer's hotfix-tier doc edits).

**Consequences** — five hand-maintained, non-automatic registration touch points, each an explicit
implementation-plan step (omitting any one means Document-Update events render as
unrecognized/vocabulary-drift in the retro report and dashboard views instead of a normal phase):
1. `tools/agent-monitoring/vocabulary.py`: `WORKFLOW_PHASES["implement-ticket"]` gains
   `"Document-Update"`; `WORKFLOW_AGENTS["implement-ticket"]` gains `"doc-updater"`.
2. `registries/glossary_registry.jsonl` gains one `category: "phase"` entry for `"Document-Update"`.
   `doc-updater`'s agent-role tooltip needs no separate registration — the dashboard's
   `_load_agent_role_descriptions()` reads `.claude/agents/*.md` frontmatter `description:` directly.
3. `dashboard-frontend/src/lib/phasePalette.ts`: `'Document-Update'` added to the `WorkflowPhase`
   union, a `PHASE_FAMILY` entry (`'build'`, alongside `Implement`/`'Sync Docs'`), and a
   `PHASE_PALETTE` hex value stepped within that family's OKLCH-lightness band, re-validated via the
   dataviz skill's `validate_palette.js`. No automated cross-language sync guard exists with
   `vocabulary.py` — `src/test/phasePalette.test.ts`'s completeness assertion must be hand-updated
   from 21 to 22, by design, as the sync-drift alarm.
4. `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced` (and any
   sibling count-based test against `vocabulary.py`) must be re-run and, if count-based, updated.
5. No change needed to `docs/agent-monitoring/schema.md`'s prose tables (already documented as not a
   source of truth by any tooling).

## Scope
- Scope-only epic: create and track the three child implementation tickets listed below (to be
  scoped separately, as standard-tier tickets, after this epic is created).
  1. **Core agent + phase wiring** (to be scoped): new `.claude/agents/doc-updater.md` subagent
     definition; new Document-Update phase in `.claude/workflows/implement-ticket.js` inserted
     between Implement's `agent()` call and the existing `doc_staleness_check.py` `bash()` call
     (lines ~773-835 today); orchestrator merges doc-updater's own `files_changed` into what that
     check evaluates before it runs; `doc_staleness_check.py`'s own internal pass/fail logic stays
     unchanged.
  2. **Monitoring/vocabulary registration** (to be scoped): `tools/agent-monitoring/vocabulary.py`
     gains `"Document-Update"` in `WORKFLOW_PHASES["implement-ticket"]` and `"doc-updater"` in
     `WORKFLOW_AGENTS["implement-ticket"]`; `registries/glossary_registry.jsonl` gains one new
     `category: "phase"` entry for `"Document-Update"`;
     `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced`
     re-verified (object-identity check, not count-based — expected to pass without modification,
     but must be re-run, not assumed).
  3. **Dashboard phase-palette registration** (to be scoped): `dashboard-frontend/src/lib/phasePalette.ts`
     gains `'Document-Update'` to the `WorkflowPhase` union (22nd member), a `PHASE_FAMILY` entry in
     the `'build'` family (alongside `Implement` and `'Sync Docs'`), a `PHASE_PALETTE` hex value
     stepped within that family's existing OKLCH-lightness band and re-validated via the dataviz
     skill's `validate_palette.js`; `dashboard-frontend/src/test/phasePalette.test.ts`'s completeness
     assertion updated from 21 to 22.
- Record the design doc's Decision/Scope-boundary/Data-flow/Error-handling/Consequences sections
  (summarized above in Request Summary) as the binding spec child tickets must implement against.
- This epic's own completion condition: all three child tickets scoped, implemented, and `DONE`,
  with `docs/architecture/doc_updater_agent.md`'s `## Status` updated from `Proposed` to `Accepted`
  (or equivalent) as part of the last child ticket's close.

## Out of Scope
- No direct implementation of any child ticket's work in this epic itself — epic tier is
  scope-only, per this repo's convention (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`,
  `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`).
- Scoping or creating the three child tickets themselves — they are referenced here by intended
  scope only and will be scoped as separate standard-tier tickets in a follow-up call.
- Deviating from `docs/architecture/doc_updater_agent.md`'s Decision/Scope-boundary/Error-handling
  sections without a documented revisit — the design doc's own "Revisit Trigger" section defines
  the two specific conditions under which that's warranted (promoting `docs_skipped` into a second
  Verify-time cross-reference; `docs/audits/` gaining its own re-run automation). Any other
  deviation found necessary during child-ticket implementation must be raised back to this epic
  before proceeding, not silently absorbed into a child ticket's scope.
- Editing `docs/parity_ledger/*.yaml`, `docs/archive/`, `docs/scenarios/`, `docs/entity/`, or
  `docs/audits/` content — all five are explicitly out of doc-updater's scope per the design's
  Scope-boundary table and stay that way.
- Changing `parity-updater`, `finalizer`, `planner`, or `plan.md`'s shape — the design doc states
  no change to any of these.
- The two follow-up items noted in the design doc's Consequences section but explicitly marked
  not-in-scope-here: correcting `.claude/agents/implementer.md`'s stale `src/data/` reference, and
  (already fully retracted during spec review) the claim that `src/logging/` lacks `docs/` coverage.
- Promoting `docs/architecture/doc_updater_agent.md`'s own `## Status` from `Proposed` — that
  happens at the end of the last child ticket's close, not as part of this epic's own scoping pass.

## Acceptance Criteria
- [x] Three child tickets are created (via `ticket-scoper`, standard tier) matching the scopes
      described above: core agent + phase wiring; monitoring/vocabulary registration; dashboard
      phase-palette registration.
- [x] All three child tickets reach `DONE` in `tickets/done/`.
- [x] Post-implementation, `.claude/agents/doc-updater.md` exists and the Document-Update phase is
      live in `.claude/workflows/implement-ticket.js` at the seam specified (between Implement's
      `agent()` call and `doc_staleness_check.py`'s `bash()` call), for every tier including hotfix.
      Verified directly: phase block at lines 774-838, unconditional (no tier guard), preceding the
      doc-staleness gate comment at line 839.
- [x] `tools/agent-monitoring/vocabulary.py`, `registries/glossary_registry.jsonl`,
      `dashboard-frontend/src/lib/phasePalette.ts`, and `dashboard-frontend/src/test/phasePalette.test.ts`
      all reflect the new `Document-Update` phase / `doc-updater` agent consistently (no vocabulary
      drift reported by `validate.py` or the dashboard's drift-detection view). Verified directly:
      `python3 tools/agent-monitoring/validate.py` produces zero Document-Update/doc-updater/drift
      warnings.
- [x] `docs/ai/workflows.md`'s `implement-ticket` phase table and `docs/ai/system_overview.md`'s
      hotfix-tier pipeline summary (`Scope → Implement → Test → Parity → Verify → Finalize`) are
      both updated to include Document-Update, as part of whichever child ticket implements the
      phase wiring (flagged here, not fixed in this epic). Verified directly: both files now show
      `Document-Update` in their respective phase table/tier-routing rows.
- [x] `docs/architecture/doc_updater_agent.md`'s `## Status` is updated from `Proposed` to
      `Accepted` (or equivalent) once all three child tickets are `DONE`. Done as part of this
      epic's own close.
- [x] This epic's own `## Scope`/`## Out of Scope` state only tracking/sequencing, with no direct
      implementation claimed for the parent itself.

## Related Tickets
- TCK-20260803-DOCS-STRUCTURE-AUDIT (done) — prerequisite structure audit this design depended on;
  confirmed all 26 top-level `docs/` subfolders real/populated and `_SKIP_DOC_SUBDIRS` accurate
  before the design's per-family rule table was written.
- TCK-20260802-DOC-UPDATE-DISCIPLINE (done) — built the three-layer enforcement this design builds
  on top of: `investigator`'s mandatory `## Docs Requiring Update` section, the
  `doc_staleness_check.py` wiring immediately after Implement, and (pre-existing) Verify's
  independent `check_docs_to_update_coverage` re-derivation. Not a duplicate — this epic is about
  *who* executes doc edits and *how*, not the enforcement/gate mechanism itself, which stays
  unchanged per the design doc's own Rationale ("No new blocking logic, only a corrected input").
- TCK-20260711-DOC-STALENESS-GATE-CHECK / TCK-20260720-GATE-CHECK-WIRING-DECISIONS — shipped and
  wired `doc_staleness_check.py`, the gate whose input this design corrects.
- TCK-20260803-DOC-UPDATER-CORE-WIRING (done) — `.claude/agents/doc-updater.md` +
  Document-Update phase wiring in `implement-ticket.js`.
- TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION (done) — `vocabulary.py` +
  `glossary_registry.jsonl` registration; also fixed a pre-existing gap discovered during its Test
  phase, a second vocabulary-declaration site in `agent-orchestration/workflows/implement-ticket.yaml`
  that neither this ticket's nor CORE-WIRING's own Investigate phase had surfaced.
- TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE (done) — `phasePalette.ts` +
  `phasePalette.test.ts` registration.

## Related Docs
- `docs/architecture/doc_updater_agent.md` — the authoritative design doc this epic tracks
  implementation of (Proposed status, staged but not committed at scoping time).
- `docs/ai/workflows.md` — `implement-ticket` phase table (lines ~81-93) will need a new
  Document-Update row; does not currently list it (confirmed by direct read during scoping).
- `docs/ai/system_overview.md` — hotfix-tier pipeline summary (line ~117,
  `Scope → Implement → Test → Parity → Verify → Finalize`) will need Document-Update added, since
  the design states the phase runs for every tier including hotfix (confirmed by direct read
  during scoping; flagged here per this ticket's scoping instructions, not fixed in this epic).
- `docs/ai/agents.md` — will likely need a `doc-updater` section, mirroring the existing
  `parity-updater`/`mechanics-auditor` sections (not confirmed required, but the established
  pattern for every other agent in this pipeline).
- `.claude/agents/parity-updater.md` — direct structural precedent for `doc-updater.md`'s Output
  contract and per-family rule table shape.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-DOCS-STRUCTURE-AUDIT/` — prerequisite structure-audit
  investigation this design's per-family rule table depended on.
- None found specifically covering doc-updater agent design or implementation planning beyond the
  design doc itself.

## Related Code Areas
None — scope-only epic tracking child tickets; no direct implementation in this ticket, per this
repo's epic-ticket convention.

## Assumptions / Open Questions
- Assumes `docs/architecture/doc_updater_agent.md` (Proposed, staged but uncommitted at scoping
  time) will be committed before or alongside the first child ticket's work — this epic does not
  itself commit that file. If the design doc changes materially before child tickets are scoped,
  this epic's summary (and the child tickets derived from it) would need re-verification against
  the updated doc.
- `layer: ai` chosen per CLAUDE.md's explicit note that this repo's `layer: ai` means "the Claude
  agent/orchestration system," not gameplay AI/cognition — correct fit since this epic is entirely
  about `implement-ticket.js` pipeline tooling, not simulation mechanics.
- Tags chosen from the existing registered set (`workflows`, `documentation`, `agent-monitoring`,
  `dashboard`, `process-improvement`) to cover the three child tickets' distinct areas (phase/agent
  wiring, monitoring vocabulary + glossary registry, dashboard frontend) — none required
  registering a new tag.
- No parity_ledger overlap found — this is agent-orchestration tooling, not a simulation-mechanics
  change, so no `docs/parity_ledger/*.yaml` entry applies (confirmed by grep across
  `docs/parity_ledger/` for doc-updater/Document-Update references — zero hits).
- Three child tickets are referenced here by intended scope only, as instructed — they are not
  created in this call. If a future scoping pass finds the design doc's line-number citations
  (e.g. `implement-ticket.js` lines ~773-835, `phasePalette.ts`'s 21-member union) have drifted due
  to unrelated intervening work, that child ticket's own scoping pass must re-verify against
  current code rather than trusting this epic's snapshot.

## Implementation Notes
All three child tickets implemented and closed in dependency order (core wiring → vocab
registration → dashboard palette), as directed. This epic itself performed no direct
implementation, per epic-tier convention — its only direct action at close time is promoting
`docs/architecture/doc_updater_agent.md`'s `## Status` from `Proposed` to `Accepted`, which this
ticket's close performs.

One real gap surfaced during child-ticket execution, not anticipated at epic-scoping time: a
second orchestration-contract vocabulary site, `agent-orchestration/workflows/implement-ticket.yaml`,
existed independently of `tools/agent-monitoring/vocabulary.py` and was missed by both this epic's
own scoping pass and CORE-WIRING's Investigate phase. VOCAB-REGISTRATION's Test phase caught it via
a real test failure (`test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`), and it was
fixed there along with 4 downstream stale-literal test failures it exposed — documented in that
ticket's own Deviations/Implementation Notes, not silently absorbed.

After all three child tickets landed, the newly-built Document-Update phase/doc-updater agent had
not yet been exercised on any real ticket (all three child tickets' own doc edits were made by the
generalist `implementer` agent or by the orchestrator directly, since the phase didn't exist yet
when CORE-WIRING ran, and the two subsequent tickets were orchestrated by hand against the
already-current `implement-ticket.js` without re-picking-up the new phase in this session's manual
JS-to-tool-call translation). This is a known, disclosed gap, not a defect in the shipped feature —
the phase is fully wired, tested, and gate-approved; it simply hasn't been dogfogged yet. Left as a
known-follow-up rather than expanded into new epic scope.

## Test Summary
No new tests run directly by this epic (epic tier is scope-only). Aggregate child-ticket test
results: CORE-WIRING 98 passed, VOCAB-REGISTRATION 193 passed (124 narrow + 69 additional
downstream-affected), DASHBOARD-PALETTE 141 passed — all scoped pytest runs, no full-suite run per
Testing Rule. `python3 tools/agent-monitoring/validate.py` re-run directly during this epic's close
and confirms zero Document-Update/doc-updater vocabulary-drift warnings.

## Files Changed
- `docs/architecture/doc_updater_agent.md` — `## Status` updated from `Proposed` to `Accepted`
  (this epic's only direct file edit).

All other implementation files were changed by the three child tickets individually (see each
ticket's own `## Files Changed` in `tickets/done/`); not re-listed here to avoid duplicate
attribution.

## Completion Summary
All three child tickets (core wiring, vocabulary registration, dashboard palette registration)
shipped and reached `DONE` in dependency order. The Document-Update phase and doc-updater agent
are live in `implement-ticket.js` for every tier including hotfix, correctly seamed before the
doc-staleness gate, with no vocabulary drift across `vocabulary.py`, the glossary registry, or the
dashboard phase palette. `docs/architecture/doc_updater_agent.md` is promoted to Accepted as part
of this close. One real investigation gap (the `agent-orchestration/` duplicate vocabulary site)
was found and fixed during child-ticket execution rather than at epic-scoping time; documented
above rather than silently absorbed. The one open, disclosed item is that the new phase has not yet
been exercised on a real ticket in this session — a known follow-up, not a blocker to this epic's
completion.

