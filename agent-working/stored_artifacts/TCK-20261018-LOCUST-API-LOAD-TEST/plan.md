---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-LOCUST-API-LOAD-TEST
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-LOCUST-API-LOAD-TEST

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Plan (from the ticket Scope and the dispatch)
1. `tools/loadtest/locustfile.py`: API only, admission-gated read endpoints plus `/health`, 429 as its own failure category, no think time.
2. Key setup without `src` changes: `tools/loadtest/keys.py` writes N random keys to a gitignored file and prints the `RPG_API_KEY_HASHES` value; `tools/loadtest/compose.loadtest.yaml` sets it on the backend.
3. `tools/loadtest/run.py`: fixed user steps, R repeats, per-step CSVs, a JSON manifest (commit, image id, host spec, engine state, observability on/off, fleet state), USE sampling, a summary table and a saturation rule.
4. `locust==2.46.7` in a new `[dependency-groups] loadtest` group in `pyproject.toml` and `uv.lock`; `.gitignore` lines; register `tools/loadtest/**` to the platform domain's `owns`; `tools/loadtest/README.md`.
5. Unit tests for the summary maths with fixed CSV fixtures; a smoke run (after lead's clearance).
6. Amendment 2026-10-18 (accepted by platform-planner): keys rotate per request over the pool, not one per user; a pool ceiling is printed; knee-based saturation rule; idle baseline for host swap and disk; status key outside the pool; all containers sampled.
7. After the measured window (2026-10-18): the runner reads the engine status key at the start and end of every repeat (tick, governor/health/observability mode, ticks/s).

Commits: f05bfb84d, 017cd242e, 46da5bc3e, 65d27f7e7, d861325fa, 7a226b866, f83cbde54.
