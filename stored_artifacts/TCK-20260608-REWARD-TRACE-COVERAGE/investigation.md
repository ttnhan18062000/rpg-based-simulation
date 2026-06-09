# Investigation — TCK-20260608-REWARD-TRACE-COVERAGE

## Findings
- resolve_attack: had REWARD_SOURCE, missing REWARD_CATEGORY
- resolve_skill_usage: had no trace dict at all; CombatUpdate returned without trace=
- resolve_multi_attack: had REWARD_SOURCE, missing REWARD_CATEGORY
- CombatUpdate.trace: Dict[str, float] typed but accepts Any in practice (source strings already stored there)
- resolve_attack computes damage internally from ATK/DEF; no `damage` kwarg
- V2EntityBuilder is the correct factory for test entities
