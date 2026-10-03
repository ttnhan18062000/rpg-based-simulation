---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
phase: done
date: 2026-08-17
tags: [architecture, engine]
---

# TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

## Title
Remove dead & declared-but-unused infrastructure: RabbitMQ/Kafka, src_legacy/, tests_legacy/

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
Both `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`'s source audits confirmed two independent
pieces of dead infrastructure. RabbitMQ and Kafka are fully provisioned, health-checked, and
credentialed in `docker-compose.yml`/`pyproject.toml`, but zero application code imports either
(`pika`/`confluent_kafka` — repo-wide grep, zero matches); worse, the anomaly-detection worker's
container hard-depends on RabbitMQ's healthcheck despite never sending it a byte, so a RabbitMQ
failure can take down a real subsystem for no functional reason. Separately, `src_legacy/` and
`tests_legacy/` (601 files combined) contain nothing but stale `.pyc` bytecode with no surviving
`.py` source behind them. Both audits independently rank this the single highest-priority finding
in either report — the only one that can cause a real outage for a reason unrelated to the
affected subsystem's own function.

## Scope
Full findings and evidence are in `docs/plans/dead_infra_removal_epic.md`. Concrete scope:
- Un-couple `ai_worker`'s startup from RabbitMQ's healthcheck (`docker-compose.yml:70-71`).
- Decide and record RabbitMQ/Kafka's fate: commit to a real use case and scope it properly, or
  remove `pika`/`confluent-kafka` from `pyproject.toml`, the `rabbitmq`/`kafka`/`zookeeper`
  services from `docker-compose.yml`, and associated env vars.
- Delete the dead bytecode in `src_legacy/` + `tests_legacy/` (598 `.pyc` files, zero surviving
  `.py` source), but first relocate the 3 git-tracked, load-bearing oracle JSONs out of
  `tests_legacy/parity/{movement,interaction,town}_oracle/results.json` to a non-"legacy"-named
  home (e.g. `tests/parity/oracles/`) and update `ORACLE_ROOT` in
  `tests/integrity/test_parity_guards.py` accordingly — see Assumptions/Open Questions.

## Out of Scope
- Building a real RabbitMQ/Kafka use case, if that's the eventual decision instead of removal.
- Any other dead-code audit beyond the two specifically-confirmed trees.

## Acceptance Criteria
- [x] `ai_worker`'s container start no longer depends on RabbitMQ's healthcheck.
- [x] Either RabbitMQ/Kafka are fully removed (deps, services, env vars) or a real use case is
      scoped and tracked as separate follow-on work — not left indefinitely provisioned-but-unused.
- [x] `src_legacy/`/`tests_legacy/` contain no dead `.pyc` bytecode; the 3 real parity-oracle
      `results.json` files are relocated (not deleted) and `test_parity_guards.py` still passes
      against their new path.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/dead_infra_removal_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- docker-compose.yml
- pyproject.toml
- src_legacy/
- tests_legacy/

## Assumptions / Open Questions
- Whether there's real future intent for RabbitMQ/Kafka is an open decision for the requester —
  neither audit found evidence of one.
- **Independently re-verified 2026-08-19 (this session, before any implementation):** the audits'
  premise is only mostly true. 598 of 601 files are genuinely dead `.pyc` bytecode with no
  surviving `.py` source — safe to delete outright. But 3 files ARE git-tracked and load-bearing:
  `tests_legacy/parity/{movement,interaction,town}_oracle/results.json`, read by
  `tests/integrity/test_parity_guards.py::test_oracle_artifact_existence` (`STRICT LAW`, currently
  passing). Deleting the whole tree as originally scoped would break that test. There's also
  history here: `TCK-20260427-LEGACY-RESTORATION` (done, 2026-04-27) explicitly restored these
  directories after an earlier deletion, per direct user request, specifically "preserved for
  parity verification" — its own Out of Scope says the user "specifically asked to not remove
  them." The correct scope is prune-dead-bytecode-and-relocate-the-oracle, not delete-the-tree;
  reflected in Scope/Acceptance Criteria above.
- **Downgraded from epic to standard tier (2026-08-18):** originally created as one of 10
  sub-epics under `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`, but on review this doesn't meet
  the "large multi-ticket initiative" bar — it's 2-3 related, mostly mechanical changes that fit
  one standard ticket's own Investigate→Plan→Implement→Test→Parity→Verify pipeline. `staging_artifacts/TCK-20260817-DEAD-INFRA-REMOVAL-EPIC/` (investigation.md, plan.md, test_plan.md) is still required before implementation, per standard-tier Definition of Done, and has not been created yet.

## Implementation Notes
Implemented plan.md's 8 steps in order:
1. Removed `pika>=1.3.2` and `confluent-kafka>=2.6.0` from `pyproject.toml`'s
   `[project.dependencies]`. Left `redis>=5.0.0` and optional-dependency blocks untouched.
2. Removed the `rabbitmq` and `kafka`/`zookeeper` service blocks from `docker-compose.yml`; removed
   `RABBITMQ_URL`/`KAFKA_URL` env vars and the corresponding `depends_on` entries from both `backend`
   (soft list-form coupling) and `ai_worker` (hard `condition: service_healthy` gate — this is AC1);
   removed `rabbitmq_data`/`zookeeper_data`/`kafka_data` from the top-level `volumes:` block. Added
   new `tests/architecture/test_docker_compose_dependency_hygiene.py` with 3 tests covering AC1/AC2.
   `docker compose config` exits 0 against the resulting file (validated post-change).
3. `git mv`'d the 3 git-tracked oracle `results.json` files from
   `tests_legacy/parity/{movement,interaction,town}_oracle/` to
   `tests/parity/oracles/{movement,interaction,town}_oracle/`, preserving git history. Updated
   `ORACLE_ROOT` in `tests/integrity/test_parity_guards.py` from `"tests_legacy/parity"` to
   `"tests/parity/oracles"`. This step landed strictly before Step 4 per the plan's ordering
   requirement.
4. Confirmed (again, independently) zero git-tracked files remained in either `src_legacy/` or
   `tests_legacy/` after Step 3's relocation, then `rm -rf`'d both directories entirely (216 + 382
   dead `.pyc` files). Removed the now-vestigial `"tests_legacy"` entry from
   `[tool.pytest.ini_options].norecursedirs` in `pyproject.toml`. Added
   `test_no_pyc_bytecode_remains_in_legacy_trees` to `tests/integrity/test_parity_guards.py`
   asserting both directories no longer exist (this is AC3's other half).
5. Corrected 18 RabbitMQ/Kafka-specific checklist items in `docs/compliance/checklist.md`
   (INFRA-007–014, 017, 022, 041, 054, 056, 061, 062, 064, 071, 075) from `[x]` to `[ ]` with an
   appended `(unverified — cited test file does not exist; see
   TCK-20260817-DEAD-INFRA-REMOVAL-EPIC)` note, since their cited evidence files
   (`test_broker_isolation.py`, `test_brokerless_import.py`, `test_infra_recovery.py`,
   `test_infrastructure_isolation.py`) do not exist on disk. Left INFRA-063 (the Redis line in the
   same numeric range) untouched per the plan's explicit Do Not Touch guard — see Deviations note
   in `plan.md` for the resulting discrepancy against the plan's own Verify-section grep count.
6. Reconciled the 11 P0 parity-ledger entries (INFRA-010, 011, 014, 017, 022, 041, 054, 056, 064,
   071, 075) in `docs/parity_ledger/infrastructure.yaml`: `status` → `unsupported`, `v2_evidence`
   rewritten to state the confirmed zero-import fact plus this ticket's removal, `divergence_note`
   set to reference this ticket. For the 12th entry, INFRA-174, kept `status: verified`, populated
   the previously-null `test_path` with
   `tests/unit/kernel/test_worker_fallback.py::test_force_local_override` (confirmed to exist),
   and narrowed `text`/`v2_evidence`/`divergence_note` to describe what that test actually proves
   (in-process thread-pool fallback via `WorkerManager`, not broker-specific behavior). YAML
   parses cleanly; diff confirmed exactly 12 entries changed.
7. Marked `docs/architecture/performance_optimization.md`'s body `## Status` section
   superseded/historical for its RabbitMQ-specific "AI Task Batching" mechanism (kept the doc, did
   not delete it — its other decisions remain valid and were separately implemented). Appended a
   note under `## Revisit Trigger` stating `pika`/`confluent-kafka` were removed by this ticket and
   that future AI-task-batching work must be re-scoped against the Redis-based pipeline. Frontmatter
   `status: active` was left untouched — the plan's Change instruction named only the body `##
   Status` heading, not frontmatter.
8. Ran the full scoped verification pass: `pytest tests/integrity/ -v` (15 passed, 1 pre-existing
   skip, 2 pre-existing xfail — all unrelated to this ticket), `pytest
   tests/architecture/test_docker_compose_dependency_hygiene.py -v` (3 passed), `pytest
   tests/architecture/ -v` (64 passed), `pytest tests/simulation_quality/test_feed.py -v` (13
   passed, including the kafka-mode-rejection guard, unchanged), `pytest --collect-only -q` (9183
   tests collected, zero collection errors).

## Test Summary
All Step 8 scoped commands passed with no failures/errors:
- `tests/integrity/` — 15 passed, 1 skipped (pre-existing), 2 xfailed (pre-existing)
- `tests/architecture/test_docker_compose_dependency_hygiene.py` — 3 passed (new file)
- `tests/architecture/` (full) — 64 passed
- `tests/simulation_quality/test_feed.py` — 13 passed (kafka-mode rejection guard unchanged)
- `pytest --collect-only -q` — 9183 tests collected, 0 collection errors
No `pytest tests/` unscoped run was performed, per the plan's explicit instruction.

## Files Changed
- `pyproject.toml` — removed `pika`/`confluent-kafka` dependencies; removed `tests_legacy` from
  `norecursedirs`
- `docker-compose.yml` — removed `rabbitmq`/`kafka`/`zookeeper` services, their env vars,
  `depends_on` entries (both `backend` and `ai_worker`), and their volumes
- `tests/architecture/test_docker_compose_dependency_hygiene.py` — new file (3 tests)
- `tests/integrity/test_parity_guards.py` — `ORACLE_ROOT` repointed; added
  `test_no_pyc_bytecode_remains_in_legacy_trees`
- `tests/parity/oracles/movement_oracle/results.json` — relocated via `git mv` from
  `tests_legacy/parity/movement_oracle/results.json`
- `tests/parity/oracles/interaction_oracle/results.json` — relocated via `git mv` from
  `tests_legacy/parity/interaction_oracle/results.json`
- `tests/parity/oracles/town_oracle/results.json` — relocated via `git mv` from
  `tests_legacy/parity/town_oracle/results.json`
- `src_legacy/` — deleted entirely (216 dead `.pyc` files, 0 tracked)
- `tests_legacy/` — deleted entirely (382 dead `.pyc` files remaining after relocation, 0 tracked)
- `docs/compliance/checklist.md` — 18 RabbitMQ/Kafka-specific items marked unverified
- `docs/parity_ledger/infrastructure.yaml` — 12 P0 entries reconciled (11 → `unsupported`, 1
  (INFRA-174) corrected in place with a real `test_path`)
- `docs/architecture/performance_optimization.md` — `## Status` marked superseded/historical;
  `## Revisit Trigger` note appended
- `docs/engine/contracts/infrastructure_overview.md` — removed the stale `rabbitmq`/`kafka`/
  `zookeeper` Service Index entries (doc-updater phase; these were listed as live services, which
  became actively wrong post-removal)
- `docs/engine/contracts/infrastructure_compat_contract.md` — §4 strengthened from "not included
  in the current baseline" to explicitly state the dependencies/services are structurally absent
  (resolves Verify's `docs_to_update_coverage` condition; investigation.md/plan.md had judged this
  optional, but a real edit removes the ambiguity for the static check going forward)
- `docs/plans/dead_infra_removal_epic.md` — `## Status` section added marking the epic Resolved
- `docs/plans/architecture_resilience_remediation_roadmap.md` — Epic A marked Resolved with
  cross-reference to this ticket
- `staging_artifacts/TCK-20260817-DEAD-INFRA-REMOVAL-EPIC/plan.md` — added `## Deviations` section

## Completion Summary
Removed RabbitMQ/Kafka entirely (dependencies, docker-compose services, env vars, `depends_on`
coupling on both `backend` and `ai_worker`) with a new architecture-hygiene test guarding the
removal; relocated the 3 git-tracked, load-bearing parity-oracle `results.json` files out of
`tests_legacy/` into `tests/parity/oracles/` and repointed `test_parity_guards.py` before deleting
the remaining 598 dead `.pyc` files across `src_legacy/`/`tests_legacy/`; and reconciled the three
downstream doc/ledger surfaces this removal invalidated (`docs/compliance/checklist.md`'s
fabricated-citation items, 12 P0 entries in `docs/parity_ledger/infrastructure.yaml`, and the stale
RabbitMQ-batching ADR in `docs/architecture/performance_optimization.md`). All three acceptance
criteria are satisfied and the full scoped verification pass (Step 8) is green.

`docs/engine/contracts/infrastructure_compat_contract.md`: investigation.md/plan.md/doc-updater all
independently judged its existing §3/§4 wording already factually accurate post-removal and not
requiring a change. On Verify re-check, the mechanical `docs_to_update_coverage` static check
still flagged it (by design it can only check "was this path touched," not "was it correctly
judged unnecessary"). Rather than rely on a discretionary override each Verify run, made a real,
substantive §4 edit strengthening "not included in the current baseline" to state the deps/services
are now structurally absent (not merely disabled) — this is genuinely new factual content, not a
cosmetic edit to dodge the check.
