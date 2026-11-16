"""Reusable A/B testing helpers (only numpy + scipy needed)."""
import math

from scipy import stats


def sample_size_per_group(baseline, mde_relative, alpha=0.05, power=0.80):
    """Users needed per group for a two-sided two-proportion test."""
    p1 = baseline
    p2 = baseline * (1 + mde_relative)
    p_bar = (p1 + p2) / 2
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    num = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
           + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p2 - p1) ** 2)


def srm_check(n_control, n_treatment, expected_ratio=0.5):
    """Sample Ratio Mismatch: chi-square test on assignment counts."""
    total = n_control + n_treatment
    exp = [total * expected_ratio, total * (1 - expected_ratio)]
    _, p = stats.chisquare([n_control, n_treatment], exp)
    return p


def two_proportion_test(x_c, n_c, x_t, n_t, alpha=0.05):
    """Z-test for difference in proportions + CI on the absolute difference."""
    p_c, p_t = x_c / n_c, x_t / n_t
    p_pool = (x_c + x_t) / (n_c + n_t)
    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se_pool
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    zc = stats.norm.ppf(1 - alpha / 2)
    diff = p_t - p_c
    return dict(p_control=p_c, p_treatment=p_t, abs_diff=diff,
                rel_lift=diff / p_c, ci_low=diff - zc * se,
                ci_high=diff + zc * se, p_value=p_value)
