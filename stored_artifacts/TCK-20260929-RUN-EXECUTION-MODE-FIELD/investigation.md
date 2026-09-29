# Investigation — TCK-20260929-RUN-EXECUTION-MODE-FIELD

The ticket itself already names every reader and writer this touches (drafted by
agent-working-design after direct code review). This file records the completed consumer audit
and the design decisions made while implementing.

## Consumer audit (see ticket's own Implementation Notes for the full per-reader writeup)
All 6 known readers of the run `workflow` field read it via `.get("workflow")` (or, for
`vocabulary.infer_workflow`, don't read it at all — infers from `run_id` prefix). None reject an
unrecognized extra key. `record_run.py`'s own `validate_record()` has no `additionalProperties`
restriction — confirmed directly by reading it, not assumed.

## Design decision: per-group avg duration, not a shared blended computation
"Pipeline avg duration excludes hand and unlabelled runs" is satisfied by computing each
group's average from only that group's own `duration_s` values (a `defaultdict(list)` bucketed
by resolved `execution_mode`, then one avg per bucket) — structurally correct by construction,
not a filter bolted onto the existing shared-average code path.

## Design decision: legacy `workflow: "hand-orchestrated"` (W36) is "unlabelled", not "hand"
Confirmed against the ticket's own Out of Scope line ("Inferring 'hand' for legacy rows... is not
built here") — `execution_mode` presence is the only signal checked, `workflow`'s value is never
consulted for this classification. Verified with a dedicated test
(`test_legacy_hand_orchestrated_workflow_value_lands_in_unlabelled_not_hand`) and against the real
corpus (which does contain these 20 W36 rows).

## Real-corpus state at implementation time
Ran `generate()` over the full real corpus before any writer change: all runs show as
"unlabelled" (zero existing rows carry `execution_mode`, as expected — this is a brand-new
field). Confirms the migration path is purely additive going forward; no historical row changes.
