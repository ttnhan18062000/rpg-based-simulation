---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS
phase: done
date: 2026-08-20
tags: [engine]
---

# TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS

## Title
requirements.txt is missing redis and python-json-logger, both core pyproject.toml dependencies CI never installs any other way

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`pyproject.toml`'s `[project.dependencies]` (the authoritative dependency source, actively
maintained) declares `redis` and `python-json-logger` as core, non-optional dependencies.
`requirements.txt` — which its own header states is "Installed by CI" — is missing both entirely
(verified via direct grep, case-insensitive, whole-file, not just an anchored pattern miss).
Live-confirmed via `.github/workflows/test.yml`: **all 13 CI job steps install dependencies via
`pip install -r requirements.txt` only** — none ever run `pip install -e .` or otherwise install
from `pyproject.toml`. CI genuinely does not install these two packages at all. Both are
importable in the local dev venv, which is masking the gap locally (likely installed via a
separate `pip install -e .` at some point), but a fresh CI runner has no such fallback. `redis` in
particular is a real runtime dependency of `RedisStreamAdapter`/`RedisStreamConsumer`
(`src/observability/stream/`) — the exact subsystem `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`
modified this session.

**Production is confirmed unaffected** — checked directly: `backend.Dockerfile` (used by the
`backend`, `ai_worker`, and `watchdog` `docker-compose.yml` services) installs via
`pip install .` against `pyproject.toml`, never touching `requirements.txt` at all. This gap is
CI/local-dev-only, not a production risk — narrows the blast radius but doesn't remove the need
to fix it, since CI is meant to be a faithful proxy for the real dependency set.

**Exact pins to add**, sourced from `uv.lock` (the canonical resolver output, not guessed):
`redis==7.3.0`, `python-json-logger==4.0.0` — both also match what's currently importable in the
local dev venv.

## Scope
- Add `redis==7.3.0` and `python-json-logger==4.0.0` to `requirements.txt` (exact pins per
  `uv.lock`, matching the file's existing `==` pin style).
- Verify a genuinely fresh install (`pip install -r requirements.txt` in a clean venv, not the
  existing local dev venv) succeeds and the previously-missing packages import correctly.

**(2026-08-20) Full audit now complete** — all of `pyproject.toml`'s dependency groups checked
against their respective requirements files, not just core:
- All 11 core deps: exactly `redis`/`python-json-logger` missing (this ticket's original finding).
- `[dev]` extras: `pytest`/`httpx`/`hypothesis` present in `requirements.txt`; `mypy`'s absence is
  intentional (CI has its own dedicated `pip install mypy` step in the `typecheck` job);
  `memray`'s absence is intentional (its own test file's docstring confirms it's deliberately
  lazy-imported, "importable without memray"); `testcontainers[redis]` is absent but also
  genuinely unused anywhere in the codebase — a different problem, not a missing-install gap, spun
  into its own ticket: `TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY`.
- `[knowledge]` extras: fully present in `requirements-knowledge.txt`, no gap.
- `[search-mcp]` extras (`mcp`): present in `requirements.txt`, no gap.

## Out of Scope
- Reconciling `requirements-knowledge.txt`'s separate, deliberately-scoped package list — that
  file's split from `requirements.txt` is intentional and well-documented (see its own header and
  `docs/guidelines/agent_working_environment.md`), not part of this gap.
- Any change to `pyproject.toml` itself — it's the correct, authoritative source; `requirements.txt`
  is the one that needs to catch up to it.

## Acceptance Criteria
- [x] `redis` and `python-json-logger` are present in `requirements.txt`.
- [x] A full audit confirms no other `pyproject.toml` dependency group has a similar gap — done
      2026-08-20, see Scope. Only `testcontainers` surfaced, and it's a different problem (phantom
      dependency), tracked separately.
- [x] `pip install -r requirements.txt` in a genuinely clean venv succeeds and both packages
      import successfully afterward.

## Related Tickets
- TCK-20260702-CI-REQUIREMENTS-SPLIT (prior related incident — a `pip install -r requirements.txt`
  CI failure; context only, this ticket is a new, distinct gap)
- TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC (the subsystem that made `redis`'s absence from
  `requirements.txt` a live risk, not just a hygiene issue)
- TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY (surfaced by this ticket's own full-audit
  follow-up, different problem, tracked separately)
- TCK-20260820-HOTFIX-DOCKERFILE-STALE-LIBRDKAFKA-BUILD-DEP (sibling finding from the same
  production-vs-CI verification pass)

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- requirements.txt
- pyproject.toml (reference only, not changed)

## Assumptions / Open Questions
- Why this hasn't already caused a visible CI failure is still not fully explained (production is
  now confirmed unaffected, see Request Summary, but CI is a separate question) — possibly the
  currently-exercised fast-lane test paths never actually import `redis`/`python-json-logger` at
  collection time, or CI's own venv caching happens to retain a prior install. Not required to
  root-cause the absence of failure, only to close the gap.

## Implementation Notes
Independently re-verified all claims before implementing (not taken on faith): `grep -in "redis\|python-json-logger" requirements.txt` returned zero hits pre-fix; `pyproject.toml`'s `[project.dependencies]` confirmed both as core (`redis>=5.0.0`, `python-json-logger>=2.0.7`); `uv.lock` confirmed the exact resolved pins (`redis==7.3.0`, `python-json-logger==4.0.0`); `.github/workflows/test.yml` confirmed 12 job steps use `pip install -r requirements.txt`, zero use `pip install -e .`/`pip install .`.

Added both entries to `requirements.txt` in alphabetical order matching the file's existing convention: `python-json-logger==4.0.0` between `python-dotenv` and `python-multipart`; `redis==7.3.0` between `PyYAML` and `referencing`.

## Test Summary
Created a genuinely fresh venv (`python3 -m venv /tmp/clean_venv_reqcheck`, no local dev venv reuse), ran `pip install -r requirements.txt`, confirmed both packages import successfully afterward: `redis.__version__ == "7.3.0"`, `pythonjsonlogger` imports cleanly. Scratch venv removed after verification.

## Files Changed
- requirements.txt

## Completion Summary
Added `redis==7.3.0` and `python-json-logger==4.0.0` to `requirements.txt`, matching `uv.lock`'s
resolved pins exactly. Both are core `pyproject.toml` dependencies that CI's `pip install -r
requirements.txt`-only install path (confirmed: zero jobs install from `pyproject.toml`) was
silently missing — `redis` in particular is a real runtime dependency of
`RedisStreamAdapter`/`RedisStreamConsumer`. Verified via a genuinely clean venv install, not the
existing local dev venv (which was masking the gap). Full dependency-group audit (dev/knowledge/
search-mcp extras) confirmed no other similar gap exists; the one other finding
(`testcontainers[redis]`, unused) is tracked separately in
`TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY`.
