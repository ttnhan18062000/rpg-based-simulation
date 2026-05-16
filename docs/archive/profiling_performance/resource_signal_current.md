Using the latest design pattern in your uploaded source, the current solution is:

```text
resource pressure signal
→ ResourceGovernor evaluates against RuntimeProfile limits
→ RuntimeStatus changes operational mode
→ GovernorPolicy reduces engine behavior
```

It is **not** currently:

```text
resource hits max
→ engine immediately kills work / sheds entities / blocks new entities / raises fatal error
```

It mainly enters a **degraded/survival mode** and returns a policy.

---

# Current behavior when profile resource limit is hit

## 1. The governor checks pressure signals

`ResourceGovernor._get_indicated_mode(...)` evaluates signals such as:

```text
work_debt_total
tick_compute_ms
memory_estimate_mb
worker_utilization
queue_utilization
replay_backlog_kb
```

against the limits in `RuntimeProfile`.

The most important thresholds are:

```python
if signals.work_debt_total >= profile.max_work_debt:
    return RuntimeMode.SURVIVAL

if signals.tick_compute_ms >= profile.max_tick_budget_ms * 1.5:
    return RuntimeMode.SURVIVAL

if signals.memory_estimate_mb >= profile.max_ram_mb:
    return RuntimeMode.SURVIVAL
```

So if RAM reaches the assigned maximum:

```text
memory_estimate_mb >= max_ram_mb
```

the engine should enter:

```text
SURVIVAL
```

---

# 2. Before max is reached, it degrades earlier

The current code has earlier warning levels.

## CONSTRAINED

Triggered when:

```text
tick_compute_ms >= 70% of max_tick_budget_ms
worker_utilization >= 70%
queue_utilization >= 70%
memory_estimate_mb >= max_ram_mb * degradation_threshold_ram
```

Meaning:

```text
The engine tries to react before hitting the hard maximum.
```

## DEGRADED

Triggered when:

```text
work_debt_total >= 50% of max_work_debt
tick_compute_ms >= max_tick_budget_ms
worker_utilization >= 90%
queue_utilization >= 90%
replay_backlog_kb >= 90% of max_replay_buffer_kb
```

## SURVIVAL

Triggered when:

```text
work_debt_total >= max_work_debt
tick_compute_ms >= 150% of max_tick_budget_ms
memory_estimate_mb >= max_ram_mb
```

---

# 3. The governor returns a policy

After mode is selected, `GovernorPolicy.from_mode(...)` converts it into engine behavior flags.

Current policy matrix:

| Mode          | Opportunistic work | Non-authoritative periodic | Diagnostics | Metrics | Concurrency | Replay                    |
| ------------- | -----------------: | -------------------------: | ----------- | ------- | ----------: | ------------------------- |
| `NORMAL`      |                yes |                        yes | FULL        | HIGH    |         1.0 | FULL                      |
| `CONSTRAINED` |                yes |                        yes | MINIMAL     | HIGH    |         1.0 | FULL, no subsystem traces |
| `DEGRADED`    |                 no |                        yes | ERROR       | LOW     |         0.5 | MINIMAL                   |
| `SURVIVAL`    |                 no |                         no | MUTED       | MUTED   |        0.25 | OFF                       |

This comes directly from `GovernorPolicy.from_mode(...)`.

So when a resource reaches the maximum, current intended behavior is:

```text
SURVIVAL mode
disable opportunistic work
disable non-authoritative periodic work
mute diagnostics
mute detailed metrics
reduce concurrency to 25%
disable replay
```

---

# 4. Escalation is immediate, recovery is controlled

Current `ResourceGovernor.evaluate(...)` does this:

```text
if indicated_mode > current_mode:
    escalate immediately

if indicated_mode < current_mode:
    recover only if _can_recover(...) allows it

else:
    keep dwelling in same mode
```

So the current solution avoids slow reaction when pressure rises.

But it avoids thrashing during recovery by using:

```text
dwell time
confidence window
recovery watermark
```

The tests show this intended behavior: recovery requires several sustained good samples rather than immediately dropping back to normal.

---

# Current weakness / gap

The current solution is mostly **policy-level degradation**, not full resource enforcement.

Meaning:

```text
It detects pressure and returns a policy.
```

But the actual engine still needs every subsystem to respect the policy.

Example:

```text
Policy says replay_allowed=False.
ReplaySink must actually skip replay emission.

Policy says allow_non_authoritative_periodic=False.
Scheduler/pipeline must actually skip periodic non-critical systems.

Policy says concurrency_limit=0.25.
Executor/worker manager must actually reduce concurrency.
```

Some parts appear wired, such as worker execution accepting `concurrency_limit` in the executor/worker flow.

But from the current design, I would not assume every expensive subsystem fully obeys the policy yet.

---

# Investigation result

Current resource-max solution:

```text
1. Detect pressure through PressureSignals.
2. Compare against RuntimeProfile.
3. Escalate RuntimeMode.
4. Return GovernorPolicy.
5. Subsystems are expected to reduce optional work, replay, diagnostics, and concurrency.
```

Current missing/uncertain part:

```text
Hard backpressure is not clearly complete.
```

For example, I do not see from the current snippets a guaranteed behavior like:

```text
if max_ram_mb exceeded:
    stop spawning entities
    stop accepting new work
    force queue shedding
    compact replay buffers
    clear nonessential caches
    reduce LOD
```

The current `SURVIVAL` policy gives the right signals, but you should verify each subsystem obeys it.

---

# What should happen when a resource hits max

I suggest defining this exact contract:

## If memory reaches max RAM

```text
Mode: SURVIVAL

Actions:
- stop spawning new entities
- disable replay
- disable full diagnostics
- skip strategic/social/world periodic systems
- compact or rotate replay buffers
- drop non-critical queued work
- switch distant entities to background/dormant LOD
- prevent API full-state deepcopy
```

## If tick time exceeds budget

```text
Mode:
- >= 70% budget: CONSTRAINED
- >= 100% budget: DEGRADED
- >= 150% budget: SURVIVAL

Actions:
- reduce optional work
- run strategic less often
- defer non-critical periodic work
- cap work processed per tick
```

## If queue utilization is high

```text
Mode:
- >= 70%: CONSTRAINED
- >= 90%: DEGRADED

Actions:
- reduce scheduled work
- drop opportunistic work
- batch similar work
- limit new work generation
```

## If replay backlog is high

```text
Mode:
- >= 90% replay buffer: DEGRADED

Actions:
- reduce replay richness to MINIMAL
- then OFF in SURVIVAL
```

---

# Tests you should add next

## 1. Memory max should enter survival

```python
def test_memory_max_enters_survival(base_profile):
    gov = ResourceGovernor()
    status = RuntimeStatus()

    signals = PressureSignals(
        memory_estimate_mb=base_profile.max_ram_mb,
    )

    policy = gov.evaluate(
        base_profile,
        signals,
        status,
        current_tick=1,
    )

    assert status.current_mode == RuntimeMode.SURVIVAL
    assert policy.replay_allowed is False
    assert policy.allow_opportunistic is False
    assert policy.allow_non_authoritative_periodic is False
    assert policy.concurrency_limit == 0.25
```

## 2. Memory warning should enter constrained

```python
def test_memory_warning_enters_constrained(base_profile):
    gov = ResourceGovernor()
    status = RuntimeStatus()

    signals = PressureSignals(
        memory_estimate_mb=(
            base_profile.max_ram_mb
            * base_profile.degradation_threshold_ram
        )
    )

    policy = gov.evaluate(
        base_profile,
        signals,
        status,
        current_tick=1,
    )

    assert status.current_mode == RuntimeMode.CONSTRAINED
    assert policy.diagnostic_verbosity == "MINIMAL"
```

## 3. Policy must be consumed by scheduler

```python
def test_survival_policy_drops_non_authoritative_periodic_work():
    """
    In SURVIVAL mode, scheduler must not emit non-authoritative periodic work.
    """
```

## 4. Policy must be consumed by replay

```python
def test_survival_policy_disables_replay_emit():
    """
    In SURVIVAL mode, ReplaySink must not emit replay events.
    """
```

## 5. Policy must be consumed by spawning/world dynamics

```python
def test_survival_policy_blocks_entity_spawning():
    """
    In SURVIVAL mode, world dynamics should not add non-critical entities.
    """
```

---

# My judgment

The current solution is good as a **first-level governor**:

```text
Pressure → mode → policy
```

But it is incomplete as a **full resource protection system** unless every expensive subsystem consumes that policy.

So the next enhancement should be:

```text
Add policy-enforcement tests per subsystem.
```

Specifically verify:

```text
Scheduler obeys allow_opportunistic / allow_non_authoritative_periodic
Replay obeys replay_allowed / replay_richness
WorkerManager obeys concurrency_limit
Observability obeys metrics_detail
WorldDynamics obeys policy before spawning
Strategic systems obey policy/cadence
API avoids full-state copy in survival/degraded mode
```

That will tell you whether hitting max profile resources actually protects the engine or only changes a status flag.
