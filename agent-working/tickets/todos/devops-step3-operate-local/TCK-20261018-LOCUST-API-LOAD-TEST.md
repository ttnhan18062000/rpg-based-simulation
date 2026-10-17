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
- `locust==2.46.7` in `[dependency-groups] loadtest` (not a default group; 14 days old on 2026-10-18).
- **Runtime dependency changes (for the PR body, under "Runtime dependency changes"):** `uv lock` moved `requests` 2.32.3 -> 2.34.2, forced by locust's constraint on it; `requests` is a runtime dependency of the project, so this is a runtime bump. 2.34.2 includes the fix for CVE-2024-47081 (`.netrc` credential leak). Evidence that the backend still passes: the `tests/api` result recorded in Test Summary (lead cleared the run on 2026-10-18 because `requests` changed).
- **cffi:** the lock now has two cffi entries, 2.0.0 and 2.1.1. `uv tree --invert --package cffi` shows the project resolves cffi 2.0.0 (via cryptography, pyjwt, mcp). The lock's own markers split the two by platform only: 2.0.0 for `sys_platform != 'win32'`, 2.1.1 for `sys_platform == 'win32'` (the gevent/locust side). On Linux, where the runtime image and CI run, there is one cffi, 2.0.0. This is a clean marker fork; lead decides (planner asked).
- Generated session agent cards (`.claude/agents/session-platform-*.md`) were regenerated: the `owns` glob is embedded there and `tools/sessions/validate.py` reports generated-drift without them.
- `.gitignore`: `tools/loadtest/.keys.txt` and `tools/loadtest/runs/`.

## Test Summary
- PASS: tests/tools/test_loadtest_summary.py (14 tests, under a 800M cap).
- PASS: `PYTHONPATH=. tools/sessions/validate.py` generated-drift findings fixed by regenerating the cards (re-run needed after commit).
- Cleared run 2026-10-18 (3G cap, own basetemp, one suite at a time, main checkout venv which still has requests 2.32.3, so the `requests` 2.34.2 bump is NOT exercised by these runs):
  - `tests/static`: 96 passed (includes `test_ci_uv_install`).
  - `tests/tools`: 4994 passed, 56 skipped, 1 xfailed (17m14s).
  - `tests/api`: 148 passed, 2 failed (`test_observability_websocket_suite` resource-time-limit TimeoutError; `test_ws_delta_envelope_new_field_...` ConnectionRefused to 127.0.0.1:8008). A re-run of the two files failed three different live-server ws tests (`test_ws_json_handshake`, `test_ws_msgpack_delta_payload_shape`, `test_ws_delta_envelope_includes_null_spatial_placeholder_field`, same ConnectionRefused), 3 passed. The failing set changes between runs, no `src/` or test file changed in this branch: looks like live-server startup timing on a loaded host, NOT shown to be pre-existing (no baseline run on main yet).
- ws flake comparison and `requests` 2.34.2 evidence, 2026-10-18 (same branch code, `tests/api/test_observability_websocket.py` + `tests/api/test_ws_protocol.py`, alternating old/new; 3G cap, own basetemp, host memory >= 2.5 GB before each; scratch venv from `uv sync --locked --no-install-project --no-group lint` on the new uv.lock, requests 2.34.2, deleted afterwards):

  | run | venv | requests | result | failing tests |
  |---|---|---|---|---|
  | ws1-old | shared | 2.32.3 | 6 passed (83.5 s) | none |
  | ws1-new | scratch | 2.34.2 | 6 passed (27.3 s) | none |
  | ws2-old | shared | 2.32.3 | 6 passed (27.1 s) | none |
  | ws2-new | scratch | 2.34.2 | 6 passed (77.0 s) | none |
  | ws3-old | shared | 2.32.3 | 6 passed (27.0 s) | none |
  | ws3-new | scratch | 2.34.2 | 6 passed (26.8 s) | none |
  | full tests/api | scratch | 2.34.2 | 150 passed (74.3 s) | none |

  Reading: no failure in 6 of 6 ws runs and in the full `tests/api` on 2.34.2, so `requests` 2.34.2 is not a regression for the backend API tests. The two earlier failures (shared venv, 2.32.3) did not recur; the slow runs (77-84 s vs 27 s) in both venvs point to load-dependent live-server startup timing, not to the dependency. Run-to-run host load was not controlled.
- **Smoke run, 2026-10-18, SMOKE, NOT A MEASUREMENT** (default profile + observability + `tools/loadtest/compose.loadtest.yaml`; 250 keys; 30 s per step after a 5 s warm-up; R=1; Locust 2.46.7 on the host; host available memory min 4690 MB, swap 2.4-2.8 GB, abort guard never triggered; commit 46da5bc3e plus uncommitted fixes):

  | run | users | req/s | p50 ms | p95 ms | 429 | 5xx |
  |---|---|---|---|---|---|---|
  | pool | 5 | 167.6 | 21 | 78 | 9 of 4875 (0.2 %) | 0 |
  | pool | 10 | 182.0 | 41 | 140 | 0 of 5283 | 0 |
  | single shared key | 10 | 399.4 | 16 | 58 | 9237 of 11616 (79.5 %) | 0 |

  - Pool: no 429 at 10 users (acceptance met). 9 at 5 users: not explained (the first-start burst of keys whose buckets the earlier runs had drained is a guess, not shown). Single key: 429s in their own `admission_429` category, as required.
  - The single-key run's req/s is mostly fast rejections, so it is not comparable to the pool numbers.
  - Peak `docker stats` of the backend in the pool steps: CPU 133.9 % (5 users) and 131.4 % (10 users) of one core, memory 164 and 129 MiB; Locust process CPU 46 % and 42 % of one core; host CPU (vmstat us+sy) 49 % and 43 %; run queue 9 and 12 (nproc 6). Throughput barely rises from 5 to 10 users (168 -> 182 req/s) while latency doubles: consistent with the backend using about 1.3 cores, not shown to be the single limit.
- **Findings from the smoke run (all fixed in the same ticket unless marked OPEN):**
  1. FIXED: `parse_failures_csv` did not see 429s. Locust writes a `catch_response` failure as `CatchResponseError('admission_429')`; the first run reported 0.0 % while the CSV held about 12,000 429s. The test fixtures used the bare message, so the unit tests passed on the wrong format. Fixtures now use the real format.
  2. FIXED (deviation from the ticket's "one key per Locust user"): with no think time one user sends tens to hundreds of req/s, far above one key's refill of 3/s, so a per-user key still measured the per-key bucket (the first pool run with per-user keys logged 4085 + 2596 + 1391 + 2640 = 10,712 429s in its 5-user step; the request total for that step was not recorded, rps x 30 s suggests most requests). Keys now rotate round-robin per request over the pool; the ceiling is about 3 x pool size req/s (250 keys: about 750 req/s) and the runner prints it.
  3. FIXED: the manifest crashed on a `Path` in the settings.
  4. OPEN (decision for the planner, not changed): the `backend_cpu` rule treats 100 % as one core ("the backend is one process"), but the backend reached 131-134 % at 5 users, so the rule reports `backend_cpu` as saturated at the lowest step of every run. The rule needs a better definition (for example against the cores the backend can really use, or against run-queue/host CPU) before the measured run.
  5. OPEN: the `swap` rule uses host-wide vmstat si+so, which other sessions can move (7992 KB/s at the 5-user step); it did not win here only because `backend_cpu` is checked first.
  6. OPEN: manifest `engine_state` was `None` in the pool run (the status request used key 0, whose bucket the earlier run had drained, so it got a 429); `image_digests.backend_repo_digest` holds the image name (`platform-backend`), not a digest, because a locally built image has none. Only the image id is a real identifier.
  7. After the run: `data/runs` holds a root-owned run dir created by the backend container (`run_1792263138_5169_1_3e0de9d3`), reported to the planner, not cleaned. The scratch venv, `.keys.txt` and `tools/loadtest/runs/` were deleted.

## Files Changed
`tools/loadtest/*` (new), `tests/tools/test_loadtest_summary.py`, `pyproject.toml`, `uv.lock`, `registries/session_roles.yaml`, `.claude/agents/session-platform-{implementer,planner}.md`, `.gitignore`, this ticket.

## Completion Summary
(open)
