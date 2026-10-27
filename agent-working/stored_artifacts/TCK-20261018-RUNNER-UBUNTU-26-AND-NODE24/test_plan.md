---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24
artifact_type: test_plan
tags: [platform, delivery]
---

# Test plan: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| deploy-docs.yml changes only the setup-node major and node-version | static | diff check | none: criterion from the ticket AC | `git diff` shows exactly 2 changed lines; YAML parses | `git diff origin/main -- .github/workflows/deploy-docs.yml`; `python3 -c "import yaml;yaml.safe_load(open('.github/workflows/deploy-docs.yml'))"` |
| tests/static pass, including test_ci_step_summary_reporting | static | test run | none: criterion from the ticket AC | all pass | `.venv/bin/python3 -m pytest tests/static -q --basetemp=<own>` |
| roles diff moves exactly one path; route returns platform; cards in sync | static | route + generator check | none: criterion from the ticket AC | `route.py` prints platform; cards regenerate with no further diff; sessions validate 0 findings | `python3 -m tools.sessions.route .github/workflows/deploy-docs.yml`; `PYTHONPATH=. python3 tools/sessions/generate_agents.py`; `PYTHONPATH=. python3 tools/sessions/validate.py` |
| roles/cards tests and registry drift | static | test run | none: criterion from the ticket AC | all pass | `pytest` over the sessions/roles tests in tests/unit/tools and tests/tools, plus the registry drift test |
| ACTIONS-MAJORS-COMBINED closable or its gap named | static | evidence check | PR #588 body and comments, run artifacts | each evidence item shown or named missing | `gh pr view 588`, `gh run view`, artifact listing; `done_checker_static.py --ticket-id TCK-20261014-ACTIONS-MAJORS-COMBINED` |
| publish-images first run on 26 (after 2026-10-19) | CI observation | run log read | Actions API | image name/version, step conclusions, annotations recorded | `gh api` on the run, jobs and annotations |
