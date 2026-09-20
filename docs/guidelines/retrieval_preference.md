---
status: active
layer: ai
authority: P2
audience: agent
---

# Retrieval Preference Order

`TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS`. Applies *after* CLAUDE.md's
mandatory Context Scan (`search_docs` → `graphify query` → registry, still a Hard Rule, still
runs first and is not narrowed by this doc) has already identified the target file(s) and
approximate location. This governs what happens next, once you know *where* to look and are
deciding *how much of it* to read.

## The preference order

1. **Symbol/reference search** — `graphify query "<symbol>"`, `grep`, or the Explore agent to find
   the exact definition site or call sites, rather than opening a file to scan it visually.
2. **Targeted line ranges** — once you know the symbol's location, `Read` with `offset`/`limit`
   around it, not the whole file.
3. **Dependency inspection** — follow imports/references only as far as the task requires,
   preferring ranged reads of the referenced symbol over opening the whole dependency.
4. **Full-file read** — the explicit fallback, not the default. Legitimate when:
   - reviewing an unfamiliar module end-to-end before making changes to it;
   - auditing a file for a corpus-wide property (every function has a docstring, every branch is
     tested, etc.) where a partial view can't establish the property;
   - the file is short enough that a ranged read would cost more round-trips than it saves (a
     ranged read of a 40-line file is not a win).

## The failure mode this trades against

**A ranged read that turns out to be insufficient must be widened immediately, not worked
around.** Concluding from a partial read — inferring the rest of a function's behavior, assuming a
class has no other methods that matter, or missing a sibling test/contract that a full-file read
would have surfaced — is a real and confirmed failure mode, not a hypothetical one. Under-context
(missing an active constraint, paired test, contract, or prior decision) is the risk this ordering
trades against over-context (reading more than the task needs); it is not a lesser risk. When
genuinely unsure whether a range captured everything relevant, read more — the preference order
above is a default, not a rule that overrides correctness.

## What this does not change

- CLAUDE.md's Context Scan and its ordering (`search_docs` → `graphify query` → registry, before
  grep/read) is unaffected — this doc governs retrieval *after* that scan, never a substitute for
  it.
- No gate, ratchet, or blocking check enforces this — it is guidance, not a mechanism. Agent
  monitoring measures read behavior (see `docs/agent-monitoring/schema.md`'s `tools` table, the
  `read_ranged` field) as a side effect, not as a compliance check.

## Related

- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  — the future epic this is a small, immediately-actionable slice of; its "Progressive disclosure"
  design principle is the same idea this doc applies today, without waiting for that epic's
  provider-agnostic infrastructure.
- `docs/agent-monitoring/schema.md` — `tools` table, `read_ranged` field (measures whether this
  guidance is actually being followed).
