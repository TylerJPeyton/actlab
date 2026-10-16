"""Problem generators.

Each generator takes a `random.Random` and returns a `Problem` whose answer
is computed by the library itself. To add a topic, write a function and
decorate it with `@problem(exam, topic)`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from actlab.fam import credibility, life, loss_models
from actlab.fm import annuities, bonds, duration, interest, loans


@dataclass(frozen=True)
class Problem:
    exam: str
    topic: str
    prompt: str
    answer: float
    solution: str

    def check(self, guess: float, rel_tol: float = 0.001) -> bool:
        """Accept answers within 0.1% of the true value (exam answer choices are rounded)."""
        return abs(guess - self.answer) <= max(rel_tol * abs(self.answer), 1e-9)


Generator = Callable[[random.Random], Problem]


@dataclass(frozen=True)
class GeneratorInfo:
    exam: str
    topic: str
    fn: Generator


GENERATORS: list[GeneratorInfo] = []


def problem(exam: str, topic: str) -> Callable[[Generator], Generator]:
    def register(fn: Generator) -> Generator:
        GENERATORS.append(GeneratorInfo(exam, topic, fn))
        return fn

    return register


def generate(rng: random.Random, exam: str | None = None, topic: str | None = None) -> Problem:
    """Pick a matching generator at random and produce a problem."""
    pool = [
        g
        for g in GENERATORS
        if (exam is None or g.exam.lower() == exam.lower()) and (topic is None or g.topic.lower() == topic.lower())
    ]
    if not pool:
        raise ValueError(f"No problems for exam={exam!r}, topic={topic!r}.")
    return rng.choice(pool).fn(rng)


def _pct(rng: random.Random, lo: float, hi: float, step: float = 0.25) -> float:
    """A 'nice' random percentage between lo% and hi%, returned as a decimal."""
    n = int(round((hi - lo) / step))
    return (lo + step * rng.randint(0, n)) / 100.0


# --- FM -----------------------------------------------------------------------


@problem("FM", "interest")
def nominal_conversion(rng: random.Random) -> Problem:
    i_m = _pct(rng, 3, 12)
    m = rng.choice([2, 4, 12, 365])
    eff = interest.nominal_to_effective(i_m, m)
    return Problem(
        "FM",
        "interest",
        f"A nominal rate of {i_m:.2%} is convertible {m} times per year. "
        "Find the equivalent effective annual rate (as a decimal).",
        eff,
        f"i = (1 + i^({m})/{m})^{m} - 1 = (1 + {i_m}/{m})^{m} - 1 = {eff:.6f}",
    )


@problem("FM", "annuities")
def annuity_pv(rng: random.Random) -> Problem:
    i = _pct(rng, 2, 9)
    n = rng.randint(5, 30)
    pmt = rng.choice([100, 250, 500, 1000, 2500])
    due = rng.random() < 0.5
    factor = annuities.ad_n(i, n) if due else annuities.a_n(i, n)
    when = "beginning" if due else "end"
    symbol = "ä" if due else "a"
    return Problem(
        "FM",
        "annuities",
        f"Payments of {pmt} are made at the {when} of each year for {n} years. "
        f"At an effective rate of {i:.2%}, find the present value.",
        pmt * factor,
        f"PV = {pmt} {symbol}_{n} = {pmt} x {factor:.6f} = {pmt * factor:.4f}",
    )


@problem("FM", "annuities")
def increasing_annuity_pv(rng: random.Random) -> Problem:
    i = _pct(rng, 3, 8)
    n = rng.randint(5, 20)
    value = annuities.increasing_annuity(i, n)
    return Problem(
        "FM",
        "annuities",
        f"Payments of 1, 2, 3, ..., {n} are made at the end of years 1 through {n}. "
        f"At {i:.2%} effective, find the present value.",
        value,
        f"(Ia)_{n} = (ä_{n} - {n} v^{n}) / i = ({annuities.ad_n(i, n):.6f} - {n} x {(1 + i) ** -n:.6f}) / {i} = {value:.6f}",
    )


@problem("FM", "loans")
def loan_balance(rng: random.Random) -> Problem:
    loan = rng.choice([10_000, 25_000, 50_000, 100_000, 250_000])
    i = _pct(rng, 3, 8)
    n = rng.choice([10, 15, 20, 25, 30])
    k = rng.randint(1, n - 1)
    pmt = loans.level_payment(loan, i, n)
    bal = loans.outstanding_balance(loan, i, n, k)
    return Problem(
        "FM",
        "loans",
        f"A loan of {loan:,} is repaid with level annual payments at the end of each year for {n} years "
        f"at {i:.2%} effective. Find the outstanding balance immediately after the {k}th payment.",
        bal,
        f"P = L / a_{n} = {pmt:.4f}.  Prospectively, B_{k} = P a_{n - k} = {pmt:.4f} x {annuities.a_n(i, n - k):.6f} = {bal:.4f}",
    )


@problem("FM", "bonds")
def bond_price(rng: random.Random) -> Problem:
    face = 1000
    coupon_rate = _pct(rng, 2, 10, 0.5)
    yield_rate = _pct(rng, 2, 10, 0.5)
    years = rng.randint(3, 20)
    n = 2 * years
    price = bonds.bond_price(face, coupon_rate / 2, yield_rate / 2, n)
    return Problem(
        "FM",
        "bonds",
        f"A {years}-year {face} par bond pays semiannual coupons at a nominal annual rate of {coupon_rate:.2%}. "
        f"Find its price to yield {yield_rate:.2%} convertible semiannually.",
        price,
        f"P = Fr a_n + C v^n with r = {coupon_rate / 2}, i = {yield_rate / 2}, n = {n}:  "
        f"{face * coupon_rate / 2:.2f} x {annuities.a_n(yield_rate / 2, n):.6f} + {face} x {(1 + yield_rate / 2) ** -n:.6f} = {price:.4f}",
    )


@problem("FM", "duration")
def bond_macaulay_duration(rng: random.Random) -> Problem:
    coupon = _pct(rng, 3, 10, 1)
    i = _pct(rng, 3, 10, 0.5)
    n = rng.randint(3, 10)
    flows = [(t, 100 * coupon) for t in range(1, n + 1)]
    flows[-1] = (n, 100 * coupon + 100)
    d = duration.macaulay_duration(flows, i)
    return Problem(
        "FM",
        "duration",
        f"A bond with face 100 maturing in {n} years pays annual coupons at {coupon:.0%}. "
        f"Find its Macaulay duration at an effective yield of {i:.2%}.",
        d,
        f"D_mac = Σ t v^t CF_t / Σ v^t CF_t = {d:.6f}",
    )


# --- FAM-L --------------------------------------------------------------------

_SULT = life.LifeTable.sult()


@problem("FAM", "life-annuities")
def sult_annuity(rng: random.Random) -> Problem:
    x = rng.randrange(30, 85, 5)
    value = life.annuity_due(_SULT, x, 0.05)
    a_x = life.whole_life_insurance(_SULT, x, 0.05)
    return Problem(
        "FAM",
        "life-annuities",
        f"Using the SULT at i = 5%, find ä_{x}, the EPV of a whole life annuity-due of 1 per year on ({x}).",
        value,
        f"ä_x = Σ v^k k_p_x = {value:.5f}.  Check: (1 - A_{x}) / d = (1 - {a_x:.5f}) / {0.05 / 1.05:.6f} = {(1 - a_x) / (0.05 / 1.05):.5f}",
    )


@problem("FAM", "premiums")
def sult_premium(rng: random.Random) -> Problem:
    x = rng.randrange(30, 70, 5)
    n = rng.choice([10, 15, 20])
    benefit = rng.choice([50_000, 100_000, 250_000])
    kind = rng.choice(["term", "endowment"])
    premium = life.net_level_premium(_SULT, x, 0.05, kind, n, benefit)
    insurance = life.insurance(_SULT, x, 0.05, kind, n)
    annuity = life.annuity_due(_SULT, x, 0.05, n)
    label = "term insurance" if kind == "term" else "endowment insurance"
    return Problem(
        "FAM",
        "premiums",
        f"For a {n}-year {label} of {benefit:,} on ({x}), payable at the end of the year of death, "
        f"with level annual premiums for {n} years, find the net premium. Use the SULT at 5%.",
        premium,
        f"P = b A / ä_{x}:{n} = {benefit:,} x {insurance:.6f} / {annuity:.6f} = {premium:.4f}",
    )


# --- FAM-S --------------------------------------------------------------------


@problem("FAM", "coverage-modifications")
def pareto_per_payment(rng: random.Random) -> Problem:
    alpha = rng.choice([2, 3, 4])
    theta = rng.choice([1000, 2000, 5000])
    d = rng.choice([250, 500, 1000])
    dist = loss_models.Pareto(alpha, theta)
    per_loss = loss_models.expected_payment_per_loss(dist, d)
    value = loss_models.expected_payment_per_payment(dist, d)
    return Problem(
        "FAM",
        "coverage-modifications",
        f"Losses follow a Pareto distribution with α = {alpha}, θ = {theta}. "
        f"A policy has an ordinary deductible of {d}. Find the expected payment per payment.",
        value,
        f"E[X] - E[X∧{d}] = {dist.mean():.4f} - {dist.lev(d):.4f} = {per_loss:.4f} per loss;  "
        f"divide by S({d}) = {dist.sf(d):.6f} to get {value:.4f}.  "
        f"(Shortcut: for a Pareto, the excess loss is Pareto(α, θ + d), mean (θ + d)/(α - 1).)",
    )


@problem("FAM", "coverage-modifications")
def exponential_ler(rng: random.Random) -> Problem:
    theta = rng.choice([500, 1000, 2000, 4000])
    d = rng.choice([100, 250, 500, 1000])
    dist = loss_models.Exponential(theta)
    value = loss_models.loss_elimination_ratio(dist, d)
    return Problem(
        "FAM",
        "coverage-modifications",
        f"Losses are exponential with mean {theta}. Find the loss elimination ratio for a deductible of {d}.",
        value,
        f"LER = E[X∧d] / E[X] = θ(1 - e^(-d/θ)) / θ = 1 - e^(-{d}/{theta}) = {value:.6f}",
    )


@problem("FAM", "aggregate")
def compound_poisson_variance(rng: random.Random) -> Problem:
    lam = rng.choice([2, 3, 5, 10])
    mean_x = rng.choice([100, 200, 500])
    sd_x = rng.choice([50, 100, 200])
    value = loss_models.compound_variance(lam, lam, mean_x, sd_x**2)
    return Problem(
        "FAM",
        "aggregate",
        f"Claim counts are Poisson with mean {lam}. Claim sizes have mean {mean_x} and standard deviation {sd_x}, "
        "independent of counts. Find the variance of aggregate losses.",
        value,
        f"For compound Poisson, Var(S) = λ E[X^2] = {lam} x ({sd_x}^2 + {mean_x}^2) = {value:,.0f}",
    )


@problem("FAM", "credibility")
def buhlmann_premium(rng: random.Random) -> Problem:
    epv = rng.choice([100, 200, 400, 800])
    vhm = rng.choice([10, 20, 25, 50])
    n = rng.randint(2, 10)
    prior = rng.choice([50, 100, 150])
    xbar = prior + rng.choice([-30, -20, -10, 10, 20, 30])
    z = credibility.buhlmann_z(n, epv, vhm)
    value = credibility.credibility_estimate(z, xbar, prior)
    k = credibility.buhlmann_k(epv, vhm)
    return Problem(
        "FAM",
        "credibility",
        f"For a risk, EPV = {epv} and VHM = {vhm}. The overall mean is {prior}. "
        f"A policyholder has {n} years of experience averaging {xbar}. Find the Bühlmann credibility premium.",
        value,
        f"k = EPV/VHM = {k:g}; Z = n/(n+k) = {z:.6f}; P_c = Z x̄ + (1-Z) μ = {value:.4f}",
    )


@problem("FAM", "credibility")
def limited_fluctuation(rng: random.Random) -> Problem:
    p = rng.choice([0.90, 0.95, 0.99])
    k = rng.choice([0.025, 0.05, 0.10])
    cv = rng.choice([0, 1, 1.5, 2])
    value = credibility.full_credibility_claims(p, k, "aggregate", cv)
    return Problem(
        "FAM",
        "credibility",
        f"Claim counts are Poisson and claim sizes have coefficient of variation {cv}. "
        f"Find the expected number of claims needed for full credibility of aggregate losses "
        f"if the observed value must be within {k:.1%} of the mean with probability {p:.0%}.",
        value,
        f"λ_0 = (y_p / k)^2 = ({credibility.z_value(p):.4f} / {k})^2 = {credibility.full_credibility_standard(p, k):.2f}; "
        f"n = λ_0 (1 + CV^2) = {value:.2f}  (the exam tables round y_p to 1.645, 1.960, 2.576)",
    )
