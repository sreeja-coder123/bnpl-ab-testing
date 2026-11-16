# A/B Test: BNPL button at checkout

## 1. Design
- **Hypothesis:** Offering BNPL reduces payment friction and lifts checkout conversion.
- **Primary metric:** conversion, baseline 12%, MDE +8% relative
- **Guardrails:** refund rate (should not worsen), revenue/user
- **alpha=0.05, power=0.8** -> 18,604 users per group

## 2. Data quality: Sample Ratio Mismatch
- Control 18,748 vs Treatment 18,460; SRM p-value = 0.135
- PASS: assignment looks healthy.

## 3. Primary metric: conversion
- Control 11.97% vs Treatment 13.11%
- Absolute diff +1.15 pp (95% CI +0.47 to +1.82 pp)
- Relative lift +9.6%, p-value = 0.0008

## 4. Guardrail: refund rate (per order)
- Control 4.41% vs Treatment 4.01%, p-value = 0.4907
- Guardrail OK.

## 5. Secondary: revenue per user
- Control Rs 54.4 vs Treatment Rs 62.8 (+15.5%), p-value < 0.0001

## 6. Decision
- **SHIP: primary metric wins, guardrails healthy.**
- Also quantify: extra orders/month = lift x monthly eligible users; weigh against refund cost and BNPL partner fees.

## 7. Why you should not peek at p-values daily
- 3,000 simulated A/A tests (no true effect), 14 days:
  - Check only at the end: false positive rate = 5.0%
  - Stop at first p<0.05 in daily checks: false positive rate = 21.1%
- Takeaway: pre-commit to the sample size/duration, or use sequential testing methods.