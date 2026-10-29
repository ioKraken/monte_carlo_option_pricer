import numpy as np
import pytest

from greeks import GreeksCalculator as G
from monte_carlo import MonteCarloEngine

S, K, T, R, SIGMA = 100.0, 100.0, 1.0, 0.05, 0.25


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_european_mc_matches_black_scholes(option_type):
    price, se, _ = MonteCarloEngine(seed=1).price_european_option(S, K, T, R, SIGMA, 500_000, option_type)
    bs = G.black_scholes_price(S, K, T, R, SIGMA, option_type)
    assert abs(price - bs) < 4 * se


def test_put_call_parity():
    c = G.black_scholes_price(S, K, T, R, SIGMA, "call")
    p = G.black_scholes_price(S, K, T, R, SIGMA, "put")
    assert c - p == pytest.approx(S - K * np.exp(-R * T))


def test_american_put_exceeds_european_put():
    am, _ = MonteCarloEngine(seed=1).price_american_option_lsm(S, K, T, R, SIGMA, 100_000, 50, "put")
    assert am > G.black_scholes_price(S, K, T, R, SIGMA, "put")


def test_american_call_equals_european_call_without_dividends():
    am, _ = MonteCarloEngine(seed=1).price_american_option_lsm(S, K, T, R, SIGMA, 100_000, 50, "call")
    assert am == pytest.approx(G.black_scholes_price(S, K, T, R, SIGMA, "call"), abs=0.3)


def test_paths_shape_and_start():
    paths, terminal = MonteCarloEngine().simulate_price_paths(S, K, T, R, SIGMA, 1000, 20)
    assert paths.shape == (1000, 21)
    assert np.all(paths[:, 0] == S)
    assert np.array_equal(paths[:, -1], terminal)


def test_engines_are_independent_and_reproducible():
    a = MonteCarloEngine(seed=7).price_european_option(S, K, T, R, SIGMA, 10_000)[0]
    np.random.rand(5)  # touching the global RNG must not matter
    b = MonteCarloEngine(seed=7).price_european_option(S, K, T, R, SIGMA, 10_000)[0]
    assert a == b


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_delta_gamma_match_finite_differences(option_type):
    h = 0.01
    up, mid, dn = (G.black_scholes_price(S + d, K, T, R, SIGMA, option_type) for d in (h, 0, -h))
    assert G.calculate_delta(S, K, T, R, SIGMA, option_type) == pytest.approx((up - dn) / (2 * h), abs=1e-6)
    assert G.calculate_gamma(S, K, T, R, SIGMA) == pytest.approx((up - 2 * mid + dn) / h**2, abs=1e-4)


def test_implied_vol_roundtrip():
    price = G.black_scholes_price(S, K, T, R, 0.32, "call")
    assert G.calculate_implied_volatility(price, S, K, T, R, "call") == pytest.approx(0.32, abs=1e-4)
