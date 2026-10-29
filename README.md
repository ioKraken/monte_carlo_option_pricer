#  Monte Carlo Option Pricer

A high-performance option pricing engine built with Python and Streamlit, combining Monte Carlo simulation with real-time market data from Yahoo Finance.

---

## Features

- **European & American Option Pricing** — Monte Carlo simulation for European options, and Longstaff-Schwartz (LSM) algorithm for American options
- **Black-Scholes Comparison** — Side-by-side comparison of Monte Carlo vs analytical Black-Scholes pricing for European options
- **Option Greeks** — Analytical Black-Scholes Greeks (Delta, Gamma, Vega, Theta, Rho); a Newton-Raphson implied-volatility solver is available in `greeks.py`
- **Live Market Data** — Latest stock price and 3-month historical volatility via Yahoo Finance
- **Simulated Tick Stream** — Random-walk tick data seeded from the latest price (no real Kafka broker)
- **Performance Benchmarking** — Built-in tool that measures simulations/second on your machine
- **Interactive Dashboard** — Streamlit-powered UI with sensitivity analysis, price path visualization, and Greeks heatmaps

---

## Project Structure

```
monte_carlo_option_pricer/
│
├── app.py              # Streamlit dashboard (main entry point)
├── monte_carlo.py      # Monte Carlo engine (European + American LSM pricing)
├── greeks.py           # Black-Scholes Greeks calculator + implied volatility
├── market_data.py      # Yahoo Finance data feed + Kafka stream simulator
├── tests/              # pytest suite
└── pyproject.toml      # Project dependencies
```

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/ioKraken/monte_carlo_option_pricer.git
cd monte_carlo_option_pricer
```

**2. Install dependencies**
```bash
pip install numpy pandas plotly scipy streamlit yfinance
```

Or:
```bash
pip install -e .
```

Run the tests with `pip install -e .[dev] && pytest`.

**3. Run the app**
```bash
streamlit run app.py
```

---

## Usage

Once the app is running, open `http://localhost:8501` (Streamlit's default port) in your browser.

**Sidebar controls:**
- Toggle **Live Market Data** to fetch real-time stock prices by ticker (e.g., `AAPL`, `TSLA`)
- Set **Spot Price, Strike Price, Time to Expiration, Risk-Free Rate, Volatility**
- Choose **Option Type** (Call / Put) and **Option Style** (European / American)
- Set the **number of simulations** (1,000 to 1,000,000; American options are capped at 200,000 because LSM stores every path in memory) and **time steps**

**Dashboard tabs:**
| Tab | Description |
|---|---|
| Pricing | Run simulation, compare MC vs Black-Scholes, sensitivity analysis |
|  Price Paths | Visualize simulated GBM paths and payoff distribution |
|  Greeks | Delta, Gamma, Vega, Theta, Rho — analytical + heatmaps |
|  Performance | Benchmark computation speed across simulation counts |
|  Data Stream | Simulated high-frequency Kafka-like market data stream |

---

## Methods

### Monte Carlo Simulation
Simulates stock price paths using **Geometric Brownian Motion (GBM)**:

```
S(t) = S(0) * exp((r - 0.5σ²)t + σ√t * Z)
```

where `Z ~ N(0,1)`. Option price is the discounted expected payoff across all simulated paths.

### Longstaff-Schwartz (LSM) for American Options
Uses backward induction with polynomial regression to estimate the **continuation value** at each time step, determining the optimal early exercise boundary.

### Black-Scholes Greeks
Analytical closed-form solutions for all five Greeks, plus **Newton-Raphson implied volatility** solving.

---

## Tech Stack

- **Python 3.11+**
- **NumPy** — vectorized simulation
- **SciPy** — normal distribution for Greeks
- **Streamlit** — interactive dashboard
- **Plotly** — interactive charts
- **yFinance** — live market data
- **Pandas** — data handling

---

## Performance

Throughput depends on hardware. Use the **Performance** tab to measure it on your machine. European pricing is fully vectorized and typically reaches millions of simulations per second; American (LSM) pricing is slower because it runs a regression at every time step.

---

## License

MIT License
