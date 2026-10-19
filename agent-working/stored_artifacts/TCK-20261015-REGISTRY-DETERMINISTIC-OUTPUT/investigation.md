---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT
artifact_type: investigation
tags: [delivery, determinism, process-improvement]
---

# investigation — TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT

Source: RETRO-2026-W41 final note finding 1. `tools/generate_registry.py` wrote `# Generated: <utc now>` on every run, so a no-op regeneration still changed the file. Readers: grep over tools/, tests/, .github/ and the Makefile found only the writer and two tests, neither parsing it for meaning (`--check` compares parsed entries, so comments never mattered). Measured effect: see the replay in the plan and `replay_registry_merges.sh`.
