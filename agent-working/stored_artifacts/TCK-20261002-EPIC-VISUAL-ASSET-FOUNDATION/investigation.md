---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION
artifact_type: investigation
tags: [mcp, architecture, documentation]
---

# Investigation (roll-up of the children's findings) — TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION

- `search_docs` and `graphify query` were consulted at the start of every child and returned nothing relevant for `visual_assets/`; the findings below come from direct reads and from experiments against the pinned Aseprite 1.3.18.6.
- **Aseprite facts that shaped the design:** the file format spec matches what Aseprite writes; layers, frames, cels and tags are exactly countable from chunk headers; the palette size Aseprite reports after loading equals the stored count except for an all-opaque-black palette, which it rebuilds from the pixels (so intake quarantines it as unverifiable instead of guessing).
- **Trust boundaries found while building:** the quarantine and review folders are gitignored and writable by any local process, so `adopt` re-renders itself and checks the image the human opened instead of trusting stored files; a producer preview cannot be trusted to depict its source, so the store renders the source; a revocation could be sidestepped through a second intake of the same bytes, so adoption compares the source hash across all assets.
- **Identity decisions:** artifacts are identified by decoded pixels (`pixels-v1`) because PNG bytes are not stable; intake ids cover all three files; handoff ids cover `package.json`; an approver edit is detectable only because records carry hashes of the records they point at.
- **Process findings:** a test without isolation once wrote into the real `~/.cache` workspace (removed, fixed); an uncapped combined test run was OOM-killed once, after which every suite ran separately under a memory cap; `origin/main` moved the agent-working paths mid-epic and was merged prefix-only.
