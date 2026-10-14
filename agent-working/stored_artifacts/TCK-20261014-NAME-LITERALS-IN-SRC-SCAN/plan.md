---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261014-NAME-LITERALS-IN-SRC-SCAN
artifact_type: plan
tags: []
---

# plan — TCK-20261014-NAME-LITERALS-IN-SRC-SCAN

1. Write `tools/name_literal_scan.py`: an AST scan of src/ that loads the content catalogs and the world-declared ids, and lists every string literal compared against or used to look up a content id.
2. Run it on rpg-next 3696d0402 and store the one table as the investigation.
3. Fix nothing; the table goes to the designer (D56).
