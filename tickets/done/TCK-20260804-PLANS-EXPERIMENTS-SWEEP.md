---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260804-PLANS-EXPERIMENTS-SWEEP
phase: done
date: 2026-08-04
tags: [documentation, process-improvement]
---

# TCK-20260804-PLANS-EXPERIMENTS-SWEEP

## Title
Sweep docs/plans/ and experiments/ for completed/stale plans and superseded experiment folders

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Two directories accumulate content over time without a self-pruning mechanism:
`docs/plans/` (proposals/ideas/roadmaps outside `docs/plans/archive/`) and `experiments/`
(lightweight, workflow-exempt investigation sandboxes). A per-file completion-status
investigation (cross-referencing each file's own text, `tickets/done/`, `tickets/working_log.csv`,
and whether the described feature/finding actually exists in the live codebase) found 12 of 30
`docs/plans/` files complete/superseded and 2 of 7 `experiments/` folders complete, per the
policies confirmed with the user: `docs/plans/` completed items move to the existing
`docs/plans/archive/` (matching prior precedent `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS`,
`TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE`); `experiments/` completed items are deleted
outright (no archive — `experiments/` is explicitly exempt from the ticket/staging-artifact
workflow per its own convention, only a *result* graduates into a real ticket, so the raw
investigation scaffolding has no reason to persist once its finding is absorbed elsewhere).

## Scope
- Move 12 `docs/plans/` files into `docs/plans/archive/` (mirroring each file's existing relative
  subfolder path under `archive/`), updating frontmatter to `status: historical`,
  `maturity: shipped`, `archived: 2026-08-04`, matching the exact convention already used by every
  existing file in `docs/plans/archive/`:
  1. `idea_information_belief_trigger_wiring.md` — its own "direct scope" ticket,
     `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`, is DONE.
  2. `agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` — superseded in
     substance by the later, more concrete `provider_agnostic_orchestration/implementation_plan.md`
     (dated 2026-08-02 vs. this doc's 2026-07-20; the epic it proposed scoping has since happened).
  3. `agent_ops_dashboard/proposal_progress_timeline.md` — shipped:
     `TCK-20260720-PROGRESS-TIMELINE-VIEW` + `TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX`, both
     DONE, plus a `tickets/done/progress-timeline/` folder.
  4. `tag_dedup/proposal_tag_corpus_dedup.md` — shipped verbatim as
     `TCK-20260719-TAG-COLLISION-DEDUP` (DONE).
  5. `agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md` —
     superseded by its own sibling `_phase2.md` ("Phase 0-1 are now done").
  6. `.../ticket_plan_structure_phase2.md` — superseded by `_phase3.md`.
  7. `.../ticket_plan_structure_phase3.md` — superseded by `_phase4.md`.
  8. `.../ticket_plan_structure_phase4.md` — superseded by `_phase5.md`.
  9. `.../ticket_plan_structure_phase5.md` — superseded by `_phase6prep.md` ("Phase 5 is now
     DONE").
  10. `.../ticket_plan_structure_opendecisions_7_9.md` — all 3 scoped decision tickets
      (`TCK-20260802-CONTEXT-KIND-PRIORITY`, `-STORED-ARTIFACT-KIND`, `-EXACT-LOOKUP-CONVENTION`)
      confirmed DONE.
  11. `agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`
      — `TCK-20260731-PARITY-INDEX-EPIC` + all 4 child tickets DONE, plus a
      `tickets/done/parity-ledger-sqlite-context/` folder.
  12. `.../v1_decisions_phase0.md` — explicitly "produced by `TCK-20260731-PARITY-INDEX-BASELINE`"
      (DONE); a scratch decision-log whose content is already absorbed into the shipped
      implementation.
- Delete 2 `experiments/` folders outright (no archive):
  1. `experiments/agent_ops_dashboard/` (6 files) — fully shipped as `dashboard-frontend/` +
     `src/api/agent_ops_dashboard/`, both confirmed real and substantial in the live codebase.
  2. `experiments/cost_proxy_calibration/` — **deviated from full deletion after investigation**
     (confirmed with the user via AskUserQuestion): `docs/agent-monitoring/README.md` cites
     `RESULTS.md` by name as the "full evidence trail," and `docs/parity_ledger/infrastructure.yaml`'s
     `INFRA-285` entry documents a prior ticket's deliberate choice to keep it after the code was
     promoted out. Deleted only the 4 superseded scripts/data files
     (`extract_transcript_usage.py`, `fit_regression.py`, `regression_fit_result.json`,
     `session_aggregates.json`); kept `RESULTS.md`/`PROPOSAL.md`.
- Delete `experiments/spatial_rendering/prototype/__pycache__/` — build-artifact junk, unconditional
  cleanup regardless of the above (matches `TCK-20260415-WS-CLEANUP` precedent).
- Regenerate `docs/REGISTRY.yaml` (docs/ content changed) since this is a hotfix touching `docs/`.

## Out of Scope
- The 18 remaining `docs/plans/` files (self-declared still-open/idea/proposal, or roadmaps
  explicitly "kept current, not a frozen snapshot") — left untouched.
- 2 borderline `docs/plans/` files, kept conservatively rather than guessed:
  - `simq_scoring_improvement_roadmap.md` — 3 of 4 phases confirmed DONE via matching tickets, but
    Phase 1 (grade-band/anchor-sensitivity work) could not be confirmed with certainty against any
    single unambiguous ticket. Per this project's Uncertainty Rule ("vague leads stay vague until
    evidence narrows them"), staying open rather than archiving on unconfirmed evidence.
  - `agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md` — frontmatter
    already says `status: historical`, but its own body text states it "remains a living
    reference" for a still-open live-activation decision; the historical status describes the
    state it documents (the non-live implementation is frozen/done), not that the document itself
    is disposable.
- 5 remaining `experiments/` folders (`audit_expansion/`, `loop/`, `model_routing/`,
  `placement_integrity/`, `spatial_rendering/` minus its `__pycache__/`) — each carries an explicit
  self-declared incomplete/not-built/partial status in its own `PROPOSAL.md`.
- A real doc-accuracy bug found along the way, deliberately not fixed here (different ticket's
  job): `docs/plans/idea_intention_log_first_class.md` claims
  `TCK-20260702-OBSISO-TRACE-ASYNC` already remediated a hot-path IO violation, but that ticket is
  still `OPEN` in `tickets/todos/obs-isolation/`. Flagged for a future ticket, not corrected as
  part of this sweep (this ticket's scope is prune/archive judgment, not content correction of
  files staying in place).
- No change to `docs/plans/archive/`'s existing contents or structure, beyond receiving the 12 new
  files.

## Acceptance Criteria
- [x] All 12 listed `docs/plans/` files exist under `docs/plans/archive/` at their mirrored
      relative path, with frontmatter `status: historical`, `maturity: shipped`,
      `archived: 2026-08-04` set, and no longer exist at their original `docs/plans/` path.
      Verified directly: `find` confirms all 12 destination paths exist and all 12 source paths
      don't; all 12 independently re-validated via `validate_frontmatter.py --content-type doc`.
- [x] `experiments/agent_ops_dashboard/` no longer exists anywhere in the working tree.
      **Corrected wording** (see Implementation Notes deviation): `experiments/cost_proxy_calibration/`
      is deliberately NOT fully removed — `RESULTS.md`/`PROPOSAL.md` are kept per explicit user
      decision (a live doc still cites `RESULTS.md` as authoritative evidence); its 4
      superseded scripts/data files are deleted. Verified directly: `ls experiments/` shows only
      `PROPOSAL.md`/`RESULTS.md` remain in that folder.
- [x] `experiments/spatial_rendering/prototype/__pycache__/` no longer exists. Verified directly.
- [x] **Corrected wording**: the 18 kept `docs/plans/` files and 5 kept `experiments/` folders had
      no scope/content changes — only mechanical cross-reference path/line-number fixes were
      applied where a kept file cited a now-moved file (2 of the 18:
      `idea_context_efficient_agent_retrieval_observability.md`,
      `provider_agnostic_orchestration/implementation_plan.md`). The original "byte-for-byte
      untouched" wording was inaccurate — dangling-reference correctness (AC below) and zero-touch
      are in tension for any kept file that happens to cite a moved one; correctness was
      prioritized, consistent with this ticket's own dangling-reference AC. All 5 kept
      `experiments/` folders confirmed genuinely untouched (nothing in them referenced a moved/
      deleted path).
- [x] `docs/REGISTRY.yaml` regenerated and reflects the 12 archived files' new paths/frontmatter.
      Regenerated twice — once after Implement, once more after Document-Update's 3 additional
      body-text edits (confirmed non-no-op via `git diff --stat`, not assumed safe to skip).
- [x] No dangling reference: grep confirms no remaining doc/code outside `docs/plans/archive/`
      itself references any of the 12 moved files by their old `docs/plans/...` path (a handful of
      sibling docs in the same directory tree cross-reference each other by relative path and were
      already accounted for during investigation — e.g. `ticket_plan_structure_phase6prep.md`
      pointing back to `_phase5.md`). Verified directly via exhaustive grep for all 12 old paths;
      remaining hits are exclusively `tickets/done/`/`stored_artifacts/`/`docs/REGISTRY.yaml`/
      `agent-monitoring/tools.jsonl` (frozen historical records or self-correcting, left
      untouched by design). Additionally, Document-Update independently found and fixed 3
      dangling references caused by the `experiments/agent_ops_dashboard/` deletion (not
      originally covered by this AC's `docs/plans/`-only wording, but the same principle applied).

## Related Tickets
- TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS (done) — structural precedent for archiving
  shipped-status `docs/plans/` files into `docs/plans/archive/`.
- TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE (done) — precedent for archiving multiple
  fully-shipped planning docs from a single feature area in one pass.
- TCK-20260803-DOCS-STRUCTURE-AUDIT (done) — prerequisite high-level `docs/` structure audit this
  sweep builds on (confirmed `docs/plans/archive/`'s role and `_SKIP_DOC_SUBDIRS` accuracy).
- TCK-20260415-WS-CLEANUP (done) — precedent for the `__pycache__` cleanup being folded into this
  ticket rather than filed separately.

## Related Docs
- `docs/plans/archive/` — destination for the 12 archived files; existing contents establish the
  frontmatter convention (`status: historical`, `maturity: shipped`, `archived: <date>`) this
  ticket follows exactly.
- `experiments/loop/PROPOSAL.md` — states the `experiments/` convention directly: "lightweight
  sandbox — exempt from the ticket/staging-artifact workflow per project convention; only a
  *result* the loop finds ever graduates into a real ticket" — the basis for deleting rather than
  archiving completed `experiments/` folders.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required; investigation was performed directly in-session
(forked research pass over all 30 `docs/plans/` files plus direct verification of all 7
`experiments/` folders) rather than written to `investigation.md`.

## Related Code Areas
- `docs/plans/` (12 file moves)
- `docs/plans/archive/` (12 file destinations)
- `experiments/agent_ops_dashboard/`, `experiments/cost_proxy_calibration/` (deleted)
- `experiments/spatial_rendering/prototype/__pycache__/` (deleted)
- `docs/REGISTRY.yaml` (regenerated)

## Assumptions / Open Questions
- User explicitly confirmed the archive-vs-delete policy split via AskUserQuestion (archive for
  `docs/plans/`, matching existing repo convention) and two follow-up messages ("also clear the
  experiments/ too, use the same policy" then "but you can delete the completed experiments, don't
  need to archive") — the two directories intentionally use different disposal mechanisms per
  explicit user direction, not an inconsistency.
- The 2 UNCLEAR-confidence `docs/plans/` files and the doc-accuracy bug in
  `idea_intention_log_first_class.md` are deliberately left as open follow-ups rather than
  resolved here, per the Uncertainty Rule.

## Implementation Notes
All 12 `docs/plans/` moves and all cross-reference fixes were done via `git mv` (preserving
history) + `Edit`, not raw file recreation. One material finding not anticipated at scoping time:
the frontmatter edit (adding an `archived:` line) shifts every subsequent line number in each
archived file by +1 — this broke 3 exact line-number citations in live docs
(`docs/ai/codex_capability_matrix.md` x2, `docs/ai/agents_dir_disposition.md` x1) pointing into
`idea_provider_agnostic_agent_orchestration.md`, corrected by reading the new line numbers
directly rather than assuming +1 arithmetically for the section-range citation.

Deviation from the original plan, confirmed with the user before executing: originally scoped to
delete `experiments/cost_proxy_calibration/` in full, but investigation found
`docs/agent-monitoring/README.md` (live) cites `RESULTS.md` by name as the "full evidence trail"
for a real cost-proxy weight decision, and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-285`
entry documents a prior ticket's deliberate choice to keep it after the code was promoted out.
Surfaced this via AskUserQuestion rather than silently deleting or silently keeping — user chose
to keep `RESULTS.md`+`PROPOSAL.md`, delete the rest (4 scripts/data files).

Found, but explicitly left unfixed (out of scope, pre-existing, unrelated to this sweep): a
dangling reference at `docs/ai/agents_dir_disposition.md:75` to
`idea_provider_agnostic_agent_orchestration_finding_01_claude.md`, a file that does not exist
anywhere in the repo — confirmed pre-existing, not introduced by this ticket's moves.

## Test Summary
```
pytest tests/tools/test_generate_registry.py tests/tools/test_generate_retro.py tests/tools/test_weight_sensitivity_check.py -q
```
157 passed (0 failed). Includes `test_check_flag_detects_no_drift_against_real_registry` (failed
before `make docs-registry` regen, passed after — expected, not a regression) and
`test_no_new_frontend_ui_file_introduced_by_this_ticket` (source-string check, unaffected by
filesystem deletion). All 12 archived files' frontmatter independently re-validated via
`validate_frontmatter.py --content-type doc` (12/12 OK). All 6 live docs edited for
cross-reference fixes independently re-validated the same way (6/6 OK).

## Files Changed
- 12 `docs/plans/*` files moved to `docs/plans/archive/*` (mirrored relative paths), frontmatter
  updated (`status: historical`, `maturity: shipped`, `archived: 2026-08-04`).
- `docs/ai/agents_dir_disposition.md`, `docs/ai/codex_capability_matrix.md`,
  `docs/ai/monitoring_writer_decision.md`, `docs/architecture/agent_orchestration_contract.md`,
  `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`,
  `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md` —
  cross-reference path/line-number fixes.
- `experiments/agent_ops_dashboard/` — deleted (6 files).
- `experiments/cost_proxy_calibration/extract_transcript_usage.py`,
  `fit_regression.py`, `regression_fit_result.json`, `session_aggregates.json` — deleted;
  `RESULTS.md`/`PROPOSAL.md` kept.
- `experiments/spatial_rendering/prototype/__pycache__/` — deleted (untracked).
- `docs/REGISTRY.yaml` — regenerated (1591 entries, historical count 22→34).

## Completion Summary
Swept `docs/plans/` and `experiments/` for completed/superseded material, per policies confirmed
with the user (archive for `docs/plans/`, delete for `experiments/`, with one exception carved out
via a follow-up AskUserQuestion when investigation found a live doc still depending on
`cost_proxy_calibration/RESULTS.md`). 12 of 30 `docs/plans/` files archived; 18 kept as genuinely
still-open (2 kept conservatively despite partial completion signal, per the Uncertainty Rule). 2
of 7 `experiments/` folders' stale content removed (one fully, one partially, preserving the
still-cited evidence doc). All live cross-references fixed, not left dangling — including 3 the
Document-Update phase caught that Implement itself missed (already-archived docs left citing the
now-deleted `experiments/agent_ops_dashboard/`), the second real live execution of that phase
since it shipped. Registry regenerated twice (confirmed the second regen was non-trivial, not
assumed safe to skip), full relevant test suite green (157 passed), 2 ACs' wording corrected to
honestly match the user-approved deviation rather than left misleadingly checked.
