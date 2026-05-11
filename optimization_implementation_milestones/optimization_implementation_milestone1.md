# Milestone 1 — Choose Realistic Runtime Profiles

## Objective

You said current profiles are too low and you can use up to 4 GB.

This milestone finds the smallest good profile instead of guessing.

---

## Technical tasks

### 1.1 Run profile matrix

Test these combinations:

```text
IDLE_1000:
  512 MB
  1 GB
  2 GB
  4 GB

IDLE_5000:
  512 MB
  1 GB
  2 GB
  4 GB

RESOURCE_1000:
  1 GB
  2 GB
  4 GB

MIXED_1000:
  1 GB
  2 GB
  4 GB
```

For each, record:

```text
p95 tick ms
peak RSS
memory delta
phase breakdown
worker utilization
```

---

### 1.2 Define profile decision rules

A profile is acceptable if:

```text
p95 tick < 50 ms
peak RSS < 75% of max RAM
memory_delta is stable
no conformance failure
no replay backlog growth
```

Example:

```text
1 GB profile:
  Accept if peak_rss < 750 MB

2 GB profile:
  Accept if peak_rss < 1500 MB

4 GB profile:
  Accept if peak_rss < 3000 MB
```

---

### 1.3 Update runtime profile defaults

After measurement, define:

```text
DEFAULT_PROFILE
LARGE_WORLD_PROFILE
STRESS_PROFILE
CERTIFICATION_PROFILE
```

Recommended likely starting point:

```text
DEFAULT_PROFILE:
  2 GB RAM
  4 workers
  50 ms tick budget

STRESS_PROFILE:
  4 GB RAM
  4 or 8 workers
  50 ms tick budget
```

But only set this after measurement.

---

## Exit criteria

You can answer:

```text
For 1000 entities, use profile X.
For 5000 entities, use profile Y.
4 GB is needed only when scenario Z exceeds 2 GB.
```

---
