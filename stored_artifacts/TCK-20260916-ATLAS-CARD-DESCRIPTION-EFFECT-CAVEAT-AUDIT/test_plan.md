---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT
artifact_type: test_plan
tags: [architecture, investigation, schema]
---

# Test Plan — TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT

This ticket's own deliverable is a set of `registries/mechanisms.yaml` corrections (some, none, or
many — a clean sweep with zero new findings beyond `camp`/`motivation_doctrine` is an explicitly
acceptable outcome per AC #3), not new production code. "Testing" here means: confirming the
registry stays internally valid, confirming every consumer artifact converges with it, and
confirming no unrelated card moved.

## Normal flow
- `MechanismRegistry` / `registry.py`'s own `validate()` passes clean (93 mechanisms) after every
  edit.
- `test_mechanism_artifact_convergence.py` passes — every mapped card's badge/tier matches its
  mechanism's current `state`.
- `test_mechanism_wiring_map_classdef.py` (or the currently-named drift test) passes — no
  undeclared wiring-map drift.

## Edge cases
- A correction where the OLD verdict is itself already recorded (e.g. re-confirming `camp`'s own
  existing `contradicted` verdict is untouched, not duplicated).
- A flagged candidate that, on real code-level check, turns out to be a false positive — recorded
  in investigation.md with the reasoning, registry left untouched, no spurious edit.

## Failure modes
- A regenerator (`mechanism_atlas_regenerate.py` / `mechanism_capabilities_regenerate.py`) moving
  more than the expected card(s) — caught by convergence tests failing on an unrelated id.
- A `state` correction made without a citation to the specific description text or divergence-record
  entry that justified it (violates this ticket's own AC #2/§Scope discipline) — caught by review,
  not a script.

## Regression-prone paths
- The `SPLIT_CARD_MECHANISMS` / `PARTIAL_COVERAGE_CARDS` cards in
  `mechanism_atlas_card_mapping.py` — badge-index mistakes here are the most likely source of a
  wrong mechanism attribution; double-check badge index against the card's own title/desc text
  before citing it as evidence for a specific mechanism id.

## Commands
```
python3 -c "from tools.mechanism_registry.registry import MechanismRegistry; MechanismRegistry('registries/mechanisms.yaml').validate()"
python3 -m pytest tests/unit/tools/test_mechanism_artifact_convergence.py tests/unit/tools/test_mechanism_wiring_map_classdef.py tests/unit/tools/test_mechanism_atlas_regenerate.py tests/unit/tools/test_mechanism_capabilities_regenerate.py -q
```
