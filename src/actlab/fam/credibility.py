"""Credibility theory (FAM-S).

Limited fluctuation: how much data is enough to fully trust it?
Bühlmann: weight the data by Z = n / (n + k), with k = EPV / VHM.
"""

from __future__ import annotations

import math
from statistics import NormalDist


def z_value(p: float) -> float:
    """y_p: the standard normal quantile at (1 + p) / 2."""
    return NormalDist().inv_cdf((1.0 + p) / 2.0)


def full_credibility_standard(p: float, k: float) -> float:
    """λ_0 = (y_p / k)^2: expected claims for full credibility of a Poisson frequency."""
    return (z_value(p) / k) ** 2


def full_credibility_claims(p: float, k: float, target: str = "aggregate", cv_severity: float = 0.0) -> float:
    """Expected number of claims needed for full credibility, assuming Poisson frequency.

    target:
        "frequency"  λ_0
        "severity"   λ_0 CV_X^2
        "aggregate"  λ_0 (1 + CV_X^2)   (pure premium / aggregate losses)
    """
    lam0 = full_credibility_standard(p, k)
    cv2 = cv_severity**2
    if target == "frequency":
        return lam0
    if target == "severity":
        return lam0 * cv2
    if target == "aggregate":
        return lam0 * (1.0 + cv2)
    raise ValueError(f"Unknown target: {target}")


def partial_credibility_factor(n: float, n_full: float) -> float:
    """Square-root rule: Z = min(1, sqrt(n / n_full))."""
    return min(1.0, math.sqrt(n / n_full))


def buhlmann_k(epv: float, vhm: float) -> float:
    """k = EPV / VHM (expected process variance over variance of hypothetical means)."""
    return epv / vhm


def buhlmann_z(n: float, epv: float, vhm: float) -> float:
    """Z = n / (n + k)."""
    return n / (n + buhlmann_k(epv, vhm))


def credibility_estimate(z: float, observed_mean: float, prior_mean: float) -> float:
    """P_c = Z x̄ + (1 - Z) μ."""
    return z * observed_mean + (1.0 - z) * prior_mean
