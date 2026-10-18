---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation: Aseprite job "timeout" under host load

## Question
A sub-second Aseprite job (slowest measured 0.258 s, `docs/assets/budgets.md`) sometimes fails `tests/visual_assets/drawing/integration/test_ops.py` on a timeout against `JOB_TIMEOUT_S = 30`. Which phase eats the time?

## Method (2026-10-18, this machine: 6 vCPU, 9.9 GB, VirtualBox guest, other sessions running)
- Code read: `visual_assets/drawing/backend/sandbox.py::bwrap` uses `Popen` + `communicate(timeout=JOB_TIMEOUT_S)`. `communicate` drains both pipes, so a full stdout/stderr buffer cannot deadlock it. No lock, no display or socket is involved (`aseprite -b`, `--unshare-all`).
- Unloaded phase probe (`evidence/probe.py`, 8 rounds): sandbox start 0.03-0.27 s, `aseprite --version` through the sandbox 0.04-0.59 s, trivial batch 0.05-0.40 s.
- Loaded runs: `test_ops.py` under 6-12 busy loops (`evidence/runload3.sh`), one at a time, in a `systemd-run --scope -p MemoryMax=3G`, with `--basetemp` of my own. A pytest plugin (`evidence/phaseplug.py`) times every `sandbox.bwrap` call. An external sampler (`evidence/extsamp.py`, a plain `sleep(1)` loop OUTSIDE the scope) records scheduling gaps.

## Findings
1. Every job that ran normally took 0.15-2.1 s even at load average 35-45. The sandbox, Aseprite start, script and drain phases never came near 30 s.
2. All 4 loaded runs failed on ONE call that took 37-172 s (run 1: 67 s; run 2: 152 s; run 3: 188 s, call 172.4 s; run 4: call 37.4 s). The failure is the conftest SIGALRM budget (`tests/conftest.py`, 60 s) or the 30 s bound, both wall-clock.
3. In run 3 the in-process sampler thread (2 s tick) logged nothing for 167 s, and the process tree sampled at the end held no sandbox or Aseprite process of ours: the job had finished; the Python process was simply not running.
4. Run 4 settles it: the external sampler, a separate trivial process outside the scope, shows `GAP mono 37.7s wall 37.7s` at 14:04:42, matching the 37.4 s call to the second. Earlier gaps: 16.9 s, 3.8 s, 2.1 s, 1.6 s. A `sleep(1)` process was not scheduled for 37 s, so the whole guest stalled; the job was healthy.
5. Host state at the time: load average 35-75 (mostly other sessions: a question-bank run, localsearch, indexers), 2.5-2.6 GB of swap in use, 200 MB free, system CPU 52 %, swap-in 3.5 MB/s. `/proc/stat` steal reads 0 (VirtualBox does not report it), so the host-side cause is not visible from inside. This matches the earlier note on VirtualBox host starvation (soft lockups on idle CPUs).

6. Two more sampled runs (5 and 6, same load, external sampler on) repeat it: run 5 slowest calls 20.0/19.5/17.4 s vs gaps 18.0/17.7/17.5 s; run 6 slowest calls 39.1/21.6/19.9 s vs gaps 37.8/22.2/20.2/18.0 s. Raw samples: `evidence/ext_sampler_run{4,5,6}.txt`, `evidence/phase_run{4,5,6}.txt`.

## Cause
Not a phase of the job and not a defect in `sandbox.py`: the guest as a whole stalls for tens of seconds to minutes under host plus guest contention (swap thrash), and every wall-clock bound (30 s job, 60 s test budget) then trips even though the job needed 0.2 s. The ticket's hypotheses (pipe drain, lock, display/socket wait) are ruled out: `communicate` drains, no lock or display exists, and the process tree was empty at the stall.

## Not established
- Whether u24desktop shows it: unknown (no run records from that machine in this repo).
- Whether the stall is memory pressure in the guest or CPU starvation by the VirtualBox host; the guest cannot tell (steal = 0).

## Implication for the fix
There is no code defect to fix in `visual_assets/drawing/**`. Raising `JOB_TIMEOUT_S` would only move the line (stalls reached 172 s). See plan.md for the options.
