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

**Update (2026-08-17):** every epic below except C now has its own epic-tier tracking ticket and
dedicated plan document — created 2026-08-17, still scope-only (no `create-tickets` run against
any of them yet):

| Epic | Ticket | Document |
|---|---|---|
| A — Dead Infra Removal | `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` | `docs/plans/dead_infra_removal_epic.md` |
| B — Engine Liveness & Health | `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC` | `docs/plans/engine_liveness_health_epic.md` |
| C — Doc Drift Reconciliation | *(none — amended into `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` directly)* | — |
| D — Redis Stream Resilience | `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` | `docs/plans/redis_stream_resilience_epic.md` |
| E — Epic-Staleness Status-Aware | `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` | `docs/plans/epic_staleness_status_aware_epic.md` |
| F — HTTP Admission Control | `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` | `docs/plans/http_admission_control_epic.md` |
| G — Architecture Boundary Hardening | `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` | `docs/plans/architecture_boundary_hardening_epic.md` |
| H — Error-Handling Hygiene | `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC` | `docs/plans/error_handling_hygiene_epic.md` |
| I — Determinism Verification Gap | `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC` | `docs/plans/determinism_verification_gap_epic.md` |
| J — Codebase Navigability Hygiene | `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` | `docs/plans/codebase_navigability_hygiene_epic.md` |
| K — Codebase Health Observatory Tooling | `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` | `docs/plans/codebase_health_observatory_tooling_epic.md` |

All ten tickets live in their own `tickets/todos/<name>/` folder, not `tickets/inprogress/`.

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

- No rate limiting, no authentication, no per-client admission control on any REST endpoint
  (`src/api/server.py` registers only `CORSMiddleware` + `GZipMiddleware`).
- `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` is a spec-invalid combination —
  fix regardless of exposure plans, since it signals unreviewed middleware config even though
  browsers reject the actual credentialed-wildcard case today.
- Extend the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary
  (`docs/architecture/observability_hot_path_safety_contract.md`) to the HTTP layer instead of
  inventing a new scheme — full proposed mode design already in D23 §L.

*Evidence: D23 §E, §G, §L (R6).*

### Epic G — Architecture Boundary Enforcement Hardening
**Priority: P2**

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

- Split `src/lab/workflows.py` (2,694 LoC, 9 `*Workflow` classes) into one file per workflow —
  mechanical, low-risk, meaningfully improves navigability of the single largest `src/` file.
- Investigate `src/observability/mining/`'s naming overlap (`MiningExperimentController`,
  `MiningReviewWorkflow`/`MiningQualityGate`, `AIAgentInvestigationRunner`) — targeted read
  required before any consolidation; flagged Suspicious, not confirmed duplicative.
- Standardize `tests/unit/domains/` vs. flat domains-subpackage test-dir placement — a
  discoverability fix, not a coverage gap (coverage exists for all 19 `domains` subpackages
  today, just inconsistently located).
- Verify `pipeline.py`/`tactical.py` test coverage directly — both are simultaneously high-churn
  (top-5) and high-centrality (god-node-defining) with no exactly-named dedicated unit test file;
  plausibly covered indirectly via integration/kernel determinism suites, not confirmed either
  way.
- Resolve `tests/helpers/` under-utilization (7 of 1,140 sampled test files import it directly) —
  determine whether reuse happens invisibly via `conftest.py` fixtures instead.

*Evidence: D24 §D, §F, §I.*

### Epic K — Codebase Health Observatory Tooling
**Priority: P3, deliberately built last**

- `make codebase-health-baseline`: permanent LoC/churn snapshot target, excluding known
  append-only process files (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
  `docs/REGISTRY.yaml`) by name/pattern — without this exclusion, every report is dominated by
  expected bookkeeping churn, not real instability signal.
- `code-health impact <path>` command: composable almost entirely from data that already exists
  (`graphify-out/` edge data, `tests/architecture/` boundary tests, `docs/REGISTRY.yaml`'s
  `related_code_areas` field) — full worked design in D24 §L.
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
- **Epic F is explicitly gated on deployment plans** by both audits — do not front-load auth/rate
  work if this system stays on a trusted network.
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
