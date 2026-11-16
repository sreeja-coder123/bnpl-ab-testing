"""
CLI: how many users and how many days do I need?

Example:
  python sample_size.py --baseline 0.12 --mde 0.08 --daily-users 6000
"""
import argparse
import math

from ab_toolkit import sample_size_per_group

ap = argparse.ArgumentParser()
ap.add_argument("--baseline", type=float, default=0.12,
                help="baseline conversion rate, e.g. 0.12")
ap.add_argument("--mde", type=float, default=0.08,
                help="minimum detectable effect, relative (0.08 = +8%%)")
ap.add_argument("--alpha", type=float, default=0.05)
ap.add_argument("--power", type=float, default=0.80)
ap.add_argument("--daily-users", type=int, default=6000,
                help="eligible users per day entering the experiment (total)")
a = ap.parse_args()

n = sample_size_per_group(a.baseline, a.mde, a.alpha, a.power)
days = math.ceil(2 * n / a.daily_users)
days_rounded = max(7, math.ceil(days / 7) * 7)  # whole weeks avoid weekday bias

print(f"Baseline conversion : {a.baseline:.2%}")
print(f"Target MDE          : +{a.mde:.0%} relative "
      f"({a.baseline:.2%} -> {a.baseline*(1+a.mde):.2%})")
print(f"Alpha / Power       : {a.alpha} / {a.power}")
print(f"Users per group     : {n:,}")
print(f"Total users         : {2*n:,}")
print(f"Min duration        : {days} days -> run for {days_rounded} days "
      f"(whole weeks)")
