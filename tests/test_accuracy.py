"""Accuracy checks against independent reference values.

References: a Cox-Ross-Rubinstein binomial tree (converges to the true American
price), Hull's textbook example, and the Longstaff-Schwartz (2001) benchmark
grid of American puts (K=40, r=6%).
"""
import numpy as np
import pytest

from greeks import GreeksCalculator as G
from monte_carlo import MonteCarloEngine


def binomial_price(S, K, T, r, sigma, option_type, american, steps=2000):
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    disc = np.exp(-r * dt)

    def payoff(prices):
        return np.maximum(prices - K, 0) if option_type == "call" else np.maximum(K - prices, 0)

    def prices_at(i):
        return S * u ** np.arange(i, -1, -1) * d ** np.arange(0, i + 1)

    values = payoff(prices_at(steps))
    for i in range(steps - 1, -1, -1):
        values = disc * (p * values[:-1] + (1 - p) * values[1:])
        if american:
            values = np.maximum(values, payoff(prices_at(i)))
    return values[0]


def test_black_scholes_matches_hull_textbook_example():
    # Hull, S=42 K=40 r=10% sigma=20% T=0.5 -> call 4.76, put 0.81
    assert G.black_scholes_price(42, 40, 0.5, 0.10, 0.20, "call") == pytest.approx(4.76, abs=0.005)
    assert G.black_scholes_price(42, 40, 0.5, 0.10, 0.20, "put") == pytest.approx(0.81, abs=0.005)


def test_binomial_reference_matches_black_scholes_for_european():
    ref = binomial_price(100, 100, 1, 0.05, 0.25, "put", american=False)
    assert ref == pytest.approx(G.black_scholes_price(100, 100, 1, 0.05, 0.25, "put"), abs=0.01)


def test_european_put_matches_longstaff_schwartz_paper():
    # Longstaff & Schwartz (2001), Table 1: European put S=36, sigma=.2, T=1 -> 3.844
    assert G.black_scholes_price(36, 40, 1, 0.06, 0.2, "put") == pytest.approx(3.844, abs=0.001)


# (S0, sigma, T): spans in-the-money, at-the-money and out-of-the-money puts
LS_GRID = [
    (36, 0.2, 1), (36, 0.4, 2),
    (38, 0.2, 2),
    (40, 0.2, 1), (40, 0.4, 2),
    (44, 0.2, 1), (44, 0.4, 2),
]


@pytest.mark.parametrize("S0,sigma,T", LS_GRID)
def test_american_put_lsm_matches_binomial_reference(S0, sigma, T):
    ref = binomial_price(S0, 40, T, 0.06, sigma, "put", american=True)
    est, _ = MonteCarloEngine(seed=3).price_american_option_lsm(S0, 40, T, 0.06, sigma, 100_000, 50, "put")
    # LSM is a (slightly) low-biased estimator; 0.08 is tight enough to catch
    # the look-ahead bug that once overpriced in-the-money puts by $1+.
    assert abs(est - ref) < 0.08


def test_deep_in_the_money_american_put_is_at_least_intrinsic():
    est, _ = MonteCarloEngine(seed=1).price_american_option_lsm(20, 40, 1, 0.06, 0.2, 50_000, 50, "put")
    assert est >= 20 - 1e-9
    assert est == pytest.approx(binomial_price(20, 40, 1, 0.06, 0.2, "put", True), abs=0.05)


def test_standard_error_shrinks_like_inverse_sqrt_n():
    engine = MonteCarloEngine(seed=5)
    se_small = engine.price_european_option(100, 100, 1, 0.05, 0.25, 10_000)[1]
    se_large = engine.price_european_option(100, 100, 1, 0.05, 0.25, 1_000_000)[1]
    assert se_small / se_large == pytest.approx(10, rel=0.15)


def test_confidence_interval_coverage():
    """About 95% of 2-sigma intervals should contain the true price."""
    bs = G.black_scholes_price(100, 100, 1, 0.05, 0.25, "call")
    hits = 0
    for seed in range(100):
        price, se, _ = MonteCarloEngine(seed=seed).price_european_option(100, 100, 1, 0.05, 0.25, 20_000)
        hits += abs(price - bs) < 1.96 * se
    assert 88 <= hits <= 100


def test_terminal_prices_have_risk_neutral_mean_and_log_vol():
    S0, r, sigma, T = 100, 0.05, 0.25, 1
    _, terminal = MonteCarloEngine(seed=9).simulate_price_paths(S0, 100, T, r, sigma, 200_000, 20)
    assert terminal.mean() == pytest.approx(S0 * np.exp(r * T), rel=0.005)
    assert np.log(terminal / S0).std() == pytest.approx(sigma * np.sqrt(T), rel=0.01)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_greeks_signs_and_bounds(option_type):
    g = G.calculate_all_greeks(100, 100, 1, 0.05, 0.25, option_type)
    assert (0 < g["Delta"] < 1) if option_type == "call" else (-1 < g["Delta"] < 0)
    assert g["Gamma"] > 0 and g["Vega"] > 0 and g["Theta"] < 0


def test_vega_and_rho_match_finite_differences():
    base = lambda **kw: G.black_scholes_price(**{"S": 100, "K": 100, "T": 1, "r": 0.05, "sigma": 0.25, **kw})
    h = 1e-4
    assert G.calculate_vega(100, 100, 1, 0.05, 0.25) == pytest.approx((base(sigma=0.25 + h) - base(sigma=0.25 - h)) / (2 * h) / 100, abs=1e-5)
    assert G.calculate_rho(100, 100, 1, 0.05, 0.25, "call") == pytest.approx((base(r=0.05 + h) - base(r=0.05 - h)) / (2 * h) / 100, abs=1e-5)
    # theta is per day, so compare against -dV/dT / 365
    assert G.calculate_theta(100, 100, 1, 0.05, 0.25, "call") == pytest.approx(-(base(T=1 + h) - base(T=1 - h)) / (2 * h) / 365, abs=1e-5)
