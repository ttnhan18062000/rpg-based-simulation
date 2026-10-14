---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION
date: 2026-10-14
tags: [performance, benchmarking, regression]
---

# Plan: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION

Measurement only. No `src/` edit outside `src/perf/`. **Nothing runs before perf-planner approves this file and #591 has merged** (the corpus loader of `tools/perf/rerun_baselines.py` lands there). Branch `perf-tick-cost-growth`, stacked on `perf-profile-api-dead-refs` (#595) so the ticket files exist; it re-bases on main once #595 and #591 merge. Host rules (lead-planner owns the machine): foreground, one process at a time, `systemd-run --user --scope -p MemoryMax=<cap> -p MemorySwapMax=0`, loadavg and swap read before each run (pause above 7 GB swap or under 1.5 GB available), lead-planner told before any run expected above about 3 GB, an OOM or cap hit stops the plan and is reported, the cap is never raised.

## Conditions from perf-planner's review (GO, 2026-10-14), applied
- **(a) Pinned helper:** importing `tests/helpers/kernel_pinning.PinnedNormalGovernor` into a `tools/perf` module is approved (precedent: `tools/perf/memory_probe.py` imports from `tests/`). Every profile header states **"pinned fixes the RuntimeMode only"** and lists the wall-clock inputs that still move outside `audit_mode`: the mid-tick budget throttle's wall-clock reading (report-only since DEV-014), the queue and worker wall-clock signals, and the scheduler's tick-time inputs.
- **(b) Tools without touching the shared `.venv`:** py-spy by `uv tool install py-spy==0.4.2` (the `uv.lock` version; a user-level binary; `profile_tick` launches the child with the repo's `.venv` python, so py-spy needs none of the repo's dependencies). **Never `uv sync --group perf` into `.venv`.** Memory attribution: stdlib **`tracemalloc` first** (a snapshot before and after the world build, top 25 by traceback); memray only if tracemalloc cannot attribute, in a scratch venv outside the repo with `PYTHONPATH` to the `.venv` site-packages; the doc names the tool used. lead-planner is asked before any install.
- **(c) Old commits:** no `git worktree add`. `git archive <sha> | tar -x -C <dir under the session scratchpad>` and run from there with the `.venv` python and `PYTHONPATH=<that dir>`. Old-commit profiles are labelled **live contract** (the old tree has no pinned helper) and compare by phase **share**, not absolute ms. An old tree that does not run is reported and left alone, not patched.
- **(d) movement[5000]:** only after the 100 to 2000 curve; I message perf-planner and lead-planner with the extrapolated RSS and wall time and wait for the go.
- **(e) py-spy overhead:** measured first and written into `investigation.md` (rate chosen) before any main run.
- **Resource conditions (lead-planner, via perf-planner; swap was at 7.0 of 8 GB):** before **each corpus run** (about 1.7 GB) `free -m` must show **at least 2.5 GB available**, logged next to the run; if lower, wait, and if it stays lower tell lead-planner and do not run. Before every run (all kinds) at least 2.5 GB available, and **swap above 7.5 GB pauses everything** (tell lead-planner). **No profiling run overlaps another session's heavy job**; if lead says hold, I hold. py-spy launches the target (`py-spy record -o ... -- python ...`), never attaches to a running PID (attach needs ptrace rights; no sysctl is changed; a permission failure stops the work and is reported). memray: ask again first. At the end I delete **only the scratch directories I created** (the `git archive` trees, any memray venv) and list them in the ticket; I also list what I installed (`uv tool uninstall py-spy` removes it).
- **Order constraint:** the corpus-world runs need `rerun_baselines`' loader, which is on main (#591) but not on this stacked branch until #595 lands and main is merged into it (perf-planner: not before). Until then only the synthetic scenarios (idle, combat, mixed, strategic, movement curve) run.

## 1. Fixed work without a `src/` edit (assumption A1)
The profiles must compare the same work, so the governor mode must not move. Four contract variants, all selectable from `tools/perf` alone:
| id | how | what it fixes | what it still lets move |
|---|---|---|---|
| **pinned** (the reference) | `Kernel(profile, state, rng, governor=PinnedNormalGovernor(), flags={no_replay, no_frame_pacing, audit_mode: False})`; the class is the shared `tests/helpers/kernel_pinning.py::PinnedNormalGovernor` (the only allowed copy: an architecture guard flags a new local one), imported from the tool. `Kernel.__init__` takes `governor` (`src/engine/kernel.py:64`), so no `src/` change. | the RuntimeMode (always NORMAL) | other wall-clock inputs outside `audit_mode` (its docstring says so); DEV-014 made the budget throttle report-only, so a non-audit run no longer sheds results |
| **canonical** | `src.perf.profiles.canonical_variant(PROD_LARGE)` (the same variant mechanism T08 used) | the governor reads a modelled cost, so the mode sequence is host-independent; it left NORMAL for 6 records in T08, which is a finding, not a defect of the tool | the measured tick ms (telemetry) |
| **audit** | `flags={"audit_mode": True}` | `ZeroedSignalSource` keeps NORMAL | **adds work**: start/end fingerprint and the dirty-set audit (`kernel.py:419-435`); used only to measure what audit mode adds (fingerprint share), never as the work reference |
| **live** | the profile as `profile_tick.py` runs it today | nothing | the governor; kept as the "what T08 saw" comparison |
Each profile records which contract it used (header field), its mode sequence and loadavg. If a pinned run still shows a shifted work counter (processed-work counters in `phases.json`) I report that and stop, I do not edit `src/`. `profile_tick.py` gets one `--contract {live,pinned,canonical,audit}` option (default `live`, behaviour unchanged) and a `--world <corpus world>` option that calls the loader of `rerun_baselines.py` (no third loader). A unit test pins the option mapping and that `live` is byte-for-byte today's behaviour.

## 2. Scenarios, and what each run is expected to cost
Numbers cited: `reports/perf/t08` summaries (stored as `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS/evidence.md`): avg tick ms and worker peak RSS (`peak_rss_mb`) and wall per run (`wall_s`, which includes world build, warmup and the sampled ticks). A profile run is 3 warmup + 30 measured ticks (the tool's default), so the wall is about 33 x tick plus state build; py-spy adds its overhead (section 3).
| scenario | avg tick (T08, canonical) | peak RSS (T08) | one profile run, expected | cap |
|---|---|---|---|---|
| `idle_100` | 36-62 ms | 64 MB | about 10 s, 0.1 GB | 1 GB |
| `combat_10` | 31-60 ms | 64 MB | about 10 s, 0.1 GB | 1 GB |
| `mixed_200` (140 entities) | 167-182 ms | 78 MB | about 10-15 s, 0.1 GB | 1 GB |
| `strategic_100` | 399-496 ms | 81-91 MB | about 20-30 s, 0.1 GB | 1 GB |
| `simq_corpus_frontier_extended` | 166 ms | 1703 MB (`wall_s` 180 s for 1100 ticks) | about 30 s plus the world build, 1.7 GB | 2.5 GB |
| `simq_corpus_frontier_marches` | 98 ms | 1568 MB | about 20 s plus the world build, 1.6 GB | 2.5 GB |
| movement scaling 100, 500, 1000, 2000 | 100: 101-135 ms (T08) | 100: 76 MB | 100: 10 s; larger sizes: see section 4, measured as a curve, not guessed | 1 GB, raised only after a measured size and my message to lead-planner |
Every run is done under **pinned** and **canonical** (AC1), plus **live** for the two cheapest scenarios and **audit** for `strategic_100` and `frontier_extended` only (fingerprint share). Total about 40 short runs, none above 3 GB, one at a time. Heavy memory (section 6) uses memray on the two corpus worlds only.

## 3. py-spy overhead
`py-spy record` is sampling (`--rate 250` default in `profile_tick.py`) in a child it launches itself, so no elevated privilege. Its overhead is **measured, not assumed**: on `idle_100` and `strategic_100`, 3 repetitions each of the same pinned run (a) without py-spy (tick avg from the `phases` data of a no-sampling child) and (b) at 250 Hz and (c) at 100 Hz; report mean tick ms and the ratio, and use the lowest rate whose ratio is within 5 % for the rest. The folded stacks are shares, not absolute ms; absolute ms come from the per-phase table of the same run. py-spy and memray are **not installed** in the repo venv (`.venv` has neither): I install the `perf` dependency group into a scratch venv outside the repo (`uv`), and tell lead-planner before the download. If it cannot be installed, the plan stops at the per-phase tables and says so.

## 4. movement[5000] against combat_10 (AC4)
They are almost certainly **different scenarios at different scale**: `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` measured `combat_engagement` at 3.2-3.4 s per tick on `build_movement_state(5000)` (5000 entities, `PERF_2GB_LOCAL`, with cooperation 10.2-10.9 s of a 11.9-16.5 s tick, and 16 s on another box), while T08 measured `combat_engagement` at 28-43 ms in `strategic_100` / `mixed_200` (100-140 entities). Plan: run `movement` at 100, 500, 1000, 2000 entities under **pinned** (same builder, same profile), fit `combat_engagement` ms against entity count (a power law, reported with the fit), and compare the extrapolated 5000 with 3.2-3.4 s; run 5000 only if the extrapolated RSS and wall are sane (state the expected values before, from the curve; the 5000-entity state alone is expected to be about 0.5-1 GB from the T08 per-entity RSS slope, which I must tell lead-planner about if above 3 GB) and capped. Then `combat_10`: 10 against 10 entities has no movement, so I report its `combat_engagement` ms per entity pair next to the movement curve. Also note the box dependence the ticket records (3.2 s vs 16 s on identical code): every number here carries host, CPU, loadavg.

## 5. Then-versus-now, call sites, the three held tickets
- **Old commits (scope 4):** `git worktree add --detach <scratch> <sha>` for `20f773dee` (2026-05-15, the date of the May baseline files), `c84352465` and `132bf09ca` (both exist). Run the same scenario through `BenchHarness` there (the old tree's own `profile_tick.py` if present, else the old `BenchHarness` with the same builder call), `profile_diff.py` old vs now. If an old commit does not import or the scenario builder differs, I say so and do not reconstruct it. Scratch worktrees are deleted afterwards (they are mine).
- **Call-site attribution (AC2):** every phase above 5 % of the tick gets folded-stack evidence from the same run, grouped by the first `src/` frame under the phase function, with the excerpt in the doc.
- **Fingerprint (`TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`):** read `kernel.py:664` (REFINED_UPDATE under `replay_allowed`) and `:1096`; with the `pinned` flags (`no_replay=True`) check whether `fingerprint()` appears in the folded stacks at all, and its share under `audit`; close or update with that evidence.
- **Decision trace (`TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`):** look for `decision_trace_writer` frames on the tick thread in the folded stacks (py-spy `--threads` shows the thread); if none, close as not-a-tick-cost with the folded-stack evidence.
- **Hostility projection (`TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`):** the `is_hostile_compat` to `project_relation` share from the movement curve; the fix stays with rpg Lane B.

## 6. Memory (AC6)
`frontier_extended` peaked at 1703 MB and `frontier_marches` at 1568 MB (T08 `peak_rss_mb`), `rss_delta` 1587 and 1454 MB: the growth happens at world build, not over the ticks, so memray runs with 3 warmup + 5 ticks (memray slows a run by a large factor, so few ticks, and the run stays short), cap 2.5 GB. Output: top allocation sites at the high-water mark. Whether anything checks a profile's declared memory: already found in T08 (no memory comparison in `BenchHarness` or `compare()`; the memory guard is LIVE-only); I propose a perf-owned check (record the ratio `rss_high_water / ram_mb` in the benchmark record and flag above 1 as a note, not a gate, OD-8) in the doc and file a ticket, not build it here.

## 7. Output and acceptance map
`docs/performance/tick_cost_growth.md` with: the per-scenario phase table (all contracts, each with host, CPU, loadavg, main sha, mode sequence); the top call sites with share and folded-stack excerpts; per hotspot "legitimate work" or "waste" with the reason; a ranked rpg hand-off list (file, function, expected saving) that lead-planner can post to #593; the input for the option (i) decision (the budget the legitimate work needs, derived from the pinned tick cost, not from the canonical mode). AC1 table 2 and section 1; AC2 section 5; AC3 section 5; AC4 section 4; AC5 section 7; AC6 section 6; AC7 the resource rules above and the py-spy measurement in section 3. A first step before any run: a unit test (`tests/unit/perf/test_profile_tick_contract.py`) for the new options, run without any heavy process.

## 8. What I need from perf-planner
Answered by the conditions above (all three approved with changes).
