---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN
artifact_type: investigation
tags: [observability]
---

# Investigation
- Cross-block locals: none survive between the per-entity blocks except `entity`, `prior_ent`, `eid`; `e_upd`, `real_combat_upd`, `hp_diff`, `near_death_hp`, `gold_diff` are assigned before use inside their own block. `_is_real_number` is used only by the vitals blocks. `conservation_law_verified` reads the events emitted so far, so it takes `emitted` as an argument.
- `events` is read in exactly one place (above). All other blocks only append.
- Three tests read the source text of `event_extractor.py` and had to follow the code: `test_event_extractor_agency2.py::TestAntiDriftGuards` (`last_defer_reason`, now the strategy module), `test_passive_death_cause_and_rebirth_defeat_lifecycle.py` (`death_reason ... == "COMBAT"`, now the combat module), `test_event_extractor_progression.py::test_detector_literals_are_gone` (now the whole package).
- The phase18 allowlist (`tests/architecture/test_phase18_import_boundaries.py`, `codebase/structure/importlinter.toml` c03) lets only `event_extractor.py`, `event_shapers.py` and `cognition/recorder.py` import `src.domains`/`src.systems`. Widening it is a gate change outside this ticket, so the two domain-touching pieces stay reachable only from `event_extractor.py`.
- `_MAX_CONSECUTIVE_REJECTIONS` stays imported in `event_extractor.py` (the `n3-private-name-import` exception stays) and reaches the rejection-cascade function through `ctx.max_consecutive_rejections`.
- One behavior-neutral addition: the silent `except (TypeError, ValueError): pass` in the `threat_evolved` block now logs at debug level (the new module would otherwise add an `e3-silent-except` exception). It emits nothing and changes no event.
- Findings for codebase-planner, not changed here: about 210 parity-ledger lines cite `src/observability/event_extractor.py` as evidence for events that now live in `src/observability/extraction/`; the file still exists, so no citation breaks.
