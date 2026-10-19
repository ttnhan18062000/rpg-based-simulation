---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD
artifact_type: plan
tags: [architecture, testing]
---

# Plan

The investigation (investigation.md) finds a guest-wide stall, not a slow or hung job phase. No change to `visual_assets/drawing/**` is justified by the evidence, so the guarded-file proof refresh is not needed unless the planner picks option B.

## Options (planner / lead to choose)
- A (recommended): no code change. Record the cause in `docs/assets/drawing_tools.md` ("Timeouts and stray sandboxes": a timeout with a sub-second job and a load average far above the core count is a host stall, how to confirm it with the external gap sampler, and to rerun when the host is quiet). Close the ticket with the cause named. Docs only, so no Aseprite proof refresh and no budgets row. File the host-side question (memory and swap pressure on the guest) with lead-planner.
- B: make the timeout stall-aware: on `TimeoutExpired`, compare the wall wait with a monotonic tick measured in a helper thread, and raise a distinct `AdapterError` ("host stalled for N s") instead of the plain timeout message, so a stall is named rather than misread as a hung Aseprite. Touches guarded files (`sandbox.py`, tests), so it needs the proof refresh and the lead's heavy-run OK. It does not make the test pass during a stall.
- C (rejected by the ticket): raise the bound, skip, mark flaky, retry.

## Scope guard
No edits outside docs until the planner picks A or B.

## Decision
Option A, chosen by asset-planner on 2026-10-18 (lead-planner agreed). Done: docs note in `docs/assets/drawing_tools.md`; ticket acceptance criterion replaced, not passed.
