Below is the deeper breakdown of the remaining issues and how I would repair them.

I’m focusing on **actionable implementation gaps**, not general code quality.

---

# 1. Expansion gate still violates the Option A rule

## Issue

Earlier we agreed on **Option A**:

```text
YAML comments like # STATE: ... are human planning notes only.
They must not drive validation or implementation maturity checks.
```

Most of the code now follows this, especially `test_active_data_consumer.py`, which uses `ContentUsageMatrix` and graph coverage instead of comment scanning. The current test explicitly says active content is defined by `ContentUsageMatrix`. fileciteturn71file2

But `test_expansion_gate.py` still scans YAML comments:

```python
_ACTIVE_STATES = frozenset({"EXISTING-LOGIC", "LEGACY-EXPORT", "REDESIGNED-CORE"})
_STATE_RE = re.compile(r"#\s*STATE:\s*(\S+)")
_ID_RE = re.compile(...)
```

That means the expansion gate is still partially treating comments as machine-readable validation input. fileciteturn71file1

## Why this is risky

This creates two different maturity systems:

```text
Correct system:
ContentUsageMatrix → family-level implementation state

Old/drift system:
YAML # STATE comments → per-record implementation maturity
```

Future AI agents may copy the expansion gate approach and reintroduce comment-based validation elsewhere.

## Proposed solution

Replace the expansion gate’s comment scanner with the same approach used in `test_active_data_consumer.py`.

### Implementation direction

Remove:

```python
_ACTIVE_STATES
_STATE_RE
_ID_RE
_KNOWN_INACTIVE_CONTENT
```

Replace gate item 04 with:

```text
ContentUsageMatrix active families
→ reference graph coverage
→ documented consumer check
```

The expansion gate should call shared helper functions instead of maintaining its own inline baseline.

### Suggested helper

```python
def collect_active_content_family_violations(
    matrix: Mapping[str, ContentFamilyMatrixEntry],
    ref_graph: ContentReferenceGraph,
) -> list[str]:
    ...
```

Then both tests can use the same helper:

```text
tests/integration/content/test_active_data_consumer.py
tests/integration/content/test_expansion_gate.py
```

### Acceptance checklist

```text
- [ ] test_expansion_gate.py no longer imports re/yaml just to scan comments.
- [ ] No _STATE_RE exists in expansion gate.
- [ ] No ACTIVE_STATES from YAML comments exists.
- [ ] Gate item 04 uses ContentUsageMatrix.
- [ ] Expansion gate and active-data-consumer gate share the same logic.
- [ ] YAML comments remain human-only.
```

---

# 2. Expansion gate docstring is stale

## Issue

`test_expansion_gate.py` still says CAT-REL-099 is a pre-existing defect and that blocked items are marked `xfail(strict=False)`. But in the current Phase 40 code, the actual gate list no longer marks item 11 as xfail in the pass-condition list. fileciteturn71file0

## Why this is risky

Even if code passes, stale documentation misleads the next AI agent.

An agent may see this:

```text
CAT-REL-099 is expected failure
```

and assume world assembly is still allowed to be broken.

## Proposed solution

Update the docstring to reflect current reality.

### Replace this idea

```text
Items blocked by CAT-REL-099 are marked xfail.
```

### With this

```text
All gate items are expected to pass.
Historical defect CAT-REL-099 was resolved by ensuring all composition/module references resolve through the catalog.
```

### Acceptance checklist

```text
- [ ] No stale CAT-REL-099 xfail language remains.
- [ ] Gate 11 is documented as a hard pass condition.
- [ ] If a future known defect appears, it must be tracked in a separate issue registry, not hidden in test comments.
```

---

# 3. Knowledge update approval test is too permissive

## Issue

The Phase 40 E2E test does the right high-level flow:

```text
generate → prepare → register → compact → investigate → enhance → approve → knowledge update
```

But the approved knowledge update check is too loose:

```python
assert approved_result["status"] in ("SYNCED", "READY", "NO_INSIGHTS", "BLOCKED")
```

This means an approved update can still return `BLOCKED` and the test passes. fileciteturn72file17

## Why this is risky

This weakens the approval gate proof.

The test currently proves:

```text
The workflow did not crash.
```

But it does not prove:

```text
Approved insight actually becomes synchronized knowledge.
```

## Proposed solution

Split the test into three explicit cases.

### Case 1 — No approval

Expected:

```text
BLOCKED
```

or a clear approval-related exception.

### Case 2 — Approval exists but no approved insights

Expected:

```text
NO_INSIGHTS
```

### Case 3 — Approval exists and approved insights exist

Expected:

```text
SYNCED
```

No `READY`, no `BLOCKED`.

### Suggested test structure

```python
def test_knowledge_update_without_approval_is_blocked(...):
    ...

def test_knowledge_update_with_approval_but_no_insights_returns_no_insights(...):
    ...

def test_knowledge_update_with_approved_insight_syncs(...):
    ...
```

### Acceptance checklist

```text
- [ ] Unapproved insight cannot sync.
- [ ] Approved empty insight set returns NO_INSIGHTS.
- [ ] Approved non-empty insight set returns SYNCED.
- [ ] BLOCKED is not accepted in the approved-success path.
- [ ] Audit trail records approval check and sync result.
```

---

# 4. Phase 40 E2E is still mostly simulated

## Issue

The registration workflow tests create manual run folders directly, including fake manifests and child reports. That is useful for workflow testing, but it does not prove compatibility with a real completed engine run artifact. fileciteturn72file8

## Why this is risky

The lab workflow may work with synthetic artifacts but fail against real outputs from the engine/observability repository.

Right now, the system proves:

```text
Register workflow can read a hand-written lab_run_manifest.json.
```

It should also prove:

```text
Register workflow can consume real artifacts emitted by a kernel/sweep run.
```

## Proposed solution

Add one operational integration test that produces or loads a real run artifact.

### Option A — Produce a small real run in test

Use a minimal kernel/simulation run:

```text
1 tick
1 entity
LIGHT observability
temporary run_id
```

Then pass that real output into:

```text
RegisterSimulationResultWorkflow
```

### Option B — Use a checked-in golden run artifact

Create a small fixture:

```text
tests/fixtures/lab_runs/minimal_completed_run/
```

It should contain the same schema emitted by the real engine.

### Better long-term option

Use both:

```text
unit/integration tests → golden fixture
nightly/e2e test → real produced run
```

### Acceptance checklist

```text
- [ ] Register workflow accepts real engine-produced artifact structure.
- [ ] Manifest schema matches real RunArtifactRepository output.
- [ ] Missing/corrupt artifact still blocks correctly.
- [ ] The synthetic manual-run tests remain for edge cases.
- [ ] At least one test proves real-run compatibility.
```

---

# 5. Reward classification is centralized, but still semantically shallow

## Issue

`CombatRewardClassificationService.classify_defeated_target()` now exists, which is good. Combat resolution calls it and records `REWARD_SOURCE` / `REWARD_CATEGORY`. fileciteturn70file1

But the classification logic is still shallow:

```python
defender_faction = Faction(defender.identity.faction)
if defender_faction == Faction.MONSTER_HORDE:
    return HOSTILE_CREATURE
```

Then it falls back to legacy `EntityRole`. fileciteturn70file2

The tests also encode the current shortcut: `MONSTER_HORDE` means hostile creature. fileciteturn70file10

## Why this is risky

This is better than scattered enum checks, but it does not fully use the cleaned relation model.

The current logic says:

```text
monster_horde faction = hostile creature
```

But the relation system already supports contextual hostility, for example wild beasts can be hostile only when nearby or engaged. fileciteturn71file3

So reward classification can disagree with combat legality/tactical relation semantics.

## Proposed solution

Make reward classification use the same relation semantics path as attack legality.

### Current order

```text
Faction.MONSTER_HORDE shortcut
→ EntityRole fallback
```

### Better order

```text
RelationProjectionService / faction semantics
→ clean identity classification
→ compatibility mapping
→ legacy EntityRole fallback
```

### Suggested interface

```python
class CombatRewardClassificationService:
    @classmethod
    def classify_defeated_target(
        cls,
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
        relation_context: RelationContext | None = None,
    ) -> RewardClassification:
        ...
```

### Suggested source values

```text
relation_projection
clean_identity
compatibility_projection
legacy_entity_role
none
```

### Acceptance checklist

```text
- [ ] Reward classification calls faction semantics or relation projection service.
- [ ] Contextual beast far away does not automatically classify as hostile reward unless combat context says hostile.
- [ ] Engaged/nearby contextual beast can classify as hostile creature.
- [ ] Legacy MONSTER still works through fallback.
- [ ] Reward tests assert source = relation_projection for clean path.
```

---

# 6. Expansion gate duplicates active-data consumer logic

## Issue

`test_expansion_gate.py` says its baseline is inline and must stay in sync with `test_active_data_consumer.py`. fileciteturn71file1

## Why this is risky

That is a maintenance smell.

Two tests now need to be updated together manually. AI agents often miss this kind of duplication.

## Proposed solution

Move shared logic into one helper module.

### Suggested file

```text
tests/helpers/content_usage_gate.py
```

### Suggested helpers

```python
def assert_active_families_have_documented_consumers(...):
    ...

def assert_active_families_have_graph_coverage(...):
    ...

def assert_content_usage_matrix_covers_catalog_families(...):
    ...
```

Then:

```text
test_active_data_consumer.py uses helpers
test_expansion_gate.py uses helpers
```

### Acceptance checklist

```text
- [ ] No duplicated active-content baseline in expansion gate.
- [ ] No “must stay in sync” comment remains.
- [ ] Both tests call shared helper.
- [ ] Failure messages remain readable.
```

---

# 7. Phase 40 approval/audit assertions are too broad

## Issue

The current E2E audit test only requires some audit events to exist and accepts either `workflow_started` or `approval_recorded`. fileciteturn72file17

## Why this is risky

This proves the audit log is non-empty, but not that the correct safety sequence happened.

## Proposed solution

Assert a minimum ordered audit sequence.

### Expected event sequence

```text
workflow_started: GenerateSimulationSetup
workflow_completed: GenerateSimulationSetup
workflow_started: PrepareSimulationExecution
workflow_completed: PrepareSimulationExecution
manual_boundary_declared
workflow_started: RegisterSimulationResult
workflow_completed: RegisterSimulationResult
workflow_started: ProposeSimulationEnhancements
workflow_completed: ProposeSimulationEnhancements
approval_required
approval_recorded
workflow_started: UpdateKnowledgeStore
workflow_completed: UpdateKnowledgeStore
```

The exact event names can differ, but the test should verify equivalent semantics.

### Acceptance checklist

```text
- [ ] Audit log records workflow start/completion.
- [ ] Audit log records manual execution boundary.
- [ ] Audit log records approval required.
- [ ] Audit log records approval recorded.
- [ ] Audit log records knowledge sync result.
- [ ] Test fails if approval is bypassed.
```

---

# 8. Agentic workflow layer is strong, but still artifact-driven

## Issue

The workflow contracts are good: workflows declare allowed actions, forbidden actions, inputs, and expected artifacts. For example, `PrepareSimulationExecution` explicitly forbids executing the simulation, and `UpdateKnowledgeStore` forbids updating without approval. fileciteturn71file15

But most tests verify artifact creation and stage transitions, not deep semantic correctness.

## Why this is risky

A workflow can write:

```text
execution_readiness_report.md
```

and pass even if the actual command would fail.

A workflow can write:

```text
investigation_report.md
```

and pass even if its diagnosis is shallow.

## Proposed solution

Add semantic assertions per workflow.

### Examples

For `PrepareSimulationExecution`:

```text
- generated command references an existing scenario/experiment
- command has expected output path
- command does not execute
- budget report matches run count/tick count
```

For `RegisterSimulationResult`:

```text
- completed_run_count matches child runs
- failed_run_count matches failed children
- artifact index includes required files
```

For `InvestigateSimulationResult`:

```text
- known anomaly fixture produces expected anomaly type
- known healthy fixture produces no false critical issue
```

For `ProposeSimulationEnhancements`:

```text
- critical issue produces proposal
- low-confidence issue does not auto-propose patch
- proposed patch is not applied
```

### Acceptance checklist

```text
- [ ] Each workflow has at least one semantic test, not only file-existence test.
- [ ] Negative cases exist for unsafe actions.
- [ ] Reports are validated structurally and semantically.
```

---

# 9. Formal test ownership map is still missing

## Issue

The code has many tests with markers and good docstrings, but I still do not see a formal ownership map that says:

```text
which test owns which phase/contract
which test is smoke vs regression vs architecture guard
which test must be updated when a module changes
```

## Why this is risky

The test suite is now large. Without ownership, future agents may duplicate tests or weaken the wrong one.

## Proposed solution

Add:

```text
docs/testing/test_ownership_map.md
```

or machine-readable:

```text
tests/test_ownership.yaml
```

### Suggested format

```yaml
phase_20_28:
  content_matrix:
    owner_tests:
      - tests/integration/content/test_active_data_consumer.py
      - tests/unit/content/test_content_usage_matrix.py
    purpose: "Family-level content runtime usage validation"
    do_not_duplicate_with:
      - tests/integration/content/test_expansion_gate.py

phase_34:
  expansion_gate:
    owner_tests:
      - tests/integration/content/test_expansion_gate.py
    purpose: "Pre-horizontal-expansion readiness gate"
    depends_on:
      - active_data_consumer
      - strict_matrix
```

### Acceptance checklist

```text
- [ ] Every major phase has owner tests.
- [ ] Architecture guards are separated from integration tests.
- [ ] Expansion gate references owner tests instead of duplicating their logic.
- [ ] New AI-agent work can locate the right test to update.
```

---

# Highest-priority repair sequence

| Priority | Issue                                            | Proposed fix                                      | Why first                                     |
| -------: | ------------------------------------------------ | ------------------------------------------------- | --------------------------------------------- |
|        1 | Expansion gate scans `# STATE` comments          | Replace with `ContentUsageMatrix` helper          | Restores Option A consistency                 |
|        2 | Expansion gate stale CAT-REL text                | Update docstring and gate wording                 | Prevents future confusion                     |
|        3 | Knowledge update approved path accepts `BLOCKED` | Split approval tests by expected status           | Makes approval proof meaningful               |
|        4 | E2E uses synthetic run artifacts                 | Add one real-run registration test                | Proves operational compatibility              |
|        5 | Reward classification uses faction shortcut      | Use relation projection/faction semantics service | Aligns reward with runtime relation semantics |
|        6 | Audit checks are loose                           | Assert required audit event sequence              | Makes safety proof stronger                   |
|        7 | No formal test ownership map                     | Add `test_ownership_map.md` or YAML               | Prevents future test drift                    |

---

# What “done” should mean

After these fixes, I would expect:

```text
Phase 20–28 repair:
  9.0 / 10

Phase 29–34:
  8.5+ / 10

Phase 35–40:
  8.0+ / 10
```

The main architectural condition is:

```text
No validation gate should use YAML comments as machine-readable implementation state.
No approved knowledge-update test should pass with BLOCKED.
No lab E2E should be considered operational unless at least one test consumes real engine-produced run artifacts.
```
