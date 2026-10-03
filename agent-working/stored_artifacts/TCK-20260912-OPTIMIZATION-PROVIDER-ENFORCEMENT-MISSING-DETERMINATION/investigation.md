# Investigation — TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION

## Real finding: the module targets a calling convention that doesn't exist

`ProviderBudgetEnforcement.execute_call()` expects `entity_id`/`region_id` keyword scope arguments
on every wrapped call. The real, live provider call sites don't use that shape:
`ResourceOpportunityProvider.get_opportunities()` (a real, called-in-production provider, per the
origin investigation's own confirmed consumer paths — `kernel.py`, `adventure_scorer.py`,
`action_intent.py`, `resolver.py`, `generator.py`) takes a full `entity` object and derives its own
region internally. The module was written against a calling convention this codebase doesn't use —
the same shape as `ENABLE_COOPERATION`/`ENABLE_SOCIAL_COOPERATION` and `shop_stock` naming nothing
in the sibling `ORPHANED-CAPABILITY-DETERMINATION`: an artifact describing a system that either
moved on or never arrived.

Confirmed (per this ticket's own origin) no live rate-limiting or call-budget mechanism exists at
any scope for provider calls: `src/observability/performance/{models,profiler}.py`'s
`provider_call_count` is a passive metrics counter only; `src/api/admission_control.py`'s real
token-bucket limiter operates per-API-client, a different scope entirely.

## Overlap with `BUDGET-MANAGER-MISSING-DETERMINATION`

Both tickets ultimately ask a version of "is provider-call volume a real, observed risk." Answered
once, here: no evidence of an observed problem, and real providers do run live and uncapped today.
`ORPHANED-CAPABILITY-DETERMINATION`'s own capability 3 (`degradation.py`'s `get_provider_cap()`)
inherits this same finding rather than being independently re-investigated.

## Disposition (user decision, routed via peer): delete, record the capability

Same reasoning as `ORPHANED-CAPABILITY-DETERMINATION`'s capabilities 1/2/4: an artifact of a
calling convention the codebase doesn't use, not a shortcut to a real capability. Deleted; the
underlying idea (provider call-rate limiting) is recorded as a real, worth-considering future
capability in `docs/plans/design_enhancement/performance_milestones_epic.md`, explicitly noting a
fresh implementation would need its own signature design against real provider call sites, not a
revival of this one.

## Non-import-reference guard

`.github/workflows/*.yml`/`Makefile`: zero hardcoded references to `provider_enforcement.py`,
`ProviderBudgetEnforcement`, or its dedicated test file
(`tests/unit/world/providers/test_phase10_provider_budget_enforcement.py`). Confirmed the
containing test directory (`tests/unit/world/providers/`) retains other real test files
(`test_resource_opportunity_provider.py`) — not left hollow.
