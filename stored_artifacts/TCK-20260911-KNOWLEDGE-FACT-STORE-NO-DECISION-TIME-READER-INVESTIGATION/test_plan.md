# Test Plan — TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION

This is a documentation-only disposition — no code changed, so no new automated tests. The real
verification is the investigation's own evidence trail:

## Real evidence (see investigation.md for full detail)
- Fresh grep re-verification of every real `self_model.knowledge.facts` access outside
  `self_model.py` — confirms the original write/passthrough/trace-only finding, with one correction
  to a prior ticket's imprecise "real consumers" citation (`cognition_extras.py` reads `.unknowns`,
  not `.facts`).
- Real 500-tick instrumented `frontier_living_world` reproduction (seed 7, the same scenario this
  whole audit arc uses) — `InformationAssimilationService.assimilate()` patched directly, confirmed
  **zero calls**, tracing precisely why (two independently-gated real write paths, both empty in
  practice today).
- Git chronology confirming `KnowledgeFact`/assimilation postdates `BeliefEntry` by ~5 weeks, and
  `ENABLE_INFORMATION_INTENT_EXECUTION` postdates `KnowledgeFact` by ~7 weeks with its own explicit
  deferral ticket.
- Real grep confirmation that `CapabilityContext.region_data`/`.enemy_data` are never populated by
  any of the three real `CapabilityContext` construction sites in `src/`.

## Regression check
Since only docs and a new ticket file were added (no `src/`/`tests/` changes), no regression suite
run is required by this ticket's own scope. `tests/integrity/test_no_duplicate_content_blocks.py`
and `validate_frontmatter.py` cover the structural correctness of the ticket/doc changes themselves.

## Acceptance criteria mapping
- Complete, re-verified classification of every real access → investigation.md Step 1.
- Design-intent determination with real evidence → investigation.md Steps 2-3 (git chronology,
  real instrumentation, the "name the missing behaviour" test applied honestly).
- Deliberately-write-only-or-not disposition → neither cleanly; documented at its real, more
  nuanced size instead of forced into either original framing, per peer review's explicit approval.
- `belief_and_detour_contract.md` updated → done, stating the subsystem is inert end to end and
  naming the downstream consequence for the flag decision.
- No regression in `tests/unit/cognition/`, `tests/unit/strategic/` → N/A, no code changed.
