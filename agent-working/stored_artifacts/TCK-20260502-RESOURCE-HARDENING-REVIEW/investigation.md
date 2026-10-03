---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260502-RESOURCE-HARDENING-REVIEW
artifact_type: investigation
tags: [resource, hardening, review]
---

# Investigation: Resource Hardening Review

## Findings
- `src_legacy/` and `tests_legacy/` are currently deleted in the working tree. Git shows them as deleted.
- The `logic_checklist_exhaustive_v2.md` has 1702 items but only ~3% are marked complete.
- Many items marked complete use `<!-- VERIFIED v2: ... -->` which is not machine-parsable proof as requested by the review.
- The `ResourceTransactionResolver` in `pipeline.py` currently uses a simple list scan for grouping, which can be broken by non-contiguous intents.
- Combat rewards currently duplicate gold/xp in both `CombatUpdate` and `ResourceTransferIntent`.

## Conflict Resolution Logic
The review suggests:
```python
source_key = f"{source_kind}:{source_id}"
```
This should be tracked during the `apply` phase of the pipeline.

## Ledger Validation
The ledger validator needs to parse:
```text
- [x] **[RPG-0001]** description <!-- ID: RPG-0001 SOURCE: path TEST: path PROOF: type -->
```
It should check if `SOURCE:` and `TEST:` files exist.
