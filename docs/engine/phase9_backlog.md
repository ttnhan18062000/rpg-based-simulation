# Phase 9 Backlog: Strategic & Social Cognition

This document defines the authoritative row set for Phase 9, derived from the [Legacy Replacement Ledger](../engine/legacy_replacement_ledger.md).

## Row Set (10 items)

| Ledger ID | Feature | Original Source | Closure Condition |
| :--- | :--- | :--- | :--- |
| LEG-RPG-116 | Strategic pivot (Danger) | `integration/strat/test_danger.py` | Contract test: entity pivots project on regional danger event |
| LEG-RPG-117 | Scar detection | `integration/strat/test_scar.py` | Contract test: entity detects and investigates nearby scars |
| LEG-RPG-119 | Betrayal (Avenge) | `integration/strat/test_avenge.py` | Contract test: betrayal turning point adds Avenge directive |
| LEG-RPG-123 | Refutation drops trust | `ai/test_refute.py` | Contract test: failed lead reduces source trust score |
| LEG-RPG-125 | Contradiction degrades cert | `ai/test_cert.py` | Contract test: contradicted leads lose certainty |
| LEG-RPG-141 | Dynamic Quests | `unit/systems/test_quest.py` | Contract test: quest generation from scar/blocker state |
| LEG-RPG-144 | Innate Talents (Genetics) | `unit/core/aspects/test_genetics.py` | Contract test: talent multipliers from genetic profile |
| LEG-RPG-145 | Skill scaling (Types) | `unit/core/aspects/test_scale.py` | Contract test: physical/magical/elemental scaling |
| LEG-RPG-150 | Belief cycle (Rumors) | `unit/ai/test_belief.py` | Contract test: rumor decay, belief refresh, threat estimation |
| LEG-RPG-151 | Narrative memory logging | `unit/ai/test_narrative.py` | Contract test: turning points persist and bias future behavior |

## Excluded from Phase 9

- **Phase 10 Compatibility**: CLI/WebSocket/Telemetry parity (LEG-SYS-012..016).
- **Phase 10 Progression**: Combat rewards, veterancy, breakthroughs, class gear (LEG-RPG-126..134).
- **Phase 10 Advanced Combat**: Exhaustion, wound/scar permanence, stamina drain (LEG-RPG-153, 158).
- **Phase 10 Social Depth**: War state transitions, territory conquest/liberation, recruitment haggling negotiation rounds.

## Atomic Checklist Items (Part 1 §Strategic + §Social)

In addition to the 10 ledger rows, Phase 9 must close these unchecked atomic items:

### Strategic Mind (8 items)
1. Project switching uses interruption resistance / margin logic
2. Leads are retained under profile-specific bandwidth limits
3. Concerns are retained under profile-specific intake limits
4. Detours are suggested from blockers and leads within breadth/depth limits
5. Rejected/tested leads are suppressed to avoid blind retries
6. Event interpretation can mutate directives, projects, concerns, and source trust
7. Knowledge remains uncertain until resolved
8. Cognition graph export exposes persisted strategic state without becoming source of truth

### Social (8 items)
1. Private betrayal history can override public recruiter reputation
2. Social learning updates familiarity/trust-like bonds from interaction evidence
3. Social contracts and obligations are explicit strategic objects
4. Breaking or honoring contracts has persistent consequences
5. Public reputation is distinct from private narrative meaning
6. Turning points and interpreted life events feed future strategic and social behavior
7. Party/group cooperation is purpose-driven, not just proximity clustering
8. Recruitment evaluates trust, debt, greed, capability fit, and prior trauma
