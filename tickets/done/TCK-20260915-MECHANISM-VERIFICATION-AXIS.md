---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-VERIFICATION-AXIS
phase: done
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-VERIFICATION-AXIS

## Title
Record whether each mechanism has been *observed working*, by which instrument, and when — the axis
no artifact currently has

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Every status in every brainstorm artifact answers one question: *is it built?* None answers *has it
been observed working?*

That gap produced this arc's most expensive miss. Combat judgement was correctly marked implemented
and was write-only: four conditions — flag off, flag on, output neutered, phase stubbed — all
produced exactly 1960 attacks. Nothing in the artifacts was wrong; the question was never asked.

Add a `verified` block to each mechanism in the registry:

```yaml
verified:
  instrument: scenario        # census | scenario | corpus_run | null
  verdict: observed           # observed | contradicted | inconclusive
  date: 2026-09-15
  note: "one line, what was actually seen"
```

Worked example, real as of 2026-09-15 — combat judgement is now verified at two scales: at corpus
scale the posture gate moved attacks 1960 → 837, and at scenario scale
`tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` shows risk-rejected posture → 0
attacks vs no posture → attack proceeds, with legality, range and readiness identical. Four fields
hold that. Nothing in the current artifacts can express it.

## Scope
1. **Schema extension** — `verified` on each mechanism, nullable.
2. **The unverified-visible rule** — a mechanism with `verified: null` renders in the verification
   view as `unverified`, never omitted. This is the ticket's most important requirement, see below.
3. **A verification view** — rendered section listing every mechanism with instrument, verdict, date.
4. **Volume cap, enforced not just documented** — one row per mechanism, never per test; latest
   verdict only, no history (history lives in git).
5. **Migrate the overloaded atlas badge texts.** `"Built correctly, OFF by default"`, `"Proven
   mechanic, narrow trigger"`, `"Succession never triggers"` are verification statements sitting in a
   build-status field. Move them here; leave genuine per-card colour as prose.

## Out of Scope
- Adding badge classes to carry verification. That is what this field is for.
- Per-test result feeds. The scenario component emits one verdict per mechanism.
- Automatically ingesting scenario or census output. Verdicts are written deliberately at first;
  automate only once the producers are stable.
- Verification history or trend analysis.

## Acceptance Criteria
1. Every mechanism in the registry appears in the verification view, including unverified ones.
2. A mechanism with no verdict renders as `unverified` — proven by a test that adds an unverified
   mechanism and asserts it appears. **Assert presence, not absence**: an omission bug is invisible
   to a test that only checks the verified rows look right.
3. `instrument` is constrained to the known set; an unknown instrument fails validation.
4. The view is one row per mechanism; a fixture with multiple results for one mechanism collapses to
   the latest rather than emitting several rows.
5. At least the migrated atlas texts are present as real verdicts, so the view ships non-empty.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — dependency
- `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH` — a finding surfaced *by* scenario
  verification; the kind of result this axis exists to hold

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §2 Gap 4
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the primary verdict producer

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html` — source of the overloaded badge texts
- `tests/mechanic_scenarios/` — the scenario component's own verdicts

## Assumptions / Open Questions
1. Is `corpus_run` a durable instrument or an interim one that the scenario component replaces? It
   produced the 1960 → 837 measurement, so it is real today.
2. Should `verdict: contradicted` (built, observed *not* working) be distinct from a `state` of
   `orphan`? They are different claims — one is an observation, the other a structural fact — and
   keeping them separate is probably right, but confirm while migrating.
3. How stale may a verdict be before it is shown as aged? Deferred; a date is recorded so the policy
   can be added later without schema change.

## Implementation Notes
The unverified-visible rule is the whole point. If unverified mechanisms are simply absent from the
view, this artifact reproduces the exact failure the arc was about: a real state rendered as silence.
Build the default state loud.

**`instrument` enum gap found and fixed before implementing**: the schema's own listed enum
(`census | scenario | corpus_run | null`) didn't cover direct code-trace/investigation
confirmations — the dominant verification method across this whole arc's own history, including
all three sample atlas texts this ticket migrates. Added a 4th value, `code_trace`, kept explicitly
distinct from the three runtime instruments (not a flat peer): `code_trace` proves what the code
*says* (reachable, called, a field never written) and can never establish that reachable code has
its claimed runtime effect — the exact distinction combat judgement's own write-only near-miss
turned on (a clean code trace, write-only in practice, caught only by a runtime instrument). This
is carried two ways, deliberately minimal — no invented numeric confidence field: (1) documented on
the enum value itself in `mechanisms.yaml`'s own header comment and `tools/mechanism_registry.py`'s
docstrings; (2) the verification view groups runtime-verified rows before static-verified rows
before unverified rows, so a reader scanning the table sees which kind of evidence they're looking
at.

**"Built correctly, OFF by default" decomposes across two fields, not one** — `gated` (an existing
`state` class) already covers the OFF-by-default half; only "built correctly" is a real verdict.
Migrated as the unchanged `state: gated` plus a `code_trace`/`observed` verified block whose note
covers only the built-correctly claim. A second, real instance of Gap 2's own overloaded-badge-text
claim, strengthening rather than just confirming it.

**Open Question #2 (`contradicted` vs `orphan`) settled with real data, not in the abstract**, via
the `succession` mechanism: `state: orphan` already carries "built but never fires"; the
`heir_entity_id`-never-populated code trace *confirms* that claim, it does not contradict it — so
this is `verdict: observed`, not `contradicted`. `state` and `verified.verdict` compose (both
independently point the same direction here) rather than collapsing into one field; they stay
genuinely separate fields answering different questions. The case that would actually produce
`contradicted` is the historically expensive one — `state: done` with a *runtime* instrument
finding the claimed behavior doesn't actually happen. No real `contradicted` example exists in the
current 6-verdict seed; not fabricated to fill the enum, recorded as still open for a future
mechanism that needs it.

**`combat_judgement` naming**: the ticket's own worked example and the plan doc's own §3 shape
example both use the id `combat_judgement`. The Foundation ticket's real seed uses
`combat_engagement` (the atlas card's own literal title, "Combat Engagement (Pre-Combat
Assessment)") — used the real seeded id rather than inventing a second, redundant entry that would
never resolve any `depends_on` edge pointing at it.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py`: 19 new tests (43 total in this file). Both new
validator invariants (instrument enum, verdict enum + required-field completeness) each proven on
a deliberately broken fixture; all 4 instruments and all 3 verdicts individually accepted
(parametrized, proving the enum boundaries are exact on both sides, matching the Foundation
ticket's own established test discipline). The load-bearing AC #2 test
(`test_verification_view_includes_every_mechanism_even_unverified`) explicitly asserts an
unverified mechanism's id is present in the view's output — not merely that output is non-empty —
so it fails if an omission bug is reintroduced. Collapse-to-latest tested at the function level
(2 records, different dates, assert exactly 1 row with the later date's fields) since the real
registry only ever has 0-1 records per mechanism today. Static/runtime grouping-order tested
directly. Real-registry test asserts all 6 seeded mechanisms and the full 75-row view count. Make
target + `--check` staleness mode both tested via subprocess, the staleness test using a
`tmp_path`-redirected output so the real committed markdown file is never mutated mid-test.

Combined regression suite (this file + `test_mechanism_registry_graphify_check.py` +
`test_capability_registry.py`): 63/63 passing. Re-verified with `graphify-out/` genuinely absent
(moved aside, restored immediately after) to match the real CI condition exactly — all 63 pass
under that condition too, confirming this ticket's own new code doesn't reintroduce the class of
CI-only failure the Foundation ticket found and fixed.

Scoped pytest command used throughout:
```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_graphify_check.py tests/unit/engine/test_capability_registry.py -v
```

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — `verified` block added to 6 mechanisms (75 total unchanged);
  header comment extended with the instrument/verdict enums and the static/runtime distinction
- `tools/mechanism_registry.py` — `VALID_INSTRUMENTS`/`STATIC_INSTRUMENTS`/`RUNTIME_INSTRUMENTS`/
  `VALID_VERDICTS`, 2 new `validate()` invariants, `MechanismRegistry.get_verification()`,
  `build_verification_view()`, `verification_records_from_registry()`
- `tools/generate_mechanism_verification_view.py` (new) — renders the view to markdown, `--check`
  staleness mode
- `docs/brainstorm/mechanism_verification_view.md` (new, generated) — the rendered view
- `Makefile` — `mechanism-verification-view` target
- `tests/unit/tools/test_mechanism_registry.py` — 19 new tests
- `staging_artifacts/TCK-20260915-MECHANISM-VERIFICATION-AXIS/` — investigation.md, plan.md,
  test_plan.md

## Completion Summary
DONE. `verified` block schema extended per plan, seeded with 6 real, citation-backed verdicts (not
fabricated to hit a volume target) — `combat_engagement` at both cited scales in one note per the
ticket's own "four fields hold that" framing, and the 5 migrated atlas texts (one of which, "Built
correctly, OFF by default", correctly decomposed across `state` + `verified` rather than moving
wholesale, per peer review). The unverified-visible rule (AC #2, the ticket's own stated most
important requirement) is proven by a presence-assertion test, not an absence-only check. All 5
acceptance criteria satisfied and mapped to specific tests in plan.md. A genuine schema gap
(`instrument` enum not covering the dominant code-trace verification method) was found before
implementation, flagged rather than silently resolved, and fixed with an explicit static/runtime
distinction that keeps a `code_trace` verdict from ever reading as equally strong as a
runtime-confirmed one — directly protecting against a repeat of this arc's own most expensive
mistake (combat judgement's write-only near-miss). Out-of-scope items (badge classes, per-test
feeds, automated ingestion, verification history) correctly left untouched.

**This ticket's own seed produced the epic's first real finding (per peer review, 2026-09-16), not
just infrastructure — worth stating as the artifact's first output, not a footnote: 69 of 75
mechanisms (92%) have never been verified by any instrument, and of the 6 that have, only 1 —
`combat_engagement`, by `scenario` — has *runtime* verification. The other 5 are static code
traces. So the project currently has exactly one mechanism with real evidence it does anything at
runtime.** This number could not have been stated before this ticket — no prior artifact had a
verification axis to count against. Directly motivates T3
(`TCK-20260915-MECHANISM-PRIORITY-DERIVATION`), reframed around *which unverified mechanism to
verify next*, not an abstract priority ranking over all 75.
