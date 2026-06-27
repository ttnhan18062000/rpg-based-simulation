# Plan — TCK-20260627-P1E-DOMAIN-INVENTORY

## Objective
Create `docs/audits/D19_domain_phase_inventory.md` — a D02-equivalent inventory of all
37 domain pipeline phases in `pipeline.py:refine()` and 15 sub-phases in
`world_dynamics.py:resolve_dynamics()`.

## Approach

### Step 1: Write D19 document
- Follow D02 format: frontmatter, Dimension Profile, What this answers, Classification
  Method, per-section inventory tables, Summary, Related Dimensions.
- Organize pipeline phases into groups matching pipeline.py section comments.
- Each phase row: Phase ID, Phase Name, Class/Service, File Path, Wiring Status, Description,
  Suggested Acceptance Criterion.
- World dynamics sub-phases in a separate section, split by cadence behavior.
- Wiring status vocabulary: `active` (always runs), `feature-gated` (FeatureMode flag),
  `cadence-gated` (runs on cadence tick only), `direct-call` (not via run_phase mechanism).

### Step 2: Update REGISTRY.yaml
- Add D19 entry immediately after D18 entry.
- Fields: `type: doc`, `path`, `title`, `status: active`, `layer: architecture`,
  `authority: P1`, `audience: agent`, tags.

### Step 3: Run make knowledge-index-update
- Ensures the new doc is indexed and discoverable by search_docs.

## Unresolved Questions
None. Investigation is complete. All source file paths are confirmed on disk.

## Deviations
None yet.
