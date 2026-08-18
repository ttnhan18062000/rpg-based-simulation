---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture]
---

# Epic Plan — Architecture Boundary Enforcement Hardening

**Tracking ticket:** `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`
**Source:** `docs/audits/D24_codebase_health_observatory.md` §E, §K, §M Phase 2
**Priority:** P2

## Problem

Two architecture boundary tests are genuinely strong (AST-based, hard to evade):
`tests/architecture/test_api_read_model_guard.py` and `test_phase_domain_permissions.py`. Two
more exist but are meaningfully weaker — plain substring-grep, not AST:
`test_phase18_import_boundaries.py` (checks `src/core/` never contains the literal substring
`"import src.domains"` — one directional pair, defeatable via `importlib`, aliasing, or an
indirect import) and `test_phase19_observability_boundaries.py` (same limitation, checking for
substrings like `"observability.anomaly"`). No boundary test exists at all for
`domains ↛ observability` internals or `systems ↛ engine` internals — an enforcement gap, not a
confirmed violation (whether such imports currently exist wasn't checked in either audit).

## Scope for the eventual `create-tickets` pass

- Rewrite `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py`
  using the AST-visitor pattern the two strong tests already establish in this repo — applying a
  proven, in-repo technique to two places that currently use a weaker one, not introducing
  anything new.
- Add the two missing boundary tests (`domains ↛ observability`, `systems ↛ engine`) using that
  same AST pattern — first confirm whether violating imports currently exist (neither audit
  checked this), since that changes whether the new test starts red or green.
- Lower priority within this epic, sequence after the above: a Tier-3→Tier-0 `docker-compose.yml`
  startup-dependency linter, motivated by Epic A's RabbitMQ finding — a compose-file concern, not
  a Python import, needs a different mechanism than an architecture test.

## Out of scope

- Building a general machine-readable subsystem-ownership manifest (per-subsystem allowed/
  forbidden deps, invariants, required tests) for all 38 `src/` packages — flagged by D24 §E as
  not existing today, but that's a larger initiative than hardening 4 existing/missing boundary
  tests; track separately if pursued.

## Acceptance signal for this epic (not yet broken into child tickets)

- The two weak boundary tests use AST inspection, not substring matching.
- `domains ↛ observability` and `systems ↛ engine` each have an enforced boundary test.
- Each new/upgraded test is confirmed to actually fail against a deliberately-introduced
  violation (not just pass trivially because nothing violates it yet).

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic G)
- `docs/audits/D24_codebase_health_observatory.md` (§E, §K, §M Phase 2 items 5-6)
