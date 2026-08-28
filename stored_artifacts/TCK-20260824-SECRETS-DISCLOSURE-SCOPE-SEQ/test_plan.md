---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
artifact_type: test_plan
tags: [information, feature-flags]
---

# Test Plan — TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Regression Surface

**N/A — no code changes.** This ticket's Scope and Acceptance Criteria (see
`tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md`) require only design/scope
artifacts (schema-extension design for secrecy/confidence-tier metadata, selective-disclosure
logic design) and specific statements in the ticket body (sequencing dependency, the
`DECEPTIVE_DETECTED` delta-reuse decision, the `SocialBond.sentiment`/`SourceTrustEntry`
separation statement). No file under `src/` is created, modified, or deleted by this ticket, so
there is no regression surface to protect — nothing existing can break because nothing existing
changes.

For completeness, if a *future* implementation ticket picks up this design, its regression surface
would include (documented here for that ticket's benefit, not run by this one):

- `tests/unit/domains/information/` (all files — `trust.py`, `contradiction.py`, schema/router/
  assimilation coverage)
- `tests/unit/cognition/test_information_seeking.py` (`TestLeadContradiction`,
  `TestLeadRoutingSystem`)
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
- `tests/unit/social/test_social_bonds.py`, `tests/unit/social/test_relationships.py` (if the
  design touches `SocialBond` at all, which AC4 says it explicitly should not)
- `tests/unit/config/test_phase10_feature_flags.py` (`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist —
  relevant if any new flag is introduced)

## New Tests Required

**None.** No code ships, so there is no behavior to assert against. Writing tests for a
schema/design that does not exist in `src/` yet would be testing nothing real — the prompt
explicitly warns against inventing tests for code that isn't being written, and this ticket's own
AC does not ask for tests (it asks for design artifacts and specific documented decisions).

The design artifact this ticket produces should itself specify what tests a future
implementation ticket will need (e.g. "a test asserting a HIGH-secrecy source's candidate is
excluded from `InformationQueryRouter.route()`'s results unless X"), but drafting that test list
is part of the design deliverable (plan.md), not something to execute or stub here.

## Scoped Pytest Commands

**None to run for this ticket.** No `src/` or `tests/` file changes exist to verify. Do not run
`pytest tests/` or any scoped subset as a substitute — there is nothing to regression-test.

If a reviewer wants to spot-check that the investigation's code-behavior claims are still
accurate at Verify time (e.g. confirm `ENABLE_BELIEF_ASSIMILATION` is still `ON`, confirm
`DECEPTIVE_DETECTED` still has zero callers), that is a read-only grep/inspection step, not a test
run:

```
grep -n '"ENABLE_BELIEF_ASSIMILATION"' src/domains/optimization/feature_flags.py
grep -rn "DECEPTIVE_DETECTED" src/ tests/
```

## Anti-Drift Test Guards

Since no code ships, the real anti-drift guard for this ticket is **process**, not a pytest run:

- **Scope guard**: `git diff --stat` at Verify time must show changes confined to
  `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md`,
  `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/*` (and later
  `stored_artifacts/...`), `tickets/working_log.csv`, `docs/REGISTRY.yaml`, and
  `agent-monitoring/*`. Any `src/` or `docs/mechanics/`/`docs/parity_ledger/` diff on this ticket
  is a scope violation given the Docs Requiring Update section's "None" finding and should block
  Verify.
- **Sequencing guard** (for whichever ticket implements the eventual design): before that
  ticket's own Test phase runs, it must re-confirm `ENABLE_BELIEF_ASSIMILATION ==
  FeatureMode.ON` in `src/domains/optimization/feature_flags.py` and that
  `tests/unit/config/test_phase10_feature_flags.py`'s `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist
  still includes it — a flag flip back to OFF between now and that ticket's start would
  re-invalidate this ticket's premise and should reopen the sequencing question, not be silently
  worked around.
- **Ledger guard**: `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-073` entry
  (`legacy_verified`, `test_path: null`) should not be silently upgraded to `verified` by any
  future ticket without a real `test_path` backing it — flagged in investigation.md's Parity
  Ledger Overlap section as a pre-existing gap this ticket does not fix.
