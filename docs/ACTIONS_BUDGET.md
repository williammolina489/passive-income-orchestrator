# GitHub Actions Efficiency Budget

Audit date: 2026-09-24

## Billing scope

GitHub-hosted standard runners in public repositories do not consume the private-repository included-minutes allowance. The recurring allowance pressure in this portfolio comes from the private repositories, especially `crypto-trading-bot`.

The account is currently known to be at its included Actions allowance for the September 2026 billing cycle. No paid overage or budget increase is authorized.

## September observed private workflow starts through 2026-09-24

| Repository | Observed runs | Main contributors |
| --- | ---: | --- |
| crypto-trading-bot | 1,265 | dashboard 554; challenger 220; incumbent 187; paper health 152; challenger health 146; CI 6 |
| systematic-futures-bot | 328 | CI 301 plus one-off integrity/TRAIN/data work |
| crypto-funding-basis-bot | 123 | CI 93; live validation 29; one failed workflow load |
| alpaca-paper-trading-bot | 76 | CI only |
| **Total** | **1,792** | before accounting for multi-job matrices and jobs lasting more than one billed minute |

The private crypto jobs normally finish in under one minute, but each separate private hosted job still consumes a minimum billed minute. Historical futures data-acquisition/audit jobs also ran for multiple minutes, which explains the remainder of the 2,000-minute allowance.

## Cadence classification

- **METHODOLOGY_CRITICAL / evidence-sensitive:** `Forward paper BTC cycle` hourly; `Forward challenger BTC basket` hourly. Do not reduce or combine without a separately authorized research amendment because that could change observation timing, transition opportunity timing, provenance, or failure semantics.
- **OPERATIONAL_ONLY:** paper/challenger scheduler-liveness monitoring. Move to the public orchestrator's existing hourly controller cycle.
- **OPTIONAL / publication:** read-only dashboard refresh. Reduce to daily plus manual/on-change refresh.
- **CI:** keep both supported Python versions and all safety tests; deduplicate superseded/feature-branch runs rather than dropping coverage.

## Planned recurring private-minute budget

| Workload | Cadence | Approx. minutes/month |
| --- | --- | ---: |
| Forward paper BTC cycle | hourly | 720 |
| Forward challenger BTC basket | hourly | 720 |
| Read-only dashboard | daily | 30 |
| Private hourly health crons | disabled; public orchestrator owns liveness | 0 |
| **Recurring baseline** |  | **1,470** |

The two frozen hourly evidence chains create a practical floor of about **1,440 private minutes/month** under the current GitHub-hosted architecture. Therefore a <=1,000 minute target is not safely reachable without changing evidence cadence, combining failure domains, or moving execution infrastructure.

Operating target: keep ordinary monthly usage at or below **1,700 minutes**, leaving roughly 300 included minutes for CI, bounded recovery, and supervised one-off work. If projected non-methodology work would exceed that reserve, defer it rather than enabling paid overage.

## Fail-closed quota handling

The orchestrator records a temporary known quota block through 2026-09-30. When a monitored private workflow fails before any runner step starts during that block, it is classified as:

`INFRASTRUCTURE_BLOCKED — GITHUB_ACTIONS_QUOTA`

It must not be reported as a bot, strategy, API, or research failure. Guarded scheduler recovery is suppressed while the known quota block is active.

## Safety invariants

This optimization does not authorize live trading, spending, paid runners, overage, methodology changes, strategy retuning, weakening tests, retrospective evidence, or default-branch merges.
