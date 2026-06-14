Yes. I would add **features around resource governance, artifact boundaries, and profiling**, not just patch individual leaks. Right now the system already has the right ideas — bounded queues, replay modes, optimization profiles, certification reports — but they are scattered. You need stronger “resource safety as a first-class feature.”

## My recommended new features

### 1. Certification Evidence Level

Add an explicit evidence mode:

```python
EvidenceLevel.SUMMARY
EvidenceLevel.COMPACT
EvidenceLevel.FULL
```

Default should be `SUMMARY`.

Why: your certification layer currently wants “machine-readable truth,” but it accidentally serializes runtime-heavy evidence like `final_state`. The source marks `final_state` as “optional for large states,” but the current serializer still tries `asdict(self)` and the recorder puts the result into one `proofs_bundle.json`.

Feature behavior:

```text
SUMMARY:
  pass/fail, hashes, seed, profile, resource metrics, final_state_summary

COMPACT:
  selected canonical slices, entity counts, anomaly summaries, top changed objects

FULL:
  separate canonical final_state artifact, never embedded in proofs_bundle
```

This preserves certification purpose but prevents proof artifacts from becoming runtime dumps.

---

### 2. Artifact Budget Registry

Add a central registry where every generated artifact declares:

```yaml
artifact_type: certification_result
max_size_mb: 2
retention: keep_latest_per_scenario
allow_full_state: false
compression: optional
fail_on_budget_violation: true
```

Why: you already have many artifact-producing flows: certification reports, cognition snapshots, replay chunks, behavior reports, run manifests, telemetry logs. The `.agents/workflows/compact-simulation-result.md` already shows the intent to compact heavy logs and archive raw telemetry. That should become an enforced runtime rule, not a manual workflow.

Feature behavior:

```text
Before writing artifact:
  estimate size
  check budget
  compact / split / reject / degrade
```

This prevents future “one JSON file grows forever” problems.

---

### 3. Resource Budget Gate Per Subsystem

Right now you have runtime profiles and optimization profiles, but the budget is not tied tightly enough to subsystems.

Add budget ownership:

```text
certification.max_artifact_mb
replay.max_pending_flushes
observability.max_queue_items
cognition.max_tracked_entities
hashing.max_full_hashes_per_100_ticks
worker.max_inflight_chunks
content.max_hot_path_loads
```

Why: the code already has profile-level concepts like `LOW_MEMORY`, `METROPOLIS`, and `DEBUG_REFERENCE`, with very different cache and budget settings. `DEBUG_REFERENCE` in particular allows huge movement/strategic budgets and large cache counts, which is fine for parity tests but dangerous if accidentally used in large runs.

Feature behavior:

```text
Every subsystem reports:
  current usage
  budget
  pressure state
  degradation action
```

Then your governor can degrade intelligently instead of waiting for MemoryError.

---

### 4. Runtime Resource Dashboard / Health Endpoint

Add a developer endpoint or CLI:

```bash
python -m src diagnostics resources --run-id <id>
```

Output:

```text
Subsystem        Memory Estimate   Queue/Backlog   Status
Certification    0.8 MB            3 artifacts     OK
Replay           240 KB            2 pending       WARN
Observability    1,200 events      80% queue       DEGRADED
Cognition        380 snapshots     120 entities    WARN
Hasher           42 full hashes    high CPU        WARN
Workers          12 in-flight      4 active        OK
```

Why: the stdout shows many observability/optimization failures before the final MemoryError, and pytest eventually fails while rendering/cache-writing. That means the system needs earlier visibility before the process is already dying.

This would make future leak investigation much faster.

---

### 5. Canonical Hash Scheduler

Do not compute full canonical JSON hash casually.

Current hasher builds a full canonical dictionary, sorts major collections, serializes JSON, then hashes it. That walks entities, regions, local scars, resource nodes, buildings, corpses, ground items, chests, groups, camps, blocked tiles, and more.

Feature behavior:

```text
FULL_HASH:
  start of run
  end of run
  certification boundary
  explicit audit/replay mode

LIGHT_HASH:
  tick-local dirty hash
  changed entity IDs
  changed collection signatures
```

Keep deterministic proof, but make full canonical hash a deliberate action.

---

### 6. Replay Backpressure Manager

Your replay buffer is bounded, which is good, but `extract_chunk()` pulls all staged events into a list, and `ReplayManager` can submit async persistence to a single-worker executor. If disk is slow, pending chunk lists can accumulate outside the replay buffer’s own bound.

Feature behavior:

```python
max_pending_flushes = 2

if pending_flushes >= max_pending_flushes:
    if replay_mode == FORENSIC:
        switch_to_sync_or_drop_newest()
    else:
        drop_non_authoritative_chunks()
```

Also expose:

```text
replay.pending_flushes
replay.oldest_pending_age_ms
replay.bytes_pending
```

This prevents a future hidden memory leak from async IO backlog.

---

### 7. Observability Backpressure Controller

`EventRecorder` already uses a bounded queue and `QueueDrainWorker`, but it still keeps an in-memory event list, creates queue envelopes, reconstructs events for stream publishing, and flushes file writes per event.

Add a controller that can switch observability mode dynamically:

```text
NORMAL:
  record normal events

PRESSURE:
  sample INFO events
  keep WARNING+
  batch file writes

DEGRADED:
  keep ERROR/CRITICAL only
  aggregate counters instead of raw events

SURVIVAL:
  local counters only
```

This fits the original purpose: observability should not kill the simulation.

---

### 8. Lifecycle Supervisor for Workers

You already have tests around `QueueDrainWorker` lifecycle and worker leak detection. That should become a runtime feature, not only a test helper.

Feature behavior:

```text
on Kernel shutdown:
  stop EventRecorder worker
  stop BehaviorWorker
  stop ReplayManager executor
  close file handles
  report orphan workers
```

Expose:

```python
kernel.shutdown_report()
```

Example output:

```json
{
  "workers_started": 4,
  "workers_stopped": 4,
  "open_file_handles": 0,
  "pending_replay_flushes": 0,
  "outcome": "SUCCESS"
}
```

This prevents future “thread leak but not memory leak” problems.

---

### 9. Content Repository Hot-Path Guard

Memray shows a hot path where `WorldDynamicsSystem.resolve_dynamics()` reaches `get_faction_semantics_service()`, then `repo.load_all()`, then YAML parsing. If that happens repeatedly during ticks, it is a CPU and allocation smell.

Feature behavior:

```text
ContentWarmupService:
  load YAML/content once at boot
  freeze immutable content maps
  provide read-only handles to systems
  fail test if repo.load_all() is called from tick hot path
```

Add an architecture test:

```text
No YAML/JSON disk parsing inside Kernel.tick_once()
```

This is a strong future-proofing feature.

---

### 10. Profiling Mode for Test Runner

Add a supported command/profile:

```bash
python scripts/profile_memory.py --suite certification
python scripts/profile_memory.py --suite observability
python scripts/profile_memory.py --suite full --memray
```

It should automatically use:

```text
--tb=short
-p no:cacheprovider
--resource-budget off or profiler-safe budget
split-by-test-group
save top allocation stacks
compare with previous baseline
```

Why: pytest’s own cache and traceback rendering can become the crash victim once the process is under memory pressure. Your stdout shows MemoryError inside pytest cache JSON writing near session finish.

This feature prevents you from chasing pytest internals every time.

---

## Possible future issues I would expect

| Future issue                                | Why it may happen                                                    | Preventive feature                             |
| ------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------- |
| Async replay backlog                        | Disk slower than simulation, pending futures hold chunks             | Replay Backpressure Manager                    |
| Full-state proof bloat returns              | Someone adds new evidence field and uses generic serialization again | Artifact Budget Registry + serialization tests |
| Observability overwhelms engine             | High entity count + anomaly burst + file flush per event             | Observability Backpressure Controller          |
| Content YAML parsing inside tick            | Convenience service calls `load_all()` from systems                  | ContentWarmupService + hot-path guard          |
| Debug profile accidentally used in real run | `DEBUG_REFERENCE` has huge budgets                                   | Profile safety gate                            |
| Process worker memory blow-up               | `ProcessPoolExecutor` pickles large packets/results                  | Worker packet slimming + bounded futures       |
| Cache retention across old states           | spatial/read/model caches tied to retained states                    | Cache registry with weakrefs/TTL               |
| Pytest hides root cause                     | final MemoryError happens in traceback/cache                         | Profiling test mode                            |
| Worker/file descriptor leaks                | shutdown path missed in tests or live server                         | Lifecycle Supervisor                           |

## Highest-value feature set

Do not build everything first. Build these five:

1. **EvidenceLevel + safe certification artifact schema**
2. **Artifact Budget Registry**
3. **Runtime Resource Dashboard**
4. **Replay/Observability Backpressure Controller**
5. **Profiling Mode with baseline comparison**

Those five would directly address the current issue and reduce future debugging cost.

## Priority Plan

1. **Mindset or assumption to change**
   Stop treating generated artifacts as harmless side effects. In this project, artifacts are part of the runtime system and need budgets like workers, queues, and caches.

2. **Immediate actions to take**
   Implement `EvidenceLevel`, remove generic certification serialization, add artifact size limits, then add a small resource dashboard showing certification/replay/observability/hash/worker status.

3. **Things to stop or eliminate**
   Stop using generic `asdict()`/deep JSON dumps for proof objects. Stop allowing debug/reference profiles to run in broad suites without an explicit flag. Stop doing disk/content loading from tick hot paths.

4. **Consequences and opportunity cost if you fail to change**
   You will keep fixing individual leaks while new ones appear through evidence, replay, observability, and profiling paths. The engine may pass correctness tests but become impossible to certify at scale because the certification/observability layer itself becomes the bottleneck.
