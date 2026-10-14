---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT
phase: done
date: 2026-10-08
tags: [documentation]
---

# TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT

## Title
Docs drift: correct the visual-asset docs that still describe built pieces as unbuilt, and close the batch

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Child 7 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. drawing_tools.md:18 says the store is "designed, not built"; plans/visual-asset-foundation/README.md:70,106,150 list handoff.py and test_catalog_integrity as "later ticket" though both exist (internal gap audit #16).

## Scope
- Fix those and any other drift found while doing children 1-6; refresh docs/assets/session_handoff/ snapshots; `make knowledge-index-update`; SEQUENCE status; close the epic.
- Added by the planner (2026-10-09) after child 6 found git-ignored evidence: a tracked `<name>.txt` twin for EVERY ignored file under agent-working/stored_artifacts/TCK-*VISUAL-ASSETS*/ (the exact list in `evidence_twins_manifest.txt`), a guard test, no change to the shared .gitignore.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art.

## Acceptance Criteria
- [x] Named drift fixed; snapshots refreshed; batch closed.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT/ (plan, investigation, test_plan, mutant_proof, evidence_twins_manifest.txt with the exact list: 47 files, 223,833 bytes, each with its sha256)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
- Drift fixed: drawing_tools.md, the foundation plan README, visual_assets/README.md, the register's summary rows for W02.7/W03.1/W06.3. Snapshots refreshed (the planner's own handover is stale: it says paused after child 4; flagged in the snapshot).
- Evidence repair: 47 tracked `.json.txt` twins beside the git-ignored originals (originals untouched, byte-identical, listed with sha256 in the manifest); guard `tests/visual_assets/test_stored_evidence_tracked.py`. **Disclosure: the evidence for the merged PR #418 and the earlier M5 work (browser captures, blind-check answers, look-alike reports, rule results) was local-only until this batch.**
- Epic `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` closed, folder moved to done.

## Test Summary
- 6 guard tests; the planted-mutant check failed the real-tree tests as intended. Scoped suites: see the commit report.

## Files Changed
- docs (drawing_tools, foundation plan, m1 register, session_handoff x2), visual_assets/README.md, 47 `.json.txt` twins under agent-working/stored_artifacts, tests/visual_assets/test_stored_evidence_tracked.py, tickets and artifacts.

## Completion Summary
The named docs drift is fixed, the evidence that only existed on one disk is tracked beside its originals with a guard against it recurring, the snapshots are refreshed and the batch is closed.
