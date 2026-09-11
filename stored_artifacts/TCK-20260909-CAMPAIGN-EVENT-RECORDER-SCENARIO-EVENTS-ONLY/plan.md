# Plan — TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY

Disposition approved by `rpg-feature-planning`: rename, not docstring-only. See investigation.md
for full rationale and the one correction made to the peer's named call-site list.

## Step 1 — `src/engine/scenario_runtime.py`
- `ScenarioRuntimeService.__init__`'s `event_recorder` param → `scenario_event_recorder`.
- `__slots__` entry and `self._event_recorder` attribute → `self._scenario_event_recorder`.
- All 3 usage sites in `_evaluate_after_tick()`.
- New docstring on `__init__` cross-referencing `Kernel.event_recorder` as the real stream.

## Step 2 — `src/domains/campaigns/orchestrator.py`
- `CampaignOrchestrator.__init__`'s `event_recorder` param → `scenario_event_recorder`.
- `self._event_recorder` attribute → `self._scenario_event_recorder` (all usage sites: episode
  bookkeeping, chronicle/nemesis event emission).
- Call site constructing `ScenarioRuntimeService(..., event_recorder=...)` →
  `scenario_event_recorder=...`.
- New docstring on `__init__`, same cross-reference.

## Step 3 — `src/engine/kernel.py`
- `event_recorder` property gets a docstring cross-referencing `scenario_event_recorder` as the
  unrelated narrow side channel. No functional/naming change to Kernel itself — it's correctly
  named already.

## Step 4 — `tools/calibrate_simq.py`
- `CampaignOrchestrator(manifest, event_recorder=campaign_recorder)` → `scenario_event_recorder=`.
- Comment at the `campaign_recorder` construction site explaining the split, since this is the
  exact site the original investigation started from.

## Step 5 — Test updates (no assertion-logic changes, just the renamed kwarg/attribute)
- `tests/unit/engine/test_scenario_runtime_service.py` — 4 construction sites.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — 1 construction site + 1
  `kwargs.get("event_recorder")` assertion (a real miss caught by re-running the full suite after
  the first pass, not just a mechanical grep-replace).
- `tests/unit/domains/campaigns/test_grief_urgency.py` — 4 direct `orch._event_recorder = ...`
  attribute sets.
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` — 1 construction site + a
  docstring update recording this investigation's own conclusion inline.
- `tests/integration/scenarios/test_social_memory.py` — 1 construction site + 1 comment.
- `tests/integration/tools/test_calibrate_simq_campaign_mode.py` — 1 comment.

## Scope guards
- No behavior change anywhere — every edit is a name or a comment/docstring.
- `Kernel._event_recorder`/`Kernel.event_recorder` (the correctly-named real recorder) is
  untouched.
- `NarrativeLedger`'s own separate `event_recorder` param (a different class, not part of this
  naming collision) is untouched — out of scope, not part of the peer's named rename target.
