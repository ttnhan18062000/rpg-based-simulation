---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
artifact_type: test_plan
tags: [architecture, engine]
---

# Test Plan — TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

## Regression Surface

Existing tests that must keep passing after this ticket's changes:

**Integrity / parity (highest-risk regression surface — direct dependency on the file move):**
- `tests/integrity/test_parity_guards.py::test_oracle_artifact_existence` — currently reads
  `ORACLE_ROOT = "tests_legacy/parity"`; must be updated in lockstep with the file relocation, then
  re-verified passing against the new path (`tests/parity/oracles/` per the ticket's Scope).
- `tests/integrity/test_parity_guards.py::test_oracle_schema_integrity`
- `tests/integrity/test_parity_guards.py::test_critical_parity_scenarios_presence`
- `tests/integrity/test_doc_guards.py`, `tests/integrity/test_logic_guards.py`,
  `tests/integrity/test_manifest_guards.py` — same module family, no direct dependency on the
  changed paths, but run together to catch any collateral integrity-check breakage.

**Unit (dependency-removal blast radius — confirm nothing imports the removed packages):**
- No test file currently imports `pika` or `confluent_kafka` (confirmed via repo-wide grep during
  investigation) — there is no unit test file expected to fail from removing these two
  `pyproject.toml` dependencies. Full `tests/unit/` collection should be re-run once to confirm
  this holds (a collection-time `ImportError` would surface immediately, not a targeted failure).

**Architecture guards:**
- `tests/architecture/test_phase18_import_boundaries.py`,
  `tests/architecture/test_phase19_observability_boundaries.py` — confirm the `ai_worker`
  entrypoint (`src/observability/anomaly/worker.py`) and `src/observability/stream/consumer.py`
  stay on the Redis-only path with no new import-boundary violation introduced by touching
  `docker-compose.yml`/`pyproject.toml` (these are Python-level guards; the compose/pyproject
  changes are non-Python, so this is a defensive re-run, not an expected-impact one).

**Simulation Quality (adjacent subsystem that explicitly rejects a "kafka" feed mode):**
- `tests/simulation_quality/test_feed.py` — specifically
  `test_feed.py::<test asserting QUALITY_FEED_MODE=kafka raises ValueError>` (line ~49-51) must
  keep raising `ValueError` on `QUALITY_FEED_MODE=kafka` — this is unrelated to whether the
  `confluent-kafka` package is installed (it is a plain string-match rejection in
  `src/simulation_quality/feed.py`'s config validator, not a package-presence check), so removing
  the dependency must not change this test's outcome. Explicit regression guard against
  accidentally "fixing" this validator while touching nearby infra.

**Full scoped collection check (collection-only, not full run) to catch dependency-removal
collection errors project-wide:**
- `pytest --collect-only -q` (whole repo) — used only to confirm zero `ImportError`/
  `ModuleNotFoundError` at collection time after `pika`/`confluent-kafka` are removed from the
  installed environment. Not a behavioral test; a collection-integrity check.

## New Tests Required

Per the three Acceptance Criteria:

1. **AC1 — `ai_worker`'s container start no longer depends on RabbitMQ's healthcheck.**
   - Test name: `test_ai_worker_does_not_depend_on_rabbitmq_healthcheck`
   - Category: architecture guard (compose-file static check, not a Python import guard — no
     existing AST-based test mechanism fits; this needs a small YAML-parsing assertion)
   - Verifies: parses `docker-compose.yml`, asserts `services.ai_worker.depends_on` either does
     not reference `rabbitmq` at all, or if it does, uses a form other than
     `condition: service_healthy` against `rabbitmq`.
   - Location: `tests/architecture/test_docker_compose_dependency_hygiene.py` (new file — no
     existing test touches `docker-compose.yml` structurally; confirmed via
     `grep -rl docker-compose tests/`, which returns only an unrelated JSON fixture).

2. **AC2 — RabbitMQ/Kafka fully removed (deps, services, env vars) or a real use case is
   separately tracked.**
   - If removal is the resolution (most likely, per Risks/Open Questions — no found evidence of
     real intent):
     - Test name: `test_pyproject_has_no_broker_client_dependencies`
       Category: architecture guard. Verifies: `pika`/`confluent-kafka` are absent from
       `pyproject.toml`'s `[project.dependencies]`. Location: same new
       `tests/architecture/test_docker_compose_dependency_hygiene.py` file (co-locate with AC1's
       compose check since both are "declared-infra hygiene" guards) or a sibling
       `test_pyproject_dependency_hygiene.py`.
     - Test name: `test_docker_compose_has_no_rabbitmq_kafka_zookeeper_services`
       Category: architecture guard. Verifies: `rabbitmq`/`kafka`/`zookeeper` are absent from
       `docker-compose.yml`'s `services:` and `volumes:` blocks, and no service's `environment:`
       still injects `RABBITMQ_URL`/`KAFKA_URL`.
   - If a real use case is scoped instead: no new test from this ticket — the follow-on ticket
     that builds it owns its own test plan. (Out of scope per this ticket's own "Out of Scope"
     section — noted here only so Plan doesn't silently invent broker-usage tests that belong to
     that hypothetical follow-on.)

3. **AC3 — `src_legacy/`/`tests_legacy/` contain no dead `.pyc` bytecode; oracle `results.json`
   files relocated and `test_parity_guards.py` still passes.**
   - Test name: `test_no_pyc_bytecode_remains_in_legacy_trees` (or: assert the trees no longer
     exist at all, if Implement removes them entirely once emptied — matches the ticket's likely
     end-state where both directories become empty and are deleted outright)
     Category: architecture guard. Verifies: `src_legacy/` and `tests_legacy/` either don't exist
     or contain zero `.pyc` files.
     Location: same new hygiene test file, or `tests/integrity/test_parity_guards.py` itself
     (co-locate with the oracle-existence test since both concern the same tree).
   - Modification (not new) to `tests/integrity/test_parity_guards.py`: `ORACLE_ROOT` must be
     updated to the new path (`tests/parity/oracles/` per Scope); the three existing tests
     (`test_oracle_artifact_existence`, `test_oracle_schema_integrity`,
     `test_critical_parity_scenarios_presence`) are the acceptance proof for the "still passes"
     half of AC3 — no new test needed for that half, just re-running the existing three against
     the new path.

## Scoped Pytest Commands

```bash
# Parity/integrity guards — direct dependency on the file relocation
pytest tests/integrity/ -v

# New architecture hygiene guards (once written)
pytest tests/architecture/test_docker_compose_dependency_hygiene.py -v

# Full architecture guard suite — defensive re-run, no expected behavior change
pytest tests/architecture/ -v

# SimQ feed-mode rejection guard — adjacent-system regression check
pytest tests/simulation_quality/test_feed.py -v

# Collection-only sanity check across the whole repo (catches any stray import of the removed
# packages that a targeted grep might have missed) — NOT a behavioral run
pytest --collect-only -q
```

Never `pytest tests/` as a full run. If a fuller confidence pass is wanted beyond the above,
scope it to `pytest tests/unit/ tests/integration/ tests/architecture/ tests/integrity/
tests/simulation_quality/ -m "not slow"` — still domain-scoped, not the unscoped whole suite.

## Anti-Drift Test Guards

- **Redis path must stay green:** any test in `tests/observability/` or
  `tests/simulation_quality/` exercising `RedisStreamConsumer`/`BrokerQualityFeed` must show zero
  behavior change — these are the real, live event pipeline and must not be touched by a
  RabbitMQ/Kafka-labeled change. Re-run `tests/simulation_quality/test_broker_feed_integration.py`
  and `tests/simulation_quality/test_worker.py` if `REDIS_AVAILABLE` is set in the run environment.
- **`test_oracle_*` tests must fail loudly, not silently skip, if the relocation is done wrong** —
  all three use plain `assert os.path.exists(...)`/`assert isinstance(...)`, no
  `pytest.skip`/`xfail` guards, so a wrong `ORACLE_ROOT` value surfaces immediately as a hard
  failure. Confirm no one adds a skip-if-missing guard to paper over a bad path during Implement.
  (Two of the three functions do have internal `if not os.path.exists(path): continue/return` skip
  logic *inside* the loop for schema/scenario checks — that pre-existing behavior means a totally
  wrong `ORACLE_ROOT` would make those two tests pass vacuously with zero oracles found, while
  `test_oracle_artifact_existence` alone has the unconditional `assert` that would actually catch
  it. Do not treat `test_oracle_schema_integrity`/`test_critical_parity_scenarios_presence` passing
  as proof of a correct path on their own — check `test_oracle_artifact_existence` too.)
- **`turbo_run.py`'s pre-existing broken `src_legacy` import must not be "fixed" as a drive-by** —
  if a future contributor notices `ModuleNotFoundError` while working nearby and patches it, that
  is unscoped work reviving a dead script; no test in this plan should be written in a way that
  would require `turbo_run.py` to become importable (e.g. do not add a
  `test_turbo_run_importable` test — that would silently expand scope to fixing dead tooling).
  If a diff to `scripts/turbo_run.py` shows up in this ticket's changeset with no independent
  ticket authorizing it, that is a scope-creep signal to flag at Verify.
- **`docker-compose.yml` service-removal test must check `backend`'s soft `depends_on` too, not
  only `ai_worker`'s healthcheck-gated one** — a hygiene test that only asserts on `ai_worker`
  would pass even if `backend`'s plain-list `depends_on: [redis, rabbitmq, kafka]` (lines 17-20)
  is left dangling after the services are deleted (a `depends_on` reference to a deleted service
  is itself an error `docker compose config` would catch, but the Python test suite should catch
  it first).
