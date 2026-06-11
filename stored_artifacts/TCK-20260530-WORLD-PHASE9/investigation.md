---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE9
artifact_type: investigation
tags: [world, phase9]
---

# Investigation - Compiler Integration Hardening (Phase 9)

## Current Hardcoded Defaults Analysis
In `src/worldbuilding/compiler.py`:
- **Faction Gold**: Defaults to `1000.0`. If `context` is provided and the faction is registered, it overrides it. We should ensure this pattern is fully supported and matches `CompileContext` structure.
- **Resource Harvest Ticks**: Defaults to `10`. Overridden if `context` is provided and the resource spec ID is found.
- **Building Durability**: Defaults to HP `500` and Max HP `500`. Overridden if `context` is provided and building spec ID is found.
- **Entity Stats**:
  - `hp` defaults to `100`
  - `max_hp` defaults to `100`
  - `atk` defaults to `10`
  - `attack_range` defaults to `1`
  - `readiness` defaults to `100.0`
  - `def_stat` defaults to `0` (Wait, in `compiler.py` it's not even set! But wait, `V2EntityBuilder` doesn't explicitly accept def, or does it? Wait, let's look at `compiler.py` line 257:
    ```python
    .combat(
        hp=hp,
        max_hp=max_hp,
        atk=atk,
        attack_range=attack_range,
        alive=True,
        readiness=readiness
    )
    ```
    Ah! The legacy builder combat setup in `compiler.py` doesn't pass a `def` parameter, or does it? Wait, does `def_stat` exist on the `ResolvedEntityProfile`? Let's check `ResolvedEntityProfile` definition in `src/worldassembly/models.py`:
    ```python
    def_stat: int = Field(..., alias="def")
    ```
    Wait, does `V2EntityBuilder.combat` support `def_stat` or `def`? Let's search for `V2EntityBuilder` in the codebase.
