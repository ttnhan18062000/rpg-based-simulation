---
status: historical
layer: testing
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX
phase: done
date: 2026-10-06
tags: [testing, investigation]
---

# Plan — TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX

Triage and routing only; test architecture does not fix any of the 8 reds (ticket Out of Scope).

1. For each of the 8 step-6 failures in run 37403688489 (job 112078415756), confirm it reproduces or explain it from the run, and narrow the bracket (last green step 6 on `main`: run 32937991342, 2026-08-26) where cheap.
2. Route each to its owning seat through rpg-feature-planning, which rules on domain questions; record the owner and ticket id in the ticket's Routing Status.
3. Classify the four perf `TimeoutError`s as a real regression or a budget problem, and record the missing `timeout-minutes` on the job as a finding (no change here).
4. Close once every row has a routed ticket id on `main` and the live slow run shows the failing set is mapped (issue #390).
