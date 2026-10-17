---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-LOCUST-API-LOAD-TEST
phase: open
date: 2026-10-18
tags: [platform, performance, benchmarking]
---

# TCK-20261018-LOCUST-API-LOAD-TEST

## Title
tools/loadtest: a Locust API scenario and a runner that records the method, the environment and the USE signals with every run

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D9 (Locust per the amendment) and #541 item 1. A throughput figure counts only with its method: the hardware spec,
the commit, the fleet state, the USE checklist and the run-to-run spread. This ticket builds the tool and proves it on
a short smoke run. The measured run is the next ticket.

## Scope
- **`tools/loadtest/locustfile.py`.** API only, never the simulation tick.
  - Endpoints: `/health` (no auth) and 3-5 cheap admission-gated read endpoints. Pick them from the routers mounted
    by default, and list them with their weights in the README.
  - The `X-API-Key` header comes from a pool of load-test keys, one key per Locust user. This keeps the per-key token
    bucket (30, refilled at 3/s, `src/api/admission_control.py`) from being what's measured.
  - 429 responses are a separate Locust failure category ("admission"), apart from 5xx and transport errors.
  - No think time inside a step, so the offered load is set by the user count.
- **Key setup without `src` changes:**
  - a helper writes N random keys to a gitignored file and prints the `api_key_hashes` value
    (`loadtest-<i>:<sha256>`, comma-joined);
  - a compose override `tools/loadtest/compose.loadtest.yaml` sets that env var on `backend`. Find the real env-var
    name from `src/config/loader.py`; don't guess it.
- **`tools/loadtest/run.py`** (or a shell script):
  - Runs Locust headless at fixed user steps (for example 10/25/50/100/200), each a fixed duration after a warm-up,
    repeated R times (default 3).
  - Writes Locust's CSV stats per step and repeat.
  - Records alongside them, in a JSON manifest:
    - the commit;
    - the image digests;
    - `lscpu`/`free`/`nproc`, and whether the host is a VM;
    - the engine state (tick rate, running or paused, world/profile), the observability profile on or off;
    - the fleet state: the count of other Claude sessions and their load average, from `uptime` and a process count.
  - USE sampling for the backend container and the host during each step: CPU, memory, disk I/O, network. Sources are
    `docker stats --no-stream` at an interval, plus `vmstat 1` and `pidstat` if installed; saturation signals (run
    queue, swap, throttling); errors (5xx, 429, timeouts).
  - Prints a summary table per step: req/s, p50/p95/p99, median and min-max across repeats, error rates. It names the
    first resource that saturated, with the rule used to decide it (written in the README).
- **Locust runs on the host** (not in the backend container), outside the cap from the host rules. Its own CPU use is
  recorded too, because Locust shares the 6 vCPUs with the backend. The README says so.
- **Dependency:** `locust` in a new `[dependency-groups] loadtest` group in `pyproject.toml`, plus `uv.lock`. Not a
  runtime dep. These files are lead-owned: lead-planner reviews the diff (approved in principle 2026-10-18). After the pin,
  run `tests/static` (CI uv pin tests) and **all** of `tests/tools`.
- `.gitignore` gets one line for the load-test key file (lead approved; lead reviews it in the PR).
- **Register `tools/loadtest/**`** to the platform domain's `owns` in `registries/session_roles.yaml`, in this PR (D8
  supersession route: the owner confirms the literal diff; agent-working-planner reviews by comment).
- `tools/loadtest/README.md`: how to run it, the method, and the saturation rule.

## Out of Scope
- The measured run and its record (`TCK-20261018-API-LOAD-TEST-MEASURED-RUN`).
- py-spy profiling (perf's toolkit, through perf-planner).
- Any CI job that runs Locust. Any `src` change, including admission limits.

## Acceptance Criteria
- A 2-step smoke run (for example 5 and 10 users, 30 s each, R=1) against the local default profile completes, after
  asking lead-planner. It writes CSVs, the manifest and the summary, and 429s show up in their own category
  (**running locally**; the smoke numbers are not a measurement and are labelled that way).
- With the key pool on, a 10-user step shows no 429s. With a single shared key it does (shown once: proof that the
  pool works).
- Unit tests for the summary maths (percentile spread across repeats, the saturation rule) using fixed CSV fixtures.
  They live where the repo's tests for `tools/` live and use `tools.agent_working_paths` for any agent-working path
  (memory: paths guard).
- The CI pin tests pass after the `uv.lock` change (`tests/static`, including `test_ci_uv_install`). `tests/tools`
  passes with the new files (memory: regen REGISTRY / new files).
- `tools/sessions/validate.py` passes with the new `owns` glob.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. No step-2 dependency: it can be built in parallel with step 2.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D7, D9), `docs/engine/performance_contract.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/loadtest/` (new), `pyproject.toml`, `uv.lock`, `registries/session_roles.yaml`, `.gitignore` (the key file)

## Assumptions / Open Questions
- The load-test keys never reach git. Only their hashes go into the override's env var, at run time.
- If the default profile serves no world data (empty endpoints), pick endpoints that do real work, or record that
  the measured paths are cheap. Don't load a world through the tick to fill them.

## Implementation Notes
- Env var for the key hashes: `RPG_API_KEY_HASHES` (ConfigLoader prefix `RPG_` + field `api_key_hashes`, `src/config/loader.py`, `src/cli/entry.py`). The override reads it from `LOADTEST_API_KEY_HASHES` and fails if unset.
- Endpoints (all admission-gated except /health): live/status 3, state 2, live/health 2, entities 1, /health 2. Whether they do real work on the default profile is not yet checked (needs the smoke run).
- `classify_failure` lives in `summary.py` (no locust import) so tests run without the loadtest group; `locustfile.py` imports it and needs `PYTHONPATH=<repo>` (run.py sets it).
- Warm-up is a separate, unrecorded Locust invocation per repeat. USE: `docker stats`, `vmstat 1`, `ps` of the Locust process. pidstat/throttling not sampled (not needed for the smoke).
- `locust==2.46.7` in `[dependency-groups] loadtest` (not a default group; 14 days old on 2026-10-18). `uv lock` also moved `requests` 2.32.3 -> newer and `cffi` 2.0.0 -> 2.1.1 (locust's dependencies); lead should look at those two in the uv.lock diff.
- Generated session agent cards (`.claude/agents/session-platform-*.md`) were regenerated: the `owns` glob is embedded there and `tools/sessions/validate.py` reports generated-drift without them.
- `.gitignore`: `tools/loadtest/.keys.txt` and `tools/loadtest/runs/`.

## Test Summary
- PASS: tests/tools/test_loadtest_summary.py (14 tests, under a 800M cap).
- PASS: `PYTHONPATH=. tools/sessions/validate.py` generated-drift findings fixed by regenerating the cards (re-run needed after commit).
- PENDING (clearances needed): 2-step smoke run (needs a stack start), single-key 429 proof, `tests/static` incl. `test_ci_uv_install`, all of `tests/tools`.

## Files Changed
`tools/loadtest/*` (new), `tests/tools/test_loadtest_summary.py`, `pyproject.toml`, `uv.lock`, `registries/session_roles.yaml`, `.claude/agents/session-platform-{implementer,planner}.md`, `.gitignore`, this ticket.

## Completion Summary
(open)
