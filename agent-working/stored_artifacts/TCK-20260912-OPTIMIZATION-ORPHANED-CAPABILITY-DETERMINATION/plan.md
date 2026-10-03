# Plan — TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION

Delete `degradation.py`, `cache_strategy.py`, `dirty_scheduler.py`, `trace_governor.py` in full
(superseded cores included, per the ticket's own Scope) and their dedicated test files. Preserve
any independent, non-redundant test coverage found riding along (found one instance —
`test_degraded_fallback.py` — edited surgically, not deleted). Correct
`admission_control.py`'s illustrative-reference comments. Record the 3 structurally-real capability
ideas (provider rate-limiting, per-category budget enforcement, cross-tick dirty drain,
repeat-summarization) in `docs/plans/design_enhancement/performance_milestones_epic.md`, the real
current performance-initiative planning doc — not the deferred-tuning register, per peer's explicit
instruction that this is for ideas, not numbers.

Shared with the sibling tickets' own deletions (`budget_manager.py`, `provider_enforcement.py`) —
one PR, one capability-preservation section, since peer explicitly asked for the package-level
conclusion to read as one finding with eight instances, not eight separate outcomes.
