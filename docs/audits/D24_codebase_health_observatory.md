---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, testing, observability, documentation]
---

# D24 — Codebase Health & Architecture Observatory

## Audit Profile

| Axis | Value |
|---|---|
| **Subject** | rpg-based-simulation |
| **Scope** | Is this codebase becoming easier or harder to understand, change, verify, and operate as it grows — for both human and AI-agent maintainers? |
| **Method** | Direct repo measurement (LoC, git churn, dependency graph via `graphify`) + two independent investigation passes, cross-verified against implementation |
| **Cost posture** | Tiered by explicit user choice — measured what's cheap (topology, LoC, churn, dependency graph via existing `graphify-out/`), investigated what needs judgment (abstraction health, test quality, AI-agent navigability, doc drift), designed rather than built what has no historical data yet (scorecard trends, PR-impact reports) |
| **Posture** | Independent third-party review — no vendor process, no ticket workflow, findings stated as-is |
| **Audit date** | 2026-08-17 |
| **State** | `done` (audit complete; remediation tracked separately) |

**What this audit answers:** Codebase-scale health — LoC, churn, dependency-graph centrality,
test architecture, AI-agent navigability, and documentation drift — as distinct from D23's
failure-mode/resilience focus.

**Related dimensions:** D17 (Documentation Currency) — this audit's doc-drift findings (§G)
independently corroborate and narrow D17/D23's phase-count and watchdog-doc findings rather
than discovering new ones; it adds the structural observation that nothing in this repo's
tooling validates that a doc-cited file path actually exists. D23 (Architecture & Resilience
Audit) — companion audit run in the same session; several D23 findings (RabbitMQ/Kafka,
phase-count drift) are referenced here as "from a prior audit" and cross-checked, not re-derived.

**Remediation tracking:** `docs/plans/architecture_resilience_remediation_roadmap.md`,
`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`.

---

## A. Executive Summary

This is a large, actively-maintained codebase (113k source LoC / 684 files, 179k test LoC / 1,269 files, 38 top-level `src/` packages, 595 commits) that is **healthier than its raw size suggests**, mainly because its most central code is also its most-tested and most-deliberately-architected code — a pattern that doesn't happen by accident. The files git history shows changing most often (`engine/pipeline.py`, `core/state.py`, `api/engine_manager.py`, `engine/kernel.py`) are the *same* files the dependency graph shows as most-connected (`AuthoritativeState`, `Kernel`, `StateUpdate`). That convergence is the single best sign in this audit: the team has kept its highest-leverage code both correct-by-construction (frozen state, AST-enforced boundaries) and well-covered (determinism/replay suites), instead of it silently rotting under the weight of frequent change.

The risk is not in the core — it's in **accumulated peripheral debt and a documentation trust gap**, both of which are cheap to fix:

- **Two entire top-level directories (`src_legacy/`, `tests_legacy/`, 601 files combined) contain nothing but stale compiled bytecode** — every `.py` source file behind them has already been deleted, leaving only `.pyc` remnants of a pre-`AuthoritativeState` engine generation. Zero functional value, real risk of confusing an agent or a grep-based tool into thinking they're live code.
- **Documentation drift is real but narrow, not systemic**: two specific docs (the pipeline phase-count trio and the watchdog status/path mismatch, both previously identified) are wrong; a fresh 7-doc spot-check elsewhere came back clean. The actual gap is structural — **nothing in this repo's tooling checks that a file path cited in a doc still exists**, so drift like this can only be caught by a manual audit, never automatically.
- **A live "stuck workflow" turned out not to be stuck** — the AI-agent staleness hook has flagged `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` as idle throughout this entire session, but the ticket itself explicitly says `BLOCKED`, with a dated rationale, pending a human sign-off it names precisely. The hook has no way to read that — it measures file-mtime idleness, not ticket intent. That's a fixable, concrete AI-agent-safety gap, not a process failure.
- **Import-boundary enforcement is real but uneven**: two boundary tests are AST-based and hard to evade; two more exist but are plain substring-grep, easy to defeat with an indirect import; several plausible boundary pairs (`domains` ↛ `observability`, `systems` ↛ `engine`) have no enforcement at all. *(This finding is point-in-time as of this audit's 2026-08-17 pass — resolved by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` on 2026-08-19; see §K for current state.)*

None of the top findings require a rewrite, a new subsystem, or new infrastructure. Every recommendation below is either a deletion, a doc fix, a test-hardening pass reusing an already-proven pattern in this repo, or a small script.

---

## B. Repository Map

**Source scale:** 684 `.py` files / 113,132 LoC across 38 top-level `src/` packages. **Test scale:** 1,269 files / 179,470 LoC — tests outweigh source by LoC (~1.59:1), consistent with this repo's stated emphasis on determinism/replay/regression coverage.

**Largest subsystems by LoC:**

| Subsystem | LoC | Files | Has `tests/<name>/`? |
|---|---|---|---|
| `observability` | 27,192 | 135 | yes |
| `engine` | 17,866 | 92 | yes |
| `domains` | 13,622 | 121 | no top-level dir — see §F |
| `core` | 8,333 | 44 | yes |
| `lab` | 7,849 | 19 | no |
| `systems` | 6,710 | 70 | yes |
| `api` | 6,472 | 32 | yes |

**Repository root has ~35 top-level directories**, spanning product code (`src/`, `tests/`, `frontend/`, `dashboard-frontend/`, `website/`, `config/`, `data/`, `grafana/`), dev tooling (`scripts/`, `tools/`, `registries/`), and a substantial amount of agent-process meta-infrastructure (`agent-monitoring/`, `agent-monitoring-index/`, `agent-orchestration/`, `staging_artifacts/`, `stored_artifacts/`, `pilot_requests/`, `parity-index/`, `knowledge-index/`, `reviews/`, `tickets/`). Two more top-level trees — `src_legacy/` and `tests_legacy/` — are pure dead weight (§I).

**A separate, parallel agent-tooling subsystem** — the "Codex pilot" work — lives entirely outside `src/`: `tools/agent_codex_*` (8 directories), `tests/agent_codex_*` (7+ directories), a top-level `.codex/`, and 14 `stored_artifacts/TCK-*CODEX*` tickets, governed by `agent-orchestration/` contract files. It's dev-meta-tooling for running a second AI agent provider (Codex) alongside Claude in this repo, not part of the simulated domain.

**Dependency graph** (via the repo's existing `graphify-out/`, built from commit `f7348ed0`, indexing 2,750 files / ~1.6M words — note this corpus mixes code, docs, and tickets, not code alone): 30,875 nodes, 94,480 edges, 62% extracted / 38% inferred. **God nodes** (most-connected): `AuthoritativeState` (2,433 edges), `V2EntityBuilder` (1,503), `EntityState` (1,373), `StateUpdate` (1,210), `EntityUpdate` (1,053), `Kernel` (429), `DeterministicRNG` (430), `CatalogRepository` (425). **No true cross-module import cycles** were found — the only cycles graphify reports are 8 single-file self-references (a module importing itself, a known false-positive pattern for singleton/registry code), not real A→B→A circularity.

---

## C. Current Health Baseline

| Metric | Value |
|---|---|
| Source LoC / files | 113,132 / 684 |
| Test LoC / files | 179,470 / 1,269 |
| Test:source ratio (LoC) | 1.59 : 1 |
| Top-level `src/` packages | 38 |
| Test subdirectories | ~50 |
| Commits (full history) | 595 |
| Docs (`.md`) | 776 |
| `docs/REGISTRY.yaml` size | 950 KB / 30,114 lines (auto-generated) |
| Dead bytecode files (`src_legacy/` + `tests_legacy/`) | 601, zero surviving `.py` source |
| Declared-but-unused core dependencies | `pika`, `confluent-kafka` (from a prior, separate audit — see D23) |

**CI already implements the fast-feedback tiering the framework asks about**: `.github/workflows/test.yml` shards tests into multiple parallel per-subsystem jobs (unit-core-world, unit-gameplay, etc.), all running `pytest -m "not slow"`, with a separate `slow`/`extra_slow` marker system defined in `pyproject.toml`. This is a real, working answer to "does the project need test sharding / fast-slow tiers" — **it already has both.** What's missing is any captured timing/duration data from those CI runs, so trend-tracking of CI duration (framework §9/§17) can only be designed, not measured, until that capture is added.

---

## D. Architectural Hotspots

Cross-validating **git churn** (595 commits) against **graph centrality** (god nodes) surfaces the real hotspots — and confirms they're being handled deliberately, not accidentally:

| File | Commits | Centrality signal |
|---|---|---|
| `src/engine/pipeline.py` | 21 | authoritative mutation pipeline core |
| `src/core/state.py` | 19 | defines `AuthoritativeState` (#1 god node, 2,433 edges) |
| `src/api/engine_manager.py` | 19 | engine/API lifecycle boundary |
| `src/engine/tactical.py` | 18 | — |
| `src/core/enums.py` | 18 | — |
| `src/engine/world_loop.py` | 17 | — |
| `src/engine/kernel.py` | 17 | defines `Kernel` (god node, 429 edges) |
| `src/systems/generator.py` | 16 | — |
| `src/engine/apply.py` | 16 | — |
| `src/core/updates.py` | 15 | defines `StateUpdate`/`EntityUpdate` (1,210/1,053 edges) |

**Coverage check on these hotspots**: `kernel.py` has strong, dedicated coverage — `tests/unit/kernel/` (4 files) plus `tests/integration/kernel/` (13 files, including determinism/replay/milestone suites) — coverage matches its centrality. `pipeline.py` and `tactical.py`, both top-5 by churn, have **no exactly-named dedicated unit test file** in `tests/unit/engine/`'s 15 files. This is **not confirmed as a gap** — they're plausibly covered indirectly through the integration/kernel determinism suites — but it's worth a direct check given both are simultaneously high-churn and high-centrality, exactly the combination the framework's hotspot heuristic (`complexity × change_frequency × centrality × test_weakness`) flags as highest-priority.

**A naive "most-changed files" ranking would mislead you.** By raw commit count, the top files repo-wide are `agent-monitoring/tools.jsonl` (405), `tickets/working_log.csv` (263), `agent-monitoring/runs.jsonl`/`events.jsonl` (248 each), `docs/REGISTRY.yaml` (198) — all append-only process/bookkeeping files that are *supposed* to change on every ticket by design, not architectural instability signals. Any hotspot tool built for this repo needs to exclude these by name/pattern, or every report will be dominated by noise.

**Two complexity-distribution watch items** (not cross-validated with churn, so lower confidence, worth a closer look rather than immediate action):
- `src/lab/workflows.py` — 2,694 LoC, the single largest file in `src/`, containing 9 distinct `*Workflow` classes (Generate/Prepare/Register/Compact/Investigate/Propose/Update/Revert). Cohesive theme, each class a legitimate ~250-400 line pipeline stage — a mild file-level organization smell (arguably one-file-per-workflow), not a god-class.
- `src/observability/mining/` — 10 files, 2,302 LoC, with three similarly-named orchestration classes (`MiningExperimentController`, `MiningReviewWorkflow`/`MiningQualityGate`, `AIAgentInvestigationRunner`). The naming overlap makes the boundary between them unclear from names alone — **Inferred, not confirmed** as duplicative; worth a targeted read before touching it.

---

## E. Dependency Analysis

**No true cross-module import cycles** — confirmed above (§B), a genuinely positive finding for a 684-file codebase.

**God nodes classify as legitimately foundational, not accidental.** `AuthoritativeState`, `Kernel`, `StateUpdate`/`EntityUpdate`, `EntityState` sit at the center of a deliberately single-writer architecture (frozen dataclasses, AST-enforced single apply path — established in D23). High fan-in here is the intended shape of the system, not an emergent god-module problem.

**Import-boundary enforcement is real but inconsistent in rigor.** Two tests are genuinely strong:
- `tests/architecture/test_api_read_model_guard.py` — AST-based, blocks `src/api/` from importing `AuthoritativeState`/`EntityState` outside `TYPE_CHECKING`.
- `tests/architecture/test_phase_domain_permissions.py` — AST-based, enforces which kernel phase may read/write/emit which domain.

Two more exist but are weaker:
- `tests/architecture/test_phase18_import_boundaries.py` — checks `src/core/` never contains the *substring* `"import src.domains"` — string-match, not AST, one directional pair only.
- `tests/architecture/test_phase19_observability_boundaries.py` — checks the engine hot path doesn't contain substrings like `"observability.anomaly"` — same limitation.

Substring checks are meaningfully weaker than AST checks: they can be defeated by `importlib`, import aliasing, or an indirect import chain, and they don't generalize the way an AST visitor does. **No boundary test was found for `domains` ↛ `observability` internals or `systems` ↛ `engine` internals** specifically — an enforcement gap, not a confirmed violation (whether such imports currently exist wasn't checked in this pass). *(Point-in-time as of this audit's 2026-08-17 pass. `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (2026-08-19) rewrote both weak tests to AST and added both missing boundary tests via a pinned-exception model — see §K and `docs/audits/D14_coupling_depth.md`'s Coupling Inventory, which confirms the "enforcement gap, not confirmed violation" framing here was wrong: real violations did exist, 2 and 13 sites respectively.)*

**No machine-readable, code-subsystem ownership manifest exists.** `agent-orchestration/` (`contract.yaml`, `skills.yaml`, `hook-surface-policy.yaml`) is real and well-built, but scoped entirely to *agent-workflow process* — it references `src/` paths only inside human-readable skill descriptions, not as an enforced allowed/forbidden-dependency graph. The framework's §13 subsystem-manifest concept (per-subsystem allowed/forbidden deps, invariants, required tests) doesn't exist for `src/`'s 38 packages today; the closest approximations are the four architecture tests above, which are narrow and directional rather than a general manifest.

---

## F. Test Architecture Analysis

**Mocking discipline is healthy.** Sampled `tests/unit/engine/test_lifecycle_supervisor.py`: constructs a real `Kernel`/`AuthoritativeState`, mocks only the RNG (a genuine external boundary), asserts on real return-object fields rather than mock call sequences. Repo-wide, only 13 of 62 sampled files in `tests/unit/engine`+`tests/unit/core` use `MagicMock`/`@patch`, and only 13 files across all of `tests/unit` assert on `call_count`/`assert_called` — the classic "testing implementation, not behavior" smell is rare here.

**`tests/helpers/` is under-leveraged.** Only 7 of 1,140 sampled test files import the shared helpers module (`assertions.py`, `domain.py`, `entities.py`, `presets.py`, `resources.py`, `runtime.py`) directly. Ten `conftest.py` files near the top of the tree could be providing reuse invisibly via fixture injection instead — **unable to verify which explanation is true** without deeper sampling. Either way, this is worth resolving: if helpers/ really is under-used, individual test directories are likely hand-rolling redundant setup; if reuse happens via conftest fixtures, that pattern deserves documentation so it's discoverable.

**The `src/domains/` "no test directory" claim is misleading, not true.** There's no top-level `tests/domains/`, but `tests/unit/domains/` (12 subpackages, 108 files) plus `tests/integration/domains/` (17 files) cover most of it, and the remaining domains subpackages (campaigns, faction, culture, optimization, etc.) are tested under their own flat top-level dirs (`tests/unit/campaigns/`, `tests/unit/faction/`, ...) rather than nested under `unit/domains/`. **Net: coverage exists for all 19 `domains` subpackages** — this is a directory-naming inconsistency, not a coverage gap. It's still worth fixing: an agent searching only `tests/unit/domains/` for coverage would wrongly conclude 7 subpackages are untested.

**Test economics**: no timing/duration data is currently captured anywhere in CI, so slow-test/CI-duration trend tracking (framework §9) can be *designed* (see §J/§M) but not *measured* in this pass.

---

## G. Documentation Drift Report

**Confirmed drift is real but narrow** — from D23 (a prior, separate audit of this same repo): (1) three documents disagree on the authoritative pipeline's phase count (6 / 7 / 32), one citing a source file (`src/engine/authoritative_pipeline.py`) that does not exist; (2) `docs/architecture/simulation_watchdog.md` is marked `Status: Proposed` but is referenced elsewhere as if built, with a file-path claim (`src/utils/watchdog.py`) that doesn't match the real implementation (`src/observability/watchdog.py`).

**A fresh 7-doc spot-check elsewhere came back clean.** `docs/core/dirty_state_and_dependency.md`, `docs/engine/candidate_selection.md`, `deterministic_execution.md`, `governance_logic.md`, `known_limitations.md`, `docs/architecture/world_repository_layout.md`, and `world_assembly_architecture.md` were checked against source: every referenced file path and class name resolves correctly (`MovementCandidateSelector`, `DeterministicRNG`, `CanonicalStateHasher`, `DirtySetLeakError`, `TownResolutionSystem`, `WorldCompiler`, and others all confirmed present at their cited locations). One doc even correctly documents a historical removal (`WorldTemplateExpander`, removed by `TCK-20260701-WORLDTEMPLATE-REMOVE`, confirmed absent from `src/`).

**Conclusion: drift clusters, it doesn't spread.** Two docs are wrong; a reasonable additional sample is right. This changes the prioritization — the fix is "correct these two docs," not "re-audit all 776."

**The structural gap is real, though**: nothing in this repo validates that a file path cited inside a doc actually exists. `tools/generate_registry.py` (which builds `docs/REGISTRY.yaml`) parses `related_code_areas` as free text with no `os.path.exists()` call anywhere in it, and no other script in `tools/` or `scripts/` performs doc-path validation. **This is precisely the check that would have caught both known drift issues automatically**, without requiring a human or an AI-agent audit to find them by hand.

---

## H. AI-Agent Risk Analysis

**Machine-readable guardrails are real for docs/tickets, absent for code subsystems.** `registries/layer_registry.jsonl` (19 entries), `tag_registry.jsonl` (60), `tag_category_registry.jsonl` (4), and `glossary_registry.jsonl` (57) all exist and are genuinely wired into `tools/validate_frontmatter.py`, which imports live registry values rather than hardcoded enums — confirmed by its own migration history (`TCK-20260718-LAYER-REGISTRY-CONVERSION`). This is a solid, functioning system — but it governs ticket/doc *frontmatter*, not `src/` code ownership. There is no equivalent manifest telling an agent (or a human) what a given `src/` subsystem is allowed to depend on, what invariants it must preserve, or which tests are required before touching it (see §E).

**A concrete, current case study: the "stuck" epic that wasn't.** `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` has been flagged by the repo's own automated staleness hook as idle past its 5-day window *throughout this entire session*. Reading the actual ticket tells a different story: 5 of its 6 child tickets are done (`TCK-20260730-CLAUDE-EXECUTION-IDENTITY`, `PROVIDER-HOOK-POLICY`, `CODEX-POSTTOOL-ADAPTER`, `CODEX-RUNTIME-SHADOW`, `CODEX-PILOT-EXECUTOR`); the sixth (`CODEX-CONTROLLED-PILOT`) is intentionally parked. The epic's own `## Assumptions / Open Questions` section states, dated: *"2026-08-02 decision: temporarily defer live Codex activation... This epic remains BLOCKED... resumption requires a new explicit owner decision and the governed human prerequisites."* Its frontmatter literally says `phase: blocked`. The remaining ticket's acceptance criteria require a human-authored `pilot_requests/<ticket_id>.yaml` and a `CODEX_LIVE_PILOT_HUMAN_SIGNOFF=1` environment variable that nothing sets automatically.

This is **not** ambiguous ownership, a missing dependency, or silent neglect — it's a deliberately governed pause, fully documented, one `cat` away from being understood. The gap is narrower and more fixable than "the workflow got stuck": **the automated staleness hook measures file-mtime idleness and has no way to read ticket-status semantics**, so it flags a correctly-parked, well-documented policy gate identically to an actually-forgotten workflow. Teaching the hook to check `## Status: BLOCKED` before firing would resolve this specific false positive without weakening its usefulness for genuinely stuck work.

**Repository sprawl adds real orientation cost**, though it's partially mitigated. ~35 top-level directories mix product code, dev tooling, and heavy agent-process meta-infrastructure. `CLAUDE.md` does a fair amount of work directing traffic (its Context Scan mandate, registry pointers), but an agent operating without that context file loaded would face a nontrivial cold-start cost. The two dead trees (`src_legacy/`, `tests_legacy/`, §I) compound this: their names alone give no signal that they're inert, so both a human and a naive grep-based tool could waste real effort on them.

**Boundary enforcement is uneven** (detailed in §E): strong AST guards exist at the API/engine split, but `domains` ↛ `observability` and `systems` ↛ `engine` have no enforced boundary at all — an agent modifying either of those has a materially weaker safety net than one modifying the API layer. *(Resolved by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`, 2026-08-19 — both boundaries are now enforced via pinned-exception AST tests, not a clean/zero-violation guarantee; see §K.)*

---

## I. Complexity Reduction Opportunities

| Opportunity | Est. removable | Risk | Verification needed |
|---|---|---|---|
| Delete `src_legacy/` + `tests_legacy/` (pure stale `.pyc`, zero surviving source) | 601 files, ~0 LoC of real source | Very low | Confirm these directories are git-ignored or safe to `git rm`; confirm no build/tooling step still references them |
| Resolve RabbitMQ/Kafka dead infrastructure (from D23) | 2 core deps, 2 docker-compose services, associated env vars | Low | Decide real-use-case-vs-delete first; independent of code-health concerns but the same finding, worth closing together |
| Fix the 2 known doc-drift clusters (phase count, watchdog status/path) | Small LoC, high trust cost | Very low | None — just edit the docs |
| Add doc-path-existence CI check | N/A (new, small script) | Very low | — |
| Split `src/lab/workflows.py` (2,694 LoC / 9 classes) into one file per workflow | 0 net LoC removed, meaningfully improves navigability of the single largest `src/` file | Low | Straightforward mechanical split; check no other file relies on same-file class adjacency |
| Investigate `src/observability/mining/` naming overlap (Controller/Workflow/QualityGate/Runner) | Unknown until read | Unknown | Targeted read required before any consolidation — flagged Suspicious, not confirmed |
| Standardize `tests/unit/domains/` vs. flat domains-subpackage test dirs | 0 LoC, pure discoverability fix | Very low | Pick one convention, move files |
| Resolve `tests/helpers/` under-utilization (7/1,140 files) | Unknown until the conftest-vs-hand-rolled question is answered | Low | Sample a few of the 1,133 non-importing test files to see whether they duplicate helper logic |

---

## J. Proposed Observatory

Most of the infrastructure this needs **already exists in some form** — the gap is wiring it together and adding the two genuinely missing pieces, not building from scratch:

- **Repository inventory + LoC/test breakdown**: the ad hoc script run for this audit (`find` + `wc -l` grouped by subsystem) is trivial to make a permanent `make codebase-health-baseline` target, writing a snapshot file.
- **Dependency graph**: `graphify-out/` already provides this. The one gap — its corpus mixes code, docs, and tickets (2,750 files / 1.6M words) rather than being a pure code-dependency graph — means fan-in/fan-out/cycle metrics for `src/` specifically would benefit from filtering graphify's existing edge data by node type, not rebuilding it.
- **Git hotspot analysis**: the churn script run here is cheap and reusable, but **must exclude known append-only process files** (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`, `docs/REGISTRY.yaml`) by name/pattern, or every report will be dominated by expected-to-churn bookkeeping noise (§D).
- **Doc-path-existence CI check**: the single highest-value net-new piece. A small script extracting path-shaped strings from `docs/**/*.md` and verifying they resolve, wired into the existing `.github/workflows/deploy-docs.yml` as a hook point. Would have caught both known drift clusters automatically.
- **Change-impact command**: see §L — mostly composable from existing pieces.
- **Historical snapshots + scorecard**: no existing mechanism persists metrics over time. Simplest approach: an appended JSON/YAML file, following the same pattern `agent-monitoring/runs.jsonl` already uses for accumulating structured records — new, but a small, well-precedented addition.

---

## K. Architecture Fitness Functions

**Already enforced, hard invariant, AST-based (strong):**
- API layer cannot import authoritative mutable state (`test_api_read_model_guard.py`)
- Only the resolution phase may perform authoritative mutation (`test_phase_domain_permissions.py`)
- `core` ↛ `domains`, `observability` ↛ `engine` (Kernel-facade only), `observability` ↛ `domains`/`systems` (pinned allowlist) (`test_phase18_import_boundaries.py`)
- hot path ↛ heavy observability analyzers (`test_phase19_observability_boundaries.py`)
- `domains` ↛ `observability` internals (2 sites pinned as grandfathered exceptions), `systems` ↛ `engine` internals (13 sites pinned as grandfathered exceptions) (`test_phase18_import_boundaries.py`) — resolved by `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (2026-08-19) as a freeze-at-baseline: the pinned counts are frozen, not eliminated, and no new violation past the pinned sites is permitted. See `docs/audits/D14_coupling_depth.md`'s Coupling Inventory.

**Proposed, not yet enforced:**
- **`src/engine/kernel.py` imports 5 real, currently-shipping heavy observability analyzer
  submodules** (`observability.reporting`/`.cognition`, lines 129, 277, 278, 289, 1111 — lazy
  imports) that `test_hot_path_does_not_import_heavy_analyzers` never caught, because the *old*
  substring-grep version of that test matched only the bare, un-prefixed form
  (`"observability.anomaly"`, no `src.` prefix), which never matches this codebase's real
  `from src.observability...` import style. Discovered incidentally during
  `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`'s AST rewrite (2026-08-19) but deliberately
  left unfixed and undetected-by-test: `kernel.py` was not named in that ticket's Scope Guards,
  pinned-exception lists, or Related Code Areas, so the rewritten test preserves the old test's
  literal (bare-prefix) matching behavior rather than silently catching this and either failing
  the build or inventing an unreviewed pinned-exception list for `kernel.py`. **Recommended
  follow-up**: a scoped ticket to either add `kernel.py` to a pinned-exception list (reviewed on
  its own merits, mirroring the `domains`/`systems` precedent above) or refactor it off the heavy
  analyzer submodules, then tighten the test to `src.`-aware matching. See
  `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/plan.md`'s Deviations
  section for the full discovery detail.
- Tier-3 systems cannot become startup dependencies of Tier-0 systems — hard invariant, directly motivated by D23's finding that a Tier-3 observability worker's container startup was hard-blocked by an unused RabbitMQ healthcheck. This is a `docker-compose.yml`-level constraint, not a Python import, so it needs a different mechanism (a small compose-file linter), not an architecture test.
- Doc-referenced file paths must exist — hard invariant candidate, cheap, directly closes the gap in §G/§J.
- Source files above a size threshold require review flag — **soft heuristic**, not a CI failure (per the framework's own "do not turn every preference into a failing rule" guidance) — flag files like `src/lab/workflows.py`, don't block on them.
- Count of broad `except Exception` handlers should not increase without justification — **soft heuristic**, motivated by D23's finding of 481 such handlers repo-wide; track the trend, don't gate on the absolute number.

---

## L. Change-Impact Model

Proposed design for a `code-health impact <path>` command (not built in this pass — this section is deliberately design-only, since there's no historical infra yet to build it against). It would be substantially composable from data that **already exists**, not built from nothing:

- **Direct/transitive dependents** — from `graphify-out/`'s existing edge data.
- **Relevant invariants + architecture rules** — from `tests/architecture/`'s existing (if uneven — §K) boundary tests, matched to the target path's subsystem.
- **Required tests** — inferred from the target path's subsystem plus `docs/REGISTRY.yaml`'s existing `related_code_areas` field, which already links docs/tickets to code paths.
- **Criticality tier** — inferred from the churn × centrality cross-validation done manually in §D; this could become a standing classification instead of an ad hoc audit step.

**Worked example, grounded in this audit's real data** — `src/engine/pipeline.py`:

```
Subsystem:            Engine (Tier 0 — top-3 by both churn and graph centrality)
Direct dependents:    engine/kernel.py, engine/apply.py (via graphify edges)
Required tests:       tests/unit/kernel/, tests/integration/kernel/
                       (determinism/replay/milestone suites)
Relevant invariants:  single-writer mutation, per-tick atomicity
Architecture rules:   test_phase_domain_permissions.py
Note:                 no exactly-named tests/unit/engine/test_pipeline.py found —
                       verify coverage is real before treating this as fully covered
```

This is a near-term, buildable Phase 3 item (§M), not speculative tooling — most of its inputs are sitting in the repo already.

---

## M. Incremental Implementation Plan

**Phase 1 — cheap, immediate, no new infrastructure**
1. Delete `src_legacy/` and `tests_legacy/` (601 dead `.pyc` files).
2. Fix the 2 known doc-drift clusters (pipeline phase count, watchdog status/path).
3. Add the doc-path-existence CI check (§G/§J's highest-value net-new item).
4. Make the LoC/churn baseline script a permanent `make` target, with process-file exclusions baked in.

**Phase 2 — reuse proven in-repo patterns**
5. Upgrade `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` from substring-grep to AST, matching `test_api_read_model_guard.py`'s pattern.
6. Add the two missing boundary tests (`domains` ↛ `observability`, `systems` ↛ `engine`) using that same AST pattern.
7. Standardize domains test-directory placement; verify `pipeline.py`/`tactical.py` test coverage directly.

**Phase 3 — compose existing data into new tooling**
8. Build the `code-health impact <path>` command from `graphify-out/` + `docs/REGISTRY.yaml` + `tests/architecture/` — most inputs already exist (§L).
9. Teach the epic-staleness hook to check ticket `## Status` before flagging, closing the false-positive gap identified in §H.

**Phase 4 — new infrastructure, do last**
10. Historical metric snapshots (append-only file, same pattern as `agent-monitoring/runs.jsonl`) + a multi-dimension scorecard (trend arrows, not a single score, per the framework's own guidance).
11. PR/AI change-impact report generator, built on top of Phase 3's impact model.

**Explicitly deferred, not recommended yet**: a Tier-3→Tier-0 docker-compose startup-dependency linter (§K) — real and motivated by a confirmed finding, but lower volume/frequency than the Python-import boundary work above; sequence it after Phase 2 rather than alongside it.

---

## Evidence Note

Findings above are drawn from direct measurement in this session (LoC, git churn, `graphify-out/` graph data, CI/dependency file inspection) plus two independent, narrowly-scoped investigation passes (test architecture/abstraction health; AI-agent navigability/doc drift), cross-checked against each other where their scopes touched. Claims not explicitly qualified as Inferred/Suspicious/Unable-to-verify in running text are Confirmed. Two items are explicitly flagged as needing a closer look before acting on them: (1) whether `pipeline.py`/`tactical.py` are genuinely covered indirectly via integration/kernel suites, or represent a real coverage gap; (2) whether `src/observability/mining/`'s three similarly-named orchestration classes are legitimately distinct or partially duplicative.
