# Investigation — TCK-20260619-E43-SOCIAL-MEMORY

## Summary

Per-episode reputation is solid (SOC-193: public reputation and private relationship/bond are separate state). `SocialMemoryService` (`src/systems/social_systems/memory.py:L6`) handles per-tick place attachment and nemesis promotion — it does NOT handle cross-episode transfer. This epic adds the serialization/deserialization layer that bridges episodes via `CampaignState.NarrativeLedger`.

## Key Findings

### What Already Exists

**SocialMemoryService** (`src/systems/social_systems/memory.py:L6`):
- `tick_place_attachment()`: passive attachment increment per tick
- `check_nemesis_promotion()`: upgrades enemies with grudge ≥ 3.0 to nemesis_ids
- Does NOT have: cross-episode export, import, decay, faction memory

**EntityState social fields** (inferred from SocialUpdate at `src/core/updates.py:L273`):
- `place_attachment: Dict[str, float]` (region → attachment score)
- `nemesis_ids: Set[int]`
- `grudge_history: Dict[int, float]` (entity_id → grudge score)
- Reputation is per-entity per-faction: likely `faction_reputation: Dict[str, float]`

**D01 audit** says [MISSING — BLOCKED]: "Nothing persists betrayal/rescue/cooperation history across episodes." Requires E32 NarrativeLedger as storage layer.

**Existing compliance**: SOC-193 in `docs/compliance/checklist.md` — public reputation separate from private relationship. Cross-episode transfer must maintain this distinction.

### What Is Missing

1. `SocialMemoryRecord` — durable cross-episode model: per-entity serialized reputation delta, interaction_history
2. `SocialMemoryExporter` — end-of-episode hook: reads entity social state, computes deltas, writes to CampaignState
3. `SocialMemoryImporter` — start-of-episode hook: reads CampaignState, applies legacy reputation to entity initial state
4. Decay logic: reputation scores decay toward neutral over episodes; grudges decay slower than cooperations
5. Faction memory: faction hostility is collective — survives even if all known members die
6. Consequence events: `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`

### Architecture Note

Exporter/Importer are campaign orchestration hooks, NOT embedded in `AuthoritativeState`. Location: `src/domains/campaigns/social_memory.py`. They hook into `CampaignOrchestrator._advance_state()` (E32C) as post-episode and pre-episode callbacks.

**Decay rates** (design intent, not arbitrary):
- Friendship half-life: 3 episodes (60% retention per episode)
- Grudge half-life: 7 episodes (90% retention per episode)
- Betrayal: grudge delta = +5.0 (slow decay) vs. cooperation: reputation delta = +1.0 (faster decay)

**Faction memory model**: separate from entity memory — `faction_social_memory: Dict[str, float]` maps `entity_id → faction_hostility_score`. This persists even when specific NPC members die because the faction-as-collective tracks it.

### Related Docs
- `docs/simulation/domains/social_systems_contract.md` (add SocialMemoryRecord, exporter/importer)
- `docs/parity_ledger/social_narrative.yaml` (add cross-episode entries as verified)
- New: `docs/simulation/domains/social_memory_contract.md`
