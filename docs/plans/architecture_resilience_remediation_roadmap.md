---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, engine, observability, testing, documentation]
---

# Architecture, Resilience & Codebase Health — Remediation Roadmap

## Purpose

Two independent audits — `docs/audits/D23_architecture_resilience.md` (failure modes, resource
governance, distributed-system operability) and `docs/audits/D24_codebase_health_observatory.md`
(codebase-scale health, dependency graph, test architecture, AI-agent navigability) — were run
against this repo in the same session (2026-08-17). Both are thorough, evidence-cited, and stage
their own findings by priority. This document does not re-derive those findings; it **groups
them into epic-sized units of work** so a single one can be picked, investigated properly, and
turned into real tickets via the `create-tickets` pipeline — without committing to all ten at
once.

**This is a planning document, not an implementation plan.** No code or doc fix from either audit
has been applied yet. `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` tracks this roadmap; it is
scoped as investigation/prioritization only — breaking any one epic below into concrete child
tickets is deferred until that epic is chosen.

**Update (2026-08-17):** every epic below except C got its own tracking ticket and dedicated plan
document, created 2026-08-17, initially all epic-tier and scope-only.

**Update (2026-08-18):** audited all 10 sub-epic tickets against this project's actual epic-tier
bar ("large multi-ticket initiative") and found 8 of 10 had been mechanically split from this
roadmap's sections without individually re-testing tier fit. Downgraded A, B, D, F, G, H, I to
standard tier and E to hotfix tier — each now carries a concrete, directly-actionable scope and
acceptance criteria, no `create-tickets` pass needed. J and K remain epic tier (genuinely
multi-ticket-shaped). No ticket was removed.

| Epic | Ticket | Document | Tier | Status (as of 2026-08-19) |
|---|---|---|---|---|
| A — Dead Infra Removal | `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` | `docs/plans/dead_infra_removal_epic.md` | standard | **Resolved** |
| B — Engine Liveness & Health | `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC` | `docs/plans/engine_liveness_health_epic.md` | standard | **Resolved** |
| C — Doc Drift Reconciliation | *(none — amended into `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` directly)* | — | — | — |
| D — Redis Stream Resilience | `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` | `docs/plans/redis_stream_resilience_epic.md` | standard | **Resolved** |
| E — Epic-Staleness Status-Aware | `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` | `docs/plans/epic_staleness_status_aware_epic.md` | hotfix | **Resolved** |
| F — HTTP Admission Control | `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` | `docs/plans/http_admission_control_epic.md` | standard | open (deployment confirmed trusted-network-only 2026-08-19; CORS item extracted) |
| G — Architecture Boundary Hardening | `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` | `docs/plans/architecture_boundary_hardening_epic.md` | standard | **Resolved** |
| H — Error-Handling Hygiene | `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC` | `docs/plans/error_handling_hygiene_epic.md` | standard | **Resolved** |
| I — Determinism Verification Gap | `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC` | `docs/plans/determinism_verification_gap_epic.md` | standard | **Resolved** |
| J — Codebase Navigability Hygiene | `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` | `docs/plans/codebase_navigability_hygiene_epic.md` | epic | open (all 4 items resolved/extracted; awaits 2 sibling tickets reaching done) |
| K — Codebase Health Observatory Tooling | `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` | `docs/plans/codebase_health_observatory_tooling_epic.md` | epic | open (unblocked — prerequisite Epic G done; 2 of 4 items extracted) |

**(2026-08-19)** Three new tickets extend this tree, plus one item resolved without a ticket:
- `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` — Epic J's item 3 (domains test-dir placement),
  extracted once concretely verified (13 of 19 `src/domains/` subpackages correctly nested under
  `tests/unit/domains/`, 6 flat: `campaigns`, `chronicle`, `culture`, `faction`, `feature_packs`,
  `optimization`). Sourced from this session's own test-base structure review, not the D23/D24
  audits.
- `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT` — Epic J's item 1 (`src/lab/workflows.py`
  split), extracted once concretely investigated via AST structural parsing (8 milestone-numbered
  pipeline classes + 1 shared helper, 10 facade-preservable import call sites).
- Epic J's item 2 (`src/observability/mining/` naming overlap) resolved directly within J itself
  — AST-level investigation found 4 distinct, non-overlapping pipeline-stage classes, not
  duplicative. No ticket needed.
- `TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK` — a new finding: `.github/workflows/test.yml`
  enumerates test directories by explicit path with no automated completeness guard, the same
  class of gap `TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS` fixed once (16 dirs, 439
  tests) without adding lasting protection against recurrence — live re-check found
  `tests/regression/test_behavioral_5k.py` still uncovered by any explicit path today, saved only
  by marker-luck.

**(2026-08-18)** The 8 downgraded (standard/hotfix) tickets moved from their own
`tickets/todos/<name>/` folder to flat `tickets/todos/TCK-*.md` files — standard/hotfix tier
tickets in this project don't carry a per-ticket subfolder. J and K, still epic tier, keep their
`tickets/todos/<name>/` folders. None of the ten live in `tickets/inprogress/`.

## Important connection to existing work

**Epic C below is not new work — it extends an epic already in flight.**
`TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC` (created earlier the same session, before these
audits ran) already tracks `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` and
`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`, which cover the exact `architecture.md` vs. `kernel.md`
6-phase/7-phase contradiction both audits independently re-discovered. These audits add two
pieces of evidence those tickets don't have yet:
- `docs/guides/simulation.md` cites `src/engine/authoritative_pipeline.py` — a file that does
  not exist.
- Root `CLAUDE.md` itself states a third number: "32-phase refinement sequence," for the same
  subsystem.

Both should be folded into `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`'s scope when that ticket is
implemented, not re-ticketed here. `docs/audits/D23_architecture_resilience.md` §B and
`docs/audits/D24_codebase_health_observatory.md` §G carry the full evidence trail.

---

## Epic breakdown

Each row cites its source audit section(s) so the eventual `create-tickets` proposal doc can
pull evidence directly rather than re-deriving it.

### Epic A — Dead & Declared-but-Unused Infrastructure Removal
**Priority: P0** (the one finding that can take down a real subsystem for an unrelated reason)
**Status: Resolved** by `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` — RabbitMQ/Kafka were removed
entirely (deps, services, env vars, `depends_on` gates) rather than scoped to a real use case;
`src_legacy/`/`tests_legacy/` were deleted (with the 3 load-bearing oracle `results.json` files
relocated first). See `docs/plans/dead_infra_removal_epic.md`'s `## Status` for detail.

- Un-couple `ai_worker`'s startup from RabbitMQ's healthcheck (`docker-compose.yml:70-71`) —
  pure risk-reduction, independent of the broader keep-or-remove decision.
- Decide the fate of RabbitMQ/Kafka: commit to a real use case and scope it, or remove the
  `pika`/`confluent-kafka` deps, the `rabbitmq`/`kafka`/`zookeeper` services, and associated env
  vars entirely. Zero application code imports either today (repo-wide grep confirmed).
- Delete `src_legacy/` + `tests_legacy/` (601 files, pure stale `.pyc`, zero surviving `.py`
  source) — confirm git-ignored/safe-to-remove and no tooling still references them first.

*Evidence: D23 §B, §E, §I (R1); D24 §B, §C, §I.*

### Epic B — Engine Liveness & Real Health Signal
**Priority: P0**
**Status: Resolved** by `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC` — `/health` now reflects real
`V2EngineManager` background-thread liveness and last-tick staleness (pause-aware,
`ok`/`degraded`/`unhealthy`, HTTP 503 on `unhealthy`), and `SimulationWatchdog`'s critical
escalation now also routes a `WatchdogTrip` `AlertEvent` through `AlertsManager`/`AlertRouter`/
`WebhookAlertSink` (webhook sink default-disabled via new `docker-compose.yml` env vars until an
operator configures them). `docs/architecture/simulation_watchdog.md`'s status/path/responsibility
claims are corrected. Both bullets below now describe pre-fix history. See
`docs/plans/engine_liveness_health_epic.md`'s `## Status` for detail.

- `/health` (`src/api/server.py:126-128`) is a hardcoded `{"status": "ok"}` with no relationship
  to whether `V2EngineManager`'s background thread is alive or ticking. Make it check
  engine-thread liveness + last-tick recency.
- `docs/architecture/simulation_watchdog.md` is marked `Status: Proposed` and describes an
  implementation path (`src/utils/watchdog.py`) that doesn't match the real, running artifact
  (`src/observability/watchdog.py`, log-only escalation, no external alert dispatch). Fix the
  doc's status/path claims, and wire at least one real external alert channel or explicitly
  document the watchdog as log-only until built.

*Evidence: D23 §D (R2), §K.*

### Epic C — Documentation Drift Reconciliation *(extends `AUDIT-ENGINE-DOCS-DRIFT`, not a new epic)*
**Priority: P1**

- Fold the `CLAUDE.md` "32-phase" claim and `docs/guides/simulation.md`'s nonexistent-file
  citation into `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`'s scope.
- Fix the watchdog doc's status/path mismatch (shared with Epic B — same doc, coordinate rather
  than duplicate).
- Add the doc-path-existence CI check: a small script extracting path-shaped strings from
  `docs/**/*.md` and verifying they resolve via `os.path.exists()`, wired into
  `.github/workflows/deploy-docs.yml`. Flagged by D24 as the single highest-value net-new piece
  of tooling in either audit — would have caught both known drift clusters automatically. This
  is genuinely new scope, not covered by the existing kernel-concurrency epic.

*Evidence: D23 §B (R4); D24 §G, §J (doc-path-existence check), §M Phase 1.*

### Epic D — Redis Stream Consumer Resilience
**Priority: P1**
**Status: Resolved** by `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` — handler exceptions now
retry via Redis's own `XPENDING`/`XCLAIM` PEL-reclaim mechanism up to `MAX_DELIVERY_ATTEMPTS = 3`
before routing to a derived `{stream_name}:dlq` DLQ stream; malformed-payload ack+drop is
unchanged; a process-death-before-ack orphaned PEL entry is now reclaimed and redelivered rather
than lost; `connect()` backs off with jitter (base 0.2s, doubling, capped 30s, ±20% jitter),
resetting on success. Parity ledger entries `INFRA-359`/`INFRA-360`/`INFRA-361` and a new §7 in
`observability_hot_path_safety_contract.md` document the new behavior. See
`docs/plans/redis_stream_resilience_epic.md`'s `## Status` for detail.

- `src/observability/stream/consumer.py:79-102` ACKs malformed payloads and transient handler
  failures identically — no DLQ, no retry budget. Separate the two: malformed → ack+drop (already
  correct); transient failure → bounded retry + literal DLQ stream.
- No `XCLAIM`/`XPENDING` logic exists — a message that succeeds in the handler but whose process
  dies before `xack()` sits orphaned in the consumer group's PEL forever. Add PEL reclaim.
- The ~100ms reconnect loop on sustained Redis outage has no backoff or jitter. Add both.
- Blast radius is bounded (Tier 3, observability/anomaly-detection only, downstream of the
  authoritative gameplay pipeline) — real and silent, not catastrophic.

*Evidence: D23 §D (R3), §G, §K.*

### Epic E — Agent-Tooling Fix: Epic-Staleness Status Awareness
**Priority: P1** (small, precisely scoped, high-value)
**Status: Resolved** by `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` —
`tools/agent-monitoring/epic_staleness_check.py` now reads each candidate epic's body `## Status`
field and routes `BLOCKED` candidates into a new, separate "Informational: BLOCKED epics (not
stale — deliberately parked)" report section that the hook's fire-trigger (`find_stale_epics`)
never returns from; `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` no longer surfaces as stale. See
`docs/plans/epic_staleness_status_aware_epic.md`'s `## Status` for detail.

- `make agent-monitoring-epic-staleness` measures file-mtime idleness only — it has flagged
  `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` as stale throughout this entire session despite
  that ticket's frontmatter literally stating `phase: blocked` and its body carrying a dated,
  explicit deferral rationale. Teach the hook to check ticket `## Status` (specifically
  `BLOCKED`) before firing.
- This is a live false positive, not a hypothetical — it has fired in this session's own tool
  output multiple times while this exact roadmap was being written.

*Evidence: D23 §F; D24 §A, §H (full case study).*

### Epic F — HTTP-Layer Admission Control & Auth
**Priority: P2, gate explicitly on deployment plans**
**(2026-08-19)** Deployment-plan decision confirmed by the requester: this API surface stays on a
trusted network, no public/untrusted exposure planned. Auth and admission control (the two bullets
below) stay explicitly deferred, not investigated further, until that changes.

- No rate limiting, no authentication, no per-client admission control on any REST endpoint
  (`src/api/server.py` registers only `CORSMiddleware` + `GZipMiddleware`).
- **(2026-08-19) Extracted to `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`.**
  `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` is a spec-invalid combination —
  fix regardless of exposure plans, since it signals unreviewed middleware config even though
  browsers reject the actual credentialed-wildcard case today.
- Extend the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary
  (`docs/architecture/observability_hot_path_safety_contract.md`) to the HTTP layer instead of
  inventing a new scheme — full proposed mode design already in D23 §L.

*Evidence: D23 §E, §G, §L (R6).*

### Epic G — Architecture Boundary Enforcement Hardening
**Priority: P2**
**Status: Resolved** by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (2026-08-19) — both
weak substring-grep tests were rewritten to AST inspection, reusing the `if TYPE_CHECKING:`
line-range-collection technique `test_api_read_model_guard.py` already establishes. The two
missing boundaries (`domains ↛ observability`, `systems ↛ engine`) were added, resolved via a
pinned-exception model: 2 real `domains → observability` sites and 13 real `systems → engine`
sites were found currently shipping and are frozen as grandfathered exceptions rather than
eliminated — not a claim that either boundary is now cleanly, fully honored. No `src/domains/`
or `src/systems/` production file was touched. The first two bullets below now describe pre-fix
history; the compose-file linter bullet remains open, unaddressed by this epic. See
`docs/plans/architecture_boundary_hardening_epic.md`'s `## Status` and
`docs/audits/D14_coupling_depth.md`'s Coupling Inventory for detail.

- `tests/architecture/test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py`
  are plain substring-grep checks (defeatable via `importlib`/aliasing/indirect import) — upgrade
  both to the AST-visitor pattern `test_api_read_model_guard.py` and
  `test_phase_domain_permissions.py` already establish in this repo.
- No boundary test exists for `domains ↛ observability` internals or `systems ↛ engine`
  internals — add both using the same AST pattern (enforcement gap, not a confirmed violation;
  whether such imports currently exist wasn't checked in either audit).
- Lower priority, deferred: a Tier-3→Tier-0 `docker-compose.yml` startup-dependency linter
  (motivated by Epic A's RabbitMQ finding) — a compose-file concern, not a Python import, needs
  a different mechanism than an architecture test.

*Evidence: D24 §E, §K, §M Phase 2.*

### Epic H — Error-Handling Hygiene
**Priority: P2, explicitly targeted, not a blanket sweep**
**Status: Resolved** by `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC` — `WebhookAlertSink` now
computes a real capped-exponential-with-jitter backoff (`_compute_backoff_delay`, mirroring
`RedisStreamConsumer`'s Epic D precedent) in place of the linear sleep, and gates dispatch behind
a new 3-state (closed/open/half-open) circuit breaker that opens after
`CIRCUIT_BREAKER_FAILURE_THRESHOLD` consecutive failed full-dispatch cycles and half-open-probes
after a cooldown; `send()`'s external signature and fire-and-forget semantics are unchanged. A
targeted broad-except review of six highest-consequence areas (authoritative apply path,
content-registry adapters, kernel tick loop, replay persistence, worker execution,
tactical/reward fallbacks) found no site needing a fix — every reviewed site already re-raises
typed, converts to a typed result, or is an explicitly documented non-authoritative fallback. See
`docs/plans/error_handling_hygiene_epic.md`'s `## Status` for detail.

- `WebhookAlertSink` (`src/observability/alerts/sinks.py:39-92`) — the only real retry/backoff
  implementation in the codebase — is linear (`time.sleep(0.5 * attempt)`) despite an in-code
  comment claiming "exponential backoff." No jitter, no circuit breaker. Fix the comment or
  implement real exponential backoff+jitter; add a simple circuit breaker.
- 481 broad `except Exception`/bare `except` sites coexist with a 40+-class exception taxonomy
  that's largely unused by callers. Both audits explicitly caution against a blanket sweep — this
  is a targeted review of the highest-consequence sites (state mutation, persistence, replay)
  only.

*Evidence: D23 §D (R7, R8), §J; D24 §K (soft heuristic: track the trend, don't gate on it).*

### Epic I — Determinism Verification Coverage Gap
**Priority: P3 — only worth doing if off-path mutation bugs are a live concern**
**Status: Resolved** by `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC` — via the "at minimum"
branch below: `DEGRADED`/`SURVIVAL` run outputs are now explicitly labeled reduced-verification.
A new cumulative `RuntimeStatus.max_mode_reached` tracks the worst `RuntimeMode` reached during a
run; `Kernel.shutdown()` derives `verification_level` (`"FULL"`/`"REDUCED"`) from it and surfaces
the value on `ShutdownResult`, `RunManifest` (`run_manifest.json`), and `run_report.json`/`.md`.
The cheap always-on partial/sampled fingerprint alternative was not pursued — the labeling branch
was judged sufficient. The Tier-2 `audit_mode` fingerprint gate and the DEGRADED/SURVIVAL
canonical-hash gate remain deliberately conditional, unchanged by this epic. See
`docs/plans/determinism_verification_gap_epic.md`'s `## Status` and `docs/engine/known_limitations.md`
§2.4 for detail.

- The Tier-2 SHA-256 fingerprint check that would catch a subtle off-path field mutation during
  a read-only phase is gated behind `audit_mode=True` — invisible in a default production run.
- Canonical hash comparison (the strongest determinism proof) is skipped in DEGRADED mode and
  absent in SURVIVAL mode — unavailable exactly when the system is under the load most likely to
  produce a subtle bug.
- Consider a cheap always-on partial/sampled fingerprint instead of all-or-nothing `audit_mode`
  gating; at minimum, flag DEGRADED/SURVIVAL run outputs as "reduced verification."

*Evidence: D23 §C, §J (R5).*

### Epic J — Codebase Navigability & Test Hygiene
**Priority: P3**

- **(2026-08-19) Extracted to `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`.** Split
  `src/lab/workflows.py` (2,694 LoC, 9 `*Workflow` classes) into one file per workflow —
  AST-verified: 8 milestone-numbered pipeline classes + 1 shared helper, mechanical, low-risk.
- **(2026-08-19) Resolved directly, not duplicative — no ticket needed.**
  `src/observability/mining/`'s naming overlap (`MiningExperimentController`,
  `MiningReviewWorkflow`/`MiningQualityGate`, `AIAgentInvestigationRunner`) — AST-level structural
  investigation (signatures + docstrings) found 4 distinct, non-overlapping pipeline-stage
  responsibilities (execute → AI-investigate → human-review → CI-gate).
- **(2026-08-19) Extracted to `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`.** Standardize
  `tests/unit/domains/` vs. flat domains-subpackage test-dir placement — verified exact split: 13
  of 19 `src/domains/` subpackages nested correctly, 6 (`campaigns`, `chronicle`, `culture`,
  `faction`, `feature_packs`, `optimization`) flat.
- **(2026-08-19) Resolved directly, genuinely covered — not a gap.** `pipeline.py`/`tactical.py`
  test coverage — both are simultaneously high-churn (top-5) and high-centrality (god-node-
  defining) with no exactly-named dedicated unit test file, but `grep` for actual call sites found
  `AuthoritativeApplyPipeline.refine()` called by 71 test files and `TacticalDecisionSystem`'s
  public methods called by 15 more — exercised through this repo's existing distributed
  per-domain pattern, not untested.
- **(2026-08-19) Resolved directly, explained not neglected.** `tests/helpers/` under-utilization
  (7 of 1,140 sampled test files import it directly) — `grep` confirmed zero `conftest.py` files
  import it (ruling out invisible reuse); 359 test files use `V2EntityBuilder` (the production
  builder) directly instead, which already covers the same need.

All 4 original items now resolved or extracted; this epic has no remaining unscoped work of its
own — see `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`'s Acceptance Criteria for what it's
still waiting on.

*Evidence: D24 §D, §F, §I.*

### Epic K — Codebase Health Observatory Tooling
**Priority: P3, deliberately built last**
**(2026-08-19)** Its own prerequisite (Epic G) is confirmed done — this epic is now genuinely
unblocked, not just theoretically scoped.

- **(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`.**
  `make codebase-health-baseline`: permanent LoC/churn snapshot target, excluding known
  append-only process files (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
  `docs/REGISTRY.yaml`) by name/pattern — without this exclusion, every report is dominated by
  expected bookkeeping churn, not real instability signal.
- **(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`.**
  `code-health impact <path>` command: composable almost entirely from data that already exists
  (`graphify-out/` edge data, `tests/architecture/` boundary tests, `docs/REGISTRY.yaml`'s
  `related_code_areas` field) — full worked design in D24 §L. Extracted once each data source was
  individually verified (found `graphify` needs a custom traversal, no ready CLI verb; found
  `related_code_areas` only 53.3% filled with mixed path/symbol shapes).
- Historical metric snapshots (append-only file, same pattern as `agent-monitoring/runs.jsonl`)
  + a multi-dimension scorecard (trend arrows, not a single score).
- PR/AI change-impact report generator, built on top of the impact-model command above.

*Evidence: D24 §J, §L, §M Phase 3-4.*

---

## Sequencing notes

- **Epic A and B are the only two audits both independently rank P0** — real outage risk (A) and
  a false-positive liveness signal that could mask a genuine engine crash (B). Neither depends on
  the other or on anything else in this roadmap.
- **Epic C should not be started as fresh scoping** — it's an amendment to an already-created
  ticket (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`). The doc-path-existence CI check inside it is
  the one piece of genuinely new scope.
- **Epic E is small enough to knock out opportunistically** — one hook, one conditional check,
  motivated by a bug this exact session watched fire repeatedly.
- **Epic F is explicitly gated on deployment plans** by both audits — **confirmed 2026-08-19**:
  this system stays on a trusted network, so auth/rate work stays deferred, not front-loaded.
- **Epics I, J, K are all P3 and explicitly conditional** in their source audits ("only worth
  doing if...", "targeted read required before...", "deliberately built last") — none should be
  picked before A/B/D/E without a specific reason.

---

## References

- `docs/audits/D23_architecture_resilience.md` — full audit, failure-mode/resilience focus
- `docs/audits/D24_codebase_health_observatory.md` — full audit, codebase-health/navigability focus
- `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` — tracking ticket for this roadmap
- `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC`, `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` — the
  existing epic/ticket Epic C extends
