---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE

## Current Behavior

`experiments/cost_proxy_calibration/validate_rank_order.py` (pre-promotion, read in full) is a
92-line script with everything inlined into one `main()`: file reading, grouping, scoring under
two **hardcoded** weight dicts (`W_SHIPPED`, `W_FITC` — the latter being the experiment's own,
explicitly-not-adopted Fit C regression result), rank computation, and `print()`-based reporting,
including an inline `import numpy as np` used only for a Spearman correlation calculation. No test
coverage exists for it (it lives under `experiments/`, which this repo's convention exempts from
the standard ticket/test workflow). Its own module docstring already frames it as reusable
("the gate itself... is reusable, independent of Fit C's own validity") — this ticket promotes
that reuse into a real, tested `tools/agent-monitoring/` module.

`tools/agent-monitoring/cost_proxy.py`'s live constants (`W_BASH=0.001`, `W_AGENT=50`, `W_EDIT=1`)
confirmed as the correct default baseline source — read directly, never re-hardcoded a second time
in the promoted module (the exact mistake the pre-promotion script made, hardcoding `W_SHIPPED` as
its own literal copy rather than importing).

`tools/agent-monitoring/*_check.py` naming/shape precedent confirmed via direct read of
`epic_scope_orphan_check.py`/`epic_staleness_check.py`: module docstring explaining purpose and
"advisory only" framing, dataclass/typed-report-shaped output, a `main()` CLI entry point.

`Makefile`'s `agent-monitoring-*` targets (confirmed via direct read): `agent-monitoring-retro`,
`agent-monitoring-validate`, `agent-monitoring-query` (the last taking a `$(ARGS)` passthrough,
the exact pattern this ticket's new target needs since the weight-check tool takes CLI flags).
None of the existing `agent-monitoring-*` targets are listed in the Makefile's `.PHONY` line —
confirmed by direct grep, so the new target follows that same (unlisted) precedent rather than
introducing a new convention.

## Mechanics/Engine Constraints

None — agent-monitoring is orchestration/observability tooling, not simulation gameplay.

## Parity Ledger Overlap

None expected: this ticket only moves/refactors a sandbox script into a tested tool — no `src/`
file touched, no on-disk schema change, no change to `cost_proxy.py`'s shipped constants or
`compute_cost_proxy_score()`'s formula. Confirmed at Parity time (see `plan.md`).

## Prior Work

The experiment itself (`experiments/cost_proxy_calibration/PROPOSAL.md`,
`experiments/cost_proxy_calibration/RESULTS.md`) produced `validate_rank_order.py` as its §4 step 4
validation gate — this ticket is the deferred "promote the reusable part" follow-up the results doc
itself already recommended ("If a future ticket does revisit these weights, it should re-run this
experiment's `validate_rank_order.py` gate... before shipping"). `TCK-20260719-COST-PROXY-CALIBRATION-NOTE`
(sibling ticket, same batch) already added a calibration-provenance note to
`docs/agent-monitoring/README.md`'s "What It Does NOT Capture" section — this ticket's own README
addition is placed immediately after that note, not overlapping it (confirmed no edit conflict:
the C5 addition ends before the Navigation section; this ticket's new paragraph is inserted between
them).

## Risks and Open Questions

None outstanding — both decisions the ticket's own Assumptions section flagged as needing a
Plan-phase call are made and documented in `plan.md`.

## Anti-Drift Hazards

- The promoted module must read `cost_proxy.py`'s live `W_BASH`/`W_AGENT`/`W_EDIT` constants as
  its baseline default — never re-hardcode a second literal copy (the exact anti-pattern the
  pre-promotion script itself had).
- No numpy dependency — `tools/agent-monitoring/*.py` scripts run via bare `python3`, not
  guaranteed a numpy-equipped interpreter; the Spearman correlation must be computed in pure
  Python.
- The candidate weight set must never have a baked-in default (no Fit C literal shipped as a
  fallback) — every invocation must explicitly supply `--candidate-weights`, per the ticket's own
  explicit Out-of-Scope statement ("both weight sets remain purely CLI-supplied comparands, never
  a baked-in default").
- Must never modify `tools/agent-monitoring/cost_proxy.py`'s shipped constants or scoring formula.

## Process Note (self-flagged, per this project's traceability rule)

**This investigation, and the sibling `plan.md`/`test_plan.md`, were written retroactively**, after
`tools/agent-monitoring/weight_sensitivity_check.py` and
`tests/tools/test_weight_sensitivity_check.py` were already implemented and independently verified
(10/10 tests passing). A session-limit stall interrupted the original implement-ticket pipeline
run partway through — real, correct implementation work landed on disk (confirmed by direct
inspection: the module's shape, naming, and behavior all match the ticket's own Scope/AC exactly),
but no `staging_artifacts/` directory, and no `agent-monitoring/runs.jsonl`/`events.jsonl` records,
existed for this run at the time of the stall. Every claim in this document and its siblings was
independently re-verified against the real, current state of the code — not merely asserted —
mirroring exactly how `TCK-20260719-AGENT-ROLE-GLOSSARY` (earlier in this same session) handled and
documented an identical situation.
