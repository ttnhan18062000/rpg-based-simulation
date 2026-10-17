# tools/loadtest

Locust API load test with the method recorded next to the numbers (ADR D9, TCK-20261018-LOCUST-API-LOAD-TEST).
It loads the HTTP API only, never the simulation tick.

A throughput figure counts only with its method. Every run writes `manifest.json`: commit and dirty flag, backend image
id, `lscpu`/`free`/`nproc`, whether the host is a VM, the engine state (`/api/v1/observability/live/status`),
whether the observability profile is up, and the fleet state (`uptime`, count of `claude` processes).

## Run

```bash
uv sync --group loadtest                                   # locust is not in any default group
# 990 keys, not 1000: the server keeps at most 1000 client entries (_MAX_CLIENT_ENTRIES in src/api/admission_control.py), so the pool plus the
# status key must stay under that or the oldest client is evicted mid-run. 990 keys carry about 2970 req/s before per-key 429s.
export LOADTEST_API_KEY_HASHES="$(python3 tools/loadtest/keys.py -n 990)"   # writes tools/loadtest/.keys.txt (gitignored)
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
admission control. There is no wait between tasks, so offered load = user count. Keys rotate round-robin **per request** over the pool (not one key per user): with no think time a single user sends far more than one key's 3 req/s, so a per-user key would measure the per-key bucket. The pool carries about 3 x pool-size req/s before 429s start (250 keys: about 750 req/s); 429s show up as `admission_429` if the offered load passes that.

Failure categories (Locust's failure messages): `admission_429` (rate limited), `server_5xx_<code>`, `http_<code>`
(other 4xx), and anything else is a transport error. They are counted separately in the summary.

## USE sampling

Before step 1 the runner records a 30 s idle baseline (`--baseline-seconds`). During each step and repeat it samples
every container of the compose project (`docker stats --no-stream`: CPU %, memory, net/block I/O) every
`--sample-interval` seconds, `vmstat 1` for the host (run queue, swap, block I/O, CPU), and the Locust process's own CPU.
The printed table ends with a per-container peak table (CPU % of one core, memory MiB).

Locust runs on the host, outside the backend container and outside any memory cap. It shares the host's vCPUs with the
backend, so `locust_cpu_pct` is recorded in `summary.json`: a high value means the generator, not the API, is the limit.

Host swap and disk (`vmstat si+so`, `bi+bo`) are host-wide, so other sessions move them. They are context, not
verdicts: each step reports its mean minus the idle baseline and flags `host_swap` / `host_disk` only when that is more
than 1 MB/s above baseline.

## Key pool and ceiling

Keys rotate per request over the pool, so the pool carries about 3 x pool size req/s before per-key 429s start
(990 keys: about 2970 req/s). The server keeps at most 1000 client entries (`_MAX_CLIENT_ENTRIES`), so the pool plus the
status key stay under that. Every summary prints the ceiling, and a step whose throughput is above 50 % of it is flagged
`near_pool_ceiling`: the measured run has to stay well below it.

`keys.py` also writes one extra key that is not in the pool (`.status-key.txt`, client id `loadtest-status`). The
manifest reads the engine state (`/api/v1/observability/live/status`) with it before any load starts, so that read never
competes with the load or gets a 429.

## Saturation rule

Saturation is the first step (ascending users) where **throughput gains less than 10 % over the previous step while p95
rises by at least 50 %**. At that step the resource is named, and the branch that fired is recorded:

1. host CPU (vmstat `us+sy`) >= 90 %, or run queue > nproc: `host_cpu`;
2. otherwise backend CPU within 10 % of its maximum over all steps: `backend_process` (GIL/engine contention; Python with
   native threads can use more than one core, so there is no fixed per-core threshold);
3. otherwise `unattributed`.

If there is no such step the summary says so. Separately, each step carries context flags (not verdicts): `memory_near_limit`
(backend memory >= 90 % of its `mem_limit`, `--mem-limit-mb`), `admission_429` and `server_5xx` (>= 1 % of requests),
`host_swap`, `host_disk`, `near_pool_ceiling`.

The rule lives in `tools/loadtest/summary.py` (`find_saturation`, `step_flags`, `above_baseline`,
`ceiling_warning`) and is tested in `tests/tools/test_loadtest_summary.py`. Per step, throughput and p50/p95/p99 are
reported as the median and min-max across repeats.

## Profiled hold
A single-step hold while py-spy samples the backend. Uses `tools/loadtest/compose.profile.yaml` on top of the other two files, for this hold only:
the throughput and observability-on runs never use it, so their backend has no `SYS_PTRACE`. `PY_SPY_BIN` must point to a static py-spy binary
(host: `~/.local/bin/py-spy` 0.4.2); the overlay refuses to load without it.

```
export PY_SPY_BIN=~/.local/bin/py-spy
C="docker compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml -f tools/loadtest/compose.profile.yaml"
$C up -d backend
# start the hold (users N chosen from the throughput run), then 15 s later, after the warm-up:
PYTHONPATH=. python3 -m tools.loadtest.run --users N --duration 120 --repeats 1 --warmup 15 --baseline-seconds 0 --label profiled
# find the uvicorn PID, do not assume 1 (the slim image may have no pgrep/ps, so read /proc; not yet run, check it at the window)
PID=$($C exec -T backend sh -c 'for d in /proc/[0-9]*; do tr "\0" " " < $d/cmdline 2>/dev/null | grep -q "src serve" && echo ${d#/proc/} && break; done')
$C exec -u 0 backend /opt/py-spy record --pid "$PID" --nonblocking --rate 100 --duration 90 --format raw -o /app/data/profile.raw
$C cp backend:/app/data/profile.raw ./profile.raw           # then convert to SVG with a flamegraph tool
```

`-u 0` is needed: `ptrace_scope=1` allows attaching only for root with the added capability, while the target stays uid 1000.
Label for the record: "py-spy nonblocking 100 Hz attached during the hold; latency during the hold is not a measured figure".
