# Test Plan — TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING

## New tests

`tests/unit/social/test_domain_7_social.py`:

- `test_find_group_for_contract_returns_matching_group` — two groups in state, one with
  `contract_id="rec_contract_1"`, one unrelated (`contract_id="other_contract"`). Asserts the
  lookup returns the correct group (`id == 100`), not the unrelated one.
- `test_find_group_for_contract_returns_none_when_no_group_formed` — a group exists but with a
  different `contract_id`; querying for a contract id that formed no group returns `None` rather
  than raising or matching incorrectly.

## Regression scope

- `tests/unit/social/test_domain_7_social.py` — direct module tests, includes the two new cases.
- `tests/unit/domains/cooperation/` — cooperation-domain unit tests (party cohesion / social
  scoring reads `GroupRecord`).
- `tests/integration/domains/cooperation/` — integration coverage for the cooperation phase,
  including `test_phase7_cooperation_phase.py` which exercises `GroupSystem` through a real tick.
- `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` — imports `GroupSystem`,
  campaign-level integration.

## Results

- `tests/unit/social/test_domain_7_social.py`: 7 passed (5 pre-existing + 2 new).
- `tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/unit/social/
  tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py`: 336 passed, 0 failed.

No regression. New function is purely additive (no existing call site touched), consistent with
zero failures outside the two new tests.
