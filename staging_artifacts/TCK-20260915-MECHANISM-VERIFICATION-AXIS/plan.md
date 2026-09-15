---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-VERIFICATION-AXIS
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260915-MECHANISM-VERIFICATION-AXIS

## Summary

Add a nullable `verified` block to each mechanism in `docs/brainstorm/mechanisms.yaml`, extend the
reader/validator, build a verification view (function + rendered output), and seed it with 5 real,
citation-backed verdicts across 6 mechanisms (`combat_engagement`'s own note covers two scales).
`instrument` gets a 4th value, `code_trace`, kept explicitly distinct from the three runtime
instruments per peer review — see investigation.md for the full reasoning.

## Step 1 — Schema extension

```yaml
mechanisms:
  - id: combat_engagement
    layer: entity
    depends_on: [action_pacing_readiness]
    state: done
    verified:
      instrument: scenario   # census | scenario | corpus_run | code_trace
      verdict: observed      # observed | contradicted | inconclusive
      date: "2026-09-16"
      note: >-
        Corpus: posture gate moved attacks 1960 -> 837. Scenario: risk-rejected posture -> 0
        attacks vs no posture -> attack proceeds, all else identical.
```

`verified` is `null` (key absent or explicit `null`) for every mechanism with no recorded verdict
— this is the *only* way to represent "unverified." When `verified` is present, all 4 sub-fields
are required and `instrument` is never itself `null` inside a present block (avoids two ways to
express the same "unverified" state — a deliberate simplification over the ticket's own header
comment, which listed `null` as one of `instrument`'s own possible values; recorded here since it's
a real, if small, interpretation choice).

Header comment block updated: document the 4-value `instrument` enum, the static/runtime
distinction (`code_trace` proves structure; the other three prove runtime effect — a `code_trace`
verdict never implies reachable code has its claimed effect), and the `verdict` enum.

Seed the 5 rows from investigation.md's Final Verdicts table (6 mechanisms — `combat_engagement`
plus the 5 `code_trace` entries). `state` values are unchanged on all 6 — only `verified` is added.

## Step 2 — Reader extension (`tools/mechanism_registry.py`)

```python
VALID_INSTRUMENTS = frozenset({"census", "scenario", "corpus_run", "code_trace"})
STATIC_INSTRUMENTS = frozenset({"code_trace"})       # proves structure, not runtime effect
RUNTIME_INSTRUMENTS = frozenset({"census", "scenario", "corpus_run"})
VALID_VERDICTS = frozenset({"observed", "contradicted", "inconclusive"})

class MechanismRegistry:
    def get_verification(self, mechanism_id) -> Optional[dict]:
        """None if unverified (verified: null or absent). Never raises for a missing id --
        returns None, mirroring get_state()'s own unknown-id contract."""
        ...
```

## Step 3 — Validator extension

Two new invariants (5th and 6th overall, alongside Foundation's original four), same
list-of-error-strings contract as `validate()` already uses:
- every present `verified.instrument` is in `VALID_INSTRUMENTS`
- every present `verified.verdict` is in `VALID_VERDICTS`

A `verified` block missing a required sub-field (`instrument`/`verdict`/`date`/`note`) is also an
error — proven by its own broken fixture, matching Foundation's own AC #4 discipline (every
invariant proven failing on a deliberately broken fixture, never just a clean pass).

## Step 4 — Verification view

New function `build_verification_view(registry_data) -> List[dict]` (same module — this is a
read/transform over the registry, not a new subsystem) returning **exactly one row per mechanism**
(AC #1), each row `{id, layer, state, verified: bool, instrument, verdict, date, note}` —
`verified=False` rows have `instrument=None`/`verdict="unverified"`/`date=None`/`note=None`, never
omitted from the list (AC #2). Rows sorted static-evidence-last (or grouped) so a reader scanning
the output sees runtime-confirmed rows separated from code-trace-confirmed ones, per peer's
grouping requirement — concretely: verified-runtime rows first, verified-code_trace rows next,
unverified rows last, each group internally sorted by `id` for determinism.

**"Collapse to latest" (AC #4) is tested at the function level, not against real data** — today's
registry only ever has one `verified` block per mechanism (hand-authored, no multi-source feed
exists; Out of Scope explicitly excludes auto-ingestion), so there is nothing to collapse in the
real file. `build_verification_view()`'s own internal per-mechanism resolution is still written to
accept and correctly collapse multiple verification-record inputs to the latest-by-date (future-
proofing for whenever an ingestion pipeline is built, without a schema change) — proven by a
Python-level test constructing 2+ verification dicts for one mechanism id directly against the
function, not by hand-editing the real YAML into an unsupported shape.

**Rendered output**: new script `tools/generate_mechanism_verification_view.py` →
`docs/brainstorm/mechanism_verification_view.md`, a plain markdown table (matches this repo's
lowest-maintenance generated-doc convention; no existing HTML page is the right target yet — that
integration is T4's own explicit job, not this ticket's). New `make` target,
`mechanism-verification-view`, registered alongside `mechanism-registry-validate`.

## Step 5 — Tests

New tests in `tests/unit/tools/test_mechanism_registry.py` (extending the existing file, not a new
one — same registry, same module):
- `test_validator_rejects_unknown_instrument` / `_verdict` (deliberately broken fixtures, per AC #3)
- `test_validator_rejects_incomplete_verified_block` (missing a required sub-field)
- `test_verification_view_includes_every_mechanism_even_unverified` — **the load-bearing test per
  AC #2's own instruction to assert presence, not absence**: a fixture with one verified and one
  deliberately unverified mechanism; assert the unverified one's `id` appears in the view's row
  ids, not just that the verified one's fields look right. A test that only checks the verified row
  is correct is blind to an omission bug (this arc's own recurring failure shape) — this test must
  fail if the omission bug is reintroduced, so it explicitly iterates the fixture's own id list and
  asserts every one is present in the output, not merely that output is non-empty.
- `test_verification_view_collapses_multiple_records_to_latest` — AC #4, function-level fixture
  with 2 records for one id at different dates, assert exactly 1 row for that id using the later
  date's fields.
- `test_verification_view_groups_static_evidence_separately_from_runtime` — asserts a runtime
  (`scenario`) row and a `code_trace` row for two different mechanisms land in different, correctly
  ordered groups in the output (not interleaved arbitrarily).
- `test_real_registry_verification_view_seeds_non_empty` (AC #5) — against the real committed file,
  asserts the 6 seeded mechanisms appear with the expected instrument/verdict, and the view's total
  row count equals the real mechanism count (75) — this is the AC #1 proof against real data, not
  just a fixture.
- `test_make_target_generates_verification_view` — subprocess test for the new `make` target,
  writing to a `tmp_path`-redirected output (or asserting the real committed output stays in sync —
  decide the exact mechanism at implementation time based on how the script accepts an output path
  argument; never let a test silently leave a stale generated file uncommitted).

## Acceptance Criteria Map

| AC | Satisfied by |
|---|---|
| 1. Every mechanism appears in the view, including unverified | Step 4 (`build_verification_view` iterates all mechanisms unconditionally) + `test_verification_view_includes_every_mechanism_even_unverified` + `test_real_registry_verification_view_seeds_non_empty` |
| 2. No-verdict renders as `unverified`, proven by presence-assertion | Same tests — explicitly assert the unverified id is IN the output |
| 3. `instrument` constrained, unknown fails validation | Step 3 + its broken-fixture test |
| 4. One row per mechanism, collapses to latest | Step 4's collapse logic + its dedicated test |
| 5. Migrated atlas texts present as real verdicts, non-empty | Step 1's 6 seeded rows + `test_real_registry_verification_view_seeds_non_empty` |

## Out of Scope (reaffirmed)

Badge-class changes, per-test result feeds, automated ingestion, verification history/trend
analysis — all explicitly deferred per the ticket's own Out of Scope section.
