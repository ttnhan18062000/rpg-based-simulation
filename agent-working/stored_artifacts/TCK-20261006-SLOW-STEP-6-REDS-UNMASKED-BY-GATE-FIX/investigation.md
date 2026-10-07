---
status: historical
layer: testing
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX
phase: done
date: 2026-10-06
tags: [testing, investigation]
---

# Investigation — TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX

## Findings
- Source run: `Slow regression` step 6 in 37403688489 (head 9299891a9): 8 failed, 112 passed, 57 skipped, 1 xfailed, 1 xpassed in 1:37:09. The reds were hidden because step 6 was skipped after every step-5 failure until #360.
- Bracket: step 6 was last green on `main` in 32937991342 (2026-08-26, head eedf7d5b). The bracket holds for 7 of the 8; the campaign test was added 2026-09-09 (#150), and Lane A bisected its first bad commit to #175 (bc00caa1a).
- Rows 1–2 (5k behavioural baseline, ph9 boss assertion): domain changes; ph9's cause is #356 (world-boss spawn default OFF, decision 14). Routed to Lane B.
- Row 3 (campaign event stream): no deliberate attacks, only incidental opportunity attacks; the test was split by #367 into strict xfails plus a passing invariant test.
- Row 4 (Milestone B gate): test artefact, a per-call fake clock; fixed by #373.
- Rows 5–8 (perf timeouts): a real engine regression, not a budget problem. movement[5000] went from 0.51 s to 17.2 s per tick; bisected to #172 (cooperation pending-offer scan, fixed by #394) plus a second combat_engagement step (+3.3 s per tick), still open under Lane B's ticket.
- Finding: the `Slow regression` job had no `timeout-minutes`. Recorded here and not changed here; the reporting-path work under TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED later set 240.
- Live confirmation: run 37551894246 (issue #390). Rows 3, 4 and combat[500] are absent from the failing set; 5k, ph9, movement, passive_scaling and strategic remain, all mapped in `tools/test_architecture/slow_known_reds.yaml`.

## Docs Requiring Update
None. Triage and routing only; no behaviour, test or contract changed.
