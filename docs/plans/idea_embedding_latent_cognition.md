---
status: idea
layer: ai
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, embeddings, latent-space, cognition, personality, calibration, deferred]
---

# Idea: Embeddings & Latent Space for Entity Cognition

> **Maturity: IDEA** — Not scheduled. Consider at Phase 3+ (after E32 Campaign Runtime or E51 Chronicle).

---

## Problem

The current strategy-cognition-goal-action pipeline uses hand-tuned linear coefficients to translate personality traits into behavioral scores (e.g. `risk_multiplier = max(0.1, (1 + caution*0.8) - bravery*0.6)`). This has two weaknesses:

1. **Expressiveness**: linear terms poorly approximate the high-dimensional relationship between personality, situation, and goal preference. Calibration is slow and fragile.
2. **Life arc coherence**: personality evolution between ticks is a set of explicit mutation rules rather than an organic drift through a learned state space.

---

## Idea

Use embedding vectors and latent space representations to improve entity cognition — but only in the **offline authoring and calibration layer**, never on the runtime hot path.

### Where it helps

| Application | How |
|---|---|
| **Situation encoding** | Embed (personality + needs + social context + world state) into a vector; scoring becomes similarity to goal archetypes rather than hand-tuned formulas |
| **Life arc coherence** | Accumulated experience (events, wounds, betrayals, alliances) embedded so personality drift is movement in latent space, not explicit mutation rules |
| **Social memory** | Relationship vectors capture multi-party dynamics ("similar background, competing goals") better than a single trust float |
| **Calibration** | Use a small trained model to find scoring coefficients (e.g. E11D bravery weight) rather than grid-searching manually |
| **Narrative clustering** | Embed event sequences to find coherent arcs for the Chronicle (E51) — purely offline grouping |

### Why NOT at runtime

Two non-negotiable architectural constraints block hot-path use:

1. **Determinism**: `test_replay_determinism.py` requires bit-identical output from the same seed. Neural embeddings do not guarantee this across hardware or framework versions.
2. **Traceability**: the parity ledger and authoritative pipeline require explainable decisions. Latent space decisions are black boxes — incompatible with the audit and pipeline contract.

### The right boundary

```
Offline (allowed)          │  Runtime (blocked)
───────────────────────────┼──────────────────────────────
Inform scoring.py constants│  Goal selection
Cluster personality archs  │  Route scoring
Find coherent narrative arcs│  Tick-level decisions
Calibrate trait weights    │  Any hot-path inference
```

If ever used between-session (e.g. overnight personality evolution): fixed quantized weights + deterministic input encoding = deterministic output. Requires an explicit determinism proof before enabling.

---

## Natural Integration Points

| Epic | How embeddings fit |
|---|---|
| **E11D-SCORING-CAL** | Use embedding-based calibration to find bravery coefficient for ≥1.5× differential (recalibrated from an original ≥2× target — real 2× found unreachable, see `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`), instead of manual tuning |
| **E51 Chronicle** | Embed event sequences for narrative arc clustering and coherence scoring |
| **E43 Social Memory** | Latent relationship representation for multi-party social dynamics beyond trust float |
| **E62 Culture Drift** | Cultural embedding space where regions drift toward each other based on shared events |

---

## Open Questions

- What embedding model / dimensionality is appropriate for entity state vectors?
- How to enforce determinism if embeddings inform between-session state? (Fixed weights + serialized input hash?)
- Does latent-space personality drift need to be auditable? If so, what's the tracing strategy?

---

*Raised: 2026-06-20. Deferred pending Phase 3 completion.*
