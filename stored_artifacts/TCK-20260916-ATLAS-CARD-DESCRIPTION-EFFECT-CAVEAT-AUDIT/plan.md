---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT
artifact_type: plan
tags: [architecture, investigation, schema]
---

# Plan — TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT

## Approach

1. **Extract, don't eyeball.** Dumped all 73 mechanism-mapped atlas cards' full `desc` text
   (`docs/brainstorm/rpg_feature_atlas.html`'s `#card-sections-data` JSON blob), each card's current
   badge, and the corresponding `registries/mechanisms.yaml` `state`/`verified` block, using the
   existing `tools/mechanism_registry/mechanism_atlas_card_mapping.py` mapping (already verified
   correct by `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`, not re-derived here). This produces one
   authoritative source to read against, instead of re-reading the raw HTML by eye.
2. **Triage pass** (fork, read-only): read all 71 non-`camp`/`motivation_doctrine` entries against
   the two known caveat shapes (precondition-gap, stale-architecture vs.
   `docs/guidelines/intentional_divergences.md`), flag candidates with the exact triggering quote,
   report the full "read, no issue" id list separately so AC #1 ("every one of the 73... actually
   read, not sampled") has a checkable record.
3. **Real verification pass** (me, not the triage fork): for every flagged candidate, do the actual
   `code_trace` check this ticket's AC requires — grep for real callers/production wiring, cross-check
   the specific `intentional_divergences.md` entry cited, and only then decide precondition-gap
   (`verified: {instrument: code_trace, verdict: contradicted}`, state unchanged) vs. stale-architecture
   (`state` corrected, `verified: {instrument: code_trace, verdict: observed}`) vs. false positive
   (no change, note why).
4. **Propagate** any real correction to every consumer artifact via the existing sanctioned
   regenerators (`mechanism_atlas_regenerate.py`, `mechanism_capabilities_regenerate.py`), never by
   hand-editing the generated HTML directly, matching this arc's own established discipline.
5. **Verify convergence** — run `test_mechanism_artifact_convergence.py` and
   `test_real_wiring_map_has_no_drift_against_the_real_registry` (or its current name) after every
   edit, confirm only the expected card(s) moved.

## Files Touched (expected)
- `registries/mechanisms.yaml` — `verified` blocks added/corrected for real findings; `state`
  corrected only for confirmed stale-architecture instances.
- `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/simulation_capabilities.html` —
  regenerated (tool-written) for any `state` correction.
- `docs/brainstorm/rpg_simulation_wiring_map.html` — checked for drift, corrected only if a `state`
  change requires it (same as `status_effects`'s precedent in the coverage-extension ticket).

## Non-goals
- Re-deriving the card-to-mechanism mapping (out of scope, per ticket).
- Auto-ingesting findings from any automated instrument — every verdict here is a deliberate
  `code_trace` read, matching the ticket's own explicit scope limit.
