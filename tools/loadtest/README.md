# tools/loadtest

Locust API load test with the method recorded next to the numbers (ADR D9, TCK-20261018-LOCUST-API-LOAD-TEST).
It loads the HTTP API only, never the simulation tick.

A throughput figure counts only with its method. Every run writes `manifest.json`: commit and dirty flag, backend image
id, `lscpu`/`free`/`nproc`, whether the host is a VM, the engine state (`/api/v1/observability/live/status`),
whether the observability profile is up, and the fleet state (`uptime`, count of `claude` processes).

## Run

```bash
uv sync --group loadtest                                   # locust is not in any default group
export LOADTEST_API_KEY_HASHES="$(python3 tools/loadtest/keys.py -n 250)"   # writes tools/loadtest/.keys.txt (gitignored)
docker compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml up -d backend redis
python3 -m tools.loadtest.run --users 10,25,50,100,200 --duration 60 --repeats 3 --label baseline
```

Smoke check: `--users 5,10 --duration 30 --repeats 1 --warmup 5 --smoke` (the output says it is not a measurement).
`--single-key` makes all users share key 0, which shows the per-key limit (30 tokens, refill 3/s,
`src/api/admission_control.py`) as `admission_429` failures; the pool does not.

Output goes to `tools/loadtest/runs/<utc timestamp>/` (gitignored): per step and repeat `step<N>_r<R>_stats.csv`,
`_failures.csv`, `_use.json`; plus `manifest.json` and `summary.json`.

## Scenario

Endpoints, weight: `/api/v1/observability/live/status` 3, `/api/v1/state` 2, `/api/v1/observability/live/health` 2,
`/api/v1/entities` 1, `/health` 2 (no auth). The authenticated ones are mounted by default and gated by the
admission control. There is no wait between tasks, so offered load = user count. One key per user from the pool;
if there are more users than keys, keys are shared and the run warns.

Failure categories (Locust's failure messages): `admission_429` (rate limited), `server_5xx_<code>`, `http_<code>`
(other 4xx), and anything else is a transport error. They are counted separately in the summary.

## USE sampling

During each step: `docker stats --no-stream` of the backend container (CPU %, memory, net/block I/O) every
`--sample-interval` seconds, `vmstat 1` for the host (run queue, swap, block I/O, CPU), and the Locust process's own CPU.

Locust runs on the host, outside the backend container and outside any memory cap. It shares the host's vCPUs with the
backend, so `locust_cpu_pct` is recorded: a high value means the generator, not the API, is the limit.

## Saturation rule

The summary names the first resource that saturated: the lowest user step in which any of these holds (peak over the
step's repeats), ties broken in this order:

1. `backend_cpu`: backend container CPU >= 90 % (100 % = one core; the backend is one process).
2. `host_cpu`: host `us+sy` >= 90 %.
3. `run_queue`: vmstat `r` > nproc.
4. `memory`: backend memory >= 90 % of its `mem_limit` (`--mem-limit-mb`, default 1024).
5. `swap`: any swap in/out (`si+so` > 0).
6. `admission_429`: 429 share of requests >= 1 %.
7. `server_5xx`: 5xx share of requests >= 1 %.

The rule lives in `tools/loadtest/summary.py` (`saturated_resources`, `first_saturation`) and is tested in
`tests/tools/test_loadtest_summary.py`. Per step, throughput and p50/p95/p99 are reported as the median and min-max
across repeats.
