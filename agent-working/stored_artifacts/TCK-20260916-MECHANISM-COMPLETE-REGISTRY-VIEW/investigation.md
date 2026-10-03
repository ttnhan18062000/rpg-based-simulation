---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW

## Trigger

Second user request, via peer: list all mechanisms classified by verified/not verified, rather
than the ranked list showing only unverified ones. Real gap: `mechanism_verification_view.md` has
every mechanism but no priority; `mechanism_priority_view.md` has priority but only the unverified
subset, truncated at 25. Neither answers "what matters most, and do we know it works" in one read.

Separately, peer's own earlier attempt to answer this by hand-authoring a published artifact
(embedding the mechanism count, ranked table, and ledger directly) was caught and reverted before
landing — a hand-maintained surface duplicating generated data, which would go stale the moment
`mechanisms.yaml` changed (which the dependency-edge ticket then did, the same day). The fix
belongs in a generated view.

## Work, and why it was blocked mid-flight

The generator (`tools/generate_mechanism_registry_view.py`), the underlying function
(`all_mechanisms_combined_view()`), and its tests were drafted early, against the registry's
believed-75-mechanism state. Before landing, the registry's own node set was independently found
incomplete (`TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS`) — publishing a view titled
"complete" against a known-incomplete node set would have asserted something false, exactly the
failure this epic exists to catch in other people's documents. Work was held, uncommitted, until
that ticket (and its own follow-on, `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`) landed.

## Resumption

Once the registry reached its final 89-mechanism, `implemented_by`-bound state, the drafted
generator/tests were regenerated against it directly — no logic changes were needed, only a fresh
`make mechanism-registry-view` run and a docstring/prose pass removing now-stale "75"/"67"
references. A "node-set note" was added to the rendered output itself (not just code comments)
stating that every earlier published figure was computed against the incomplete set and is
superseded.

The generated HTML page (Scope item 2) was built fresh in this same pass:
`tools/generate_mechanism_registry_html.py`, reusing `all_mechanisms_combined_view()` so it can
never independently disagree with the markdown view. It links to the epic's own Completion
Summary for measured findings rather than restating them, and reuses the atlas's own CSS palette
for visual consistency with the corpus's other artifacts.
