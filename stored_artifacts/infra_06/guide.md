# Newcomer's Guide: Understanding "Hardening & Chaos Testing"

Welcome to the Simulation Infrastructure team! One of the most critical aspects of our engine is **Determinism**—the guarantee that the same input always produces the exact same output. 

As we scale to distributed AI workers and complex state transitions, we need to ensure the engine is "unkillable." This is where **Hardening and Chaos Testing** comes in.

---

## 1. The Challenge: "Invisible Bugs"

In a complex simulation, bugs don't always cause a crash. Instead, they might cause a **Desync**:
- **Scenario**: A network packet is dropped, or an AI worker takes too long to respond.
- **Problem**: If the engine isn't hardened, it might "stall" waiting for that result, or worse, process the next tick with partial data, breaking the history of the world.
- **Goal**: The engine must be robust enough to handle "chaos" without losing its deterministic integrity.

---

## 2. Our Defense: Property-Based Testing (Fuzzing)

We don't just write tests for "when things work." we use **Hypothesis** to test "everything at once."
- **How it works**: Instead of testing `Combat(Level 1 vs Level 1)`, we tell the computer: *"Generate any two entities with any valid stats you can dream of and fight them."*
- **The Result**: This finds "mathematical overflows" or "impossible states" (like negative health or infinite speed) that a human developer would never think to test manually.

---

## 3. Chaos Experimentation: Fault Injection

We intentionally break the system to see how it handles it.
- **Fault Injection**: We add a `chaos_mode` that randomly "kills" AI worker results or "corrupts" a data packet.
- **Graceful Degradation**: When a result is dropped, the engine shouldn't crash. It should simply say, *"I haven't heard from this entity's brain this tick. I will make them IDLE for one tick and try again next time."*

---

## 4. Why are we doing this? (The Goal)

We want to reach a state where the simulation can run for **months** without a single desync or crash, even if the underlying hardware or network is unstable. 

**That is Hardening.**

---

## 5. Summary for Developers

| Component | Metaphor | Implementation |
|-----------|----------|----------------|
| **Fuzzing** | "Throwing everything at the wall to see what sticks." | `tests/test_invariants.py` |
| **Fault Injection** | "Cutting the power cord during a tick." | `src/engine/worker_pool.py` |
| **Invariants** | "The Laws of Physics that must never break." | `src/core/models.py` |
| **Chaos Mode** | "Simulating a storm in the datacenter." | `src/config.py` |
