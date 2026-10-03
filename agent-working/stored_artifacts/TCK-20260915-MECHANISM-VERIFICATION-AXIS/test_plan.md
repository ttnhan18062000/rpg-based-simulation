---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-VERIFICATION-AXIS
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260915-MECHANISM-VERIFICATION-AXIS

## Regression Surface

Extends `tools/mechanism_registry.py` and `docs/brainstorm/mechanisms.yaml`, both built by
`TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`. Regression baseline: all 24 existing tests in
`tests/unit/tools/test_mechanism_registry.py` plus the 6/7 graphify-check tests plus the 9
capability-registry tests must keep passing unmodified — extending the schema with a new optional
field must not disturb any invariant the Foundation ticket already proved.

## New Tests Required

1. **`test_validator_rejects_unknown_instrument`** (AC #3) — fixture: a mechanism with
   `verified: {instrument: "made_up_instrument", verdict: observed, date: ..., note: ...}`. Assert
   validation fails, error names the offending mechanism id and the bad instrument value.
2. **`test_validator_rejects_unknown_verdict`** — same shape, `verdict: "made_up_verdict"`.
3. **`test_validator_rejects_incomplete_verified_block`** — fixture missing one required sub-field
   (e.g. no `date`). Assert failure.
4. **`test_validator_accepts_all_four_instruments`** (parametrized, mirrors Foundation's own
   `test_validator_accepts_every_valid_state`) — `census`/`scenario`/`corpus_run`/`code_trace` each
   individually pass.
5. **`test_verification_view_includes_every_mechanism_even_unverified`** (AC #1, #2 — the
   load-bearing test) — fixture: 2 mechanisms, one with a real `verified` block, one with
   `verified: null`. Assert BOTH ids appear in `build_verification_view()`'s output row ids —
   explicitly checking the unverified id's presence, not just that the verified row's fields are
   correct. This must fail if an omission bug is reintroduced.
6. **`test_verification_view_unverified_row_shape`** — the unverified row's own fields read as
   expected (`verified=False`/`verdict="unverified"` or equivalent — exact sentinel decided at
   implementation time and documented in the function's docstring).
7. **`test_verification_view_collapses_multiple_records_to_latest`** (AC #4) — function-level
   fixture: 2 verification records for the same mechanism id, different dates. Assert exactly 1
   output row for that id, matching the later date's fields.
8. **`test_verification_view_groups_static_evidence_separately_from_runtime`** — fixture with one
   `scenario` (runtime) verdict and one `code_trace` (static) verdict on two different mechanisms;
   assert the output's own ordering/grouping separates them (runtime group before static group,
   both before unverified), not interleaved by id alone.
9. **`test_real_registry_verification_view_seeds_non_empty`** (AC #5, against real committed data)
   — asserts all 6 seeded mechanisms (`combat_engagement`, `succession`, `self_model`,
   `information_trust_deception`, `opportunity_rumor_seeds`, `cross_episode_grief_nemesis`) appear
   with their expected `instrument`/`verdict`, and the view's total row count equals
   `len(registry.all_mechanisms())` (75) — proves AC #1 against real data, not only a fixture.
10. **`test_make_target_generates_verification_view`** — subprocess test for the new `make`
    target/script; never corrupt the real committed output file mid-test (use a redirected/tmp
    output path if the script supports one, or diff-and-restore if not — decided at implementation
    time, matching Foundation's own `tmp_path`-copy discipline for its analogous make-target test).

## Scoped Pytest Command

```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_graphify_check.py tests/unit/engine/test_capability_registry.py -v
```

Never `pytest tests/`.

## Anti-Drift Test Guards

- Test 5 must assert the unverified id's *presence* in the output, never merely `len(view) == N`
  (a count-only check could pass even if the wrong mechanism were silently dropped and a duplicate
  emitted elsewhere).
- Test 7's fixture must use two records with genuinely different dates and genuinely different
  `note`/`verdict` content, so a bug that just returns the *first* or *last-by-list-order* record
  (rather than latest-by-date) would be caught, not accidentally pass.
- Test 9 must re-derive the expected 75 mechanism count from `len(registry.all_mechanisms())`
  itself, never hardcode `75` a second time — Foundation's own seed count could change later and
  this test should not silently start asserting a stale number.
