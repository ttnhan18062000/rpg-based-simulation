---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW
artifact_type: plan
tags: [agent-monitoring, governance]
---

# Plan

1. `record_hand_orchestrated_closure.py`: a `--review-ref` option (`<PR#>#<comment id>`, both whole numbers, validated before anything is written). A pure function `review_ref_event(ref, default_agent)` builds the Review event: `status: ok`, summary naming the ref and saying the planner's PR review stands in for the step. In `main`, when a ref is given: refuse it if the tier plan has no `full` Review (hotfix) or the closer narrated a Review event; otherwise add the event before `folded_phase_events` so the fold leaves Review alone. Architecture-Verify stays skipped.
2. `path_report.py`: add one sentence to the Paths footer saying a Review recorded with a review ref counts as `ran`, not skipped (no counting change; a test pins it).
3. Docs: the README paragraph on folded phases, the module docstring, `docs/guides/delivery_process.md` only if it names the closure flags (check). CLAUDE.md is out of scope: name the example wording in the PR body.
4. Tests in `tests/tools/test_closure_recorder_folded_phases.py`: ref -> Review `ok` carrying the ref and the plan order; no ref -> byte-identical to today; bad ref, hotfix and narrated Review are refused; `path_report` stops counting a ref'd Review as skipped.
5. Own closures: `--review-ref` only once a PR review exists; until then these stay skipped.
