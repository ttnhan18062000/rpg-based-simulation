---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Fixture weeks of 12 standard hand runs: Plan omitted in 11 with `path_reason` stated in 10 (flagged) and stated in 4 (held back, reason names the 67% `unstated` share); fewer than 10 runs never flags; old rows are `predates`; an all-old period shows the predates table and no candidate; empty period wording; conditional phases are not omitted; other workflows ignored; the retro renders the section before Notes and keeps hand-written Notes without `--force`.

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: rendered section and `analyze` output over fixture runs and events
- expected effect: Plan flagged only when the sample and the stated share allow it
- selected commands: `pytest tests/tools/test_path_report.py tests/tools/test_generate_retro.py`
