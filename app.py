import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime

from monte_carlo import MonteCarloEngine
from greeks import GreeksCalculator
from market_data import MarketDataFeed

# Page configuration
st.set_page_config(
    page_title="Monte Carlo Option Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mc_engine' not in st.session_state:
    st.session_state.mc_engine = MonteCarloEngine()
if 'market_feed' not in st.session_state:
    st.session_state.market_feed = MarketDataFeed()
if 'last_price_update' not in st.session_state:
    st.session_state.last_price_update = None

# Title and description
st.title("📈 Monte Carlo Option Pricer")
st.markdown("""
**High-Performance Option Pricing with Real-Time Market Data**

This application uses Monte Carlo simulation to estimate the fair value of financial options.
Optimized for rapid computation and high-frequency demand forecasting.
""")

# Sidebar - Input Parameters
st.sidebar.header("Option Parameters")

# Market data selection
use_live_data = st.sidebar.checkbox("Use Live Market Data", value=False)

if use_live_data:
    ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
    
    if st.sidebar.button("Fetch Market Data"):
        with st.spinner("Fetching market data..."):
            market_data = st.session_state.market_feed.get_stock_data(ticker)
            st.session_state.market_data = market_data
            st.session_state.last_price_update = datetime.now()
    
    if 'market_data' in st.session_state:
        st.sidebar.success(f"✓ {st.session_state.market_data['company_name']}")
        st.sidebar.metric("Current Price", f"${st.session_state.market_data['current_price']:.2f}")
        S0 = st.session_state.market_data['current_price']
        sigma = st.session_state.market_data['volatility']
    else:
        S0 = st.sidebar.number_input("Spot Price (S₀)", value=100.0, min_value=0.01, step=1.0)
        sigma = st.sidebar.slider("Volatility (σ)", min_value=0.01, max_value=1.0, value=0.25, step=0.01)
else:
    S0 = st.sidebar.number_input("Spot Price (S₀)", value=100.0, min_value=0.01, step=1.0)
    sigma = st.sidebar.slider("Volatility (σ)", min_value=0.01, max_value=1.0, value=0.25, step=0.01)

K = st.sidebar.number_input("Strike Price (K)", value=100.0, min_value=0.01, step=1.0)
T = st.sidebar.slider("Time to Expiration (Years)", min_value=0.01, max_value=5.0, value=1.0, step=0.01)
r = st.sidebar.slider("Risk-Free Rate (r)", min_value=0.0, max_value=0.20, value=0.05, step=0.01)

option_type = st.sidebar.selectbox("Option Type", ["Call", "Put"])
option_style = st.sidebar.selectbox("Option Style", ["European", "American"])

st.sidebar.markdown("---")
st.sidebar.header("Simulation Parameters")

num_simulations = st.sidebar.select_slider(
    "Number of Simulations",
    options=[1000, 5000, 10000, 50000, 100000, 500000, 1000000],
    value=100000
)

num_steps = st.sidebar.slider("Time Steps", min_value=10, max_value=500, value=100, step=10)

# Main content area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Pricing", "📊 Price Paths", "🎯 Greeks", "⚡ Performance", "🌊 Data Stream"
])

# Tab 1: Option Pricing
with tab1:
    st.header("Option Pricing Results")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Calculate Option Price", type="primary", use_container_width=True):
            with st.spinner("Running Monte Carlo simulation..."):
                # Price the option
                if option_style == "European":
                    option_price, std_error, comp_time = st.session_state.mc_engine.price_european_option(
                        S0, K, T, r, sigma, num_simulations, option_type.lower()
                    )
                    
                    # Also calculate Black-Scholes price for comparison
                    bs_price = GreeksCalculator.black_scholes_price(
                        S0, K, T, r, sigma, option_type.lower()
                    )
                    
                    st.session_state.option_price = option_price
                    st.session_state.bs_price = bs_price
                    st.session_state.std_error = std_error
                    st.session_state.comp_time = comp_time
                    
                else:  # American
                    option_price, comp_time = st.session_state.mc_engine.price_american_option_lsm(
                        S0, K, T, r, sigma, num_simulations, num_steps, option_type.lower()
                    )
                    
                    st.session_state.option_price = option_price
                    st.session_state.comp_time = comp_time
                    st.session_state.std_error = None
                    st.session_state.bs_price = None
    
    # Display results
    if 'option_price' in st.session_state:
        st.markdown("### Pricing Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=f"{option_style} {option_type} Price",
                value=f"${st.session_state.option_price:.4f}"
            )
        
        with col2:
            if st.session_state.std_error:
                st.metric(
                    label="Standard Error",
                    value=f"${st.session_state.std_error:.4f}"
                )
        
        with col3:
            st.metric(
                label="Computation Time",
                value=f"{st.session_state.comp_time*1000:.2f} ms"
            )
        
        with col4:
            if st.session_state.bs_price and option_style == "European":
                difference = abs(st.session_state.option_price - st.session_state.bs_price)
                st.metric(
                    label="BS Price Difference",
                    value=f"${difference:.4f}"
                )
        
        # Comparison table
        if option_style == "European" and st.session_state.bs_price:
            st.markdown("### Monte Carlo vs Black-Scholes Comparison")
            
            comparison_df = pd.DataFrame({
                'Method': ['Monte Carlo', 'Black-Scholes', 'Difference'],
                'Price': [
                    f"${st.session_state.option_price:.4f}",
                    f"${st.session_state.bs_price:.4f}",
                    f"${abs(st.session_state.option_price - st.session_state.bs_price):.4f}"
                ],
                'Error (%)': [
                    f"{(st.session_state.std_error / st.session_state.option_price * 100):.4f}%" if st.session_state.std_error else "N/A",
                    "0.0000% (Analytical)",
                    f"{(abs(st.session_state.option_price - st.session_state.bs_price) / st.session_state.bs_price * 100):.4f}%"
                ]
            })
            
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Sensitivity analysis
        st.markdown("### Quick Sensitivity Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Impact of Strike Price**")
            strikes = np.linspace(S0 * 0.8, S0 * 1.2, 10)
            prices = []
            
            for strike in strikes:
                if option_style == "European":
                    price, _, _ = st.session_state.mc_engine.price_european_option(
                        S0, strike, T, r, sigma, num_simulations // 10, option_type.lower()
                    )
                else:
                    price, _ = st.session_state.mc_engine.price_american_option_lsm(
                        S0, strike, T, r, sigma, num_simulations // 10, num_steps, option_type.lower()
                    )
                prices.append(price)
            
            fig_strike = go.Figure()
            fig_strike.add_trace(go.Scatter(
                x=strikes, y=prices,
                mode='lines+markers',
                name='Option Price',
                line=dict(color='#1f77b4', width=2)
            ))
            fig_strike.update_layout(
                xaxis_title="Strike Price",
                yaxis_title="Option Price",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_strike, use_container_width=True)
        
        with col2:
            st.markdown("**Impact of Volatility**")
            vols = np.linspace(0.1, 0.5, 10)
            vol_prices = []
            
            for vol in vols:
                if option_style == "European":
                    price, _, _ = st.session_state.mc_engine.price_european_option(
                        S0, K, T, r, vol, num_simulations // 10, option_type.lower()
                    )
                else:
                    price, _ = st.session_state.mc_engine.price_american_option_lsm(
                        S0, K, T, r, vol, num_simulations // 10, num_steps, option_type.lower()
                    )
                vol_prices.append(price)
            
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=vols * 100, y=vol_prices,
                mode='lines+markers',
                name='Option Price',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_vol.update_layout(
                xaxis_title="Volatility (%)",
                yaxis_title="Option Price",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_vol, use_container_width=True)

# Tab 2: Price Paths Visualization
with tab2:
    st.header("Simulated Price Paths")
    
    num_paths_to_plot = st.slider("Number of Paths to Display", min_value=10, max_value=500, value=100, step=10)
    
    if st.button("Generate Price Paths", use_container_width=True):
        with st.spinner("Simulating price paths..."):
            price_paths, terminal_prices = st.session_state.mc_engine.simulate_price_paths(
                S0, K, T, r, sigma, num_paths_to_plot, num_steps, option_type.lower()
            )
            
            st.session_state.price_paths = price_paths
            st.session_state.terminal_prices = terminal_prices
    
    if 'price_paths' in st.session_state:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Price Path Simulation")
            
            fig_paths = go.Figure()
            
            time_steps = np.linspace(0, T, num_steps + 1)
            
            # Plot individual paths
            for i in range(min(num_paths_to_plot, 100)):
                fig_paths.add_trace(go.Scatter(
                    x=time_steps,
                    y=st.session_state.price_paths[i],
                    mode='lines',
                    line=dict(width=0.5, color='rgba(100, 100, 100, 0.3)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Plot strike price line
            fig_paths.add_trace(go.Scatter(
                x=[0, T],
                y=[K, K],
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name=f'Strike (K={K})'
            ))
            
            # Plot initial price line
            fig_paths.add_trace(go.Scatter(
                x=[0, T],
                y=[S0, S0],
                mode='lines',
                line=dict(color='green', width=2, dash='dash'),
                name=f'Initial (S₀={S0})'
            ))
            
            fig_paths.update_layout(
                xaxis_title="Time (Years)",
                yaxis_title="Stock Price",
                height=500,
                hovermode='closest'
            )
            
            st.plotly_chart(fig_paths, use_container_width=True)
        
        with col2:
            st.markdown("### Terminal Price Distribution")
            
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=st.session_state.terminal_prices,
                nbinsx=50,
                name='Terminal Prices',
                marker_color='#1f77b4'
            ))
            
            fig_dist.add_vline(
                x=K,
                line_dash="dash",
                line_color="red",
                annotation_text="Strike"
            )
            
            fig_dist.update_layout(
                xaxis_title="Terminal Stock Price",
                yaxis_title="Frequency",
                height=500,
                showlegend=False
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
        
        # Statistics
        st.markdown("### Path Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean Terminal Price", f"${np.mean(st.session_state.terminal_prices):.2f}")
        
        with col2:
            st.metric("Std Dev", f"${np.std(st.session_state.terminal_prices):.2f}")
        
        with col3:
            st.metric("Min Price", f"${np.min(st.session_state.terminal_prices):.2f}")
        
        with col4:
            st.metric("Max Price", f"${np.max(st.session_state.terminal_prices):.2f}")

# Tab 3: Greeks Analysis
with tab3:
    st.header("Option Greeks Analysis")
    
    st.markdown("""
    Greeks measure the sensitivity of an option's price to various factors.
    These are calculated using the Black-Scholes model.
    """)
    
    if st.button("Calculate Greeks", use_container_width=True):
        greeks = GreeksCalculator.calculate_all_greeks(
            S0, K, T, r, sigma, option_type.lower()
        )
        st.session_state.greeks = greeks
    
    if 'greeks' in st.session_state:
        # Display Greeks
        st.markdown("### Option Greeks")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Delta (Δ)",
                value=f"{st.session_state.greeks['Delta']:.4f}",
                help="Sensitivity to stock price changes"
            )
        
        with col2:
            st.metric(
                label="Gamma (Γ)",
                value=f"{st.session_state.greeks['Gamma']:.4f}",
                help="Rate of change of Delta"
            )
        
        with col3:
            st.metric(
                label="Vega (ν)",
                value=f"{st.session_state.greeks['Vega']:.4f}",
                help="Sensitivity to volatility (per 1%)"
            )
        
        with col4:
            st.metric(
                label="Theta (Θ)",
                value=f"{st.session_state.greeks['Theta']:.4f}",
                help="Time decay (per day)"
            )
        
        with col5:
            st.metric(
                label="Rho (ρ)",
                value=f"{st.session_state.greeks['Rho']:.4f}",
                help="Sensitivity to interest rate (per 1%)"
            )
        
        # Greeks visualization
        st.markdown("### Greeks Sensitivity Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Delta vs Stock Price
            st.markdown("**Delta vs Stock Price**")
            stock_prices = np.linspace(S0 * 0.5, S0 * 1.5, 50)
            deltas = [GreeksCalculator.calculate_delta(s, K, T, r, sigma, option_type.lower()) for s in stock_prices]
            
            fig_delta = go.Figure()
            fig_delta.add_trace(go.Scatter(
                x=stock_prices, y=deltas,
                mode='lines',
                line=dict(color='#1f77b4', width=2)
            ))
            fig_delta.add_vline(x=S0, line_dash="dash", line_color="green", annotation_text="Current")
            fig_delta.add_vline(x=K, line_dash="dash", line_color="red", annotation_text="Strike")
            fig_delta.update_layout(
                xaxis_title="Stock Price",
                yaxis_title="Delta",
                height=300
            )
            st.plotly_chart(fig_delta, use_container_width=True)
            
            # Vega vs Volatility
            st.markdown("**Vega vs Volatility**")
            vols = np.linspace(0.05, 0.75, 50)
            vegas = [GreeksCalculator.calculate_vega(S0, K, T, r, v) for v in vols]
            
            fig_vega = go.Figure()
            fig_vega.add_trace(go.Scatter(
                x=vols * 100, y=vegas,
                mode='lines',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_vega.add_vline(x=sigma * 100, line_dash="dash", line_color="green", annotation_text="Current")
            fig_vega.update_layout(
                xaxis_title="Volatility (%)",
                yaxis_title="Vega",
                height=300
            )
            st.plotly_chart(fig_vega, use_container_width=True)
        
        with col2:
            # Gamma vs Stock Price
            st.markdown("**Gamma vs Stock Price**")
            gammas = [GreeksCalculator.calculate_gamma(s, K, T, r, sigma) for s in stock_prices]
            
            fig_gamma = go.Figure()
            fig_gamma.add_trace(go.Scatter(
                x=stock_prices, y=gammas,
                mode='lines',
                line=dict(color='#2ca02c', width=2)
            ))
            fig_gamma.add_vline(x=S0, line_dash="dash", line_color="green", annotation_text="Current")
            fig_gamma.add_vline(x=K, line_dash="dash", line_color="red", annotation_text="Strike")
            fig_gamma.update_layout(
                xaxis_title="Stock Price",
                yaxis_title="Gamma",
                height=300
            )
            st.plotly_chart(fig_gamma, use_container_width=True)
            
            # Theta vs Time
            st.markdown("**Theta vs Time to Expiration**")
            times = np.linspace(0.01, 2.0, 50)
            thetas = [GreeksCalculator.calculate_theta(S0, K, t, r, sigma, option_type.lower()) for t in times]
            
            fig_theta = go.Figure()
            fig_theta.add_trace(go.Scatter(
                x=times, y=thetas,
                mode='lines',
                line=dict(color='#d62728', width=2)
            ))
            fig_theta.add_vline(x=T, line_dash="dash", line_color="green", annotation_text="Current")
            fig_theta.update_layout(
                xaxis_title="Time to Expiration (Years)",
                yaxis_title="Theta (per day)",
                height=300
            )
            st.plotly_chart(fig_theta, use_container_width=True)

# Tab 4: Performance Metrics
with tab4:
    st.header("Performance Metrics")
    
    st.markdown("""
    Monitor the computational performance of the Monte Carlo engine.
    Optimized for high-frequency demand forecasting with 10,000+ simulations per second.
    """)
    
    # Run performance benchmark
    if st.button("Run Performance Benchmark", use_container_width=True):
        with st.spinner("Running benchmark..."):
            benchmark_results = []
            
            sim_counts = [1000, 5000, 10000, 50000, 100000]
            
            for sim_count in sim_counts:
                start_time = time.time()
                
                if option_style == "European":
                    _, _, comp_time = st.session_state.mc_engine.price_european_option(
                        S0, K, T, r, sigma, sim_count, option_type.lower()
                    )
                else:
                    _, comp_time = st.session_state.mc_engine.price_american_option_lsm(
                        S0, K, T, r, sigma, sim_count, num_steps, option_type.lower()
                    )
                
                simulations_per_second = sim_count / comp_time
                
                benchmark_results.append({
                    'Simulations': sim_count,
                    'Time (ms)': comp_time * 1000,
                    'Sims/Second': simulations_per_second
                })
            
            st.session_state.benchmark_results = pd.DataFrame(benchmark_results)
    
    if 'benchmark_results' in st.session_state:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Benchmark Results")
            st.dataframe(
                st.session_state.benchmark_results.style.format({
                    'Simulations': '{:,.0f}',
                    'Time (ms)': '{:.2f}',
                    'Sims/Second': '{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Key metrics
            max_throughput = st.session_state.benchmark_results['Sims/Second'].max()
            avg_throughput = st.session_state.benchmark_results['Sims/Second'].mean()
            
            st.metric("Max Throughput", f"{max_throughput:,.0f} sims/sec")
            st.metric("Avg Throughput", f"{avg_throughput:,.0f} sims/sec")
            
            if max_throughput >= 10000:
                st.success("✓ Meets high-frequency requirement (10,000+ sims/sec)")
            else:
                st.warning("⚠ Below target throughput")
        
        with col2:
            st.markdown("### Performance Charts")
            
            fig_perf = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Computation Time vs Simulations", "Throughput vs Simulations")
            )
            
            # Computation time chart
            fig_perf.add_trace(
                go.Scatter(
                    x=st.session_state.benchmark_results['Simulations'],
                    y=st.session_state.benchmark_results['Time (ms)'],
                    mode='lines+markers',
                    name='Time',
                    line=dict(color='#1f77b4', width=2)
                ),
                row=1, col=1
            )
            
            # Throughput chart
            fig_perf.add_trace(
                go.Scatter(
                    x=st.session_state.benchmark_results['Simulations'],
                    y=st.session_state.benchmark_results['Sims/Second'],
                    mode='lines+markers',
                    name='Throughput',
                    line=dict(color='#2ca02c', width=2)
                ),
                row=2, col=1
            )
            
            fig_perf.update_xaxes(title_text="Number of Simulations", row=1, col=1)
            fig_perf.update_xaxes(title_text="Number of Simulations", row=2, col=1)
            fig_perf.update_yaxes(title_text="Time (ms)", row=1, col=1)
            fig_perf.update_yaxes(title_text="Simulations/Second", row=2, col=1)
            
            fig_perf.update_layout(height=600, showlegend=False)
            
            st.plotly_chart(fig_perf, use_container_width=True)

# Tab 5: Data Stream Simulation
with tab5:
    st.header("Real-Time Data Stream Simulation")
    
    st.markdown("""
    Simulated Kafka-like data stream for live market synchronization.
    In production, this would connect to a real Kafka broker processing 10,000+ messages/second.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        stream_ticker = st.text_input("Ticker for Stream", value="AAPL")
        num_messages = st.slider("Number of Messages", min_value=100, max_value=10000, value=1000, step=100)
        
        if st.button("Simulate Data Stream", use_container_width=True):
            with st.spinner("Generating simulated stream..."):
                stream_data = st.session_state.market_feed.simulate_kafka_stream(
                    stream_ticker, num_messages
                )
                st.session_state.stream_data = stream_data
                
                # Calculate message rate
                time_span = (stream_data['timestamp'].iloc[-1] - stream_data['timestamp'].iloc[0]).total_seconds()
                message_rate = len(stream_data) / time_span if time_span > 0 else 0
                st.session_state.message_rate = message_rate
    
    if 'stream_data' in st.session_state:
        with col1:
            st.metric("Messages Processed", f"{len(st.session_state.stream_data):,}")
            st.metric("Message Rate", f"{st.session_state.message_rate:,.0f} msg/sec")
            
            if st.session_state.message_rate >= 10000:
                st.success("✓ Meets high-frequency requirement")
            
            # Stream statistics
            st.markdown("### Stream Statistics")
            stream_stats = pd.DataFrame({
                'Metric': ['Min Price', 'Max Price', 'Avg Price', 'Volatility', 'Total Volume'],
                'Value': [
                    f"${st.session_state.stream_data['price'].min():.2f}",
                    f"${st.session_state.stream_data['price'].max():.2f}",
                    f"${st.session_state.stream_data['price'].mean():.2f}",
                    f"{st.session_state.stream_data['price'].std():.4f}",
                    f"{st.session_state.stream_data['volume'].sum():,}"
                ]
            })
            st.dataframe(stream_stats, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### Real-Time Price Stream")
            
            fig_stream = go.Figure()
            
            fig_stream.add_trace(go.Scatter(
                x=st.session_state.stream_data['timestamp'],
                y=st.session_state.stream_data['price'],
                mode='lines',
                name='Price',
                line=dict(color='#1f77b4', width=1)
            ))
            
            fig_stream.update_layout(
                xaxis_title="Timestamp",
                yaxis_title="Price",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_stream, use_container_width=True)
            
            # Volume chart
            st.markdown("### Volume Distribution")
            
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(
                x=st.session_state.stream_data['timestamp'],
                y=st.session_state.stream_data['volume'],
                name='Volume',
                marker_color='#2ca02c'
            ))
            
            fig_volume.update_layout(
                xaxis_title="Timestamp",
                yaxis_title="Volume",
                height=300
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Monte Carlo Option Pricer | High-Performance Financial Modeling | Nov 2024 – May 2025</p>
</div>
""", unsafe_allow_html=True)
