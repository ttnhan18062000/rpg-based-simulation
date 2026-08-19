---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
artifact_type: investigation
tags: [architecture, engine]
---

# Investigation — TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

## Context Scan (Step 0c)

Per the dispatch instructions, `mcp__knowledge-search__search_docs` and `graphify query` were run
before any grep/file read.

- `search_docs("Remove dead & declared-but-unused infrastructure: RabbitMQ/Kafka, src_legacy/,
  tests_legacy/")` returned, as top hits: `tickets/done/TCK-20260427-LEGACY-RESTORATION.md`,
  `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic A section),
  `docs/plans/dead_infra_removal_epic.md` (Problem/Scope/Acceptance sections),
  `docs/audits/D23_architecture_resilience.md` §E, `docs/audits/D24_codebase_health_observatory.md`
  §I, and `docs/logic_checklist_exhaustive.md` §16 ("Brokerless, recovery, and degraded-mode
  behavior"). All of these were then read in full and are cited below.
- `graphify query "dead infra removal RabbitMQ Kafka src_legacy tests_legacy"` did not surface
  RabbitMQ/Kafka/legacy-tree nodes directly (the BFS traversal anchored on unrelated cognition/
  self-model nodes and an `INFRA-215`/`docs/parity_ledger/infrastructure.yaml` test-assertion node
  from `tests/unit/engine/test_scenario_checkpointer.py`) — the graph has no extracted nodes for
  `docker-compose.yml`/`pyproject.toml` service declarations or for `src_legacy`/`tests_legacy`
  (expected: these are non-Python-AST artifacts and a bytecode-only tree, both outside graphify's
  extraction scope). The one useful lead it gave (parity ledger test-existence checks) was folded
  into the Parity Ledger Overlap section below via direct `docs/parity_ledger/infrastructure.yaml`
  reads.

## Current Behavior

### 1. RabbitMQ/Kafka provisioning
- `pyproject.toml:18-19` — `pika>=1.3.2` and `confluent-kafka>=2.6.0` are listed under
  `[project.dependencies]` (core, non-optional, non-dev).
- `docker-compose.yml:42-55` — `rabbitmq` service (`rabbitmq:3-management-alpine`) with a
  `rabbitmq-diagnostics -q ping` healthcheck.
- `docker-compose.yml:120-150` — `zookeeper` + `kafka` services (`confluentinc/cp-*:7.5.0`).
- `docker-compose.yml:10-20` (`backend`) and `docker-compose.yml:63-66` (`ai_worker`) both inject
  `RABBITMQ_URL`/`KAFKA_URL` env vars into containers that never read them.
- `docker-compose.yml:67-71` — `ai_worker.depends_on` requires `rabbitmq: condition:
  service_healthy` (hard startup gate) alongside `redis: condition: service_started`. There is no
  equivalent hard gate on `kafka`/`zookeeper` for either service.
- **Zero-import confirmation (independently re-verified this session):**
  `grep -rniE "rabbitmq|kafka|pika|confluent" --include="*.py" src/ tests/` returns zero matches
  outside `src_legacy/` (which is dead bytecode, see below) and a handful of non-functional string
  literals: `tests/tools/test_knowledge_gateway_packet_assembly.py:219-220` (a fixture literal
  asserting "Kafka is not currently used by runtime code" — itself corroborating evidence, not a
  counter-example), `tools/agent-monitoring/kgmcp_baseline_corpus.py:41,86,88` (a negative-knowledge
  eval-corpus fixture, same posture), and `tests/simulation_quality/test_feed.py:49-51` (asserts
  `QUALITY_FEED_MODE=kafka` raises `ValueError` — proves Kafka is an explicitly *rejected* feed mode
  in the real SimQ config validator, not a supported one).
- **`ai_worker`'s actual entrypoint** is `python -m src.observability.anomaly.worker`
  (`docker-compose.yml:62`). Read in full: `src/observability/anomaly/worker.py`. Its
  `LiveAnomalyWorker.start()` (line ~200) only branches on `config.stream_backend` ∈
  `{"redis", "in_process"}` and constructs `RedisStreamConsumer` for the redis case
  (`src/observability/stream/consumer.py`). There is no RabbitMQ or Kafka client construction
  anywhere in this file. This directly confirms the ticket's claim that `ai_worker` "never sends
  RabbitMQ a byte."
- `scripts/turbo_run.py:32` sets `os.environ["DISABLE_KAFKA"] = "1"` and
  `scripts/turbo_run.py:25` does `logging.getLogger("pika").setLevel(logging.WARNING)` — both are
  inert (no code anywhere reads `DISABLE_KAFKA`, and there is no `pika` logger ever created since
  nothing imports `pika`). `turbo_run.py` is not referenced by any Makefile/CI/docs other than one
  archived design doc (`docs/archive/specs/2026-03-21-turbo-run-design.md`) — it is itself
  effectively unused tooling, separately from this ticket's scope.

### 2. `src_legacy/` + `tests_legacy/` bytecode
- Confirmed file-count breakdown (601 total, matching the ticket's figure exactly):
  `src_legacy/`: 216 files, all `.pyc`, **0 `.py` files** (`find src_legacy -name "*.py" | wc -l`
  → 0). `tests_legacy/`: 385 files — 382 `.pyc` + the 3 `results.json` oracle files
  (`tests_legacy/parity/{movement,interaction,town}_oracle/results.json`).
- **Git tracking:** `git ls-files src_legacy/` → 0 results (nothing tracked). `git ls-files
  tests_legacy/` → exactly the 3 `results.json` files, nothing else. All 598 `.pyc` files are
  untracked/local-only.
- **History:** commit `677abbfb` ("Update documentation, remove legacy code (#17)", 2026-06-17)
  deleted every `.py` file under `src_legacy/` (`git log --diff-filter=D --summary -- 'src_legacy/**/*.py'`
  confirms this, e.g. `delete mode 100644 src_legacy/actions/attributes.py`) but did not touch the
  `.pyc` files that had already been compiled into loose `__pycache__`/sibling bytecode — those
  survived as orphaned bytecode with no source behind them from that point on. This ticket is the
  direct continuation of that same cleanup, one layer down (bytecode instead of source).
- **Only remaining reference to `src_legacy` anywhere in the repo:** `scripts/turbo_run.py:9` —
  `from src_legacy.utils.logging import StructuredJsonFormatter, ContextFilter`. Verified this
  import **already fails today, independent of this ticket**:
  `python3 -c "import src_legacy.utils.logging"` → `ModuleNotFoundError: No module named
  'src_legacy.utils.logging'` (there is no `.pyc` at `src_legacy/utils/logging*` — that module was
  among the ones deleted in `677abbfb` and never had surviving bytecode either). Deleting the rest
  of `src_legacy/`'s `.pyc` files does not newly break anything — `turbo_run.py` is already broken
  on this import and is not exercised by any test, Makefile target, or CI workflow
  (`grep -rl turbo_run` outside `src_legacy`/`docs/archive` → nothing).
- **Other tooling references to the directory names (not to importable content):**
  `pyproject.toml:61` lists `tests_legacy` in `[tool.pytest.ini_options].norecursedirs` (prevents
  pytest from ever walking that tree — this entry becomes vestigial, not broken, once the tree is
  emptied/removed, since an empty/nonexistent directory can't be recursed into anyway).
  `docs/REGISTRY.yaml` has no live index entries under `src_legacy/`/`tests_legacy/` (only unrelated
  substring hits on the word "legacy" elsewhere). `scripts/turbo_run.py:9` is the only executable
  reference, already covered above.
- **Load-bearing exception — already flagged in the ticket's Assumptions, independently
  re-verified here:** `tests/integrity/test_parity_guards.py:5` hardcodes
  `ORACLE_ROOT = "tests_legacy/parity"` and `test_oracle_artifact_existence()` (line 12-19) asserts
  `os.path.exists()` for all three `results.json` paths under it — currently passing (verified by
  reading the test; it is a simple `os.path.exists` assertion against files confirmed present
  above). `test_oracle_schema_integrity()` and `test_critical_parity_scenarios_presence()` also key
  off the same `ORACLE_ROOT` constant. Deleting `tests_legacy/` wholesale, as the epic plan doc
  and the original acceptance signal literally say ("`src_legacy/`/`tests_legacy/` no longer exist
  in the repo" — `docs/plans/dead_infra_removal_epic.md` line 37), would break all three tests.
  The ticket's own Scope/Acceptance Criteria (already corrected 2026-08-19, before this
  investigation) supersede that stale epic-plan line: relocate the 3 oracle JSONs to
  `tests/parity/oracles/`, update `ORACLE_ROOT`, delete everything else. This investigation
  concurs with that correction — no new evidence contradicts it, and the fresh grep above adds a
  second confirmation source (byte-for-byte git-tracked-file list) beyond what the orchestrator's
  note already established.
- **Prior direct precedent for restoring, not deleting, these exact trees:**
  `tickets/done/TCK-20260427-LEGACY-RESTORATION.md` — 2026-04-27, restored `src_legacy/` and
  `tests_legacy/` from git history "per direct user request," with `## Out of Scope` stating "user
  specifically asked to not remove them" (in the context of the *procedural engine*, i.e. the
  `.py` source, not this ticket's bytecode-only remnant). That restoration's own completion summary
  says "Legacy code is preserved for parity verification as requested" — which is exactly what this
  ticket's relocate-the-oracle-not-the-tree approach preserves, while removing everything that
  restoration ticket did *not* have a stated reason to keep (the compiled `.pyc` files, none of
  which existed as a deliberate artifact — they're a build byproduct).

## Mechanics / Engine Constraints

This ticket is infrastructure/repo-hygiene scope, not gameplay-mechanics scope — no chapter of the
Mechanics Bible (`docs/mechanics/`) constrains it directly. The one live **engine contract** that
does bear on it:

- `docs/engine/contracts/infrastructure_compat_contract.md` (status: active, layer: engine, P1),
  §3 "Infrastructure Isolation": "The core engine (`src.engine.kernel`) is guaranteed to be
  importable without external infrastructure (RabbitMQ, Kafka, Postgres) present," and §4
  "Divergences & Exclusions": "RabbitMQ/Kafka Integration: External broker support is not included
  in the current baseline." This contract already documents the target end-state this ticket
  moves toward (no real broker dependency) — removing `pika`/`confluent-kafka` fully would make the
  doc's claim strictly true rather than aspirationally true. No contradiction; the contract does
  not need a semantic rewrite, only possibly a stronger word than "not included" once the deps
  are actually gone (see Docs Requiring Update — flagged as optional/low-priority).
- No contract in `docs/engine/` asserts a load-bearing dependency on RabbitMQ/Kafka existing —
  confirmed by reading `kernel.md`, `authoritative_pipeline.md`,
  `authoritative_mutation_pipeline_contract.md`, `governance_logic.md`, `performance_contract.md`,
  `known_limitations.md` headings (none mention message brokers as a requirement; performance
  contract's hardware-class discussion is Redis-Streams-only).

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: entries INFRA-010, INFRA-011, INFRA-014, INFRA-017,
  INFRA-022, INFRA-041, INFRA-054, INFRA-056, INFRA-064, INFRA-071, INFRA-075, INFRA-174 (all P0,
  all currently `test_path: null`, all describing RabbitMQ/Kafka "disabled-mode"/"brokerless"
  behavior) need their `v2_evidence`/`status`/`divergence_note` reconciled once the RabbitMQ/Kafka
  keep-or-remove decision lands — see Parity Ledger Overlap below for why these are already
  evidentially thin, independent of this ticket.
- `docs/compliance/checklist.md`: the "RabbitMQ disabled-mode behavior" / "Kafka disabled-mode
  behavior" / "Disabled/missing dependency paths" sections (lines ~1400-1442, ~1603-1611) and the
  §16-derived INFRA-071–077 block (lines ~2720-2726) cite `tests/api/test_broker_isolation.py`,
  `tests/integration/infra/test_brokerless_import.py`, and `tests/unit/platform/test_infra_recovery.py`
  as `TEST:`/proof sources for checked-off (`[x]`) items — all three files were confirmed **not to
  exist on disk** during this investigation. This active P1 doc's broker section is already
  citing fabricated or stale evidence, and this ticket's RabbitMQ/Kafka fate decision is the
  natural trigger to correct it (either point at real coverage if any exists, or mark the items
  honestly unverified) rather than leave it silently wrong.
- `tests/integrity/test_parity_guards.py`: not a docs/ path, but its `ORACLE_ROOT = "tests_legacy/parity"`
  constant (line 5) is the literal code change this ticket's Scope requires once the 3 oracle
  JSONs are relocated to `tests/parity/oracles/` — listed here because Implement must not forget
  it; `done-checker`'s doc-coverage parser only scans this Investigation's own bullets, so it is
  called out explicitly even though it lives outside `docs/`.
- `pyproject.toml`: `[tool.pytest.ini_options].norecursedirs` (line 61) lists `tests_legacy` —
  becomes a vestigial entry once that directory is emptied/removed; harmless to leave, cleaner to
  drop in the same change. Not itself a `docs/` path, flagged for completeness alongside the
  `ORACLE_ROOT` item above (both are code/config, not docs, so neither counts toward the
  bullet-format coverage list below).

Bulleted, backtick-wrapped, `docs/`-path-only list for `done-checker`'s static coverage check
(the two non-`docs/` items above are called out in prose only, per the required format):

- `docs/parity_ledger/infrastructure.yaml`: reconcile 12 P0 broker-disabled-mode entries
  (INFRA-010/011/014/017/022/041/054/056/064/071/075/174) against the actual keep-or-remove
  decision — all currently `test_path: null` with vague, unverifiable `v2_evidence`.
- `docs/compliance/checklist.md`: correct the RabbitMQ/Kafka disabled-mode sections that cite
  three test files (`test_broker_isolation.py`, `test_brokerless_import.py`,
  `test_infra_recovery.py`) which do not exist on disk.
- `docs/engine/contracts/infrastructure_compat_contract.md`: optional — strengthen §4's "not
  included in the current baseline" wording once the deps are actually removed (currently
  accurate but soft; low priority, doesn't block Done).

## Parity Ledger Overlap

- **`docs/parity_ledger/infrastructure.yaml`, INFRA-010/011/014/017/022/041/054/056/064/071/075/174**
  (all P0): text describes RabbitMQ/Kafka "disabled-mode"/"missing broker" safety behavior. All
  twelve have `test_path: null` — already non-compliant with this project's own rule ("P0 entries
  require a passing `test_path`"), independent of this ticket. Tracing their origin:
  `docs/logic_checklist_exhaustive.md:2548-2560` (§16 "Brokerless, recovery, and degraded-mode
  behavior tied to execution") is the source checklist that generated the `RPG-INFRA-108..114`
  items these ledger entries mirror — an audit-checklist artifact, not a citation to real `src/`
  code. Given the confirmed zero-import status of `pika`/`confluent_kafka` in `src/`, there is no
  "RabbitMQ client code" or "Kafka client code" in V2 to have a disabled-mode branch at all — these
  entries describe either legacy (V1, `src_legacy/`) behavior or aspirational checklist items,
  not verified V2 behavior. This is a pre-existing parity-ledger integrity gap that this ticket's
  scope will make more visible (once the deps are actually gone, "disabled-mode behavior" for a
  library that was never imported and is now not even installed is either vacuously true or simply
  inapplicable) — flagged for the Parity phase to resolve alongside the src/doc changes, not for
  Investigate to resolve unilaterally.
- No other `docs/parity_ledger/*.yaml` file has entries whose `text` overlaps with RabbitMQ/Kafka
  or `src_legacy`/`tests_legacy` removal — confirmed by grepping all 8 ledger files for
  `legacy|oracle|rabbitmq|kafka|pika`; every other hit is either the unrelated `legacy_evidence`
  field name (present on every entry regardless of subject) or `status: legacy_verified` (a status
  value, not a reference to these two dead trees).

## Prior Work

- `tickets/done/TCK-20260427-LEGACY-RESTORATION.md` (2026-04-27) — restored `src_legacy/`/
  `tests_legacy/` from git history at explicit user request, specifically to preserve them "for
  parity verification." This is the ticket whose intent this investigation must not contradict:
  the correct reading of that ticket's "do not remove them" is about the *procedural
  engine/parity-test source*, which this ticket's scope does not touch (it only removes orphaned
  `.pyc` bytecode that has no corresponding source, and explicitly relocates rather than deletes
  the load-bearing oracle JSONs).
- `tickets/done/TCK-20260623-DEAD-CODE-REMOVAL.md` (2026-06-23) — direct precedent for how this
  project handles a "confirmed dead code" audit finding that turns out to need correction: that
  ticket's investigation phase disproved an audit's "zero importer" claim for 9 directories and
  converted the ticket into a docs-only correction instead of a deletion. The parallel here is
  structural, not evidentiary — this ticket's own dead-code claim (RabbitMQ/Kafka zero-import,
  `src_legacy`/`tests_legacy` zero-`.py`) has been independently re-verified in this investigation
  and holds up, unlike that prior case's original audit claim.
- Commit `677abbfb` (2026-06-17, "remove legacy code (#17)") — the direct predecessor action:
  deleted all `.py` source under `src_legacy/`, leaving the `.pyc` remnants this ticket now cleans
  up. Establishes that source-level legacy removal is an accepted, already-performed pattern in
  this repo; this ticket is finishing that same job at the bytecode layer.
- No stored artifact under `stored_artifacts/` addresses RabbitMQ/Kafka removal specifically
  (checked `stored_artifacts/` listing for infra/legacy/dead-named entries — none cover broker
  infra; `TCK-20260421-LEGACY-AUDIT` and `TCK-20260603-PHASE19-LEGACY-CLEANUP` cover other legacy
  cleanup rounds not overlapping this specific tree).

## Risks and Open Questions

- **Open decision, explicitly deferred to the requester per the ticket's own Assumptions:**
  whether RabbitMQ/Kafka get removed entirely or a real use case gets scoped. This investigation
  found zero evidence anywhere in the repo (docs, code, tickets, archived design docs) of an
  intended real use case — `docs/architecture/performance_optimization.md` (an ADR-style doc)
  actually proposes *using* RabbitMQ for AI-task batching, but reads as an old/superseded design
  note (no corresponding implementation exists; `src/engine/executor.py` and
  `src/engine/worker_manager.py`, the modules that would implement such batching, contain zero
  RabbitMQ code per the zero-import grep above). This is worth surfacing to the human/requester
  before Plan commits to full removal — if that ADR reflects live future intent, "remove entirely"
  would contradict it; if it's stale, Plan should note the contradiction and archive/correct it
  alongside the dependency removal. **Flagging, not assuming an answer** — a decision-blocking
  open question, not an implementation detail Plan can silently resolve.
- `docs/compliance/checklist.md`'s fabricated-looking test citations (see Docs Requiring Update)
  predate this ticket and are broader than its scope (they also cover Redis and headless-runner
  claims not part of this ticket) — recommend Plan scope the checklist correction narrowly to the
  RabbitMQ/Kafka-specific lines this ticket's change actually invalidates, not a full checklist
  audit (that would be new, unbounded scope creep).
- `docker-compose.yml` also declares `prometheus`, `grafana`, `loki`, `promtail`, `watchdog` —
  all downstream of `backend`, none downstream of `rabbitmq`/`kafka`/`zookeeper`. Confirmed no
  other service's `depends_on` references `rabbitmq`/`kafka`/`zookeeper` besides `backend`
  (env-var injection only, not a `depends_on` gate) and `ai_worker` (the hard gate). Removing the
  three services should have zero blast radius on the observability stack.
- If RabbitMQ/Kafka are removed, `docker-compose.yml`'s `volumes:` block
  (`rabbitmq_data`, `zookeeper_data`, `kafka_data`, lines 195-197) also needs pruning — not called
  out in the ticket's Scope text verbatim but implied by "remove the services"; flagging so Plan
  doesn't miss it.

## Anti-Drift Hazards

- **Do not delete `tests_legacy/parity/{movement,interaction,town}_oracle/results.json` or any
  directory containing them before they are relocated and `ORACLE_ROOT` is repointed** — this is
  the one truly load-bearing exception in either tree, and the exact mistake the original epic
  plan's phrasing ("no longer exist in the repo") would cause if followed literally instead of via
  the ticket's corrected Scope/Acceptance Criteria.
- **Do not extend this ticket into a full audit of `docs/compliance/checklist.md`'s other
  fabricated-looking test citations** (Redis, headless-runner sections use the same
  `tests/unit/platform/test_infra_recovery.py` non-existent file) — only the RabbitMQ/Kafka-
  specific lines are in scope here; the rest is a separate, unscoped finding worth its own ticket.
- **Do not treat `scripts/turbo_run.py`'s `src_legacy` import as a reason to keep any `.pyc`
  files** — it's already broken today (`ModuleNotFoundError`), unrelated to this ticket's changes,
  and out of scope to fix (no ticket currently covers it; flag but do not silently repair it as a
  drive-by).
- **Do not conflate "remove RabbitMQ/Kafka" with "remove Redis"** — Redis is the real, live event
  pipeline (`src/observability/stream/consumer.py`, `RedisStreamConsumer`) and must not be touched;
  the `REDIS_URL` env var and `redis`/`redis_data` service/volume stay untouched in
  `docker-compose.yml`.
- **`docker-compose.yml`'s `backend` service also lists `rabbitmq`/`kafka` in its own
  `depends_on`** (lines 17-20, plain list form — no `condition:`, so it's a soft ordering
  dependency, not a healthcheck gate like `ai_worker`'s). If the services are removed, this
  `depends_on` entry must be removed too, not just `ai_worker`'s — easy to fix only the healthcheck
  half (matching the ticket's most visible symptom) and miss `backend`'s softer coupling to the
  same now-nonexistent services.
