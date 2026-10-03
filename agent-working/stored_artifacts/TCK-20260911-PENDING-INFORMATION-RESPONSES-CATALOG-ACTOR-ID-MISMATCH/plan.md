# Plan — TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

1. Re-verify the premise empirically (done, see investigation.md) before writing any code.
2. Extract `WorldCompiler.compile()`'s own inline `target_population_id → actor_id` resolution
   (both `pending_information_responses` and `pending_self_model_information_events`) into a
   shared `WorldCompiler.resolve_pending_information(entities, ...)` staticmethod, parameterized
   on the entities dict — one sanctioned resolution implementation, not a duplicate.
3. Update `compile()` to call the new shared method against its own `entities` (behavior-preserving
   refactor, confirmed via the full pre-existing `test_world_compiler.py` suite).
4. Thread both fields into `CampaignOrchestrator._build_initial_state()`'s two branches, each
   resolving against that branch's own real entities dict (fresh catalog roster for episode 0,
   reconstructed survivor roster for episode N>0) — never reusing `compile()`'s own resolved
   values.
5. Tests proving the resolved entity is the intended one (not just non-empty), per the ticket's
   own acceptance bar — see test_plan.md.
6. Update the one pre-existing test that asserted the old "deliberately empty" behavior.
7. Full regression, close the ticket.
