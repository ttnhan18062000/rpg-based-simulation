---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
phase: plan
date: 2026-08-10
tags: [documentation, cognition]
---

# Plan — TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

No `src/` changes (hotfix tier, doc-only, per ticket's own Out of Scope). Per-file decisions,
following the repo's own real `docs/archive/` retirement convention
(`status: archive`, `authority: P2`, `audience: historical`, `original_date: unknown`):

## Steps

1. Create `docs/archive/systems/` (new subfolder, matching the existing per-source-directory
   pattern already used by `docs/archive/combat/`, `docs/archive/core/`, `docs/archive/world/`).
2. Move all 8 confirmed-stale files there, rewriting each one's frontmatter to the archive
   convention and prepending a short pointer note citing its real current replacement(s) (or
   disclosing the gap where none exists, per investigation.md's replacement table).
3. Rewrite `docs/systems/README.md`: keep only `faction_contract.md`/`strategic_cognition.md`
   links, add a note pointing to `docs/archive/systems/` for the retired set with a one-line
   reason (architecture predates current `src/` structure).
4. Regenerate `docs/REGISTRY.yaml` (frontmatter/status changed on 9 files).
5. Verify `search_docs`/the knowledge index no longer surfaces the archived files as if-current
   (or, if it still does since archive docs remain indexed, confirm their `status: archive` +
   `audience: historical` frontmatter is enough for a reader to recognize them as non-authoritative
   at a glance — matching how every other `docs/archive/*` file already behaves).
6. Finalize per hotfix tier.
