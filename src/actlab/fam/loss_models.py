"""Severity models, coverage modifications and aggregate losses (FAM-S).

Key quantity: the limited expected value E[X ∧ u] = ∫_0^u S(x) dx.
Almost every coverage-modification question reduces to differences of LEVs.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from statistics import NormalDist

_STD_NORMAL = NormalDist()


class Severity(ABC):
    """A non-negative continuous loss distribution."""

    @abstractmethod
    def sf(self, x: float) -> float:
        """Survival function S(x) = Pr(X > x)."""

    @abstractmethod
    def mean(self) -> float: ...

    def cdf(self, x: float) -> float:
        return 1.0 - self.sf(x)

    def lev(self, u: float) -> float:
        """E[X ∧ u] by Simpson's rule on ∫_0^u S(x) dx.

        Subclasses override this with a closed form when one exists.
        """
        if math.isinf(u):
            return self.mean()
        if u <= 0:
            return 0.0
        steps = 2000
        h = u / steps
        total = self.sf(0.0) + self.sf(u)
        for k in range(1, steps):
            total += (4 if k % 2 else 2) * self.sf(k * h)
        return total * h / 3.0


class Exponential(Severity):
    """S(x) = e^(-x/θ)."""

    def __init__(self, theta: float):
        self.theta = theta

    def sf(self, x: float) -> float:
        return math.exp(-x / self.theta) if x > 0 else 1.0

    def mean(self) -> float:
        return self.theta

    def lev(self, u: float) -> float:
        if math.isinf(u):
            return self.theta
        return self.theta * (1.0 - math.exp(-u / self.theta))


class Pareto(Severity):
    """Two-parameter (Lomax) Pareto from the FAM-S tables: S(x) = (θ / (x + θ))^α."""

    def __init__(self, alpha: float, theta: float):
        self.alpha = alpha
        self.theta = theta

    def sf(self, x: float) -> float:
        return (self.theta / (x + self.theta)) ** self.alpha if x > 0 else 1.0

    def mean(self) -> float:
        if self.alpha <= 1:
            return math.inf
        return self.theta / (self.alpha - 1.0)

    def lev(self, u: float) -> float:
        if math.isinf(u):
            return self.mean()
        if self.alpha == 1:
            return -self.theta * math.log(self.theta / (u + self.theta))
        a, t = self.alpha, self.theta
        return t / (a - 1.0) * (1.0 - (t / (u + t)) ** (a - 1.0))


class Lognormal(Severity):
    """ln X ~ Normal(mu, sigma^2)."""

    def __init__(self, mu: float, sigma: float):
        self.mu = mu
        self.sigma = sigma

    def sf(self, x: float) -> float:
        if x <= 0:
            return 1.0
        return 1.0 - _STD_NORMAL.cdf((math.log(x) - self.mu) / self.sigma)

    def mean(self) -> float:
        return math.exp(self.mu + self.sigma**2 / 2.0)

    def lev(self, u: float) -> float:
        if math.isinf(u):
            return self.mean()
        if u <= 0:
            return 0.0
        z = (math.log(u) - self.mu) / self.sigma
        return self.mean() * _STD_NORMAL.cdf(z - self.sigma) + u * (1.0 - _STD_NORMAL.cdf(z))


# --- Coverage modifications ---------------------------------------------------


def expected_payment_per_loss(
    dist: Severity,
    deductible: float = 0.0,
    max_covered_loss: float = math.inf,
    coinsurance: float = 1.0,
    inflation: float = 0.0,
) -> float:
    """E[Y^L] = α (1 + r) [E[X ∧ u/(1+r)] - E[X ∧ d/(1+r)]].

    `max_covered_loss` is u, the loss size at which the policy stops paying
    more. (The maximum *payment* is then α(u - d).)
    """
    scale = 1.0 + inflation
    return coinsurance * scale * (dist.lev(max_covered_loss / scale) - dist.lev(deductible / scale))


def expected_payment_per_payment(
    dist: Severity,
    deductible: float = 0.0,
    max_covered_loss: float = math.inf,
    coinsurance: float = 1.0,
    inflation: float = 0.0,
) -> float:
    """E[Y^P] = E[Y^L] / S(d / (1 + r))."""
    per_loss = expected_payment_per_loss(dist, deductible, max_covered_loss, coinsurance, inflation)
    return per_loss / dist.sf(deductible / (1.0 + inflation))


def loss_elimination_ratio(dist: Severity, deductible: float) -> float:
    """LER = E[X ∧ d] / E[X]."""
    return dist.lev(deductible) / dist.mean()


# --- Aggregate losses ---------------------------------------------------------


def compound_mean(mean_n: float, mean_x: float) -> float:
    """E[S] = E[N] E[X]."""
    return mean_n * mean_x


def compound_variance(mean_n: float, var_n: float, mean_x: float, var_x: float) -> float:
    """Var(S) = E[N] Var(X) + Var(N) E[X]^2."""
    return mean_n * var_x + var_n * mean_x**2


def panjer(a: float, b: float, g0: float, severity: list[float], k_max: int) -> list[float]:
    """Panjer recursion for an (a, b, 0) frequency with discrete severity on 0, 1, 2, ...

    g_k = [1 / (1 - a f_0)] * sum_{j=1}^{k} (a + b j / k) f_j g_(k-j)

    `g0` is Pr(S = 0) = P_N(f_0), the frequency's PGF evaluated at f_0.
    Returns [Pr(S = 0), ..., Pr(S = k_max)].
    """
    f = list(severity) + [0.0] * max(0, k_max + 1 - len(severity))
    g = [g0]
    scale = 1.0 / (1.0 - a * f[0])
    for k in range(1, k_max + 1):
        g.append(scale * sum((a + b * j / k) * f[j] * g[k - j] for j in range(1, k + 1)))
    return g


def panjer_poisson(lam: float, severity: list[float], k_max: int) -> list[float]:
    """Compound Poisson aggregate distribution. Poisson is (a, b, 0) with a = 0, b = λ."""
    f0 = severity[0] if severity else 0.0
    return panjer(0.0, lam, math.exp(lam * (f0 - 1.0)), severity, k_max)
