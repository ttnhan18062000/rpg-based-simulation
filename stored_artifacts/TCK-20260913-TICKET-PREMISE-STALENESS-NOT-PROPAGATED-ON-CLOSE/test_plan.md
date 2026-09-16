---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE
phase: open
date: 2026-09-14
tags: [registry, process-improvement]
---

# Test Plan — TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE

**No tests are added by this ticket.** Per Scope/Acceptance Criteria, this ticket is investigation-
only — it produces a recommendation for peer/user review and explicitly does not implement a fix
("No implementation without that review"). There is no code change to test.

## How the investigation's own measurements were verified

Not test-suite-automated (nothing to regress-test against — the measurement is a one-time snapshot
of the current ticket corpus, not a behavior a test suite pins), but reproducible by design:

1. Measurement 1 (registry doesn't index open tickets) — read `tools/generate_registry.py` directly
   (not assumed) and independently confirmed against the live, freshly-regenerated
   `docs/REGISTRY.yaml`'s own entries.
2. Measurement 2 (53.4% empty `Related Code Areas`) — computed using the exact same parsing
   functions the registry itself uses (`generate_registry.parse_body_section` +
   `parse_related_code_areas`), applied directly to the 58 real files under `tickets/todos/` and
   `tickets/inprogress/` at investigation time — not a sample, the full open-ticket corpus as it
   stood on 2026-09-14.
3. Measurement 3 (0 genuinely stale citations among populated tickets) — checked each of the 80
   citation entries in the 27 non-empty tickets against the real filesystem (`Path.exists()`), not
   assumed accurate.

Anyone re-running this investigation later should expect these exact numbers to drift (the ticket
corpus changes daily) — re-measure rather than cite these figures as still-current beyond this
ticket's own review.

## If implementation is later approved (out of scope here, recorded for the future implementer)

A real test plan for a full-text keyword/path sweep would need at minimum:
- A fixture where a closing ticket's git-touched path appears in an open ticket's prose OUTSIDE its
  `Related Code Areas` section (proving the full-text approach catches what a structured-field-only
  approach would miss — this is the entire point of the recommendation in plan.md).
- A false-positive check: a shared file path does not by itself mean an open ticket's premise was
  invalidated (noted as a real risk in this ticket's own Scope) — the sweep should flag for review,
  not auto-fail a gate.
- A real-corpus regression test asserting the sweep runs against the actual `tickets/todos/`/
  `tickets/inprogress/` corpus without raising, mirroring this session's established pattern for
  other real-corpus checks (e.g. `working_log_content_duplicate_check.py`'s own real-corpus test).

None of this is built here — recorded only so a future implementer does not have to re-derive it.
