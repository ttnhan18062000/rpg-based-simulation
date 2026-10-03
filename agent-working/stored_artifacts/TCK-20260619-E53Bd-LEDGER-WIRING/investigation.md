# Investigation — TCK-20260619-E53Bd-LEDGER-WIRING

## Key Findings

### WorldEvent.payload constraint
`WorldEvent.payload: Dict[str, float]` — cannot store string faction IDs in payload.
Must use `WorldEvent.subject: Optional[str]` for the faction pair identifier.
Format: `":".join(sorted([fid_a, fid_b]))` for deterministic dedup key in narrative ledger.

### Orchestrator method name
The harvest function is `_extract_narrative_entries()`, not `_harvest_narrative_entries()`.
Initial test drafts used the wrong name — corrected before passing.

### _SIGNIFICANCE_MAP dispatch
`_extract_narrative_entries()` checks `key = cat.value` against `_SIGNIFICANCE_MAP` dict.
Adding three new string keys is sufficient — no structural change to the harvesting logic.

### events_from_transitions placement
Must live in `diplomatic_state_machine.py` (no `src.engine` imports allowed).
Lazy-imports `WorldEvent`/`WorldEventCategory` from `src.domains.world_emergence.schema` inside the function body — avoids any import-time dependency on `src.engine`.

### Pipeline.py Phase 8d split
Prior code: single `_diplo_updates` list accumulated from both `compute_transitions()` and `_diplo_handle(AllianceProposal(...))`.
After: split into `_diplo_transition_updates` and `_diplo_alliance_updates` so `events_from_transitions()` can discriminate WAR/PEACE (from transitions) vs ALLIANCE (from alliance handler) correctly.
