import math

import pytest

from actlab.fam import credibility, life, loss_models
from actlab.fam.loss_models import Exponential, Lognormal, Pareto, Severity

approx = pytest.approx
SULT = life.LifeTable.sult()


class TestLifeTable:
    def test_sult_radix_and_probabilities(self):
        assert SULT.l(20) == 100_000
        assert 0 < SULT.q(65) < 1
        assert SULT.tpx(10, 50) == approx(math.prod(SULT.p(50 + k) for k in range(10)))

    def test_sult_published_values(self):
        # Published SULT values at i = 5%.
        assert life.annuity_due(SULT, 65, 0.05) == approx(13.5498, abs=1e-3)
        assert life.whole_life_insurance(SULT, 65, 0.05) == approx(0.35477, abs=1e-4)

    @pytest.mark.parametrize("x", [25, 50, 80])
    def test_insurance_annuity_identity(self, x):
        d = 0.05 / 1.05
        assert life.whole_life_insurance(SULT, x, 0.05) == approx(1 - d * life.annuity_due(SULT, x, 0.05))
        assert life.endowment_insurance(SULT, x, 10, 0.05) == approx(1 - d * life.annuity_due(SULT, x, 0.05, 10))

    def test_deferred_q_sums_to_one(self):
        assert sum(SULT.deferred_q(k, 1, 40) for k in range(SULT.max_age - 40 + 1)) == approx(1)

    @pytest.mark.parametrize("kind,n", [("whole", None), ("term", 20), ("endowment", 20)])
    def test_reserve_starts_at_zero(self, kind, n):
        assert life.net_premium_reserve(SULT, 45, 0, 0.05, kind, n, 1000) == approx(0, abs=1e-9)

    def test_endowment_reserve_reaches_benefit(self):
        assert life.net_premium_reserve(SULT, 45, 20, 0.05, "endowment", 20, 1000) == 1000
        assert life.net_premium_reserve(SULT, 45, 19, 0.05, "endowment", 20, 1000) < 1000

    def test_tiny_table(self):
        table = life.LifeTable({0: 100, 1: 60, 2: 20})
        assert table.q(0) == approx(0.4)
        assert table.q(2) == 1
        assert table.curtate_expectation(0) == approx(0.6 + 0.2)


class TestLossModels:
    @pytest.mark.parametrize(
        "dist", [Exponential(1000), Pareto(3, 2000), Lognormal(6, 1.2)], ids=["exp", "pareto", "lognormal"]
    )
    def test_closed_form_lev_matches_numerical(self, dist):
        for u in [100, 1000, 5000]:
            assert dist.lev(u) == approx(Severity.lev(dist, u), rel=1e-6)

    def test_lev_at_infinity_is_mean(self):
        assert Pareto(3, 2000).lev(math.inf) == approx(1000)

    def test_pareto_per_payment_shortcut(self):
        alpha, theta, d = 3, 2000, 500
        assert loss_models.expected_payment_per_payment(Pareto(alpha, theta), d) == approx((theta + d) / (alpha - 1))

    def test_exponential_memoryless(self):
        assert loss_models.expected_payment_per_payment(Exponential(1000), 300) == approx(1000)

    def test_coverage_modifications(self):
        dist = Exponential(1000)
        expected = 0.8 * 1.1 * (dist.lev(5000 / 1.1) - dist.lev(500 / 1.1))
        got = loss_models.expected_payment_per_loss(dist, 500, 5000, coinsurance=0.8, inflation=0.1)
        assert got == approx(expected)

    def test_ler(self):
        assert loss_models.loss_elimination_ratio(Exponential(1000), 1000) == approx(1 - math.exp(-1))

    def test_compound(self):
        assert loss_models.compound_mean(3, 200) == 600
        assert loss_models.compound_variance(3, 3, 200, 100**2) == 3 * (100**2 + 200**2)

    def test_panjer_poisson(self):
        lam, f = 2.0, [0.0, 0.5, 0.3, 0.2]
        g = loss_models.panjer_poisson(lam, f, 60)
        assert g[0] == approx(math.exp(-lam))
        assert g[1] == approx(lam * f[1] * math.exp(-lam))
        assert sum(g) == approx(1, abs=1e-9)
        assert sum(k * p for k, p in enumerate(g)) == approx(lam * sum(k * p for k, p in enumerate(f)), rel=1e-6)


class TestCredibility:
    def test_standard_for_full_credibility(self):
        assert credibility.z_value(0.90) == approx(1.645, abs=1e-3)
        assert credibility.full_credibility_standard(0.90, 0.05) == approx(1082.2, abs=0.5)
        assert credibility.full_credibility_claims(0.90, 0.05, "aggregate", 1.0) == approx(
            2 * credibility.full_credibility_standard(0.90, 0.05)
        )

    def test_partial_credibility(self):
        assert credibility.partial_credibility_factor(250, 1000) == approx(0.5)
        assert credibility.partial_credibility_factor(5000, 1000) == 1

    def test_buhlmann(self):
        z = credibility.buhlmann_z(5, 100, 25)  # k = 4
        assert z == approx(5 / 9)
        assert credibility.credibility_estimate(z, 120, 100) == approx(100 + 20 * 5 / 9)
