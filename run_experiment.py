"""
End-to-end A/B test for: "Add a 'Buy now, pay later' (BNPL) button at checkout"

  Primary metric : checkout conversion
  Guardrail      : refund rate on orders (must not get worse)
  Secondary      : revenue per user

Pipeline: design -> simulate data -> SRM check -> analysis -> decision.
Run: python run_experiment.py
Out: outputs/*.png, outputs/experiment_report.md
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from ab_toolkit import sample_size_per_group, srm_check, two_proportion_test

OUT = Path(__file__).parent / "outputs"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)
lines = []


def log(s=""):
    lines.append(s)
    print(s)


# ---------------- 1. Design ----------------
BASELINE, MDE, ALPHA, POWER = 0.12, 0.08, 0.05, 0.80
n_group = sample_size_per_group(BASELINE, MDE, ALPHA, POWER)
log("# A/B Test: BNPL button at checkout\n")
log("## 1. Design")
log("- **Hypothesis:** Offering BNPL reduces payment friction and lifts "
    "checkout conversion.")
log(f"- **Primary metric:** conversion, baseline {BASELINE:.0%}, "
    f"MDE +{MDE:.0%} relative")
log("- **Guardrails:** refund rate (should not worsen), revenue/user")
log(f"- **alpha={ALPHA}, power={POWER}** -> {n_group:,} users per group")

# ---------------- 2. Simulate data ----------------
# Ground truth (hidden from the 'analyst'): +10% lift, refunds slightly up.
TRUE_LIFT, REFUND_C, REFUND_T = 0.10, 0.040, 0.046

assign = rng.random(2 * n_group) < 0.5          # True = treatment
n_t = int(assign.sum())
n_c = len(assign) - n_t
conv_c = rng.random(n_c) < BASELINE
conv_t = rng.random(n_t) < BASELINE * (1 + TRUE_LIFT)

aov_c = rng.lognormal(mean=6.0, sigma=0.5, size=n_c)           # ~Rs 460
aov_t = rng.lognormal(mean=6.0 + 0.04, sigma=0.5, size=n_t)    # BNPL: bigger carts
rev_c = conv_c * aov_c
rev_t = conv_t * aov_t

orders_c, orders_t = int(conv_c.sum()), int(conv_t.sum())
ref_c = rng.binomial(orders_c, REFUND_C)
ref_t = rng.binomial(orders_t, REFUND_T)

# ---------------- 3. SRM ----------------
p_srm = srm_check(n_c, n_t)
log("\n## 2. Data quality: Sample Ratio Mismatch")
log(f"- Control {n_c:,} vs Treatment {n_t:,}; SRM p-value = {p_srm:.3f}")
srm_ok = p_srm > 0.001
log("- " + ("PASS: assignment looks healthy." if srm_ok else
             "FAIL: do not trust results, investigate assignment."))

# ---------------- 4. Analysis ----------------
res = two_proportion_test(orders_c, n_c, orders_t, n_t, ALPHA)
log("\n## 3. Primary metric: conversion")
log(f"- Control {res['p_control']:.2%} vs Treatment {res['p_treatment']:.2%}")
log(f"- Absolute diff {res['abs_diff']*100:+.2f} pp "
    f"(95% CI {res['ci_low']*100:+.2f} to {res['ci_high']*100:+.2f} pp)")
log(f"- Relative lift {res['rel_lift']:+.1%}, p-value = {res['p_value']:.4f}")
primary_win = res["p_value"] < ALPHA and res["abs_diff"] > 0

g = two_proportion_test(ref_c, orders_c, ref_t, orders_t, ALPHA)
log("\n## 4. Guardrail: refund rate (per order)")
log(f"- Control {g['p_control']:.2%} vs Treatment {g['p_treatment']:.2%}, "
    f"p-value = {g['p_value']:.4f}")
guardrail_bad = g["p_value"] < ALPHA and g["abs_diff"] > 0
log("- " + ("Guardrail BREACHED: refunds significantly higher."
             if guardrail_bad else "Guardrail OK."))

_, p_rev = stats.ttest_ind(rev_t, rev_c, equal_var=False)
log("\n## 5. Secondary: revenue per user")
log(f"- Control Rs {rev_c.mean():.1f} vs Treatment Rs {rev_t.mean():.1f} "
    f"({(rev_t.mean()/rev_c.mean()-1):+.1%}), "
    f"p-value {'< 0.0001' if p_rev < 0.0001 else f'= {p_rev:.4f}'}")

# ---------------- 5. Decision ----------------
log("\n## 6. Decision")
if not srm_ok:
    decision = "INVALID TEST: fix assignment, rerun."
elif primary_win and not guardrail_bad:
    decision = "SHIP: primary metric wins, guardrails healthy."
elif primary_win and guardrail_bad:
    decision = ("DO NOT SHIP YET: conversion wins but refunds worsen. "
                "Investigate the cause (e.g. BNPL users refunding more); "
                "consider limiting BNPL to eligible segments and re-test.")
else:
    decision = "DO NOT SHIP: no significant improvement. Iterate on the idea."
log(f"- **{decision}**")
log("- Also quantify: extra orders/month = lift x monthly eligible users; "
    "weigh against refund cost and BNPL partner fees.")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["Control", "Treatment"],
       [res["p_control"] * 100, res["p_treatment"] * 100],
       color=["#999", "#2e8b57"])
ax.set_ylabel("Conversion %")
ax.set_title(f"Lift {res['rel_lift']:+.1%} (p={res['p_value']:.3f})")
fig.tight_layout()
fig.savefig(OUT / "01_conversion.png", dpi=150)
plt.close(fig)

# ---------------- 6. Peeking simulation ----------------
log("\n## 7. Why you should not peek at p-values daily")
SIMS, DAYS, PER_DAY, P = 3000, 14, 1500, 0.12
cc = rng.binomial(PER_DAY, P, size=(SIMS, DAYS)).cumsum(axis=1)  # A/A test
tt = rng.binomial(PER_DAY, P, size=(SIMS, DAYS)).cumsum(axis=1)
n_cum = PER_DAY * np.arange(1, DAYS + 1)
pc, pt = cc / n_cum, tt / n_cum
pool = (cc + tt) / (2 * n_cum)
z = (pt - pc) / np.sqrt(pool * (1 - pool) * 2 / n_cum)
pvals = 2 * (1 - stats.norm.cdf(np.abs(z)))
fp_peek = (pvals < 0.05).any(axis=1).mean()
fp_fixed = (pvals[:, -1] < 0.05).mean()
log(f"- {SIMS:,} simulated A/A tests (no true effect), {DAYS} days:")
log(f"  - Check only at the end: false positive rate = {fp_fixed:.1%}")
log(f"  - Stop at first p<0.05 in daily checks: false positive rate = "
    f"{fp_peek:.1%}")
log("- Takeaway: pre-commit to the sample size/duration, or use sequential "
    "testing methods.")

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["Check once at end", "Peek daily"],
       [fp_fixed * 100, fp_peek * 100], color=["#5bc0de", "#d9534f"])
ax.axhline(5, color="k", ls="--", label="Nominal 5%")
ax.set_ylabel("False positive rate %")
ax.set_title("Peeking inflates false positives")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "02_peeking.png", dpi=150)
plt.close(fig)

(OUT / "experiment_report.md").write_text("\n".join(lines))
print(f"\nSaved to {OUT}")
