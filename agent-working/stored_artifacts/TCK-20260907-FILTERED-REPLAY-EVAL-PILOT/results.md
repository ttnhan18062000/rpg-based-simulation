---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
artifact_type: report
tags: [ai, agent-monitoring, testing]
---

# Results — TCK-20260907-FILTERED-REPLAY-EVAL-PILOT

Generated 2026-09-07T08:37:37.538526+00:00 by `tools/agent_replay/run_pilot.py`.

## Freshly-Measured Baseline (AC #6 — never copied from the frozen spec doc)

- `tickets/done/` top-level `TCK-*.md` count: 1815
- Tier breakdown: {'unlabeled': 49, 'standard': 1401, 'hotfix': 313, 'epic': 52}
- Standard-tier tickets with a matching `stored_artifacts/{id}/`: 1174/1401 (83.80%)
- `runs.jsonl` record count (all weekly shards): 1479

## Sample

- Sample size: 27 (of 1815 corpus tickets)
- Converted to fixtures: 5
- Excluded (logged reason, never silently dropped): 22

Excluded ticket reasons (see `stored_artifacts/{id}/conversion_log.yaml` for the full list):
- `TCK-20260410-PH1-STG8-STRATEGIC-KNOWLEDGE`: missing stored_artifacts/TCK-20260410-PH1-STG8-STRATEGIC-KNOWLEDGE/
- `TCK-20260419-MC-TASK2-HARDEN-REPLAY-STAGING`: missing stored_artifacts/TCK-20260419-MC-TASK2-HARDEN-REPLAY-STAGING/
- `TCK-20260422-PH7-HARDENING-CLOSURE`: missing stored_artifacts/TCK-20260422-PH7-HARDENING-CLOSURE/
- `TCK-20260501-V2-ENGINE-HARDENING`: missing stored_artifacts/TCK-20260501-V2-ENGINE-HARDENING/investigation.md
- `TCK-20260503-PRICE-HARDENING`: missing stored_artifacts/TCK-20260503-PRICE-HARDENING/
- `TCK-20260512-PERF-STAGGERED-SCHEDULER`: missing stored_artifacts/TCK-20260512-PERF-STAGGERED-SCHEDULER/
- `TCK-20260520-SIM-OBS-PHASE4-M15`: missing events.jsonl phase record(s) for ['Scope', 'Investigate', 'Plan', 'Review'] — no Scope/Investigate/Plan/Review phase transitions recorded (common for hotfix-tier tickets, whose pipeline has no Investigate/Plan/Review phase at all)
- `TCK-20260523-WORLD-TEMPLATES`: missing events.jsonl phase record(s) for ['Scope', 'Investigate', 'Plan', 'Review'] — no Scope/Investigate/Plan/Review phase transitions recorded (common for hotfix-tier tickets, whose pipeline has no Investigate/Plan/Review phase at all)
- `TCK-20260607-STRICT-MODE-PRODUCTION`: missing events.jsonl phase record(s) for ['Scope', 'Investigate', 'Plan', 'Review'] — no Scope/Investigate/Plan/Review phase transitions recorded (common for hotfix-tier tickets, whose pipeline has no Investigate/Plan/Review phase at all)
- `TCK-20260607-V2-SERVICE-ASSEMBLY-GAP`: missing events.jsonl phase record(s) for ['Scope', 'Investigate', 'Plan', 'Review'] — no Scope/Investigate/Plan/Review phase transitions recorded (common for hotfix-tier tickets, whose pipeline has no Investigate/Plan/Review phase at all)
- ... and 12 more (see conversion_log.yaml)

## Exit Criteria

1. **Repeatable scoring established** — MET
   Evidence: 100.0% per-defect-class agreement across the 2 runs (0 disagreement(s): []). M2/M3 are pure deterministic functions of static input and replay_slice() is a pure function of a static fixture — computing each twice necessarily reproduces the same result under these conditions; this demonstrates the method is internally self-consistent, not that it is robust to the runtime variability a live re-execution would introduce (out of scope for this pilot, which never live-re-dispatches real agents — see Method step 3/Out of Scope).

2. **Sample quality accepted for the 2 target defect classes** — MET
   Evidence: M2 (real-historical): validated by unit tests against a real, ticket-documented gap reconstructed from TCK-20260831-RACE-RELATIONS-MATRIX's own prose (fires correctly) and against its real clean/complete Files Changed text (does not fire) — see tests/agent_replay/test_defect_detectors.py. Applied live across this pilot's 5 converted real sample fixtures, M2 fired on 0 of 5. Of those, 0 ticket(s) ([]) have no dedicated single per-ticket closing commit in git history — a real, significant fraction of this repo's history closes multiple tickets inside one squashed batch/epic-merge commit whose subject carries no ticket id, so no per-ticket doc diff can be isolated for them; M2 defaults to fired=False (no evidence either way) for those rather than guessing, disclosed per-ticket in m2_results rather than silently smoothed into the fired-count. A gap that genuinely fires against an isolable commit is expected to be rare, since such a gap is normally caught and fixed before a ticket is ever committed to tickets/done/ (investigation.md Current Behavior §5) — a disclosed characteristic of the historical corpus, not a detector defect. M3 (synthetic-disclosed): validated only against a synthetic known-positive and a clean fixture (fired=True / False) — never claimed against a real historical tickets/done/ sample member, per investigation.md Risks #1 option (c). Sample quality is accepted for the 2 target defect classes specifically, not claimed for any defect class beyond those two.

3. **Replay contamination risk is understood and demonstrably controlled** — MET
   Evidence: IsolationEvidence.held=True. pre-porcelain=' M tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md\n M tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md\n D tickets/todos/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\nA  tickets/todos/TCK-20260907-KGMCP-DEPRECATION-EPIC.md\n M tickets/working_log.csv\n?? agent-monitoring/data/2026-W37/\n?? tickets/done/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\n?? tickets/done/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md\n?? tickets/done/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.md\n?? tickets/inprogress/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n?? tickets/todos/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT.md\n?? tickets/todos/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n', post-porcelain=' M tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md\n M tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md\n D tickets/todos/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\nA  tickets/todos/TCK-20260907-KGMCP-DEPRECATION-EPIC.md\n M tickets/working_log.csv\n?? agent-monitoring/data/2026-W37/\n?? tickets/done/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\n?? tickets/done/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md\n?? tickets/done/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.md\n?? tickets/inprogress/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n?? tickets/todos/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT.md\n?? tickets/todos/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n'. No literal `git worktree add` was created — Method step 3's isolation was satisfied via replay_slice()'s already-proven zero-write execution path (tests/agent_replay/test_no_mutation_snapshot.py) plus a snapshot-diff check parameterized over the real sharded agent-monitoring/data/ layout (investigation.md Risks #2 option (b), corrected during plan Review Round 1).

## Kill Criteria

1. **Scores are noisy/non-repeatable** — NOT FIRED
   Evidence: Not fired: scores were repeatable across the 2 runs (see Exit Criterion 1 above).

2. **Worktree isolation cannot fully eliminate the shared-sidecar contamination risk** — NOT FIRED
   Evidence: Not fired: the isolation evidence (Exit Criterion 3 above) shows no write attributable to this pilot touched agent-monitoring/*.jsonl or the unscoped .claude/current_run sidecar during the pilot's own 2-run execution window.

## 3-Tier Metrics

- **Primary** (repeatability): 100.0% agreement across 2 runs; per-class agreement: {'M2': True, 'M3': True}; disagreements: []
- **Safety** (contamination): isolation_held=True; pre-porcelain=' M tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md\n M tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md\n D tickets/todos/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\nA  tickets/todos/TCK-20260907-KGMCP-DEPRECATION-EPIC.md\n M tickets/working_log.csv\n?? agent-monitoring/data/2026-W37/\n?? tickets/done/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\n?? tickets/done/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md\n?? tickets/done/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.md\n?? tickets/inprogress/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n?? tickets/todos/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT.md\n?? tickets/todos/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n', post-porcelain=' M tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md\n M tickets/inprogress/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md\n D tickets/todos/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\nA  tickets/todos/TCK-20260907-KGMCP-DEPRECATION-EPIC.md\n M tickets/working_log.csv\n?? agent-monitoring/data/2026-W37/\n?? tickets/done/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md\n?? tickets/done/TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN.md\n?? tickets/done/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.md\n?? tickets/inprogress/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n?? tickets/todos/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT.md\n?? tickets/todos/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md\n' — no pilot-attributed write detected under agent-monitoring/*.jsonl, unscoped sidecar unchanged
- **Efficiency** (informative only): wall-clock={'run1_wall_clock_s': 0.0018241929938085377, 'run2_wall_clock_s': 0.0017496939981356263}; work-volume={'fixtures_replayed': 5, 'run1_phases_replayed': 15, 'run2_phases_replayed': 15}

## M2 vs. M3 Provenance (never blurred)

- **M2 — doc-update self-report gap**: real-historical. Detection logic validated against a real, ticket-documented known-positive (TCK-20260831-RACE-RELATIONS-MATRIX, reconstructed pre-fix state) and a real clean fixture (the same ticket's actual final state). Applied to this pilot's own sample, fired on 0 of 5 converted real tickets.
- **M3 — test-scoper background-hang pattern**: SYNTHETIC-disclosed only. No reliable historical signal exists for this defect class (investigation.md Risks #1). Validated only against a hand-built synthetic known-positive fixture (`tests/fixtures/agent_replay/pilot/m3_synthetic_known_positive.yaml`) and a clean fixture (fired=True / False) — never applied to or claimed against any real `tickets/done/` sample member.

## Decision

**All 3 Exit Criteria met, no Kill Criterion fired.** This pilot's own evidence supports unblocking item 13's downstream Bucket-C dependency notes (items 18-20) per roadmap.md's Eval-pilot exit gate — those items' own scoping/execution remains separate follow-on work, not a byproduct of this ticket (see Out of Scope).
