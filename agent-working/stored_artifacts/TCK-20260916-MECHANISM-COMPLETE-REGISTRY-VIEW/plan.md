---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW

## Steps

1. Wait for `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` and
   `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` to land (blocking dependency).
2. Regenerate the already-drafted `mechanism_registry_view.md` against the final 89-mechanism
   registry; remove stale "75"/"67" references from the generator's own docstrings and comments.
3. Add an explicit "node-set note" to the rendered output stating every earlier published figure
   is superseded.
4. Build `tools/generate_mechanism_registry_html.py`: reuse `all_mechanisms_combined_view()`,
   reuse the atlas's own CSS state-color palette, link to (never restate) the epic's Completion
   Summary.
5. Add the `mechanism-registry-html` Makefile target.
6. Write tests for the HTML generator mirroring the markdown view's own test shape (`--check` mode,
   staleness detection, make-target invocation, real-file-up-to-date regression).
7. Revisit and record the AC #5 truncation decision for `mechanism_priority_view.md` in its own
   generator docstring.
8. Run the full scoped suite, including with `graphify-out/` genuinely moved aside and restored.
9. Finalize alongside `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` since both landed in the same
   pass.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1. New markdown view, all mechanisms, sorted, counts stated | `generate_mechanism_registry_view.py::render()` |
| 2. New HTML page, generated, `--check` mode | `generate_mechanism_registry_html.py` |
| 3. HTML links to epic findings, never restates | explicit test (`test_render_links_to_epic_ticket_rather_than_restating_findings`) |
| 4. Other two views unmodified in structure/purpose | no changes to their generator logic, only their content via the registry's own growth |
| 5. Top-25 truncation explicitly revisited | `generate_mechanism_priority_view.py` docstring |
