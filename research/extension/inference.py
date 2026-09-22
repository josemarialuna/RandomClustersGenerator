"""Finite-sample bounds and exact trinomial coverage for paired differences."""

import numpy as np
from scipy.stats import beta, multinomial, t


def cp(count, total, alpha=0.025):
    """Two-sided Clopper-Pearson; default individual coverage 97.5%."""
    count = np.asarray(count)
    low = np.where(count == 0, 0.0, beta.ppf(alpha / 2, count, total - count + 1))
    high = np.where(count == total, 1.0, beta.ppf(1 - alpha / 2, count + 1, total - count))
    return low, high


def paired_bounds(positive, negative, total):
    lp, up = cp(positive, total)
    lm, um = cp(negative, total)
    return lp - um, up - lm


def bounded_mean(values, lower, upper):
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("at least two finite observations required")
    if np.any((values < lower) | (values > upper)):
        raise ValueError("observations outside declared support")
    mean = float(values.mean())
    mcse = float(values.std(ddof=1) / np.sqrt(len(values)))
    radius = float(t.ppf(0.975, len(values) - 1) * mcse)
    h = (upper - lower) * np.sqrt(np.log(40) / (2 * len(values)))
    return {
        "n": len(values),
        "mean": mean,
        "mcse": mcse,
        "t_low": mean - radius,
        "t_high": mean + radius,
        "hoeffding_low": max(lower, mean - h),
        "hoeffding_high": min(upper, mean + h),
    }


def exact_coverage():
    """Enumerate the full sampling distribution, not simulated coverage trials."""
    grid = [0, 0.005, 0.025, 0.1, 0.3, 0.5, 0.9, 0.975, 0.995, 1]
    rows = []
    for n in [20, 50, 200]:
        counts = np.array([(a, b, n - a - b) for a in range(n + 1) for b in range(n - a + 1)])
        a, b = counts[:, 0], counts[:, 1]
        mean = (a - b) / n
        variance = np.maximum(0, (a + b - n * mean**2) / (n - 1))
        radius = t.ppf(0.975, n - 1) * np.sqrt(variance / n)
        cp_low, cp_high = paired_bounds(a, b, n)
        h = 2 * np.sqrt(np.log(40) / (2 * n))
        methods = {
            "student_t": (mean - radius, mean + radius),
            "cp_bonferroni": (cp_low, cp_high),
            "hoeffding": (np.maximum(-1, mean - h), np.minimum(1, mean + h)),
        }
        for plus in grid:
            for minus in grid:
                if plus + minus > 1 + 1e-12:
                    continue
                probabilities = [plus, minus, max(0, 1 - plus - minus)]
                mass = multinomial.pmf(counts, n, probabilities)
                if not np.isclose(mass.sum(), 1, atol=1e-10):
                    raise AssertionError("incomplete probability mass")
                truth = plus - minus
                for name, (low, high) in methods.items():
                    covered = (low <= truth + 1e-12) & (truth <= high + 1e-12)
                    rows.append(
                        {
                            "families": n,
                            "p_plus": plus,
                            "p_minus": minus,
                            "truth": truth,
                            "method": name,
                            "coverage": float(mass[covered].sum()),
                            "expected_width": float(mass @ (high - low)),
                        }
                    )
    return rows
