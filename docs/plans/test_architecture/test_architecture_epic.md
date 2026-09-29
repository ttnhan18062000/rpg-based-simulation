---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture (core RPG as first application)

**Status: REVISION 2026-09-29f, prepared for ticket planning** (revision f changes: §3.5, §6.2, §6.3, §7.3; ticket outlines in [`ticket_outlines.md`](ticket_outlines.md)). This roadmap owns **how
tests are planned, written, selected, organized, executed, measured, reviewed, maintained and
repaired**. It does **not** own the design or schedule of RPG mechanics; another group of agents
is reworking those. Core RPG is the **first application and validation scope**, not a feature
portfolio commitment. No tickets exist yet. Detailed plans are in
[`milestone_plans.md`](milestone_plans.md); as-is facts are in
[`current_test_system_overview.md`](current_test_system_overview.md) (cited as *OV §n*).

**Inspected code:** `04f911110`; test, `src/`, CI and agent files are unchanged through
`origin/main` `9bcae32c5` (2026-09-28).
**Labels:** **[O]** observed · **[P]** provisional signal · **[I]** inference or proposal · **[H]**
historical · **[U]** unknown · **[D]** owner decision · **[RR]** reviewer recommendation, not
owner-approved · `[R#]` reference (§14).

---

## 0 · Owner priorities (governing)

1. A coherent test structure and conventions, so an agent can tell which **domains, components,
   test levels and CI lanes** matter when logic changes.
2. **Core RPG first as the application scope.** API and UI enter only on a demonstrated dependency.
3. Test planning, authoring, selection and quality review are explicit in the AI-first workflows.
4. Coverage and verification are reported by reproducible scripts or workflows, never by manual
   case review.
5. Reusable level contracts and authoring conventions, at architecture and domain level.
6. Functional and non-functional risks, by current needs and existing ownership.
7. **(2026-09-28 clarification)** No detailed test portfolio for individual RPG features now;
   feature teams own mechanic behaviour and feature acceptance criteria.

## 1 · Scope

| This roadmap owns | Feature-owning teams own |
|---|---|
| Level contracts, placement, metadata, shared harness boundaries, conventions | The exact mechanic behaviour and its specification |
| Change-impact and test-selection model | Feature-specific acceptance criteria and test requests |
| AI-first test workflow (plan, oracle review, authoring, quality review, epic coordination) | Approving changed expected outcomes for their features |
| Execution lanes, report schema, proof states, freshness | Fixing product defects found by tests |
| Failure-triage and maintenance workflow | Deciding feature redesigns (e.g. the `COMBAT_ENGAGE` dispatch finding) |
| A bounded pilot proving the above works on core RPG | Comprehensive feature proof portfolios |

**Success metric:** the system can correctly **register, locate, run, review, invalidate and
report** proofs, and route failures to the right owner. The number of feature rows proven is
**not** the success metric.

## 2 · Classification axes (kept distinct)

| Axis | Values | Reference |
|---|---|---|
| Level / scope | unit/component · kernel integration · mechanic outcome scenario · cross-domain scenario · broad simulation | [R1][R2][R7] |
| Technique | example · property · stateful property · metamorphic · characterization | [R10][R20][R11][R23] |
| Evaluation instrument | mutation · SimQ corpus evaluation · execution census · static audit/review | [R5][R12] · OV §4.7 · [R25] |
| Result type | pass/fail · measured value · drift requiring classification · finding · unknown | [R24] |

Two cautions:
- Not every pytest test has an exact oracle.
- SimQ's anchor comparison is a tolerance-band pass/fail check on one seed per run key; drift
  classification is a separate workflow; missing calibration data is `skipped-no-data` (OV §4.7).

---

## 3 · Capability C1: Test taxonomy and structure

### 3.1 Domain and component ownership map (ownership granularity only)

This map exists for **ownership, change impact and selection**. Mechanic details are *illustrative,
dated evidence* (§9), not commitments.

| Domain | Components (code roots) | Spec location | Behaviour owner / approver |
|---|---|---|---|
| Shared substrate | `src/core/` (incl. `inventory.py`), `src/engine/pipeline*.py`, `src/engine/kernel*.py`, `src/platform/` | `docs/engine/kernel.md`, `authoritative_mutation_pipeline_contract.md`, `docs/core/state.md` | owner [D] (default: the user) |
| Movement | `src/engine/movement.py`, tactical navigation | Bible ch02 | feature team for movement/combat |
| Combat | `src/engine/combat.py`, `src/engine/domain/combat_actions.py`, `src/domains/combat_engagement/` | Bible ch02 | feature team |
| Progression / anatomy | `src/progression/`, `src/domains/progression/`, `src/entities/` | Bible ch01 | feature team |
| Economy | `src/systems/` (harvest, crafting, market, economy), `src/economy/` | Bible ch03 | feature team |
| Quests / guild | `src/systems/quest*`, `guild_system.py`, `src/quests/`, quest pipeline phases | Bible ch03 + buildings/guild doc | feature team |
| Party / group | `src/systems/party.py`, `src/systems/social_systems/party*.py` | [U] | [U], assessed by G-P |

For any feature under active redesign, the architecture must answer six questions from these
artifacts. Where the answer lives:

| Question | Source |
|---|---|
| Where is its current spec? | map above + Bible / contract |
| Who owns and approves expected behaviour? | map above + review records (§6.3) |
| Which component and domain own its runtime path? | map above + impact model (C2) |
| Which level and harness fit? | level contracts (§3.2) + technique criteria (§3.3) |
| What proof is available, missing, stale or blocked? | generated report (C4) |
| Which tests and lanes to consider when it changes? | impact report (C2) |

### 3.2 Level contracts (draft)

| Level | Executed boundary | Resources | Expected-behaviour source | Oracle | Observation | Harness | Isolation | Budget [I] | Placement | Cadence |
|---|---|---|---|---|---|---|---|---|---|---|
| Unit / component | function or domain service on hand-built state | in-process | spec formula / contract | exact value or law | return value; one `ApplyPath.apply_generation` | `V2EntityBuilder`, `tests/helpers/*` | conftest registry reset | < 1 s | `tests/unit/<component>/` | every PR |
| Kernel integration | real `Kernel` + profile + RNG, no compiler | in-process | kernel/pipeline contracts | state over N ticks | committed state, events | `test_minimal_kernel.py` pattern | fresh kernel | < 10 s | `tests/integration/<area>/` | every PR |
| Mechanic outcome scenario | `WorldCompiler` + `Kernel`, one mechanic | small compiled world | spec + proposal §3.3 | occurrence and effect (control where the claim needs one) | authoritative state delta | shared scenario helper (C1 gap) | world per test | < 30 s | `tests/mechanic_scenarios/` | every relevant PR (R2) |
| Cross-domain scenario | ≥2 domains in one run | small compiled world | spec chain | effect at each hop | state per hop | same helper | same | < 60 s | `tests/mechanic_scenarios/` | every relevant PR, or nightly (then **not** PR proof, §6.2) |
| Broad simulation | long runs, corpus | profiles, corpus worlds | balance intent, invariants | monitors; anchor tolerance bands | monitors, SimQ | certification harness, SimQ | per run | minutes | slow markers | nightly / on demand |

### 3.3 Technique criteria (not a mandate)

| Technique | Choose when | Not when |
|---|---|---|
| Example | a documented value | the law must hold over ranges |
| Property [R10] | bounds, monotonicity, per-transaction conservation | one documented value is the whole oracle |
| Stateful property [R20] | invariants over action sequences | only meaningful in a compiled world |
| Metamorphic [R11] | relations between runs | replay reliability is unverified (§6.4) |
| Characterization [R23] | complex output must not drift unnoticed, with re-approval | a simpler exact oracle exists |

### 3.4 Metadata and placement

- **Claim fields** live in-file, as test-level or module-level markers: `domain(s)`, `level`,
  `proof_kind` (§6.3), `behaviour_id` (optional).
- **Staged migration** (inventory in OV §10, a guide rather than a to-do list):
  - S1: new and modified core-RPG tests;
  - S2: candidates with agreeing signals, labels auto-proposed and confirmed in bulk;
  - S3: uncertain candidates, resolved through normal work or the pilot;
  - S4: multi-domain tests declare all their domains plus a primary one;
  - S5: substrate-only importers are out of scope unless the test is about the substrate.
- `uncertain` and `unclassified` stay visible. **No manual case-by-case audit** is required to
  finish the architecture milestone.
- A consistency check compares the declared domain with imports and directory, and flags
  disagreement; it never auto-corrects.

### 3.5 Shared harness boundaries (framework, not feature proofs)

The framework gaps (OV §9) are:
- a shared scenario helper (compile → stage → run → observe, optional control arm);
- a **replay-diff helper, limited to the verified reproducibility scope** (below);
- a per-test `data/runs` cleanup fixture;
- [D] adopting or retiring `src/testing/` and the unused CLI helpers.

These are delivered as **reusable patterns**. The rules for worked examples:
- Each example uses either a **synthetic** behaviour (a clearly labelled test-only toy, placed apart
  from feature tests) or a behaviour **confirmed stable** by its owner. The only currently eligible
  confirmed-stable candidate is the authoritative-write boundary (architecture evidence); anything
  else needs feature-agent confirmation.
- **No feature-specific proof commitments.**

**Replay-diff helper scope** [O for the evidence, I for the design]. Reproducibility is verified
only for:
- hand-built `AuthoritativeState` + `Kernel` with a fixed seed, **≤ 10 ticks**, the
  `RuntimeProfile` used by `tests/integration/kernel/test_determinism_suite.py::test_reproducibility`
  (10 runs × 10 ticks, seed 42);
- sequential vs concurrent executor equivalence over 5 ticks (`test_local_vs_concurrent_equivalence`).

The helper records seed, profile, executor, tick count and world source. For inputs **outside** that
envelope — compiled worlds, longer runs, other profiles — it returns `outside-verified-scope`, not
pass/fail. The envelope widens only when a new reproducibility test proves the wider scope.
Long-run determinism is parked (§6.4).

## 4 · Capability C2: Change-impact and test selection

**Inputs** (none alone is complete):
- declared ownership map (§3.1);
- static import graph: CI-generated; interim fallback is committed with its SHA and marked `stale`;
- coverage contexts, i.e. who-tests-what [R26][R28];
- content/config rules for `data/worlds/**`, `config/**` and content-activated state (Pattern 6);
- behaviour ids.

**Output contract:**
- per change: impacted domains and components with **reasons**, recommended tests by level, and
  lanes;
- an explicit **`impact-unknown`** list, whose fallback is to run all core-RPG lanes and flag the
  change;
- per recommended test, **three separate facts: selected by the model · lane triggered by CI rules
  · executed and passed**.

**Validation:** **fault-revealing test recall on sampled seeded faults** [R27][R29].
1. Clean baseline at a pinned SHA.
2. One declared fault per isolated revision.
3. Reference run.
4. Compare the model's selection and, separately, the lane triggers.
5. Classify each fault: usable / equivalent / invalid / timed-out / unreachable / undetected.
6. Report test recall, lane recall, over-selection cost, unknown handling and the number of usable
   faults.

This is a **sample validation, never a completeness claim**. An undetected fault is only a possible
gap. The five sample change categories are: local rule, shared substrate, cross-domain,
content/runtime activation, and unmapped.

## 5 · Capability C3: AI-first authoring workflow

| Decision | Stage / role (existing) | Recorded evidence |
|---|---|---|
| Impact set | Investigate / `investigator` (+ impact report) | domains and reasons, `impact-unknown` |
| Level, technique, proof kind, oracle source, expected effect, commands (**mandatory**); negative cases, fixtures, non-functional risk (**optional**) | Investigate / `investigator`, extended `test_plan.md` | one row per AC |
| **Oracle / spec review** | the feature owner confirms the expected behaviour and its spec source *before* tests are written, when the AC changes or adds an expectation | approval recorded (§6.3 fields) |
| Tests written | Implement / `implementer`, using the level contracts and patterns | files changed |
| Commands selected | Test / `test-scoper` | command + reason |
| Test-quality review | existing `architecture-reviewer` at Architecture-Verify (`implement-ticket.js:999`), plus an explicit, diff-scoped, advisory checklist [R9][R13][R14] | substantive findings + action taken |
| Completion | `done-checker`: mandatory fields present | DoD line |
| **Epic coordination** | `implement-epic.js`: children follow the above; the epic records shared fixtures/patterns it introduces and routes cross-child impact through the impact report | epic notes |

A new conditional phase or a dedicated test agent is a **later option**, triggered only by observed
shortcomings [RR].

## 6 · Capability C4: Execution and evidence

### 6.1 Lanes and local commands

- **CI lanes** as in OV §3, plus R2's relevant-PR scenario lane (milestone_plans R2).
- **Local commands:** each level contract names its scoped command (e.g.
  `pytest tests/mechanic_scenarios -m "not slow"`). The impact report emits the local command set
  for a change.

### 6.2 Report layers and states

- **Layers, kept separate:**
  - package coverage;
  - domain coverage (`not-derived` until a producer exists);
  - test classification;
  - lane execution;
  - architecture evidence;
  - gameplay proof claims;
  - mutation evidence;
  - SimQ anchors;
  - census reachability;
  - hygiene.
- **States:** `pass` · `fail` · `measured` · `drift-classified` · `skipped` / `skipped-no-data` ·
  `not-run` · `blocked` · `unstable` · `stale` · `unknown`. Nothing defaults to 0 or pass.
- **Lane attribution:** every proof records the lane it runs in. **A proof whose test runs only
  nightly counts as nightly evidence, never as PR proof.** Moving a test from PR to nightly
  changes its report state accordingly.
- **Reproducibility:** normalized data derived from the **same input artifacts** must match.
  Separate executions keep their own results and run ids.

**How tests without an approved gameplay-proof claim appear.** Every collected test node appears
in the *classification* layer (level × technique × domain) and the *lane execution* layer (ran /
passed / failed / skipped, per lane). Only nodes with a claim **and** a valid review record appear
in a proof layer.

| Test type | Without an approved claim | With an approved claim |
|---|---|---|
| Example | `executed evidence (example)`: counted by level and domain, with lane results; **not** in any proof layer | Law evidence (law/property kind accepts examples), or gameplay proof per its kind |
| Property / stateful | `unreviewed claim` if a claim exists without review; otherwise executed evidence | Law or stateful-invariant proof |
| Characterization / golden | `change-detection evidence`: a pass means *unchanged since baseline `<hash>` approved `<date>`*. **Never counted as correctness proof**; re-baselining follows the C5 "stale baseline" class | Still change-detection evidence; a claim cannot upgrade a golden test to correctness proof |
| Broad simulation (long runs, certification, monitors) | `system-health evidence`: per-run invariant-monitor pass/fail and stability, **not** gameplay proof | Only a separately reviewed invariant claim may enter the law-evidence layer |
| SimQ anchors, census | own instrument layers (unchanged) | — |
| Architecture guard | architecture evidence | architecture evidence |

### 6.3 Proof kinds, review records, staleness

| Proof kind | Claim fields | Automated each run | Bounded first review |
|---|---|---|---|
| Law / property | law + spec section, input domain, assumptions, invariant, generator settings | collected, ran in lane, passed; seed recorded | invariant ↔ law; domain faithful |
| Stateful invariant | action vocabulary, reachable states, invariant, reproduction data | same, plus shrunk reproduction on failure | actions realistic; invariant ↔ law |
| Mechanic outcome | trigger, authoritative effect, a control only where the claim needs one | same | trigger really occurs; effect is authoritative state; control meaningful |
| Cross-domain chain | transition and effect per hop | same | every hop observed |
| Architecture guard | protected boundary, detected violation | same | detects a real violation; **reported as architecture evidence** |

- **Review record** binds: behaviour id, test identity, proof kind, the approval fingerprints below,
  reviewer, decision, date and ticket.

**Freshness has two independent parts.**

| | **Rerun required** (machine only) | **Human re-approval required** |
|---|---|---|
| Meaning | The proof must pass again at the new SHA before it counts as current | The *oracle* may have changed meaning, so a human must re-confirm it |
| Triggers (machine-checkable) | Any change to: the test file; **behaviour-path code** (`implemented_by` files + files in the test's coverage context); the harness; fixtures, worlds or config the test loads; the dependency lock | (1) **Oracle source** changed: normalized hash of the cited spec section (heading-anchored Bible/contract text). (2) **Assertion region** changed: normalized AST hash of the test's asserts, expected literals, tolerances and expected-value parametrize data (not the whole file). (3) **Claim fields** changed (behaviour id, proof kind, observed fields). (4) **Reference data** changed (golden files, anchors, baselines the test compares against). (5) **Harness observation contract** changed: a declared contract version in the helper, bumped only when observation semantics change |
| State while pending | `unverified-at-sha` until a passing run in the proof's lane | `stale-approval` (reported, excluded from the proof count) |
| Cleared by | a passing run at the current SHA | a new review record |

**A behaviour-path code change alone triggers a rerun only, never re-approval.** If the rerun passes,
the approval stays current. If the same change also edits the assertion region or reference data,
triggers (2) or (4) apply. Harness refactors without a contract-version bump → rerun only.
- Later reports validate records mechanically, without re-reading tests.
- A static check establishes only the *level*, never semantic correctness.
- **Single authority:** in-test claims are interim. When the registry epic ships the canonical
  mechanism → test link, a one-time reconciliation moves claims there, conflicts are listed for the
  owner, and the in-test metadata becomes a reference.
- **Spec changes by feature teams** flip affected approvals to `stale-approval` via trigger (1).

### 6.4 Replay reliability

- Short-run reproducibility is proven [O].
- Long-run determinism is parked.
- Sweeps claim per-seed invariants only. Exact seed replay is a separately verified condition,
  not assumed [R21 as target].

## 7 · Capability C5: Failure-triage and test-maintenance workflow

This unifies and extends the existing rules rather than replacing them in parallel:
- `docs/testing/regression_policy.md` §4–7: decision tree, triage checklist, P0 authority;
- `docs/guides/delivery_process.md` "CI Failure Triage": absent vs failing runs, real logs,
  classification;
- CLAUDE.md's gate-integrity rule.

**Target home:** `regression_policy.md`, one document, with the others linking to it [I].

### 7.1 Every failure starts with an evidence record

| Field | Content |
|---|---|
| Source | local · PR CI · nightly · corpus evaluation (SimQ / census) · generated report |
| Identity | test node id (or report layer / anchor key), lane, run id, commit SHA, artifact ids |
| Reproduction | exact command; seed, world, profile/config where relevant |
| Expected vs observed | assertion message or the measured value against the reference |
| Rerun result | same SHA rerun: same failure / passes / different failure; in isolation vs combined |
| Recent changes | commits touching the impacted components (from the impact report) |

### 7.2 Classes

| Class | Distinguishing evidence | Responsible role | Immediate action | Closure condition |
|---|---|---|---|---|
| **Product regression** | Reproduces on rerun and in isolation; a recent change touches the behaviour path; the spec is unchanged | author of the change → **feature team** for feature code | Fix the code, not the test (`regression_policy.md` §4) | Fix merged; the failing test passes in its lane; a regression test exists |
| **Test defect / wrong oracle** | Oracle contradicts the spec, or asserts an implementation detail | test author; the spec owner confirms the oracle | Fix the test **and** keep an equivalent-or-stronger assertion; never delete a requirement test without a replacement | Reviewed fix; review record renewed |
| **Intentional spec change** | Feature team changed the behaviour on purpose | **feature/spec owner** approves | Record the reason (divergence log or spec change), then update the expectation | Approval recorded; affected proofs re-reviewed (they went `stale` automatically) |
| **Order dependence / nondeterminism** | Passes alone, fails combined; or rerun differs at the same SHA | test-infra owner (this roadmap) | Diagnose by bisection / random order; **bounded quarantine** only if needed (§7.3) | Root cause fixed; combined + isolated + random order pass |
| **Environment / fixture failure** | Fails only in one environment; missing tool, network, TLS, resource budget | CI / infra owner | Fix the environment or fixture; don't touch assertions | Green in the affected environment |
| **Stale baseline / missing data** | Reference data absent or older than the code (e.g. SimQ `data/calibration/`, anchors, perf baselines) | baseline owner (SimQ owner for anchors) | Report as `stale` / `skipped-no-data`; regenerate only via the owner's approved process (`/simq-audit` for anchors) | Baseline regenerated with a recorded reason, or the state stays visible |
| **CI selection failure** | A relevant test didn't run (lane not triggered; selected-not-triggered) | this roadmap (C2/C4) | Run the missed lane manually; file a selection defect | Rule fixed; recall sample re-run |
| **Unknown cause** | None of the above established | whoever found it → triage owner | Keep the evidence record; escalate; no code or test change | Reclassified into a known class |

### 7.3 Prohibitions and bounded quarantine

- **Never make red green** by silently updating snapshots or anchors, weakening assertions, adding
  broad `skip`/`xfail`, or changing expected values. An expectation change needs the **feature/spec
  owner's approval plus a recorded reason** (reinforces CLAUDE.md gate integrity).
- **Quarantine policy** [I]: permitted only for the order-dependence / nondeterminism class.

  **Observed pytest 9.0.2 behaviour** (scratch experiment, 2026-09-29):
  - `xfail(strict=True)`: a failing test → `XFAIL` (the run stays green); a **passing** test →
    `FAILED [XPASS(strict)]`.
  - `xfail(strict=False)`: a passing test → `XPASS`, which does **not** fail the run and so hides
    fixes.
  - `raises=<Exc>`: any other exception → `FAILED`.
  - Neither mode ever expires on its own.

  **Mechanism:**
  - A dedicated marker, `@pytest.mark.quarantine(owner=..., ticket=..., expires="YYYY-MM-DD",
    reason=..., raises=<optional>)`, registered in `pyproject.toml`.
  - A `tests/conftest.py` collection hook enforces it:
    - **Exact node:** the marker must be on the test function itself (checked via
      `item.own_markers`); a class-level or module-level quarantine is a collection error.
    - **Fields:** all present; `ticket` must exist in `tickets/todos|inprogress` (not done); expiry
      at most N days after the marker is added (N [D], proposed 14).
    - **Active** (UTC date ≤ `expires`): the hook adds `xfail(strict=True, raises=<declared or
      AssertionError>)`. A fixed test therefore fails as `XPASS(strict)`, forcing quarantine
      removal. An unexpected exception type still fails.
    - **Expired:** no `xfail` is added, so the test runs normally, **and** the hook records an
      expiry error.
  - A **required check**: a static script (proposed `tools/test_architecture/quarantine_check.py`)
    runs in an always-on CI job without `continue-on-error`. It fails on any expired, malformed,
    class/module-level or closed-ticket quarantine, independent of whether the test happens to
    pass that day. A `QUARANTINE_TODAY` override exists only for testing the checker itself.
  - **Reporting:** the hook writes `quarantine_owner`, `ticket`, `expires` and `days_left` into
    JUnit `user_properties`. The report shows `quarantined` (with owner, ticket and expiry) or
    `quarantine-expired` (fails), never `pass`.
  - Replaces `regression_policy.md` §6's unbounded `xfail(strict=False)` rule. The replacement
    itself is an owner decision [D].
- **Defects found by new tests** are handed to the **feature-owning team** (ticket + evidence
  record). This roadmap does not expand into feature implementation.
- Nothing here may approve behaviour whose intended design is undecided (e.g. E11).

## 8 · Capability C6: Bounded core-RPG pilot

**Purpose:** show that the architecture works, not complete a portfolio. It uses **one or two
suitably stable changes selected with the feature agents**. If none is available, it uses an
existing stable behaviour, or a **synthetic, clearly labelled exercise**. The roadmap never
blocks on a feature redesign.

**The pilot must demonstrate that an agent can:**
1. identify impacted domains and levels (C2);
2. produce a test plan with an approved oracle (C3);
3. choose or create the appropriate test using a reusable pattern (C1);
4. run the correct local and CI lanes (C4);
5. interpret a failure and route it to the correct owner (C5, incl. one seeded or synthetic
   failure);
6. register evidence and see it reflected accurately in the report, including a deliberate
   invalidation that turns it `stale` (C4).

This subsumes the earlier workflow pilot. It is evaluated qualitatively plus with recorded
measurements (fields completed, findings acted on, `tool_call_count` as a coarse proxy), and is
directional only.

---

## 9 · Illustrative, dated evidence (not commitments)

These observations are kept because they show what the architecture must handle. They may become
obsolete as feature teams rework mechanics.

- **Combat call sites (2026-09-28)** [O]:
  - `resolve_multi_attack()` is called only from `src/engine/movement.py:240`, with `is_lethal=False`;
  - the decision path goes through `src/engine/domain/combat_actions.py:65`;
  - a 3-world, 1000-tick measurement [H] (`tickets/todos/TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION.md:455-470`)
    found most combat on the movement path.
- **`COMBAT_ENGAGE` dispatch finding** [H]
  (`tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md`, 2026-09-19
  addendum): a **feature-owner design decision**, outside this roadmap.
- **Scenario PR gap** [O]: `PERF_RE` omits several core-RPG paths (OV §3). This one is an
  architecture concern, addressed by R2.
- **Progression order-dependent tests** [O] (OV §4.2): a test-infrastructure concern, addressed by R1.
- The former evidence rows E1–E14 are mapped in the Appendix.

## 10 · Boundaries with other initiatives

| Initiative | Owns | This roadmap |
|---|---|---|
| RPG feature rework (other agents) | mechanic behaviour, feature ACs, feature proofs, defect fixes | supplies conventions, workflow and reporting; receives feature proofs through C3/C4 |
| `mechanic_verification_scenarios_proposal.md` | scenario families and design | lane/selection contract + level contract + shared helper pattern [RR] |
| Mechanism registry epic | canonical mechanism → test link | consumes and reconciles interim claims (§6.3) [RR] |
| SimQ + `/simq-audit` | scoring, anchors, drift policy; the R3 skip-visibility repair | reports states only |
| Execution census | reachability | reports `unstable` until determinism |
| Determinism ticket (BLOCKED) | long-run determinism | replay reliability as a condition (§6.4) |
| Parity ledger | law records | derived evidence state proposal (Appendix B) |

## 11 · Milestones (summary; detail in `milestone_plans.md`)

| Milestone | Capability | Depends on |
|---|---|---|
| M0a As-is baseline | C4 | — |
| R1 Test-isolation repair | C5 / C4 | — |
| R2 Scenario lane selection | C2 / C4 | — |
| M0b Post-repair baseline | C4 | R1 `verified`, R2 |
| MT Taxonomy and structure | C1 | M0a (inventory) |
| M1 Impact model v0 | C2 | M0a, MT (domain ids) |
| M2 Authoring workflow | C3 | MT (contracts, proof kinds) |
| MF Failure-triage and maintenance workflow | C5 | M0a |
| MP Bounded core-RPG pilot | C6 | M2, MF, R2; M1 if available (otherwise manual impact with reasons) |
| G-P Party ownership assessment | C1 map | — (may end `inconclusive/defer`) |

## 12 · Decision log

| Topic | Owner-approved (2026-09-28) | Current proposal | Status |
|---|---|---|---|
| Scope | — | This roadmap owns test architecture; feature teams own feature behaviour and proofs (owner clarification) | **Owner direction** |
| Core-RPG portfolio (D10, E-rows) | D10: domain by domain | Replaced by the bounded pilot; E-rows mapped (Appendix) | Superseded by owner direction |
| Report-only scorecard (D1) | yes | Host decided after the M0a output [RR] | Partly open |
| Property/metamorphic (D3), mutation baseline (D4) | yes | Now **patterns** in C1 and supporting evidence; no fixed feature targets | Kept, re-scoped |
| Hygiene (D5) | yes | R1 + quarantine policy (C5) | Kept |
| Delete `agent_codex_*` (D6) | yes | Cleanup path with an inventory first | Kept, separate path |
| Parity (D7) | re-tier | Derived evidence state; P0 = importance [RR] | Reopened |
| API now (D8) | yes | Dependency-gated [RR] | Reopened |
| Workflow pilot (D9) | yes (progression) | Folded into MP; surface chosen with the feature agents | Re-scoped |
| Instruments (D11) | — | Separate layers [RR] | Default adopt |
| Test review insertion | — | Existing reviewer + checklist [RR] | Default |
| Changed expectations | — | Feature/spec owner approves; agents cannot re-approve [RR] | Default |
| Quarantine rule vs `regression_policy.md` §6 | — | Bounded quarantine with owner and expiry | **[D]** |

## 13 · Separate paths and out of scope

- **Separate paths:**
  - R3 SimQ skip visibility (SimQ owner);
  - parity evidence (after D7);
  - cleanup (inventory first);
  - API/UI (dependency-gated);
  - replay-dependent techniques (determinism);
  - E11 (feature design decision).
- **Out of scope:**
  - feature mechanic design and schedules;
  - comprehensive feature proof portfolios;
  - scenario-family design;
  - registry/census internals;
  - SimQ scoring;
  - the determinism root cause;
  - reviewing individual tests.

---

## Appendix A · Old M3a/M3b and E-rows → new disposition

| Old item | Disposition | Note |
|---|---|---|
| M3a (fixed E2–E4 proof batch) | **Replaced** | Property/stateful *patterns* delivered in MT with worked examples; feature law proofs → feature owners |
| M3b (fixed E7–E9 proof batch) | **Replaced** | The shared scenario helper stays as an MT framework deliverable; feature outcome proofs → feature owners |
| E1 authoritative-write guard | **pilot example** | An existing stable behaviour, suitable for the MP evidence-registration/invalidation drill (as architecture evidence) |
| E2 damage law | **feature-owner responsibility** | Combat under rework |
| E3 XP curve | **feature-owner responsibility** | Progression under rework |
| E4 conservation | **pilot example (candidate)** / feature owner | A substrate law (ch03). A candidate stable surface for MP if the feature agents confirm stability; otherwise feature owner |
| E5, E6 scenarios not selected on PRs | **architecture: absorbed into R2** | A lane problem, not a feature proof |
| E7 pursuit → opportunity attack | **feature-owner responsibility** | — |
| E8 harvest → market chain | **feature-owner responsibility** | — |
| E9 quest → reward chain | **feature-owner responsibility** | — |
| E10 crafting-predicate isolation | **architecture: absorbed into R1** | A test-isolation defect |
| E11 decision-driven attack | **removed** from this roadmap | A feature design decision (owner: the user / feature team) |
| E12 real-run XP volume | **feature-owner responsibility** | Starvation epic |
| E13 party | **G-P** (ownership assessment only) | May end `inconclusive/defer` |
| E14 replay reliability | **deferred** | Determinism parked |

## Appendix B · Parity evidence model (separate path)

- `priority` = importance (schema) [O].
- Propose a derived evidence state: `test_linked` / `audit_only` / `legacy` / `missing`.
- Record the categorized baseline first (OV §4.6: 2,842 `test_path` type + 25 `proof_type` enum
  errors across 1,561 entries); enforcement comes only after that.

## 14 · References

| # | Reference | Used for |
|---|---|---|
| R1 | Google Testing Blog, "Test Sizes" (2010) — https://testing.googleblog.com/2010/12/test-sizes.html | Small/medium/large classification (D1, D2, D9) |
| R2 | Winters, Manshreck, Wright, *Software Engineering at Google*, ch. 11 & 14 — https://abseil.io/resources/swe-book/html/ch14.html | Test size and scope, larger tests |
| R3 | Crispin & Gregory, "The Agile Testing Quadrants" (after Brian Marick) — https://lisacrispin.com/2024/10/11/the-agile-testing-quadrants/ | Test purpose (Q1–Q4) |
| R4 | Google Testing Blog, "Code Coverage Best Practices" (2020) — https://testing.googleblog.com/2020/08/code-coverage-best-practices.html | Coverage is a signal, not a gate (D1) |
| R5 | Petrović & Ivanković, "State of Mutation Testing at Google", ICSE-SEIP 2018 — https://research.google/pubs/pub46584/ | Practical, scoped mutation testing (D4) |
| R6 | Vera-Pérez et al., "A Comprehensive Study of Pseudo-tested Methods", EMSE 2019 — https://arxiv.org/abs/1807.05030 | Covered-but-not-asserted code (§2 main finding) |
| R7 | Vocke, "The Practical Test Pyramid" (martinfowler.com) — https://martinfowler.com/articles/practical-test-pyramid.html | Pyramid shape (D2) |
| R8 | Google Testing Blog, "Just Say No to More End-to-End Tests" (2015) — https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html | Balancing tiers (D2) |
| R9 | Kent Beck, Test Desiderata — https://testdesiderata.com/ | Per-test quality rubric (D6, D9) |
| R10 | MacIver et al., "Hypothesis: A new approach to property-based testing", JOSS 2019 — https://doi.org/10.21105/joss.01891 | Property tests (D3) |
| R11 | Chen et al., "Metamorphic Testing: A Review of Challenges and Opportunities", ACM CSUR 51(1) 2018 | Kernel run-relation tests (D3) |
| R12 | mutmut — https://github.com/boxed/mutmut · https://mutmut.readthedocs.io/ | Mutation tool (D4) |
| R13 | Meszaros, *xUnit Test Patterns* test smells — http://xunitpatterns.com/Test%20Smells.html · https://testsmells.org/ | Smell catalog (D6, D9) |
| R14 | obra/superpowers `test-driven-development` skill + `testing-anti-patterns.md` — https://github.com/obra/superpowers (installed locally, `.claude/skills/test-driven-development/`) | Advisory test-review rubric (D9-B) |
| R15 | Luo, Hariri, Eloussi, Marinov, "An Empirical Analysis of Flaky Tests", FSE 2014 | Order-dependence as a flakiness root cause (D5) |
| R16 | pytest-randomly — https://github.com/pytest-dev/pytest-randomly | Random-order runs (D5) |
| R17 | Foster et al., "Mutation-Guided LLM-based Test Generation at Meta" (ACH), FSE 2025 — https://arxiv.org/abs/2501.12862 | Agent-written tests guided by mutants (D9-C) |
| R18 | Requirements traceability (ISO/IEC/IEEE 29148; test coverage items in ISO/IEC/IEEE 29119) — https://en.wikipedia.org/wiki/Requirements_traceability | Parity-ledger traceability (D7) |
| R19 | Schemathesis, property-based OpenAPI testing — https://github.com/schemathesis/schemathesis · https://testdriven.io/blog/fastapi-hypothesis/ | API contract tests (D8) |
| R20 | Hypothesis stateful testing (`RuleBasedStateMachine`) — https://hypothesis.readthedocs.io/en/latest/stateful.html · https://hypothesis.works/articles/rule-based-stateful-testing/ | Action-sequence invariants (D10 T3) |
| R21 | Deterministic simulation testing — Will Wilson, "Testing Distributed Systems w/ Deterministic Simulation", Strange Loop 2014 — https://www.thestrangeloop.com/2014/testing-distributed-systems-w-slash-deterministic-simulation.html · https://antithesis.com/docs/resources/deterministic_simulation_testing/ | Seed sweeps with invariants (D10 T6) |
| R22 | Rare, "Automated Testing of Gameplay Features in *Sea of Thieves*", GDC 2019 — https://www.gdcvault.com/play/1026042/Automated-Testing-of-Gameplay-Features · "Automated Testing at Scale in Sea of Thieves", Unreal Fest Europe 2019 — https://www.unrealengine.com/events/unreal-fest-europe-2019/automated-testing-at-scale-in-sea-of-thieves | Gameplay tests in minimal worlds (D10 T4/T5) |
| R23 | Characterization / golden-master tests (Feathers, *Working Effectively with Legacy Code*) — https://en.wikipedia.org/wiki/Characterization_test · https://understandlegacycode.com/blog/characterization-tests-or-approval-tests/ | Canonical-run snapshots (D10 T8) |
| R24 | Barr, Harman, McMinn, Shahbaz, Yoo, "The Oracle Problem in Software Testing: A Survey", IEEE TSE 41(5) 2015 — https://doi.org/10.1109/TSE.2014.2372785 | Oracle as a classification axis; statistical and implicit oracles (D11) |
| R25 | ISTQB Glossary, "static testing" — https://glossary.istqb.org/en_US/term/static-testing · ISTQB CTFL ch. 3 — https://astqb.org/3-1-static-testing-basics/ | Audits and reviews as static testing (D11) |
| R26 | coverage.py "Measurement contexts" (who-tests-what, dynamic contexts) — https://coverage.readthedocs.io/en/latest/contexts.html | Dynamic test → file map (§5.1) |
| R27 | Rothermel & Harrold, "A Safe, Efficient Regression Test Selection Technique", ACM TOSEM 6(2) 1997 — https://dl.acm.org/doi/10.1145/248233.248262 | Safety: fault-revealing tests as ground truth (§5.3) |
| R28 | Gligoric, Eloussi, Marinov, "Practical Regression Test Selection with Dynamic File Dependencies" (Ekstazi), ISSTA 2015 — https://dl.acm.org/doi/10.1145/2771783.2771784 | Dynamic dependencies for selection (§5.1) |
| R29 | Machalica, Samylkin, Porth, Chandra, "Predictive Test Selection", ICSE-SEIP 2019 — https://arxiv.org/abs/1810.05286 | Failure-recall framing of selection quality (§5.3) |
