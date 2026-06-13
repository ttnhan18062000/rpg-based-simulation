# Implementation Sequence — doc-hardening

These tickets are mostly independent and can be implemented in parallel.
One ordering constraint exists: the engine runtime details ticket cross-links
with the core dirty state ticket (update intents → compaction). Implement those
two in either order but update the cross-links after both are done.

## Recommended order

```
[TCK-20260613-DOC-CORE-DIRTY-STATE]              ─┐
[TCK-20260613-DOC-MECHANICS-SUBCONTRACTS]         │ parallel batch 1
[TCK-20260613-DOC-TESTING-TRACEABILITY]           ─┘

[TCK-20260613-DOC-DOMAIN-CONTRACTS]              ─┐
[TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS]         │ parallel batch 2
[TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION]       │ (all mostly independent;
[TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS]    │  engine cross-links core)
[TCK-20260613-DOC-COGNITION-SUBSYSTEM]           ─┘ (should finish before domain
                                                       contracts are closed, since
                                                       memory/perception domains
                                                       must cross-link cognition/)

[TCK-20260613-DOC-HARDENING-EPIC]               ─── close after all children done
```

## Dependency notes
- TCK-20260613-DOC-COGNITION-SUBSYSTEM should complete before finalising TCK-20260613-DOC-DOMAIN-CONTRACTS — perception and memory domain docs must link to `docs/cognition/`.
- TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION should complete before finalising TCK-20260613-DOC-DOMAIN-CONTRACTS — opportunity providers doc must be cross-linked from adventure and motivation domain docs.
- TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS and TCK-20260613-DOC-COGNITION-SUBSYSTEM must coordinate on the intelligence/knowledge_model boundary — do not write these in isolation without reading both beforehand.

## Notes
- Run `make knowledge-index-update` after each ticket completes — do not batch.
- Run `make docs-registry` once after all tickets complete to update REGISTRY.yaml.
- All new docs must have correct frontmatter before epic is closed.
