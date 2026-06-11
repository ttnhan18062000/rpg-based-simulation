---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260418-RESOURCE-CERTIFICATION-M9
artifact_type: investigation
tags: [resource, certification, m9]
---

# Investigation: Milestone 9 Certification Harness

## Objective
Implement a proof-oriented harness that certifies engine compliance with its resource envelope.

## 1. Conformance Measurement
- **Memory**: Use `psutil.Process().memory_info().rss` to monitor RAM.
- **CPU/Tick**: Measure `time.perf_counter()` delta per tick vs `max_tick_budget_ms`.
- **Pressure**: Identify the "Break Point" by injecting entities or artificially reducing `max_ram_mb`.

## 2. Hardware Classification
- We need a simple way to label the host environment.
- **CLASS_A (Server)**: > 8 cores, > 16GB RAM.
- **CLASS_B (Workstation)**: 4-8 cores, 8-16GB RAM.
- **CLASS_C (Legacy/Edge)**: < 4 cores, < 8GB RAM.
- (Note: This is an approximation for internal certification).

## 3. Scenario Design
- **Scenario Alpha (Idle)**: Basic 10-entity run. Verify 100% budget adherence.
- **Scenario Beta (Saturation)**: Create 10k entities (or enough to hit 80% RAM). Verify `Governor` kicks in with `SHED_ACTIONS`.
- **Scenario Gamma (Recovery)**: After Beta, delete 90% of entities. Verify `Governor` returns to `NORMAL`.
- **Scenario Delta (Deterministic)**: Seeded 10-tick run. Verify Hash Equivalence.

## 4. Reporting
- Certification should produce a `CERTIFICATION_REPORT.md` artifact with exact measurement tables.
