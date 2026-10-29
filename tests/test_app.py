"""End-to-end UI tests using Streamlit's AppTest (no browser, no network)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import market_data

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def app():
    return AppTest.from_file(APP, default_timeout=90).run()


def click(at, label):
    [b for b in at.button if b.label == label][0].click().run()


def test_app_loads_without_errors(app):
    assert not app.exception


def test_european_price_and_comparison_table(app):
    click(app, "Calculate Option Price")
    assert not app.exception
    assert any("Black-Scholes" in m.value for m in app.markdown)


def test_american_price_runs(app):
    app.sidebar.selectbox[1].set_value("American").run()
    click(app, "Calculate Option Price")
    assert not app.exception and "option_price" in app.session_state


def test_changing_inputs_hides_stale_result(app):
    click(app, "Calculate Option Price")
    app.sidebar.number_input[1].set_value(120.0).run()  # strike
    assert any("Inputs changed" in i.value for i in app.info)


def test_american_simulation_options_shrink_with_more_steps(app):
    app.sidebar.selectbox[1].set_value("American").run()
    [sl for sl in app.sidebar.slider if sl.label == "Time Steps"][0].set_value(500).run()
    options = app.sidebar.select_slider[0].options
    assert max(int(o) for o in options) * 501 <= 20_000_000
    assert not app.exception


def test_sensitivity_analysis_runs_on_demand(app):
    click(app, "Calculate Option Price")
    assert "sensitivity" not in app.session_state
    click(app, "Run Sensitivity Analysis")
    assert not app.exception and "sensitivity" in app.session_state


def test_failed_live_fetch_shows_error_and_falls_back(monkeypatch):
    def boom(symbol):
        raise RuntimeError("rate limited")
    monkeypatch.setattr(market_data.yf, "Ticker", boom)
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.checkbox[0].check().run()
    click(at, "Fetch Market Data")
    assert not at.exception
    assert any("rate limited" in e.value for e in at.sidebar.error)
    assert "market_data" not in at.session_state


def test_invalid_ticker_disables_fetch():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.checkbox[0].check().run()
    at.sidebar.text_input[0].set_value("DROP TABLE;").run()
    assert [b for b in at.sidebar.button if b.label == "Fetch Market Data"][0].disabled
