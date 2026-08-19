---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
artifact_type: plan
tags: [architecture, engine]
---

# Implementation Plan — TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

## Summary

This plan fully removes RabbitMQ/Kafka as declared-but-unused infrastructure (`pika`/
`confluent-kafka` from `pyproject.toml`; `rabbitmq`/`kafka`/`zookeeper` services, their
`depends_on`/`environment`/`volumes` references, from `docker-compose.yml`) and deletes the 598
dead `.pyc` files in `src_legacy/`/`tests_legacy/` after relocating the 3 git-tracked,
load-bearing oracle `results.json` files to a non-"legacy" home. It also reconciles the three
doc/ledger surfaces that this removal decision directly invalidates: 12 P0 entries in
`docs/parity_ledger/infrastructure.yaml`, the RabbitMQ/Kafka-specific lines in
`docs/compliance/checklist.md` that cite non-existent test files, and one stale ADR
(`docs/architecture/performance_optimization.md`) that proposes a RabbitMQ-based design already
superseded by history. The removal (not "scope a real use case") is the judgment call this plan
makes for AC2 — justification is in Anti-Drift Notes. No Mechanics Bible chapter or engine
contract requires RabbitMQ/Kafka; `docs/engine/contracts/infrastructure_compat_contract.md` §3/§4
already documents the target end-state ("brokers not included in the current baseline") that this
plan makes literally true.

## Steps

### Step 1 — Remove `pika`/`confluent-kafka` from `pyproject.toml`

**Files:** `pyproject.toml`

**Change:** Delete the two lines `"pika>=1.3.2",` (`pyproject.toml:18`) and
`"confluent-kafka>=2.6.0",` (`pyproject.toml:19`) from `[project.dependencies]` (verified by
reading `pyproject.toml:10-24` directly — these are core, non-optional dependencies, not under
`[project.optional-dependencies]`). Leave `"redis>=5.0.0"` (`pyproject.toml:17`) untouched — Redis
is the real, live event pipeline (`RedisStreamConsumer`) and out of scope for this ticket. Add a
new test asserting neither package remains declared (see Step 2 for the shared test file).

**Do NOT touch:** `[project.optional-dependencies]` blocks (`dev`, `knowledge`, `search-mcp`,
`pyproject.toml:26-44`) — no broker packages live there. `redis>=5.0.0` on line 17.

**Verify:** `test_pyproject_has_no_broker_client_dependencies` (new, Step 2's test file) +
`pytest --collect-only -q` (whole-repo collection, confirms no stray import of the removed
packages surfaces as an `ImportError` — per test_plan.md's "Full scoped collection check").

---

### Step 2 — Remove `rabbitmq`/`kafka`/`zookeeper` from `docker-compose.yml`, including `backend`'s soft coupling

**Files:** `docker-compose.yml`; new `tests/architecture/test_docker_compose_dependency_hygiene.py`

**Change:** Verified by reading `docker-compose.yml` in full this session (current line numbers,
re-confirmed against investigation's citations):
- Delete the `rabbitmq` service block (`docker-compose.yml:42-55`).
- Delete the `zookeeper` service block (`docker-compose.yml:120-126`) and the `kafka` service
  block (`docker-compose.yml:128-150`).
- In `backend` (`docker-compose.yml:3-26`): remove `RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/`
  (`docker-compose.yml:12`) and `KAFKA_URL=kafka:29092` (`docker-compose.yml:13`) from
  `environment:`; remove `rabbitmq` and `kafka` from `depends_on:` (`docker-compose.yml:17-20`),
  leaving only `- redis`. This is the "softer, non-healthcheck coupling" the investigation
  flagged — it is a plain list `depends_on`, not a `condition:` gate, but a `depends_on` reference
  to a deleted service is itself invalid compose config (`docker compose config` would error), so
  it must be removed in the same step as the service deletion, not left for a later pass.
- In `ai_worker` (`docker-compose.yml:57-76`): remove the same two `environment:` lines
  (`docker-compose.yml:65-66`) and remove the `rabbitmq: condition: service_healthy` entry from
  `depends_on:` (`docker-compose.yml:67-71`), leaving only `redis: condition: service_started`.
  This is the ticket's AC1 (the healthcheck-gate decoupling) — satisfied here as a direct
  consequence of full removal, not as a separate half-measure.
- Delete `rabbitmq_data`, `zookeeper_data`, `kafka_data` from the top-level `volumes:` block
  (`docker-compose.yml:191-197`), leaving `prometheus_data`, `grafana_data`, `redis_data`.
- Add new file `tests/architecture/test_docker_compose_dependency_hygiene.py` (confirmed via
  `grep -rl docker-compose tests/` that no existing test touches this file structurally) with two
  tests, both parsing `docker-compose.yml` with `yaml.safe_load`:
  - `test_ai_worker_does_not_depend_on_rabbitmq_healthcheck` — asserts
    `services.ai_worker.depends_on` has no `rabbitmq` key at all (post-removal state satisfies
    "does not reference rabbitmq" per test_plan.md's AC1 spec).
  - `test_docker_compose_has_no_rabbitmq_kafka_zookeeper_services` — asserts `rabbitmq`, `kafka`,
    `zookeeper` are absent from top-level `services:` **and** `volumes:`; asserts no service's
    `environment:` (checked as both list- and dict-style YAML, since `zookeeper`/`kafka` use dict
    style while `backend`/`ai_worker` use list style — confirmed by reading both forms in the file)
    contains a value matching `RABBITMQ_URL` or `KAFKA_URL`. Also assert `backend.depends_on`
    contains neither `rabbitmq` nor `kafka` (the soft-coupling regression guard the investigation
    called out).
  - Also add `test_pyproject_has_no_broker_client_dependencies` here (co-located per
    test_plan.md's guidance) — parses `pyproject.toml` with `tomllib`, asserts no dependency string
    in `[project.dependencies]` starts with `pika` or `confluent-kafka`.

**Do NOT touch:** `redis` service (`docker-compose.yml:28-40`), `frontend`, `prometheus`,
`grafana`, `loki`, `promtail`, `watchdog` service blocks — investigation confirmed none of these
have any `depends_on` reference to `rabbitmq`/`kafka`/`zookeeper` (they depend only on `backend`/
`prometheus`/`loki`), so zero blast radius. Do not touch `REDIS_PORT`/`REDIS_URL` anywhere.

**Verify:** `pytest tests/architecture/test_docker_compose_dependency_hygiene.py -v` (new); defensive
re-run of `pytest tests/architecture/ -v` (existing phase18/phase19 import-boundary guards, to
confirm the Python-level Redis-only path on `ai_worker`'s entrypoint is undisturbed by this
non-Python config change).

---

### Step 3 — Relocate the 3 oracle `results.json` files and repoint `ORACLE_ROOT`

**Files:** `tests_legacy/parity/{movement,interaction,town}_oracle/results.json` →
`tests/parity/oracles/{movement,interaction,town}_oracle/results.json`;
`tests/integrity/test_parity_guards.py`

**Change:** `git mv` (to preserve the git-tracked history invoked by
`TCK-20260427-LEGACY-RESTORATION`'s "preserved for parity verification" intent) each of the 3
files from `tests_legacy/parity/{name}_oracle/results.json` to
`tests/parity/oracles/{name}_oracle/results.json`. Update
`tests/integrity/test_parity_guards.py:5` — change `ORACLE_ROOT = "tests_legacy/parity"` to
`ORACLE_ROOT = "tests/parity/oracles"` (verified by reading the full file this session — this is
the only place `ORACLE_ROOT` is defined; `REQUIRED_ORACLES` at lines 6-10 stays unchanged, it only
names the oracle-directory keys, not paths). This step must land **before** Step 4 — Step 4
deletes everything remaining under `tests_legacy/`, and these 3 files are the one load-bearing
exception in either dead tree.

**Do NOT touch:** `test_oracle_schema_integrity()` (`test_parity_guards.py:21-37`) or
`test_critical_parity_scenarios_presence()` (`test_parity_guards.py:39-67`) logic — only the
`ORACLE_ROOT` constant changes; both functions' internal `if not os.path.exists(path): continue`
guards (lines 27-28, and the three per-oracle `if os.path.exists(...)` checks in the third
function) stay as-is. Per test_plan.md's Anti-Drift Test Guards: do not add a
skip-if-missing guard anywhere in this file as a way to paper over a wrong path — a wrong
`ORACLE_ROOT` must surface as a hard failure in `test_oracle_artifact_existence`, which has no such
guard today and must not gain one.

**Verify:** `pytest tests/integrity/test_parity_guards.py -v` — all three tests
(`test_oracle_artifact_existence`, `test_oracle_schema_integrity`,
`test_critical_parity_scenarios_presence`) must pass against the new path. Per test_plan.md's
warning, do not treat the latter two passing alone as proof of a correct path — confirm
`test_oracle_artifact_existence` (the one with the unconditional `assert`) passes too.

---

### Step 4 — Delete dead bytecode; drop `tests_legacy` from `norecursedirs`

**Files:** `src_legacy/` (entire directory, 216 `.pyc` files, 0 `.py` files); `tests_legacy/`
(entire directory, 382 `.pyc` files remaining after Step 3's relocation); `pyproject.toml`

**Change:** `rm -rf src_legacy/ tests_legacy/` — both trees are 100% dead bytecode after Step 3
moves out the only load-bearing content (confirmed this session: `git ls-files src_legacy/` → 0
tracked files; `git ls-files tests_legacy/` → exactly the 3 oracle JSONs, already relocated by
Step 3, so nothing else is git-tracked in either tree). Remove `"tests_legacy",` from
`[tool.pytest.ini_options].norecursedirs` (`pyproject.toml:61`, verified by reading
`pyproject.toml:55-66` this session) — it becomes a reference to a nonexistent directory once the
tree is deleted; harmless to leave but cleaner to drop in the same change (investigation's Docs
Requiring Update flagged this explicitly). Add a new test (co-located in
`tests/architecture/test_docker_compose_dependency_hygiene.py` from Step 2, or a new
`test_no_pyc_bytecode_remains_in_legacy_trees` in `tests/integrity/test_parity_guards.py` — prefer
the latter, since it concerns the same tree as the oracle tests) asserting `src_legacy/` and
`tests_legacy/` do not exist as directories at the repo root.

**Do NOT touch:** `scripts/turbo_run.py`'s `from src_legacy.utils.logging import
StructuredJsonFormatter, ContextFilter` (`scripts/turbo_run.py:9`) — confirmed this session
(re-running `python3 -c "import src_legacy.utils.logging"`) that this import already raises
`ModuleNotFoundError` today, independent of this ticket (that module was deleted in commit
`677abbfb` and never had surviving bytecode). Deleting the rest of `src_legacy/` does not newly
break this file. Do not "fix" it as a drive-by; no ticket authorizes touching `turbo_run.py`, and
test_plan.md explicitly forbids adding any test that would require it to become importable.
Do **not** touch `./build/lib/src_legacy/` — this is a separate, `.gitignore`-excluded (
`.gitignore:11`, confirmed this session), untracked build artifact directory (from a stale
`python -m build`/`pip install` run) that happens to contain a *pre-deletion* snapshot of the old
`src_legacy` tree, including real `pika`/`rabbitmq` imports in
`build/lib/src_legacy/engine/worker_pool.py`. It is not part of the repo's tracked source, not
listed in the ticket's Related Code Areas, and outside this ticket's scope entirely — confirmed
via `git status --porcelain build/` returning nothing and `git ls-files build/` returning nothing.

**Verify:** New test above; `pytest tests/integrity/ -v` (full module, per test_plan.md's
regression surface); confirm `find src_legacy tests_legacy -maxdepth 0` reports "No such file or
directory" after deletion.

---

### Step 5 — Correct the RabbitMQ/Kafka-specific lines in `docs/compliance/checklist.md`

**Files:** `docs/compliance/checklist.md`

**Change:** Verified this session by grepping and reading the exact lines: `checklist.md:1397-1398`
cite `tests/api/test_broker_isolation.py` and `tests/integration/infra/test_brokerless_import.py`
as evidence for the "B. Optional-broker disabled-mode compatibility" section's RabbitMQ block
(INFRA-007–010, `checklist.md:1402-1405`) and Kafka block (INFRA-011–014, `checklist.md:1409-1412`)
— **confirmed neither file exists on disk this session** (`test -f` returns false for both).
Separately, `checklist.md`'s "C. Worker-pool and infrastructure fallback behavior" section header
cites `tests/integration/infrastructure/test_infrastructure_isolation.py` for INFRA-017/INFRA-022
(both in this ticket's 12-entry parity-ledger list) — **also confirmed missing on disk this
session** (a fourth non-existent citation beyond the investigation's original three, found because
it directly backs two of the 12 in-scope P0 entries, not because this step re-audits the checklist
generally). For each of these RabbitMQ/Kafka-specific items — INFRA-007 through INFRA-014,
INFRA-017, INFRA-022, INFRA-041 (`checklist.md:1541`), INFRA-054/INFRA-056 (`checklist.md:1587,
1589`), INFRA-061 through INFRA-064 (`checklist.md:1605-1609`, cites no file directly but sits
under section J's broker-disabled heading), and INFRA-071/INFRA-075 (`checklist.md:2720,2724`,
citing `tests/unit/platform/test_infra_recovery.py`, also confirmed missing) — change the checkbox
from `[x]` to `[ ]` and append `(unverified — cited test file does not exist; see
TCK-20260817-DEAD-INFRA-REMOVAL-EPIC)` after each line, rather than deleting the lines outright
(the checklist's own convention elsewhere never deletes historical items, only marks them). Leave
INFRA-174 (`checklist.md:3215`) alone in this step — its cited file
`tests/unit/kernel/test_worker_fallback.py` **does exist** (confirmed this session), so it is not
part of the fabricated-citation problem; its `v2_evidence`-level mismatch (the test covers
in-process thread-pool fallback under queue saturation, not broker-specific behavior) is addressed
in Step 6 at the parity-ledger layer, not here.

**Do NOT touch:** The "Redis disabled / missing-package behavior" items (INFRA-015/INFRA-016,
`checklist.md:1412-1414`) or "Disabled-mode import isolation" items (SUB-064–066,
`checklist.md:1417-1419`) even though they sit in the same section and share some of the same
missing-file citations — Redis is real and live, out of scope. Do not touch INFRA-018–021
(`checklist.md` section C, immediately adjacent to INFRA-017/022) — these describe generic worker
fallback semantics not specific to RabbitMQ/Kafka disabled-mode, and are not in this ticket's
12-entry parity-ledger list. Do not touch the "Disabled/missing dependency paths" Redis line
(INFRA-063) inside section J. Do not perform a full audit of every other place
`test_infra_recovery.py`/`test_infrastructure_isolation.py` is cited outside the RabbitMQ/Kafka
items named above (e.g. INFRA-072–074/076–077 also cite `test_infra_recovery.py` but describe
Kafka/RabbitMQ-adjacent recovery items **not** in this ticket's 12-entry parity list — leave them
as a separately-flagged, unscoped finding, per investigation's explicit anti-drift hazard: "Do not
extend this ticket into a full audit of checklist.md's other fabricated-looking test citations").

**Verify:** No automated test covers markdown checkbox state; this is a doc-only correction. Manual
review at Verify phase: `grep -c '\[x\].*INFRA-0\(0[7-9]\|1[0-4]\|17\|22\|41\|54\|56\|6[1-4]\|7[15]\)' docs/compliance/checklist.md` should return 0 after this step (i.e., none of the 16 named items remain checked).

---

### Step 6 — Reconcile the 12 P0 parity-ledger entries

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Entries INFRA-010, INFRA-011, INFRA-014, INFRA-017, INFRA-022, INFRA-041, INFRA-054,
INFRA-056, INFRA-064, INFRA-071, INFRA-075 (11 of the 12; verified this session by reading each
entry — most currently have `status: legacy_verified`, all have `test_path: null`,
`proof_type: parity` or `null`, sourced only from `v2_evidence: Implementation proven via
exhaustive checklist audit Phase 1-11`, i.e. the same audit-checklist artifact corrected in Step 5,
not real V2 code): change `status` to `unsupported` and `v2_evidence` to state plainly that V2
`src/` never imported `pika`/`confluent_kafka` (zero-import confirmed by repo-wide grep) and that
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` removed the dependencies entirely, so "broker
disabled-mode behavior" is inapplicable rather than verified — there is no broker client code left
to have a disabled-mode branch. Set `divergence_note` to reference this ticket ID. Leave
`test_path: null` — this schema/status combination (`status: unsupported`, `test_path: null`,
populated `divergence_note`) already has direct precedent in this same ledger family, e.g.
`docs/parity_ledger/combat_movement.yaml`'s COMB-133/COMB-134 entries (verified this session:
`status: unsupported` with `test_path` absent and a `divergence_note` explaining the gap), so this
is not a new pattern being invented for this ticket.

For **INFRA-174** (the 12th entry, `docs/parity_ledger/infrastructure.yaml:1773`): do not set
`status: unsupported`. Correction (architecture-review caught a factual error here — the entry's
own `test_path` field is currently `null` at line 1780, same as the other 11; the "already has a
passing test_path" claim conflated `docs/compliance/checklist.md:3215`'s citation, a *different*
document, with this ledger's own field): the real test does exist
(`tests/unit/kernel/test_worker_fallback.py::test_force_local_override`, i.e. the function
starting at line 65, confirmed to exist this session) — set `test_path` to that value now, in this
step, rather than asserting it is already populated. Also narrow `text`/`v2_evidence` to what that
test actually proves: in-process thread-pool fallback under queue saturation via `WorkerManager`,
not broker-specific brokerless-execution behavior. Keep `status: verified` (or whatever it
currently is — read the entry directly before editing) since the underlying test is real; only
correct the claim's scope so it stops overclaiming broker coverage it was never designed to
provide, and populate the previously-null `test_path` so this P0 entry is actually compliant with
the "P0 entries require a passing test_path" rule.

**Do NOT touch:** Any other entry in `docs/parity_ledger/infrastructure.yaml` (e.g. INFRA-007–009,
INFRA-012-013, INFRA-018–021, INFRA-072–074/076-077 — not in this ticket's 12-entry list) or any
other `docs/parity_ledger/*.yaml` file — investigation confirmed (grep across all 8 ledger files)
no other file's `text` overlaps RabbitMQ/Kafka/legacy-tree removal.

**Verify:** No automated test validates ledger YAML semantics beyond schema shape; validate with
`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` (parses
cleanly) and a manual diff review at Verify confirming exactly 12 entries changed and their new
`status` values match this step's assignments.

---

### Step 7 — Mark the stale RabbitMQ batching ADR superseded

**Files:** `docs/architecture/performance_optimization.md`

**Change:** This doc (`status: active`, `docs/architecture/performance_optimization.md:2`)
proposes "AI Task Batching: Group all ready entities into a single RabbitMQ message"
(`performance_optimization.md:27`) with a "Revisit Trigger" still referencing RabbitMQ throughput
(`performance_optimization.md:43-44`). Investigation flagged this as a possible live
counter-signal to full removal and deferred the judgment call to Plan. **Resolved here as: proceed
with full removal; this ADR is stale, not live intent.** Evidence gathered this session beyond
what investigation had: `tickets/done/TCK-20260322-PERF_OPT.md` (2026-03-22, done) shows this exact
design **was already built**, in `src/engine/worker_pool.py` and
`src/workers/ai_worker_daemon.py` — but those paths resolve today only inside the gitignored,
untracked `build/lib/src_legacy/` snapshot (confirmed this session), meaning the implementation
lived entirely in the pre-`677abbfb` legacy tree and was never carried into V2 `src/`
(`src/engine/executor.py`/`worker_manager.py`, the V2 equivalents, contain zero RabbitMQ code —
confirmed by investigation's zero-import grep). No open ticket references reviving it (checked
`tickets/` for `performance_optimization`/`ai_batch_tasks`/"AI Task Batching" — only this doc and
its origin ticket, both non-actionable: one done, one a doc). Change `## Status` in the doc to
note it is superseded/historical for its RabbitMQ-specific mechanism (do not delete the doc —
it remains a valid historical record of a V1-era optimization), and append a short note under
"Revisit Trigger" stating that `pika`/`confluent-kafka` were removed by
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` and that any future AI-task-batching work must be re-scoped
against the current Redis-based pipeline (`RedisStreamConsumer`), not RabbitMQ.

**Do NOT touch:** The doc's other sections describing non-RabbitMQ-specific optimizations (grid
`bytearray` migration, shallow-copy `Model` changes, scan-radius tuning) — those were separately
implemented in `src/core/grid.py`/`src/core/models.py`/`src/ai/perception.py` per the origin
ticket and are unrelated to this ticket's broker-removal scope. Do not add a new entry to
`docs/guidelines/intentional_divergences.md` for this — per investigation's own framing, this
ticket is infrastructure/repo-hygiene scope with no Mechanics Bible chapter bearing on it directly,
and the divergence log's convention (per its existing 20-row table) is reserved for gameplay/engine
*behavior* divergences from the legacy engine, not infra-dependency-removal bookkeeping.

**Do NOT touch:** `docs/engine/contracts/infrastructure_compat_contract.md` — investigation
explicitly flagged strengthening its §4 wording as "optional... low priority, doesn't block Done."
Skip it in this plan to stay narrow; it can be picked up in any future doc pass without blocking
this ticket's Done state.

**Verify:** No test covers ADR doc prose; manual review at Verify that the doc's `## Status`
section and Revisit Trigger note are updated and internally consistent with the removal.

---

### Step 8 — Full scoped verification pass

**Files:** none (test execution only)

**Change:** Run the full scoped test set from test_plan.md, in order:
1. `pytest tests/integrity/ -v` (Steps 3-4 regression surface)
2. `pytest tests/architecture/test_docker_compose_dependency_hygiene.py -v` (new, Steps 1-2)
3. `pytest tests/architecture/ -v` (defensive full re-run)
4. `pytest tests/simulation_quality/test_feed.py -v` (adjacent-system regression guard — kafka
   feed-mode rejection must be untouched)
5. `pytest --collect-only -q` (whole repo, dependency-removal collection-error sanity check)

**Do NOT touch:** Do not run `pytest tests/` unscoped. Do not add any test that exercises real
RabbitMQ/Kafka connectivity (there is nothing left to connect to).

**Verify:** All five commands above exit 0 with no unexpected failures/errors; any failure here is
a signal to stop and report, not to route around (per CLAUDE.md's gate-bypass prohibition).

## Scope Guards

- Do not touch `redis`/`REDIS_URL`/`redis_data` anywhere in `docker-compose.yml`, or
  `RedisStreamConsumer`/`src/observability/stream/consumer.py` — Redis is the real, live event
  pipeline.
- Do not fix `scripts/turbo_run.py`'s pre-existing `ModuleNotFoundError` on
  `from src_legacy.utils.logging import ...` — already broken today, unrelated to this ticket, no
  ticket authorizes touching this file.
- Do not touch `./build/` (gitignored build artifact, untracked, contains a pre-deletion snapshot
  of the old `src_legacy`/`src` trees including real `pika`/rabbitmq imports) — not part of the
  repo's tracked source, not in the ticket's Related Code Areas.
- Do not perform a full audit of `docs/compliance/checklist.md`'s other fabricated-looking test
  citations (Redis sections, INFRA-072–074/076-077, SUB-items) — only the RabbitMQ/Kafka-specific,
  12-entry-parity-list-overlapping lines named in Step 5.
- Do not touch `docs/parity_ledger/*.yaml` entries outside the 12 named in Step 6.
- Do not touch `docs/engine/contracts/infrastructure_compat_contract.md` — optional, deferred.
- Do not add a new `docs/guidelines/intentional_divergences.md` entry — not a mechanics/behavior
  divergence.
- Do not build a real RabbitMQ/Kafka use case (ticket's own Out of Scope).
- Do not touch `prometheus`/`grafana`/`loki`/`promtail`/`watchdog` service blocks in
  `docker-compose.yml` — zero dependency relationship to the removed services.
- Do not add a skip-if-missing guard to any test in `tests/integrity/test_parity_guards.py`.

## Dependency Map

- Step 1 and Step 2 are independent of each other (different files) but both encode the same
  removal decision; Step 2's test file also covers Step 1's assertion, so land them together.
- Step 3 must complete before Step 4 (oracle relocation before wholesale tree deletion).
- Steps 1-2 (RabbitMQ/Kafka removal) and Steps 3-4 (legacy bytecode deletion) are independent of
  each other — different subsystems, no shared files.
- Step 5 (checklist correction) and Step 6 (ledger reconciliation) both depend on Steps 1-2 having
  landed (they describe the post-removal state as fact).
- Step 7 (ADR doc) depends on Steps 1-2 (references the completed removal).
- Step 8 depends on all of Steps 1-7.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `ai_worker` no longer depends on RabbitMQ's healthcheck | Step 2 | `test_ai_worker_does_not_depend_on_rabbitmq_healthcheck` |
| AC2 — RabbitMQ/Kafka fully removed (deps, services, env vars) | Steps 1, 2, 6, 7 | `test_pyproject_has_no_broker_client_dependencies`, `test_docker_compose_has_no_rabbitmq_kafka_zookeeper_services` |
| AC3 — `src_legacy/`/`tests_legacy/` no dead `.pyc`; oracles relocated; `test_parity_guards.py` passes | Steps 3, 4 | `test_oracle_artifact_existence`, `test_oracle_schema_integrity`, `test_critical_parity_scenarios_presence`, `test_no_pyc_bytecode_remains_in_legacy_trees` |

## Anti-Drift Notes

- **ADR judgment call (resolved, not left open):** `docs/architecture/performance_optimization.md`
  proposes RabbitMQ-based AI-task batching and reads `status: active`, which investigation flagged
  as a possible live counter-signal to full removal. This plan resolves it as **not** blocking:
  the design was already implemented once, in the pre-`677abbfb` legacy tree
  (`tickets/done/TCK-20260322-PERF_OPT.md`), and never carried into V2 `src/` — the only surviving
  trace is inside the gitignored `build/` artifact, not tracked source. Combined with the ticket's
  own Out-of-Scope line ("Building a real RabbitMQ/Kafka use case... is out of scope"), the default
  posture is removal absent a live counter-signal, and none was found. Step 7 corrects the doc's
  status rather than leaving it silently contradicted by the code change.
- **`build/` is a trap for both Implement and Verify:** grepping `src/`/`tests/` alone (as the
  investigation correctly did) will never show it, but a broader `grep -r pika .` from repo root
  will hit `build/lib/src_legacy/engine/worker_pool.py` and could be mistaken for a live import
  site. It is gitignored and untracked — confirm with `git check-ignore -v <path>` before treating
  any hit under `build/` as in-scope.
- **INFRA-174 is not part of the "12 entries need `status: unsupported`" pattern** — it has a real,
  existing, passing `test_path`. Do not blanket-apply Step 6's `unsupported` treatment to it; it
  needs a narrower text/evidence correction only (see Step 6).
- **Checklist correction in Step 5 found a 4th missing file** (`test_infrastructure_isolation.py`,
  cited for INFRA-017/022, both in-scope) beyond the investigation's original three
  (`test_broker_isolation.py`, `test_brokerless_import.py`, `test_infra_recovery.py`). This is
  in-scope because it backs two of the 12 already-in-scope P0 entries, not scope creep — but do not
  use this discovery to justify auditing the rest of the checklist's citations (see Scope Guards).
- **Ordering matters for Step 3→4** — deleting `tests_legacy/` before relocating the oracle JSONs
  would destroy git-tracked, load-bearing files and directly contradict
  `TCK-20260427-LEGACY-RESTORATION`'s explicit user-requested preservation intent.
- **`docker-compose.yml`'s `backend` service has a soft `depends_on` on `rabbitmq`/`kafka` that is
  easy to miss** if a change only targets `ai_worker`'s healthcheck gate (the ticket's most visible
  symptom) — Step 2 removes both in the same change.
- **After this ticket's file changes land:** `tests/` files are added/modified (Steps 2-4) — run
  `graphify update .` per CLAUDE.md's proactive-tool-use rule. `docs/` files are modified (Steps
  5-7) — run `make knowledge-index-update` before Finalize.

## Deviations

- **Step 5's Change section names a broader item set than its own Verify grep comment claims.**
  The Change paragraph's literal item list — "INFRA-007 through INFRA-014" (8 items: 007-014),
  INFRA-017, INFRA-022, INFRA-041, INFRA-054, INFRA-056, "INFRA-061 through INFRA-064" (4 items:
  061-064), INFRA-071, INFRA-075 — totals 19 named IDs. Do NOT touch explicitly carves out
  INFRA-063 (the Redis line inside that 061-064 range) from the checkbox change, leaving 18 items
  actually corrected to `[ ]` + the unverified note. Implement followed the Change section's
  literal per-ID list and the Do Not Touch carve-out for INFRA-063 exactly (checked all of
  007-014, 017, 022, 041, 054, 056, 061, 062, 064, 071, 075 to `[ ]`; left 063 as `[x]`
  untouched, per the explicit Redis-is-out-of-scope guard). The Verify section's own parenthetical
  ("i.e., none of the 16 named items remain checked") undercounts by 2 relative to the Change
  section's literal list, and its "`grep -c ... should return 0`" expectation is factually
  inconsistent with its own Do Not Touch guard for INFRA-063 — the grep pattern's `6[1-4]` clause
  matches INFRA-063 too, so after correctly leaving INFRA-063 untouched the grep returns 1, not 0.
  Implement did not alter INFRA-063 to force the grep to 0 — that would have violated the explicit
  Redis-out-of-scope Do Not Touch guard to satisfy an inconsistent verification description, which
  CLAUDE.md's gate-bypass prohibition forbids. Verified: `grep -c` with the plan's exact pattern
  returns `1`, and the single remaining match is confirmed to be `INFRA-063` (Redis), not any of
  the 18 RabbitMQ/Kafka-specific items — i.e. the substance of Step 5 (fix the fabricated broker
  citations, leave Redis alone) is satisfied; only the Verify section's own arithmetic/expected-
  count description was off.
- No other deviations. All other steps landed exactly as specified, including the Step 6
  INFRA-174 correction (real `test_path` populated, `status: verified` kept, text/evidence
  narrowed to in-process thread-pool fallback) and the ordering of Step 3 (oracle relocation)
  strictly before Step 4 (tree deletion).
