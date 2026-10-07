---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK
artifact_type: test_plan
tags: [performance, cooperation, regression]
---

# Test plan

New: `tests/unit/domains/cooperation/test_pending_offer_index.py`. Existing, rerun: `tests/unit/domains/cooperation` and the CI jobs' directory lists (unit-core, unit-domain, unit-infra, integration plus integrity plus architecture). Gates: code-health ratchet, mypy baseline, frontmatter and registry clean-export check.

## Proof Plan
- **Level**: unit (lookup choice) and corpus (canonical hash), plus a phase-level bench.
- **Proof kind**: differential test against the verbatim old scan with a disabling control; canonical-hash equality before and after on six worlds under `audit_mode`; before and after bench.
- **Oracle source**: the pre-index implementation of `find_pending_incoming_offer` (its docstring ordering: offering entity id, then contract id) and the baseline hashes at `f99cb0c6c`.
- **Expected effect**: identical hashes and decision counts; the `cooperation` phase on `movement[5000]` falls from about 11 s to well under 100 ms per tick.
- **Selected commands**: `pytest tests/unit/domains/cooperation`; the CI directory lists; `coop_hash.py` on the six worlds (baseline vs fix); `bench.py 5000 3` before and after.
