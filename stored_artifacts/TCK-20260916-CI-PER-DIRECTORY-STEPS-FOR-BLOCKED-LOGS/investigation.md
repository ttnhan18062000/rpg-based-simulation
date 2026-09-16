# Investigation — TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS

## The problem

`Unit · infra / observability` runs 17 test paths (~2,700 tests) in a single `Run` step. When it
fails and raw logs are unreachable (this environment's Fortinet TLS block on
`*.blob.core.windows.net`, confirmed repeatedly this session via
`echo | openssl s_client ... | openssl x509 -noout -subject -issuer` showing
`O = Fortinet, CN = Fortiguard SDNS Blocked Page`), nothing identifies which directory — let
alone which test — failed. Check-run annotations give only `Process completed with exit code 1`.

## The technique, verified independently this session

Step-level conclusions remain readable via `gh api repos/:owner/:repo/actions/jobs/{id}` even when
logs are blocked. Confirmed directly against this repo's own real CI, unprompted by this ticket:
diagnosing the unrelated `deploy` job failure (`TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW`)
localized the failure to step 6 `Configure Pages` (with `Build: success` and later steps
`skipped`) via step conclusions alone — no log ever read, leading directly to the real cause
(GitHub Pages not enabled).

`if: always()` is load-bearing: without it, the first failing step short-circuits the rest, and
`skipped` can be misread as `passed`. The workflow already uses `if: always()` in 10 places before
this ticket's own change, so this extends an existing convention.

## Verification that the split doesn't change test behavior

Reproduced this ticket's own claimed pre-state first: `.github/workflows/test.yml`'s `unit-infra`
job was confirmed byte-identical to its pre-diagnostic state (no half-applied prior attempt).
Baseline (combined single-step, `pytest <all 17 paths> -m "not slow and not extra_slow"`): 2696
passed, 1 skipped, 0 failed. Same 17 paths run separately with the identical marker filter, summed:
2696 passed, 1 skipped, 0 failed — exact match.
