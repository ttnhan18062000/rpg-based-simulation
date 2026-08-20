---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP
phase: done
date: 2026-08-20
tags: [documentation, process-improvement]
---

# TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP

## Title
Delete fully-shipped `experiments/placement_integrity/` and archive `docs/plans/idea_placement_legality_check.md`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`experiments/placement_integrity/` was the investigation sandbox behind the placement-legality
mini-epic. Its findings shipped as `TCK-20260716-PLACELEGAL-HARDLAW` (DONE 2026-07-30) and
`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (DONE 2026-07-30) — `tickets/working_log.csv` line 1146
literally states "Closes the placement-legality mini-epic (2/2 tickets done)". A related
follow-up root-cause fix, `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`, is
also DONE (2026-08-17). Nothing further is scoped or pending against this investigation area.

`experiments/` is explicitly workflow-exempt sandbox scaffolding — per its own stated convention
(`experiments/loop/PROPOSAL.md`: "only a *result* the loop finds ever graduates into a real
ticket") and the direct precedent `TCK-20260804-PLANS-EXPERIMENTS-SWEEP` (DONE 2026-08-04, same
layer, same tag pair), completed `experiments/` folders are deleted outright once their finding
has graduated elsewhere — never archived.

`docs/plans/idea_placement_legality_check.md` is a distillation of that same investigation trail
(its own header cites `experiments/placement_integrity/PROPOSAL.md` as "the full investigation
trail and prototype code this doc distills") and the work it describes is now fully shipped, so
per the same precedent it follows the `docs/plans/` disposal path instead: archive into
`docs/plans/archive/`, not delete.

## Scope
- Delete `experiments/placement_integrity/` in full (`PROPOSAL.md` and
  `prototype/check_placement.py`) — no archive, matching `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`'s
  established `experiments/` disposal convention exactly.
- Move `docs/plans/idea_placement_legality_check.md` to
  `docs/plans/archive/idea_placement_legality_check.md` (same relative path, mirrored under
  `archive/`, via `git mv` to preserve history), updating its frontmatter to add
  `maturity: shipped`, `archived: 2026-08-20`, and change `status: idea` → `status: historical`,
  while leaving its other existing frontmatter fields (`layer`, `authority`, `audience`, `date`,
  `tags`) untouched — matching the exact frontmatter shape already used by every file already
  under `docs/plans/archive/` (verified directly against
  `docs/plans/archive/idea_information_belief_trigger_wiring.md`).
- Fix the one confirmed live-code dangling reference: `tests/engine/test_hard_law_monitor.py`
  lines 237–238 cite both `docs/plans/idea_placement_legality_check.md` and
  `experiments/placement_integrity/PROPOSAL.md` by their old paths in an "Originating evidence"
  comment — update to the new archive path and drop the now-nonexistent `experiments/` citation
  (or note that the source sandbox was deleted post-graduation, whichever reads more accurately
  in context).
- Regenerate `docs/REGISTRY.yaml` (docs/ content changed; hotfix tier still requires this per the
  project's "After Work" rule) and stage it.

## Out of Scope
- The 5 other `experiments/` folders (`audit_expansion/`, `loop/`, `model_routing/`,
  `cost_proxy_calibration/` remnants, `spatial_rendering/`) — each still self-declares
  incomplete/partial status; not touched by this ticket.
- Any other `docs/plans/` file — this ticket only moves the one named file.
- Re-litigating or re-verifying the placement-legality mechanics/findings themselves (the
  `LAW-SPAWN-OCCUPANCY` law, the SimQ WORLD-pillar signal, or the spawn-RNG root-cause fix) — all
  three are already DONE and out of scope for a docs/experiments housekeeping ticket.
- The building-vs-building / resource-vs-resource spawn-collision gap explicitly flagged as a
  separate future follow-up in `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`'s
  Completion Summary — not this ticket's job.
- Fixing dangling references inside frozen historical records (`tickets/done/`,
  `stored_artifacts/`, `docs/REGISTRY.yaml`'s own auto-generated entries) — these are
  self-correcting or intentionally-preserved historical snapshots, matching the exact precedent
  set by `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`'s own Acceptance Criteria wording.
- Creating `staging_artifacts/{ticket_id}/` — see Assumptions/Open Questions; this is a hotfix and
  the direct precedent ticket explicitly did not create one either.

## Acceptance Criteria
- [x] `experiments/placement_integrity/` does not exist anywhere in the working tree
      (`test ! -e experiments/placement_integrity`). Verified directly.
- [x] `docs/plans/idea_placement_legality_check.md` no longer exists at its original path and
      exists at `docs/plans/archive/idea_placement_legality_check.md`, with frontmatter
      `status: historical`, `maturity: shipped`, `archived: 2026-08-20` set, and passing
      `validate_frontmatter.py --content-type doc`. Verified directly (`OK: 1 file(s) checked —
      no violations`).
- [x] Repo-wide grep for the literal strings `experiments/placement_integrity` and
      `docs/plans/idea_placement_legality_check` (old, un-archived form) returns zero hits outside
      frozen historical records (`tickets/done/`, `stored_artifacts/`, `docs/REGISTRY.yaml`).
      **One exception found and deliberately left untouched, not silently missed**: see
      Implementation Notes — `experiments/spatial_rendering/PROPOSAL.md` (a different, still-open
      `experiments/` folder this ticket's own Out of Scope section explicitly protects) also cites
      the old `experiments/placement_integrity/PROPOSAL.md` path several times. This contradicts
      this ticket's own Assumptions/Open Questions claim that
      `tests/engine/test_hard_law_monitor.py` was the only live-code reference — corrected here.
- [x] `tests/engine/test_hard_law_monitor.py`'s "Originating evidence" comment no longer cites
      either old path as live (it now cites the new archived path and notes the sandbox folder was
      deleted after shipping, per the ticket's own instruction to "note the experiments/ folder was
      deleted after shipping" rather than delete the historical note entirely), and the file's
      relevant tests still pass (12/12 in `tests/engine/test_hard_law_monitor.py`).
- [x] `docs/REGISTRY.yaml` regenerated and reflects the archived doc's new path/frontmatter;
      staged alongside `agent-monitoring/` (not yet committed — commit is a separate, later step
      not performed by this Implement pass).

## Related Tickets
- TCK-20260804-PLANS-EXPERIMENTS-SWEEP (done) — direct precedent for the archive-vs-delete
  disposal split (`docs/plans/` → archive, `experiments/` → delete) and its exact frontmatter
  convention; same layer, same tag pair.
- TCK-20260716-PLACELEGAL-HARDLAW (done) — first shipped ticket from this investigation trail.
- TCK-20260716-PLACELEGAL-SIMQ-SIGNAL (done) — second shipped ticket; working_log explicitly
  marks this as closing the "placement-legality mini-epic (2/2 tickets done)".
- TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE (done) — later root-cause fix for
  the same underlying bug class; confirms nothing further is pending in this area.

## Related Docs
- `docs/plans/idea_placement_legality_check.md` — file being moved/archived.
- `docs/plans/archive/` — destination; existing contents establish the exact frontmatter
  convention this ticket follows.
- `experiments/loop/PROPOSAL.md` — states the `experiments/` disposal convention directly
  (delete-only-graduated-work, no archive).
- `tickets/done/placement-legality/SEQUENCE.md` — records the two-ticket mini-epic sequence that
  is the shipped output of this experiments folder.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260716-PLACELEGAL-HARDLAW/` (plan.md, investigation.md, test_plan.md) —
  cites the old `experiments/placement_integrity` path; frozen historical record, left untouched
  by design (matches precedent).
- `stored_artifacts/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE/` —
  investigation.md cites the old idea-doc path; same treatment.
- No stored artifacts exist for this ticket's own investigation — hotfix tier, self-evident scope
  captured directly in this ticket (see Assumptions/Open Questions).

## Related Code Areas
- `experiments/placement_integrity/` (delete: `PROPOSAL.md`, `prototype/check_placement.py`)
- `docs/plans/idea_placement_legality_check.md` → `docs/plans/archive/idea_placement_legality_check.md`
- `tests/engine/test_hard_law_monitor.py` (dangling-reference comment fix)
- `docs/REGISTRY.yaml` (regenerated)

## Assumptions / Open Questions
- `layer: guidelines` chosen to match `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`'s own layer for the
  identically-shaped work (docs/experiments housekeeping) — confirmed registered via
  `python3 tools/layer_registry.py list`. Not `misc`; a genuine fit exists.
- The dispatching request's generic step 7 said to create `staging_artifacts/{ticket_id}/`, but
  this is a hotfix, and CLAUDE.md's Hard Rule is explicit: "Hotfix: No staging artifacts required —
  self-evident intent is captured in the ticket itself." The direct precedent ticket
  (`TCK-20260804-PLANS-EXPERIMENTS-SWEEP`) confirms this in its own Related Stored Artifacts
  section ("None — hotfix tier, no staging artifacts required"). No `staging_artifacts/` directory
  was created for this ticket; if that's wrong for this case, say so and one will be added.
- Assumes `tests/engine/test_hard_law_monitor.py:237-238` is the only live-code (non-frozen-history)
  reference to either old path — confirmed via exhaustive repo-wide grep for both exact strings;
  all other hits are in `tickets/done/`, `stored_artifacts/`, or `docs/REGISTRY.yaml`.
- Assumes the idea doc's other frontmatter fields (`layer: engine`, `authority: P2`,
  `audience: developer`, `date: 2026-07-16`, `tags: [idea, hard-law-monitor, world-generation,
  simulation-quality, determinism, correctness]`) should stay as-is during the archive move,
  matching precedent (only `status`/`maturity`/`archived` are touched, not the doc's original
  authoring metadata).

## Implementation Notes
Executed exactly per scope, mirroring `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`'s established
convention:
1. `git rm -r experiments/placement_integrity/` — deleted `PROPOSAL.md` and
   `prototype/check_placement.py` in full, no archive.
2. `git mv docs/plans/idea_placement_legality_check.md
   docs/plans/archive/idea_placement_legality_check.md`, then edited frontmatter only
   (`status: idea` → `historical`, `maturity: idea` → `shipped`, added `archived: 2026-08-20`),
   preserving key order and leaving all other frontmatter fields and the body's own
   `> **Maturity: IDEA**` callout untouched — confirmed this matches the exact shape of
   `docs/plans/archive/idea_information_belief_trigger_wiring.md` (that precedent file also leaves
   its own body `Maturity: IDEA` line untouched, frontmatter-only edit). Re-validated with
   `validate_frontmatter.py --content-type doc` → `OK: 1 file(s) checked — no violations`.
3. Updated the "Originating evidence" comment in
   `tests/engine/test_hard_law_monitor.py` (lines 237-238) to cite the new archive path and note
   the sandbox folder was deleted after shipping, per the explicit instruction not to delete the
   historical note (it documents originating evidence for a `regression`-marked test per
   `docs/testing/test_taxonomy.md`'s convention). 12/12 tests in that file still pass.
4. Regenerated `docs/REGISTRY.yaml` (`make docs-registry`) — confirmed via `git diff` it reflects
   only the path rename (`docs/plans/idea_placement_legality_check.md` →
   `docs/plans/archive/idea_placement_legality_check.md`), no unrelated churn. Pre-existing,
   unrelated `ERROR: 1 doc file(s) missing frontmatter: docs/brainstorm/character_capabilities_review.md`
   surfaced during regen — not caused by this ticket's changes, left untouched (out of scope).
   `make knowledge-index-update` was attempted per the "After Work" rule (docs content changed) but
   failed with a pre-existing environment limitation (no network access to
   `https://huggingface.co` for the embedding model download) — a known local-sandbox gap, not
   something this ticket's changes caused or can fix; noted here rather than silently skipped.

**Deviation / discrepancy found and reported, not silently resolved**: the final repo-wide grep
(step 4 of the dispatching instructions) found one additional live reference this ticket's own
Assumptions/Open Questions section did not anticipate — `experiments/spatial_rendering/PROPOSAL.md`
cites `experiments/placement_integrity/PROPOSAL.md` roughly a dozen times throughout its own body
text (describing it as "the sibling proposal that took over all placement-legality scoring").
`experiments/spatial_rendering/` is one of the 5 other `experiments/` folders this ticket's own
Out of Scope section explicitly protects ("each still self-declares incomplete/partial status; not
touched by this ticket"), and `experiments/` folders are themselves workflow-exempt investigation
sandboxes (per `experiments/loop/PROPOSAL.md`'s stated convention) rather than live, correctness-
sensitive code — closer in kind to a frozen historical record than a dangling live reference that
needs fixing. Given the ticket's own explicit Out-of-Scope guard, left this file untouched rather
than silently expanding scope to edit a different, still-open experiments folder; flagging the
discrepancy here so it's visible rather than hidden. No other unexpected hits were found — final
grep confirms exactly 3 files remain: the archived doc's own self-referential body text (its own
historical narrative, left untouched per the same frontmatter-only-edit convention as the
precedent ticket), `experiments/spatial_rendering/PROPOSAL.md` (as above), and
`tests/engine/test_hard_law_monitor.py` (intentionally still mentions the old path once, as a
historical note that the folder was deleted — not a dangling reference).

No `staging_artifacts/` were created — hotfix tier, matching the precedent ticket's own explicit
justification.

**Incident: this ticket's file operations were reverted by a concurrent session, then redone —
documented, not silently re-asserted.** After the above work first landed (uncommitted, sitting in
the shared git working tree — this repo's working directory is shared across concurrent Claude
sessions per CLAUDE.md's PR Lifecycle guidance), a different concurrent session committed
`d57da64a` ("Revert accidental inclusion of another session's experiments-cleanup work"), which
restored `experiments/placement_integrity/` and `docs/plans/idea_placement_legality_check.md` to
their pre-sweep state. That session mistook this ticket's genuine, deliberate, already-completed
work — sitting uncommitted in the shared index — for accidental cross-session contamination (the
same failure mode this session's own CLAUDE.md write-up already documents from the other
direction). This was caught during this ticket's own Verify phase, when independent verification
found the claimed deletions/archive-move absent from the working tree despite the ticket body
asserting they were done. Redone immediately after discovery: `git rm -r
experiments/placement_integrity/`, `git mv docs/plans/idea_placement_legality_check.md
docs/plans/archive/idea_placement_legality_check.md` + frontmatter edit, `docs/REGISTRY.yaml`
regenerated fresh (confirmed via `git diff --stat`: exactly 16 lines changed, a clean path-rename
diff with no unrelated churn). All re-verified via the same independent checks used the first
time (existence checks, `validate_frontmatter.py`, repo-wide grep, `pytest`) — all pass. This time,
committed promptly (see Files Changed / commit below) rather than left open in the shared working
tree, to close the collision window that caused the first revert.

## Test Summary
```
pytest tests/engine/test_hard_law_monitor.py -q
```
12 passed, 0 failed. `validate_frontmatter.py --content-type doc
docs/plans/archive/idea_placement_legality_check.md` → OK, no violations.

## Files Changed
- `experiments/placement_integrity/PROPOSAL.md` — deleted.
- `experiments/placement_integrity/prototype/check_placement.py` — deleted.
- `docs/plans/idea_placement_legality_check.md` → `docs/plans/archive/idea_placement_legality_check.md`
  (`git mv`; frontmatter updated: `status: historical`, `maturity: shipped`,
  `archived: 2026-08-20`).
- `tests/engine/test_hard_law_monitor.py` — "Originating evidence" comment updated to cite the new
  archive path and note the sandbox folder's deletion (comment-only change, no test logic change).
- `docs/REGISTRY.yaml` — regenerated to reflect the archived doc's new path.
- `tickets/inprogress/TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP.md` — this ticket file
  (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary sections filled in during this Implement pass).

## Completion Summary
Deleted the fully-shipped `experiments/placement_integrity/` sandbox outright (no archive, per the
established `experiments/` disposal convention) and archived
`docs/plans/idea_placement_legality_check.md` into `docs/plans/archive/` via `git mv`, updating its
frontmatter to `status: historical`/`maturity: shipped`/`archived: 2026-08-20` to match the exact
shape of existing archived docs. Fixed the one dangling live-code reference
(`tests/engine/test_hard_law_monitor.py`'s "Originating evidence" comment) to cite the new archive
path while preserving its historical-note purpose, confirmed via a passing 12/12 test run.
Regenerated `docs/REGISTRY.yaml`. A final repo-wide grep found and reported one additional
reference this ticket's own Assumptions section had not anticipated
(`experiments/spatial_rendering/PROPOSAL.md`, a different still-open experiments folder this
ticket's Out of Scope explicitly protects) — deliberately left untouched rather than silently
expanding scope, and the discrepancy is documented above for whoever reviews this ticket next. Pure
docs/experiments housekeeping; no `src/` behavior changed.
