---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN
phase: done
date: 2026-10-11
tags: [testing]
---

# Investigation
Two consecutive runs on 2026-10-08/09 tested the same commit, and exactly those two exposed a flapping failing set on an unchanged commit (rolling issue #390), so one same-commit rerun a day is kept. The run-level conclusion is `success` for a gate-skipped run, so the job `Slow regression` conclusion from the jobs API is the signal. See the ticket for the live collector check and the AC5 evidence.
