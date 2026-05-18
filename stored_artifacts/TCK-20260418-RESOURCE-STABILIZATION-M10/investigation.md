# Investigation: Milestone 10 Documentation and Playbook

## Objective
Establish the final project lawbook and automated integrity checks to protect the engine from future decay.

## 1. Documentation Indexing
There are currently ~25 documents in `docs/engine/`. 
- **The "Lawbook"** will serve as the top-level index and summary.
- **Milestone Contracts** will be linked as technical specifications.

## 2. Integrity Verification (Automation)
We can use a simple python script (or pytest) to crawl `docs/engine/` and verify:
- **File Presence**: Are all 10 core contracts there?
- **Section Compliance**: Do they all have "Purpose" and "Non-Goals"?
- **Link Integrity**: Do the cross-references work?
- **Terminology Jail**: Search for "Universal Performance", "Maximum speed", or other forbidden vanity language.

## 3. Playbook Structure
The playbook will be the most critical file for *new* contributors.
Sections:
- "The Authoritative Filter": How to decide if data belongs in State.
- "The Budget Contract": How to declare memory/CPU requirements for a new feature.
- "The TDD Loop": Contract -> Implementation -> Scenario.
- "Shedding Priority": How to make a feature degradable.

## 4. Contributor Templates
We should provide a `.github/PULL_REQUEST_TEMPLATE.md` (or similar) that forces users to answer:
- Is this state authoritative?
- What is the memory overhead?
- Does it respect the governor?
