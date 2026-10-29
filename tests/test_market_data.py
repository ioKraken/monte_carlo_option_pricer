"""Market data tests with Yahoo Finance mocked out (no network needed)."""
import numpy as np
import pandas as pd
import pytest

import market_data
from market_data import MarketDataFeed


class FakeTicker:
    """Daily bars with a known volatility; minute bars that would wreck a naive estimate."""
    DAILY_VOL = 0.015

    def __init__(self, symbol):
        rng = np.random.default_rng(0)
        self.daily = pd.DataFrame({"Close": 100 * np.exp(np.cumsum(rng.normal(0, self.DAILY_VOL, 63)))})
        self.minute = pd.DataFrame({"Close": 100 * np.exp(np.cumsum(rng.normal(0, 0.0005, 390)))})
        self.info = {"longName": "Fake Corp"}

    def history(self, period="1mo", interval="1d"):
        return self.minute if interval == "1m" else self.daily


def test_volatility_comes_from_daily_returns_even_in_live_mode(monkeypatch):
    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    data = MarketDataFeed().get_stock_data("FAKE", use_live=True)
    expected = FakeTicker.DAILY_VOL * np.sqrt(252)  # ~0.24
    assert data["volatility"] == pytest.approx(expected, rel=0.25)
    assert "error" not in data and data["company_name"] == "Fake Corp"


def test_fetch_failure_is_reported_not_hidden(monkeypatch):
    def boom(symbol):
        raise RuntimeError("network down")
    monkeypatch.setattr(market_data.yf, "Ticker", boom)
    data = MarketDataFeed().get_stock_data("FAKE")
    assert "network down" in data["error"]


def test_cached_data_is_flagged_when_refresh_fails(monkeypatch):
    feed = MarketDataFeed()
    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    feed.get_stock_data("FAKE")
    monkeypatch.setattr(market_data.yf, "Ticker", lambda s: (_ for _ in ()).throw(RuntimeError("offline")))
    data = feed.get_stock_data("FAKE")
    assert data["current_price"] > 0 and data["error"] == "offline"


def test_simulated_stream_shape(monkeypatch):
    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    df = MarketDataFeed().simulate_kafka_stream("FAKE", 500)
    assert len(df) == 500
    assert (df["bid"] < df["price"]).all() and (df["price"] < df["ask"]).all()
