---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION
artifact_type: plan
tags: [simulation-quality, testing, architecture]
---

# Plan — TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION

## Step 1 — Scenario (done)

`tests/mechanic_scenarios/test_action_pacing_readiness_gate.py`: reuse
`mechanic_scenario_combat_judgement_withdrawal`'s world and staging pattern, varying only
`combat.readiness` (50.0 vs 100.0) on the same forced `ATTACK` dispatch. Two tests, per §3.3's
mandatory differential requirement:
1. `test_readiness_gate_withholds_a_real_action_when_readiness_is_below_threshold`
2. `test_readiness_gate_does_not_withhold_when_readiness_meets_the_threshold`

Both must pass, and the blocking reason in test 1 must be confirmed as
`ReasonCode.INSUFFICIENT_READINESS` specifically (checked by calling `ActionRouter.execute_action`
directly and inspecting the returned `EntityUpdate`), not inferred from the attack simply not
happening — the same rigor the combat-judgement scenario's own second test enforces.

## Step 2 — Record the verdict

Add to `docs/brainstorm/mechanisms.yaml`'s `action_pacing_readiness` entry:
```yaml
verified:
  instrument: scenario
  verdict: observed
  date: "2026-09-16"
  note: "<one line, the real result>"
```
`state` stays `partial` — investigation.md's own conclusion is that this remains accurate (see
its own "Whether partial is still accurate" section), not something this ticket's own scenario
result changes. The scenario verifies the GATE specifically; the separate pacing-by-build claim is
investigated (not re-litigated as broken) and found to still validly explain `partial`.

## Step 3 — Regenerate and verify

`make mechanism-registry-validate`, `make mechanism-verification-view`,
`make mechanism-priority-view`. Confirm `action_pacing_readiness` now shows a real verdict (not
`unverified`) in the verification view, and drops out of the priority view's unverified ranking
(the view only lists currently-unverified mechanisms, so a now-verified #1 entry should simply
disappear from it, promoting #2 to #1 — confirm this is what actually happens, not assumed).

## Step 4 — Full suite + graphify-out discipline

`tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/`, full
pass, `graphify-out/` genuinely moved aside and restored — standing discipline from the whole
epic, carried forward into this follow-up work even though the epic itself is closed.

## Step 5 — Close

Hand-orchestrated closure sequence (done-checker precheck/finalize, `record_hand_orchestrated_
closure.py`, `docs/REGISTRY.yaml` regeneration) — standard tier, full staging-artifact migration
to `stored_artifacts/`.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1 (real investigation establishes the claim) | investigation.md |
| 2 (real differential scenario) | Step 1 |
| 3 (both conditions pass, reason confirmed) | Step 1 |
| 4 (verdict recorded, not adjusted for favorability) | Step 2 — `observed` is the real, earned result; the `partial` state is left correctly unchanged rather than opportunistically upgraded |
| 5 (any real defect filed, not fixed) | None found needing filing — the pacing-by-build nuance is pre-existing, already known, already correctly reflected by `partial` |
