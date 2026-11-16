# Project 2: A/B testing a "Buy Now, Pay Later" button

**Scenario:** Should we add a BNPL option at checkout? Design the experiment, analyze it, and make a ship decision.

## Run
```bash
python sample_size.py --baseline 0.12 --mde 0.08 --daily-users 6000
python run_experiment.py   # outputs/experiment_report.md + 2 charts
```

## Files
- `ab_toolkit.py`: reusable functions (sample size, SRM check, two-proportion z-test with CI)
- `sample_size.py`: CLI for planning users and duration
- `run_experiment.py`: design -> simulate -> SRM -> analysis -> guardrails -> decision -> peeking demo

## What it demonstrates
| Concept | Where |
|---|---|
| Hypothesis, primary metric, MDE | Section 1 of the report |
| Power and sample size | `sample_size_per_group` |
| Data validity (SRM) | `srm_check` |
| Effect size with confidence interval | Section 3 |
| Guardrail metrics | Refund rate, revenue/user |
| Decision rules (ship / iterate / invalid) | Section 6 |
| Peeking problem | Section 7: daily peeking inflates false positives from ~5% to ~20% |

## Talking points
- "I picked an 8% relative MDE because smaller lifts would not justify BNPL partner fees."
- "I ran for whole weeks to avoid weekday/weekend bias."
- "I checked SRM before trusting any result."
- "Our guardrail test is underpowered: with ~2,200 orders per arm it can only detect large refund-rate changes, so in production I would size the experiment for the guardrail too, or monitor refunds after launch."
- "Peeking daily raised false positives to ~20%, so I committed to the duration upfront."

## Try these variations (great for interviews)
- Change `REFUND_T` to 0.07 and re-run to see the "DO NOT SHIP YET" branch.
- Change `TRUE_LIFT` to 0.02 to see an underpowered, inconclusive test.
- Re-run `sample_size.py` with `--mde 0.03` and discuss the cost of detecting small effects.
