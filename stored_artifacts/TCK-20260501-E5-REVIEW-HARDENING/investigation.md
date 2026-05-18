# Investigation: E5 Review Implementation

## 1. Proof Governance and Ledger Validator
- Current script: `scripts/protocol_validator.py`.
- Current checklist: `logic_checklist_exhaustive_v2.md`.
- Review says: "many checklist comments say: `<!-- VERIFIED v2: ... -->`, but that is not the same as a validator that proves the source/test exists and still covers the behavior."
- I need to check how `protocol_validator.py` currently works.

## 2. Final-Gate Proof
- Current tests: Need to find where the "final gate" tests are.
- Review says: "Your final-gate tests create a passing proof bundle inside the test fixture."
- I suspect `tests/certification/` or `tests/engine/test_hardening_e5.py`.

## 3. Resource Transaction Logic (Race Cases)
- Current resolver: `src/engine/pipeline.py`.
- Review says: "two actors targets same source... both can appear valid before apply."
- I need to see how `ResourceTransactionResolver` processes intents.

## 4. Transaction Grouping
- Current grouping: `src/engine/pipeline.py`.
- Review says: "pipeline groups resource intents by scanning consecutive intents with the same `group_id`."

## 5. Combat Reward Path
- Current models: `CombatUpdate` in `src/core/updates.py`.
- Review says: "`CombatUpdate` still contains `xp_gain` and `gold_gain`, while also carrying `resource_transfers`."

---

## Action: Examine `scripts/protocol_validator.py`
Let's see what the current validator does.
