---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture Phase 2: Scale-Out to Social (plan)

**Status: APPROVED by the owner on 2026-10-03, with the recommended answers to all five §9
questions and one added constraint: do not touch RPG feature tests deeply (§9 "Owner decision").**
This is the "new owner decision" that the roadmap §6 "Phase 1 closed" block requires before any
scale-out. Child tickets still wait for gate G2 (§5).

Parent: [`roadmap.md`](roadmap.md) §6 (Phase 2 row) and §2 (measures). Epic:
`agent-working/tickets/todos/test-architecture-phase2/TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL.md`.

**Evidence base:** `origin/main` `2f520f0dd937d1ccffbe3afa9ed6c6c76c1b28a5`, measured 2026-10-03.
Every figure is dated, and the epic re-measures at start.

---

## 1 · Decision asked of the owner

Apply the Phase 1 capabilities (locate, run, report, oracle map, effectiveness, triage) to **one**
further domain, **social**. This is one batch only. Promotion, cleanup and other domains are
excluded. After the batch, the owner decides the next domain or stops (§8).

## 2 · Domain choice

`rpg-feature-planning` recommended social on 2026-10-03, and the reviewer re-checked that against
the repo.

| Domain | Verdict | Why |
|---|---|---|
| **Social** (`src/systems/social_systems/`) | **chosen** | Social has no social-layer ticket in flight and no social epic folder. Two OPEN todos in other, idle epics touch it (§5, gate G2). It has a real oracle set (§3) |
| Cognition | rejected for now | In flight: `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`, two open cognition epics, and hostility-sweep item 2 at `src/engine/cognition.py:44` |
| Strategy | rejected for now | Churning: PR #291 (goal dispatch) touches `src/ai/goals/scorers.py`, `intelligence.py` and `strategic_cognition.yaml` |
| Progression | kept separate, not first | `TCK-20261001` is parked, the starvation epic is idle, and the progression-only lane trigger has never been CI-observed. It stays on watch items (c) and (d) |

## 3 · Oracle map (inputs, not changed by this plan)

| Oracle | Role | State at `2f520f0dd` |
|---|---|---|
| `docs/mechanics/07_social_political_dynamics.md` | Behaviour (Bible chapter) | Exists, but is **not listed in CLAUDE.md's Bible table**. `rpg-feature-planning` raised this with their user. Until it is resolved, this plan treats ch07 as the behaviour source and records the gap; it does not edit CLAUDE.md |
| `docs/parity_ledger/social_narrative.yaml` | Evidence links | 294 ids: 246 verified, 44 legacy_verified, **3 divergent** (SOC-242, SOC-263, SOC-265, all P1), **1 missing** (SOC-052, P0). 227 are P0, and **211 of the 227 P0 entries have no `test_path`**, although CLAUDE.md requires one for P0 |
| `docs/simulation/social_systems_contract.md`, `docs/simulation/domains/social_memory_contract.md` | Contracts | Exist |
| `docs/world_rules/social-lineage/` (family-kinship, lineage-descent, social-relations) | World rules (these outrank the Bible where accepted) | Which Rules are classified must be confirmed with `world-rule-catalog-design` before targets are chosen (gate G4) |

**P0 evidence density by file** (ledger `v2_evidence` citations of `social_systems/*.py`, P0 only):
`appraisal.py` 8, `contracts.py` 3, every other file 0. Across all priorities, `appraisal.py` 13,
`contracts.py` 6, `relationships.py` 4, `party_lifecycle.py` 4. `reputation.py` (40 lines) is cited
once and has **no direct importer under `tests/unit/social/`**.

## 4 · Exclusions

- `src/domains/perception/`: designed, not in effect (owner decision 8).
- Dormant paths with no live caller (owner decision 7).
- **Party** (`party.py`, `party_composition.py`, `party_lifecycle.py`): no oracle document or owner
  (D-P deferred, roadmap §11).
- Writing mechanic scenarios for social. That is the feature team's job; this batch only records the
  gap.

## 5 · Entry gates (all must hold before the first child ticket activates)

| Gate | Condition | Who |
|---|---|---|
| G1 | The owner approves this plan (§9). **Met 2026-10-03** | user |
| G2 | `rpg-feature-planning` re-confirms that social is quiet at start. The confirmation names `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` (embedding-latent-cognition, touches relationship precedence) and `TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT` (intention-log-first-class), plus anything opened since | rpg-feature-planning |
| G3 | **Determinism.** The engine is not deterministic by default: `src/engine/kernel.py:612-620` drops results when `not audit_mode and elapsed > max_tick_budget_ms` (INFRA-273 / D06 §F6-F7). Any mutation or baseline run that executes the kernel sets `audit_mode=True` and relaxes `max_tick_budget_ms` (`docs/engine/deterministic_execution.md` Extension rule 5). A target whose selected tests do not run the kernel states that it doesn't. At `2f520f0dd`, the only `tests/unit/social` file that references the kernel is `test_multi_hero.py` | implementer, checked by reviewer |
| G4 | `world-rule-catalog-design` states which social-lineage Rules are classified. Targets that touch an unclassified Rule are flagged, not changed. **Answered 2026-10-03 (see below)** | world-rule-catalog-design |

**G4 answer (`world-rule-catalog-design`, 2026-10-03, checked against `origin/main`; the reviewer
re-verified the two load-bearing facts at `2f520f0dd`):**
- **Registry classification: none.** `registries/rule_classifications.yaml` has zero FAM-, LIN- or
  SOC- rows and no rule→mechanism edges. `appraisal` and `contracts` are among the 25 core-tier
  modules the registry completeness check reports as unbound. By the registry's own standard,
  every target in this batch therefore touches an unclassified Rule. Under owner decision 7,
  binding these modules is foundation step (b).
- **Catalog disposition:** Batch 09 is "PASS — ready to freeze", not frozen. FAM-01, LIN-01, LIN-02,
  SOC-01, SOC-02 and SOC-03 are ACCEPT.
- **`appraisal.py` touches a catalog-CONFLICTING entry.** `SocialAppraisalSystem.appraise_contract()`
  reads `source_entity.social.public_reputation` (line 46) and `state.clans[...].clan_reputation`
  (line 64) with no perception or knowledge gate, even for a stranger. The catalog records this as
  CONFLICTING with the inherited PERC-01/KNOW-01 (reputation reach). LIN-02's second step ("a
  specific subject learns of it") is collapsed by the same read. AGENCY-01/02 (the bond as a
  decision input) is SUPPORTED.
- **`contracts.py`:** no social-lineage Rule cites it. The nearest coverage is AUTH-01, AUTH-03,
  AUTH-05 and OWN-04, through scenarios TAR-S07 to TAR-S09 (`scenarios/foundational-batch-02.md`).

## 6 · Batch content (mapped to Phase 1 capabilities)

| # | Capability | Work | Output |
|---|---|---|---|
| 1 | Locate | Report coverage and marker coverage of `tests/unit/social/` (34 files) and the social tests elsewhere (`simulation_quality`, `architecture`, `integration`), plus a placement audit against the Epic B taxonomy | A recorded misplacement list. **No mass moves** |
| 2 | Run | Add a `src/systems/social_systems/**` case to `tests/unit/tools/test_scenario_lane_paths.py` (it routes to the dedicated job, since `PERF_RE` omits `src/systems/`). Record that no social mechanic scenario exists | One rule-level test, plus a scenario-gap record routed to the feature team |
| 3 | Oracle map | Map social tests to ledger ids, P0 first. Flag the 211 P0 entries without a `test_path` (candidate links where an existing test plainly covers the id), the 3 divergent entries, SOC-052 (missing, P0), and the ch07 Bible-table gap | A findings record. **Ledger edits that change status or link tests go to `rpg-feature-planning`; this batch proposes, it does not apply** |
| 4 | Effectiveness | **One** mutation baseline on **`appraisal.py`** (highest P0 density, with deterministic unit tests in `tests/unit/social/`). Fallback: `contracts.py`. Same provenance and staleness fields as v3 (§4.7) | `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (name provisional) and a survivor list. Survivors are findings, not fixes |
| 5 | Workflow | Observe only: if a social ticket runs the Epic C steps during the batch, record it | Observation rows, or "none observed" |
| 6 | Triage | Add a social owner-routing row to the triage procedure | One row |

**Item 4 and the CONFLICTING reputation read.** A mutation baseline measures whether tests detect
changes. It does not approve behaviour. Still, a killed mutant on lines 46 or 64 means a test pins
behaviour that the catalog records as conflicting with PERC-01/KNOW-01. The baseline file therefore
labels every mutant on the `appraise_contract` reputation-read path as **"current behaviour,
catalog-CONFLICTING"**, never as "correct". It lists those mutants separately from the rest, so a
later fix of the conflict shows up as an expected kill-to-survive change rather than a regression.
No test is added or strengthened on that path in this batch.

**Item 3 and the registry.** The oracle map uses the parity ledger's `test_path` and the catalog
only. It does not create a mechanism→test link: that link belongs to the mechanism-registry epic
(roadmap §10), and the social modules are not bound yet.

**Changed from the handover outline:** the mutation target was "reputation.py or relationships.py".
The ledger's P0 density puts it at `appraisal.py` (§3). `reputation.py` is too small and has no
direct unit importer, so it is recorded under item 3 as a coverage gap, not used as the target.

## 7 · Non-goals

No RPG behaviour change, no new or changed expectation, no ledger status change applied by this
batch, no required checks or promotion, no §9 cleanup batch, no party, and no new CI job.

## 8 · Review and exit

- The reviewer reviews each child PR against the roadmap §2 measures.
- **Batch review** (a recorded owner decision): what the six items showed for each §2 measure,
  with sample sizes stated. The owner then picks the next domain (cognition and strategy, once they
  are quiet; progression via watch item (d)) **or stops**.
- **Cost estimate:** 4–6 child tickets, mostly hotfix or standard and read-only. Item 4 is the only
  long run; its runtime is recorded in the baseline file, as v3's was. No CI cost beyond the existing non-required lane.

## 9 · Owner questions (answered 2026-10-03)

1. Approve Phase 2 for social only, as scoped here? (G1)
2. Mutation target:
   - **`appraisal.py`** (recommended): it is P0-dense, and its reputation-read mutants are labelled
     catalog-CONFLICTING as described in §6.
   - **`contracts.py`**: it has no social-lineage conflict, but its catalog coverage is
     authority-family only.
3. The 211 P0 entries without `test_path`: should this batch only *report* them (recommended), or
   should it also prepare a proposed link list for `rpg-feature-planning` to apply?
4. ch07 is missing from the CLAUDE.md Bible table. Who owns that fix? (Recommended:
   `rpg-feature-planning`, as already raised. This batch does not block on it.)
5. **Sequencing against the foundation.** Under owner decision 7, binding `appraisal` and
   `contracts` in the mechanism registry is foundation step (b), and it comes before rule-map
   classification. Should this batch:
   - (a) **start once approved** (recommended)? Every item is measurement or report only, item 3
     does not touch the registry, and findings are flagged "unbound module";
   - (b) **wait** until foundation step (b) binds the social modules?

**Owner decision (2026-10-03):** "go with your recommendation, avoid touch deeply in RPG feature
tests".
- Q1: yes, Phase 2 for social only.
- Q2: `appraisal.py`, with the reputation-read mutants labelled catalog-CONFLICTING.
- Q3: report only. No proposed link list.
- Q4: `rpg-feature-planning` owns the ch07 Bible-table fix. This batch does not block on it.
- Q5: (a) start once approved, with findings flagged "unbound module".

**Added constraint: RPG feature tests are read-only in this batch.**
- No social test file (under `tests/unit/social/`, `tests/simulation_quality/`,
  `tests/integration/` or `tests/architecture/`) is edited, moved, renamed, marked, deleted or
  strengthened.
- Item 1 measures marker coverage and placement and records findings. It does **not** add markers.
- Item 4 runs the existing tests unchanged. Survivors are findings for `rpg-feature-planning`, not
  new tests.
- The only test change in the batch is item 2's routing case in
  `tests/unit/tools/test_scenario_lane_paths.py`, which is tooling, not an RPG feature test.
