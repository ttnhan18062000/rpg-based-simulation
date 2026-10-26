# Implementation Sequence — devops-step3-operate-local

Written by hand. One PR for the folder (child 6 may stay behind), from a `platform-implementer-local-*` branch. Host ubuntu (#618).

## Order

1. TCK-20261018-LOCUST-API-LOAD-TEST  (no deps; can be built while step 2 is in flight)
1b. TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER  (before any further stack start: compose leaves root-owned data/runs otherwise; filed 2026-10-18 after the smoke run)
2. TCK-20261018-API-LOAD-TEST-MEASURED-RUN  (needs 1; heavy, quiet machine arranged by lead-planner; profiled run through perf-planner)
3. TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK  (needs 2 for the threshold, and step 2's dashboard PromQL); also needs S4 (devops-s4-base-alerts-local) for ntfy, the contact point and the policy (2026-10-18)
4. TCK-20261018-REDIS-DOWN-CAUSE-ALERT  (needs 3; signal A, redis_exporter, decided by lead review 2026-10-18)
5. TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD  (needs 1-4; heavy, run alone)
6. TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT  (done 2026-10-26; rpg's metrics reached main in #645)

Epic: TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL (closes when 1-5 are done).

## Why This Order Matters

The SLO threshold must come from the measured run (D9 before D5). The drill needs an alert that actually fires when
Redis stops, and the API SLO probably won't (see the epic's Assumptions), so the cause alert lands before the drill.
1, 3 and 4 register or edit `compose.yaml` / `registries/session_roles.yaml` in sequence, to avoid self-conflict.

Heavy runs (2, the fire tests in 3 and 4, 5) are asked of lead-planner first, one at a time, under the host rules.

## Update 2026-10-19 (R1 #648 and R2 #654 on main)

- 1, 1b and 2 are done (#627). The batch `platform-implementer-local-slo-alerts` (one PR) runs 3, 4 and 5, together with
  step-2's TCK-20261018-SCRAPE-BACKEND-METRICS-PORT first. Staging artifacts for all four were written at dispatch.
- 3 (SLO alert) needs rpg's 0.3 bucket on main (owner decision 2026-10-19; requested on #622) before its stack run.
- 6 (ai_worker lag): unblocked by #645, done 2026-10-26 (batch `platform-implementer-local-ai-worker-lag`).
- Host slots, one at a time via lead-planner: (a) redis_exporter pull; (b) one full-profile heavy run (9109 checks, age
  soak, server-side SLO numbers, SLO fire test), after the 0.3 bucket lands; (c) the Redis-stop drill under load.
