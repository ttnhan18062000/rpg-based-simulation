# Test Plan — TCK-20260616-DOCS-READABILITY-PILOT

Documentation-only change; no automated test suite applies. Verification is structural:

1. **Residual language sweep**: `grep -niE '\bphase[ _-]?[0-9]+|\bmilestone[ _-]?[0-9]+'` against each edited file — must return zero matches.
2. **Architecture-meaning preserved**: manually confirm the genuine pipeline-stage references (Cognitive Pipeline's Strategic Derivation/Resolution stages, authoritative pipeline's Objective Reward stage) still convey *when in the tick* something happens, just without a bare number.
3. **No broken links**: `grep -rn '<basename>'` across `docs/` for each edited file before editing, to catch any incoming anchor-specific links that heading changes would break. None found for the 4 pilot files.
4. **Index freshness**: `make knowledge-index-update` run after edits, confirm it reports the edited files as re-embedded.

All four checks passed for this pilot batch (see investigation.md for detail).
