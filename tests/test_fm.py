import pytest

from actlab.fm import annuities, bonds, duration, interest, loans

approx = pytest.approx


class TestInterest:
    def test_nominal_round_trip(self):
        assert interest.nominal_to_effective(0.12, 12) == approx(0.126825, abs=1e-6)
        assert interest.effective_to_nominal(interest.nominal_to_effective(0.08, 4), 4) == approx(0.08)

    def test_discount_round_trip(self):
        d = interest.discount_rate(0.05)
        assert d == approx(0.05 / 1.05)
        assert interest.rate_from_discount(d) == approx(0.05)
        assert interest.nominal_discount_to_effective(interest.effective_to_nominal_discount(0.07, 12), 12) == approx(0.07)

    def test_force_of_interest(self):
        assert interest.rate_from_force(interest.force_of_interest(0.06)) == approx(0.06)

    def test_irr(self):
        assert interest.irr([(0, -100), (1, 110)]) == approx(0.10, abs=1e-9)
        assert interest.irr([(0, -1000), (1, 100), (2, 100), (3, 1100)]) == approx(0.10, abs=1e-9)


class TestAnnuities:
    def test_known_values(self):
        assert annuities.a_n(0.05, 10) == approx(7.721735, abs=1e-6)
        assert annuities.s_n(0.05, 10) == approx(12.577893, abs=1e-6)

    def test_due_vs_immediate(self):
        assert annuities.ad_n(0.04, 12) == approx(1 + annuities.a_n(0.04, 11))
        assert annuities.sd_n(0.04, 12) == approx(annuities.s_n(0.04, 13) - 1)

    def test_zero_interest(self):
        assert annuities.a_n(0.0, 7) == 7

    @pytest.mark.parametrize("i,n", [(0.03, 5), (0.07, 20)])
    def test_varying_annuities_match_direct_sums(self, i, n):
        v = 1 / (1 + i)
        assert annuities.increasing_annuity(i, n) == approx(sum(t * v**t for t in range(1, n + 1)))
        assert annuities.decreasing_annuity(i, n) == approx(sum((n + 1 - t) * v**t for t in range(1, n + 1)))
        g = 0.02
        assert annuities.geometric_annuity(i, g, n) == approx(sum((1 + g) ** (t - 1) * v**t for t in range(1, n + 1)))

    def test_mthly_approaches_continuous(self):
        assert annuities.a_n_m(0.05, 10, 100_000) == approx(annuities.a_n_continuous(0.05, 10), rel=1e-5)


class TestLoans:
    def test_prospective_equals_retrospective(self):
        for k in range(0, 31):
            assert loans.outstanding_balance(100_000, 0.06, 30, k) == approx(
                loans.outstanding_balance_retrospective(100_000, 0.06, 30, k)
            )

    def test_schedule(self):
        rows = loans.amortization_schedule(10_000, 0.05, 10)
        assert len(rows) == 10
        assert rows[-1].balance == 0.0
        assert sum(r.principal for r in rows) == approx(10_000)
        assert rows[0].interest == approx(500)

    def test_sinking_fund_equals_amortization_when_rates_match(self):
        assert loans.sinking_fund_payment(10_000, 0.05, 0.05, 10) == approx(loans.level_payment(10_000, 0.05, 10))


class TestBonds:
    def test_par_bond(self):
        assert bonds.bond_price(1000, 0.04, 0.04, 20) == approx(1000)

    def test_premium_and_discount(self):
        assert bonds.bond_price(1000, 0.05, 0.04, 10) > 1000
        assert bonds.bond_price(1000, 0.03, 0.04, 10) < 1000

    def test_yield_inverts_price(self):
        price = bonds.bond_price(1000, 0.035, 0.0275, 16)
        assert bonds.bond_yield(price, 1000, 0.035, 16) == approx(0.0275, abs=1e-9)

    def test_book_value_ends_at_redemption(self):
        rows = bonds.book_value_schedule(1000, 0.05, 0.04, 10, redemption=1050)
        assert rows[-1].book_value == approx(1050)


class TestDuration:
    def test_zero_coupon_duration_is_maturity(self):
        assert duration.macaulay_duration([(7, 100)], 0.05) == approx(7)
        assert duration.modified_duration([(7, 100)], 0.05) == approx(7 / 1.05)

    def test_convexity_matches_numerical_second_derivative(self):
        flows = [(1, 5), (2, 5), (3, 105)]
        i, h = 0.04, 1e-4
        p = interest.npv
        second = (p(flows, i + h) - 2 * p(flows, i) + p(flows, i - h)) / h**2
        assert duration.convexity(flows, i) == approx(second / p(flows, i), rel=1e-4)

    def test_redington(self):
        i = 0.05
        liabilities = [(2, 100)]
        # Solve PV and duration matching by hand: A3 = 50(1.05), A1 = 50 / 1.05.
        assets = [(1, 50 / 1.05), (3, 50 * 1.05)]
        assert duration.is_redington_immunized(assets, liabilities, i)
        assert not duration.is_redington_immunized(liabilities, liabilities, i)
        assert not duration.is_redington_immunized([(1, 100)], liabilities, i)
