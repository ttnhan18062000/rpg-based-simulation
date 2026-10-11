---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT
artifact_type: plan
date: 2026-10-09
tags: [architecture, testing]
---

# Plan

`visual_assets/review/key_usage.py` + `python -m visual_assets.review key-usage` (report only, exit 0). Scan literals in `frontend/src` and `src` (skip tests, fixtures, node_modules); families come from the registry; findings unknown / unreferenced / adopted_unreleased / fallback_only plus dynamic references; app vs harness (the isolated pages). Registry via the read-only `catalog` layer (added to the review boundary's allowed store layers), adopted keys via `records`, latest candidate from the committed manifests. Docs in `store_contract.md`.
