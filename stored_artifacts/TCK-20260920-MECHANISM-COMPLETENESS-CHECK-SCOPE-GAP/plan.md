---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP
artifact_type: plan
tags: [architecture]
---

# Plan

1. Widen `mechanism_registry_completeness_check.py` with a second, rule-based tier (scope, candidate, unbound, wired rules in the module comment), report-only, with `WIDER_EXCLUSIONS` (infrastructure, reason each) and `WIDER_PENDING` (identity undecided, reason each).
2. Pin the tier in `test_mechanism_registry_completeness_check.py`: every wired candidate has a disposition; exclusions/pending point at real candidates and carry reasons; numbers pinned.
3. Disposition each wired candidate: bind (class-level `implemented_by`), exclude, register (identity calls from rpg-feature-planning), or pending.
4. Update `docs/plans/mechanism_claims_as_tests_initiative.md` §3.4.
