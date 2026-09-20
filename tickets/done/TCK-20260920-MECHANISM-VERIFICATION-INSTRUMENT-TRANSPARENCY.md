---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY

## Title
Runtime-verified share as a first-class rollup metric, batch 3's re-languaging, and the selection
effect recorded — peer review's direct response to §2's unearned 20/20 confidence

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Peer review of `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` (batch 3 of the
unbound-claims program) correctly challenged its own 20/20 `observed` pass rate: all 20 mechanisms
were verified with `code_trace` only, none with `scenario`/`corpus_run`, and the registry's own
runtime-verified share moved from 27% to 11% in that same batch — a real regression that existed
nowhere as a rendered figure until computed by hand under direct challenge. Three specific
questions were asked (which instrument, did any meet a differential requirement, was there a
near-miss) and answered honestly before any registry entry was touched, per explicit instruction.

Peer's own explicit fix, in three parts, **none of them re-verification**: re-language the
reporting (the `instrument` field itself was always correctly labeled `code_trace`; the prose
overstated it), make the imbalance a first-class rendered number so it can't be buried in prose
again, and record the selection effect in the claims-as-tests doc alongside the other named failure
shapes.

## Scope
1. Add `runtime_verified_share` to `registry.py::_rollup_stats()` — the fraction of a group's own
   *verified* mechanisms confirmed by a runtime instrument, denominated by `verified` not `count`.
2. Render it as a first-class column (with baseline comparison, same discipline as
   `bound_rate`/`verified_rate`) in both the markdown and HTML system rollup views.
3. Re-language `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`'s own prose: state plainly
   it was a static re-confirmation of pre-existing citations, not a differential test, and name the
   selection effect that produced the 100% pass rate.
4. Record the selection effect as its own named case in
   `docs/plans/mechanism_claims_as_tests_initiative.md`, alongside §3.1 (search failures) and §3.2
   (misattribution).
5. Update the PR #229 body to match.

## Out of Scope
- Re-verifying, downgrading, or otherwise touching any of the 20 `verified` entries batch 3
  produced — explicitly forbidden by peer's own instruction, and unnecessary: the `code_trace`/
  `observed` verdicts are accurate for what was actually checked.
- Running any real `scenario`/`corpus_run` instrument against any of the 20 — that's the census
  program, a separate, larger piece of work explicitly deferred to the roadmap session's own read.

## Acceptance Criteria
1. `runtime_verified_share` computed correctly (denominator `verified`, not `count`; `0.0` not
   undefined when nothing verified) with tests proving both.
2. Rendered as its own column, registry-wide and per-system, in both consumer views.
3. Batch 3's own ticket re-languaged to state plainly what was and wasn't done, without altering
   any registry data.
4. The selection effect recorded as a real, citable case in the claims-as-tests doc.
5. None of the 20 `verified` entries in `registries/mechanisms.yaml` modified.

## Related Tickets
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — the batch this ticket responds to and
  re-languages.
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`,
  `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION`,
  `TCK-20260920-MECHANISM-CONTRADICTED-VERDICT-TRIAGE`,
  `TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION` — same program, same PR.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §3.3 — new case study this ticket added.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY/`.

## Related Code Areas
- `tools/mechanism_registry/registry.py` (`_rollup_stats()`)
- `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`,
  `generate_mechanism_registry_html.py`
- `tickets/done/TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN.md` (re-languaged)

## Assumptions / Open Questions
None. Peer's own explicit instruction ("do not re-verify any of the 20, do not downgrade their
verdicts") is followed exactly — this ticket's own diff touches zero `verified` blocks in
`registries/mechanisms.yaml`.

## Implementation Notes
`_rollup_stats()`'s existing `runtime_verified`/`static_verified` counts already existed; what was
missing was the RATE. Added `runtime_verified_share = runtime_verified / verified_total` (0.0 when
`verified_total` is 0, matching the file's own established zero-count convention). Rendered in the
markdown rollup view as a new "Runtime Share of Verified (vs baseline)" column, and in the HTML
page both as a new rollup column and a page-wide summary sentence near the top. Confirmed the real
registry-wide number: 27.3% before batch 3, 11.0% after — matches peer's own hand-computed figures
exactly.

Re-languaged `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`'s Title, Assumptions, and
Implementation Notes to state plainly what was done (static re-confirmation of pre-existing
citations) and why the pass rate was high (selection, not adversarial checking) — appended as dated
addenda rather than silently rewriting the original text, matching this session's own established
correction discipline.

## Test Summary
`tests/unit/tools/test_mechanism_system_rollup_view.py`: 2 new tests
(`test_rollup_runtime_verified_share_is_a_rate_of_verified_not_of_count`,
`test_rollup_runtime_verified_share_is_zero_not_undefined_when_nothing_verified`).
`tests/unit/tools/test_mechanism_registry_html.py`: 1 new test
(`test_render_rollup_includes_runtime_share_of_verified_column`), including the same
module-vs-dotted-import fix this file's own prior tests already needed under this directory's
autouse system-registry-patching fixture. Full `tests/unit/tools/` suite: 263 passed.
`registry.py::validate()`: clean, 93 mechanisms.

## Files Changed
- `tools/mechanism_registry/registry.py` — `runtime_verified_share` added to `_rollup_stats()`.
- `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`,
  `generate_mechanism_registry_html.py` — new column/summary rendering.
- `tests/unit/tools/test_mechanism_system_rollup_view.py`,
  `test_mechanism_registry_html.py` — 3 new tests.
- `docs/brainstorm/mechanism_system_rollup_view.md`, `mechanism_registry.html` — regenerated.
- `docs/plans/mechanism_claims_as_tests_initiative.md` — new §3.3.
- `tickets/done/TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN.md` — re-languaged.
- PR #229 body — updated to match.

## Completion Summary
**Done.** Answered peer's 3 direct questions honestly before touching anything (all 20 are
`code_trace`, none met a differential test, no case came close to a contradiction — the selection
itself explains the 100% rate). Applied the requested fix exactly as specified: re-language, add a
durable metric, record the pattern — no re-verification, no entries touched. The runtime-verified
share is now a real, rendered, tested number that the next verification batch can't bury in prose.
