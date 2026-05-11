I verified the new checklist against the current uploaded source/test bundles:

```text id="ox9s85"
/mnt/data/logic_checklist_exhaustive(3).md
/mnt/data/all_src_latest_3.py
/mnt/data/all_test_latest_3.py
```

I did a **static ledger audit**, not a full pytest runtime audit.

# Main verdict

Your suspicion is correct.

The checklist is currently **over-green**. Many `[x]` rows should be downgraded to unchecked / unproven because they either:

```text id="28nu80"
- have no proof marker
- reference old source/test paths
- reference tests that do not exist in the current test bundle
- claim governance that is not actually enforced
- mark legacy behavior complete even though V2 replaced/removed the old surface
```

The checklist’s own standard says a row may be complete only when the behavior is implemented on the **active V2 execution path** and has credible proof, and that partial/dead-path behavior does not count. 

---

# Mechanical audit result

```text id="hhpif2"
Total checklist rows:        1,647
Rows marked [x]:             1,647
Rows marked [ ]:             0

Checked rows without structured SOURCE/TEST/PROOF: 1,625
Checked rows with structured SOURCE/TEST/PROOF:       3

Duplicate checklist IDs:      14
Mentioned legacy test names:  742
Mentioned test names missing from current tests: 728

Mentioned test-file sections: 135
Mentioned test-file sections missing from current paths: 134
```

This alone proves the ledger cannot currently be trusted as a completion ledger.

---

# High-confidence false-green issues

## 1. Z1 governance rows are marked complete, but the checklist itself violates them

These rows are marked `[x]`:

```text id="l1d0ka"
INFRA-078: Every checklist row has a stable ID.
INFRA-080: Every checked row has at least one proof path.
INFRA-081: Every checked row names the implementation path that proves it.
INFRA-082: Every checked row names the test path that proves it.
INFRA-092: CI can fail when a checked row has no proof reference.
INFRA-093: CI can fail when a divergence has no divergence-register entry.
INFRA-094: CI can fail when a proof path references a missing test file.
INFRA-095: CI can fail when a checklist item references a removed implementation path.
```

But actual audit shows:

```text id="g0g7vj"
- 1,625 checked rows do not have structured SOURCE/TEST/PROOF.
- 14 IDs are duplicated.
- Several proof paths reference missing files.
- I found no ledger_validator / validate_ledger / divergence_register / unsupported_register references in current source/test bundles.
```

So the Z1 governance rows should be downgraded. The checklist marks those governance rows complete even though the file itself still has proof gaps. 

### Downgrade now

```text id="eeb3o2"
INFRA-078 through INFRA-100
```

At minimum, downgrade:

```text id="mmmr7n"
INFRA-078
INFRA-080
INFRA-081
INFRA-082
INFRA-092
INFRA-093
INFRA-094
INFRA-095
INFRA-096
INFRA-098
INFRA-099
INFRA-100
```

---

## 2. Explicit proof paths are broken

Example:

```md id="tar3lu"
- [x] COMB-013: Tactical choice is a bounded choice among legal actions, not a geometry exploit.
  <!-- ID: RPG-TACT-013 SOURCE: src/systems/tactical.py TEST: tests/engine/test_status_hardening.py PROOF: unit -->
```

But current refactored source/test use different paths:

```text id="kvf64o"
Current likely source: src/engine/tactical.py
Current test area: tests/unit/strategic/test_status_hardening.py or tests/unit/combat/test_tactical_legality.py
```

The declared paths are invalid:

```text id="d4c5s4"
missing source: src/systems/tactical.py
missing test:   tests/engine/test_status_hardening.py
```

This row must not remain `[x]` until the proof marker is corrected and the test actually proves the exact law. The current checklist row still references the old path. 

Same problem:

```text id="w5pm5i"
STRAT-001 references tests/engine/test_strategic_hardening.py
STRAT-007 references tests/engine/test_status_hardening.py
```

Those are stale after the refactor.

---

## 3. Duplicate IDs violate the stable-ID rule

Duplicate IDs found:

```text id="frclcy"
WORLD-001
WORLD-002
WORLD-003
WORLD-004
WORLD-005
WORLD-006
SOC-042
INFRA-003
INFRA-004
SOC-141
SUB-123
SUB-156
COMB-141
COMB-142
```

This directly contradicts:

```text id="v93f3z"
INFRA-078: Every checklist row has a stable ID.
```

So `INFRA-078` cannot be `[x]`.

---

## 4. Most test-derived rows refer to old tests, not current tests

The checklist contains hundreds of rows like:

```text id="74zewe"
COMB-014: `test_reactive_cover_seeking`
COMB-015: `test_chokepoint_holding`
COMB-016: `test_cardinal_opposite_bracketing`
COMB-017: `test_tactical_mode_integration_handler`
SOC-015: `test_watchdog_aborts_on_hang`
SUB-014: `test_navigation_uses_flow_field_for_far_town`
TOWN-025: `test_visit_guild_no_legacy_goals`
STRAT-014: `test_accurate_diagnosis_high_wisdom`
```

But the current test bundle uses the refactored folder structure and many of those exact old test names are absent. Current tests do include many new unit/integration/refactor folders, but the checklist has not been updated to point to them. 

This does **not automatically mean the logic is missing**.

It means the checklist rows are **not proven**.

They should become:

```text id="z7tjze"
[ ] unproven
```

or:

```text id="rxoitl"
[x] only after SOURCE/TEST/PROOF is updated to the current real proof path
```

---

## 5. Builder compatibility rows are false green

These rows are marked complete:

```text id="czgxeg"
SUB-233: EntityBuilder default entity has stable kind, faction, alive combat state, and wander AI state.
SUB-234: `.kind()`, `.at()`, `.home()`, `.ai_state()`, `.faction()`, `.tier()` preserve exact field effects.
SUB-243: Builder supports clique, household, home building, world role, and leash fields.
```

But current V2 builder methods are the new canonical methods:

```text id="vvv0k6"
.kind()
.location()
.identity()
.inventory()
.combat()
.attributes()
aptitude()
navigation()
cognition()
strategic()
social()
biological()
lifecycle()
...
```

The old fluent aliases are not preserved:

```text id="io5omg"
.at()
.home()
.ai_state()
.faction()
.tier()
```

So `SUB-234` should not be `[x]`.

Correct status should be one of:

```text id="bc1gip"
INTENTIONAL DIVERGENCE:
V2 intentionally replaces legacy builder aliases with canonical component methods.

or

UNSUPPORTED:
Old fluent aliases are not supported.
```

And it needs a test proving the new law.

---

## 6. RNG determinism rows are overclaimed

Rows like these are marked `[x]`:

```text id="d0j48q"
INFRA-107: RNG API supports domain separation or another proven call-order-independent scheme.
INFRA-108: RNG calls are scoped by deterministic context such as domain/entity/tick/sub-id.
INFRA-109: Spawn randomness is isolated from tactical randomness.
INFRA-110: Tactical randomness is isolated from social randomness.
INFRA-118: Tests detect accidental use of global random in gameplay code.
```

Current source does have a `DeterministicRNG` with domain support, but it also still exposes stateful deprecated methods:

```text id="6nmt0z"
next_float(...)
next_int(...)
```

Current RNG tests mostly check reproducibility, isolation between instances, and state persistence. That is not enough to prove all the call-order-independent/domain-isolation claims above.

So these should be downgraded unless you add tests such as:

```text id="w0pw8i"
- adding an unrelated RNG call in SPAWN does not change COMBAT result
- adding a non-interacting actor does not perturb another actor's decision RNG
- static test fails if gameplay code imports global random
- all gameplay randomness uses get_float/get_int with domain/tick/entity/sub_id
```

The checklist currently marks a large deterministic-randomness block as complete. 

---

## 7. Infrastructure/oracle rows are overclaimed

These are marked `[x]`:

```text id="ev23ey"
INFRA-097: CI can fail when mandatory oracle files are missing.
INFRA-098: CI can fail when an oracle lacks schema version.
INFRA-099: CI can fail when an oracle lacks seed/config metadata.
```

Current parity guard checks oracle existence and basic JSON/list/scenario shape, but I did not find evidence that it validates:

```text id="l0s5uz"
schema_version
seed metadata
config metadata
```

So at least these should be downgraded:

```text id="1cso81"
INFRA-098
INFRA-099
```

---

## 8. Legacy system/class rows are marked complete but current symbols are gone

Some checklist rows still talk about legacy surfaces such as:

```text id="853mqn"
ActionSystem
AIWorkerDaemon
CombatHandler
AIBrain
WorldState
Entity.copy
ActionProposalGuard
```

Current V2 source is intentionally reorganized around:

```text id="2kwy5b"
AuthoritativeApplyPipeline
ApplyPath
Kernel
SimulationDomainLogic
V2EntityBuilder
AuthoritativeState
StateUpdate / EntityUpdate
```

That is fine, but the checklist must say:

```text id="ylwcwg"
ENHANCED / INTENTIONAL DIVERGENCE / UNSUPPORTED
```

not silently mark legacy rows `[x]`.

Example suspicious row:

```text id="hqqvqe"
COMB-088: test_ai_worker_batch_processing_logic — Verify AIWorkerDaemon correctly handles a batch of tasks.
```

Current source does not contain `AIWorkerDaemon`, so this row cannot be complete as written.

---

# Rows I would immediately downgrade

## P0 downgrade — governance/proof truth

```text id="khwecq"
INFRA-078 through INFRA-100
```

Because the checklist itself does not satisfy these laws.

## P0 downgrade — invalid explicit markers

```text id="q6m86a"
COMB-013
STRAT-001
STRAT-007
```

Because the declared `SOURCE` or `TEST` paths are stale/missing.

## P1 downgrade — old builder compatibility

```text id="8n0eey"
SUB-233
SUB-234
SUB-235
SUB-236
SUB-237
SUB-238
SUB-239
SUB-240
SUB-241
SUB-242
SUB-243
SUB-244
```

Some may be implemented under the new builder design, but they are not proven as written.

## P1 downgrade — deterministic RNG overclaims

```text id="l4p2yq"
INFRA-107
INFRA-108
INFRA-109
INFRA-110
INFRA-111
INFRA-112
INFRA-113
INFRA-114
INFRA-115
INFRA-116
INFRA-117
INFRA-118
```

Need stronger call-order and global-random guard tests.

## P1 downgrade — legacy execution symbols

```text id="jofk2y"
COMB-088
SUB-175
any row mentioning ActionSystem / AIWorkerDaemon / CombatHandler / AIBrain / WorldState / Entity.copy / ActionProposalGuard
```

Unless each row is rewritten as an intentional V2 replacement with current source/test proof.

---

# What the checklist should do now

## Rule 1 — Do not keep all rows green

Current state:

```text id="4vgd8v"
1,647 / 1,647 rows checked
```

This is not credible.

Set rows to unchecked unless they have current proof.

## Rule 2 — Require this marker for every `[x]`

Use this exact format:

```md id="lmjyps"
<!-- ID: COMB-013 SOURCE: src/engine/tactical.py TEST: tests/unit/combat/test_tactical_legality.py PROOF: unit -->
```

Required fields:

```text id="ukrqy5"
ID
SOURCE
TEST
PROOF
```

Valid proof values:

```text id="4l22su"
unit
integration
negative
race
replay
longrun
contract
regression
certification
divergence
unsupported
```

## Rule 3 — Add a validator

The validator should fail if:

```text id="bfjsbb"
- duplicate ID exists
- checked row has no proof marker
- SOURCE path does not exist
- TEST path does not exist
- PROOF value is unknown
- INTENTIONAL DIVERGENCE has no divergence note
- UNSUPPORTED has no support-boundary note
- old test paths remain after refactor
```

Minimal validator logic:

```python id="j5ifqc"
from pathlib import Path
import re
from collections import Counter

CHECKLIST = Path("logic_checklist_exhaustive.md")
SRC_ROOT = Path("src")
TEST_ROOT = Path("tests")

VALID_PROOFS = {
    "unit",
    "integration",
    "negative",
    "race",
    "replay",
    "longrun",
    "contract",
    "regression",
    "certification",
    "divergence",
    "unsupported",
}

rows = []
for lineno, line in enumerate(CHECKLIST.read_text().splitlines(), 1):
    if not line.startswith("- ["):
        continue

    checked = line.startswith("- [x]")
    id_match = re.search(r"- \[[x ]\] ([A-Z]+-\d+):", line)
    if not id_match:
        raise AssertionError(f"Line {lineno}: missing stable ID")

    row_id = id_match.group(1)
    rows.append((lineno, row_id, checked, line))

ids = [row_id for _, row_id, _, _ in rows]
for row_id, count in Counter(ids).items():
    if count > 1:
        raise AssertionError(f"Duplicate checklist ID: {row_id}")

for lineno, row_id, checked, line in rows:
    if not checked:
        continue

    marker = re.search(
        r"<!--\s*ID:\s*(\S+)\s+SOURCE:\s*(\S+)\s+TEST:\s*(\S+)\s+PROOF:\s*(\S+)\s*-->",
        line,
    )

    if not marker:
        raise AssertionError(f"{row_id} line {lineno}: checked row missing SOURCE/TEST/PROOF marker")

    marker_id, source_path, test_path, proof = marker.groups()

    if marker_id != row_id:
        raise AssertionError(f"{row_id} line {lineno}: marker ID mismatch: {marker_id}")

    if not Path(source_path).exists():
        raise AssertionError(f"{row_id} line {lineno}: missing SOURCE path {source_path}")

    if not Path(test_path).exists():
        raise AssertionError(f"{row_id} line {lineno}: missing TEST path {test_path}")

    if proof not in VALID_PROOFS:
        raise AssertionError(f"{row_id} line {lineno}: invalid proof type {proof}")
```

---

# Correct checklist policy going forward

Use these statuses:

```text id="h0x6u6"
[x]      only when current source + current test proof exists
[ ]      not implemented or not proven
ENHANCED implemented differently, proof exists
INTENTIONAL DIVERGENCE changed law, reason + test exists
UNSUPPORTED intentionally removed, support-boundary note exists
```

Do not mark a row complete just because:

```text id="ziyz4w"
- the old test existed
- the source has a similar class
- a comment says VERIFIED
- the behavior exists in a non-active path
- a registry defines data but no execution path consumes it
```

# Final recommendation

The checklist should be treated as **not yet validated**.

Immediate next step:

```text id="eh8r4f"
1. Downgrade all checked rows without SOURCE/TEST/PROOF.
2. Fix duplicate IDs.
3. Fix stale source/test paths.
4. Re-green rows in small batches by subsystem:
   - pipeline authority
   - combat legality
   - resource conservation
   - movement/occupancy
   - strategic cognition
   - social contracts
   - progression
   - world/determinism
5. Add validator to CI.
```

The source and tests may be in good shape, but the checklist is currently **not a reliable truth ledger**.
