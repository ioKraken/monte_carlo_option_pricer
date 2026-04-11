import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


class MarketDataFeed:
    """
    Simulated real-time market data feed.
    In production, this would connect to a Kafka stream for live data synchronization.
    """
    
    def __init__(self):
        self.last_update = None
        self.cache = {}
        
    def get_stock_data(self, ticker: str, use_live: bool = True) -> Dict:
        """
        Fetch stock data from Yahoo Finance.
        
        Parameters:
        -----------
        ticker : str
            Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        use_live : bool
            Whether to fetch live data or use cached data
            
        Returns:
        --------
        dict : Dictionary containing stock price, volatility, and other metrics
        """
        try:
            # Fetch stock data
            stock = yf.Ticker(ticker)
            
            # Get current price
            if use_live:
                hist = stock.history(period="1d", interval="1m")
                if len(hist) > 0:
                    current_price = hist['Close'].iloc[-1]
                else:
                    hist = stock.history(period="5d")
                    current_price = hist['Close'].iloc[-1]
            else:
                hist = stock.history(period="1mo")
                current_price = hist['Close'].iloc[-1]
            
            # Calculate historical volatility (annualized)
            returns = np.log(hist['Close'] / hist['Close'].shift(1))
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            # Get additional info
            info = stock.info
            
            data = {
                'ticker': ticker,
                'current_price': float(current_price),
                'volatility': float(volatility) if not np.isnan(volatility) else 0.25,
                'timestamp': datetime.now(),
                'company_name': info.get('longName', ticker),
                'previous_close': float(hist['Close'].iloc[-2]) if len(hist) > 1 else float(current_price),
            }
            
            self.cache[ticker] = data
            self.last_update = datetime.now()
            
            return data
            
        except Exception as e:
            # Return cached data or defaults if fetch fails
            if ticker in self.cache:
                return self.cache[ticker]
            else:
                return {
                    'ticker': ticker,
                    'current_price': 100.0,
                    'volatility': 0.25,
                    'timestamp': datetime.now(),
                    'company_name': ticker,
                    'previous_close': 100.0,
                    'error': str(e)
                }
    
    def simulate_kafka_stream(self, ticker: str, num_messages: int = 100) -> pd.DataFrame:
        """
        Simulate a Kafka data stream with high-frequency price updates.
        In production, this would connect to a real Kafka broker.
        
        Parameters:
        -----------
        ticker : str
            Stock ticker symbol
        num_messages : int
            Number of simulated messages to generate
            
        Returns:
        --------
        pd.DataFrame : Simulated streaming data
        """
        # Get base price
        data = self.get_stock_data(ticker)
        base_price = data['current_price']
        volatility = data['volatility']
        
        # Simulate high-frequency price updates
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(seconds=num_messages),
            end=datetime.now(),
            periods=num_messages
        )
        
        # Generate price movements using geometric Brownian motion
        dt = 1 / (252 * 6.5 * 3600)  # 1 second in trading year
        returns = np.random.normal(0, volatility * np.sqrt(dt), num_messages)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create DataFrame
        stream_data = pd.DataFrame({
            'timestamp': timestamps,
            'ticker': ticker,
            'price': prices,
            'volume': np.random.randint(100, 10000, num_messages),
            'bid': prices * 0.9995,
            'ask': prices * 1.0005,
        })
        
        return stream_data
    
    def get_option_chain(self, ticker: str) -> Optional[Dict]:
        """
        Fetch option chain data for a given ticker.
        
        Returns:
        --------
        dict : Option chain data including available strikes and expirations
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            
            if len(expirations) > 0:
                # Get first expiration date
                opt_chain = stock.option_chain(expirations[0])
                
                return {
                    'expirations': expirations,
                    'calls': opt_chain.calls,
                    'puts': opt_chain.puts,
                    'strikes': sorted(opt_chain.calls['strike'].unique())
                }
            else:
                return None
                
        except Exception as e:
            return None
    
    def calculate_risk_free_rate(self) -> float:
        """
        Get current risk-free rate (approximated by 10-year Treasury yield).
        In production, this would fetch from a real-time data source.
        
        Returns:
        --------
        float : Risk-free rate (annualized)
        """
        try:
            # Fetch 10-year Treasury yield
            treasury = yf.Ticker("^TNX")
            hist = treasury.history(period="1d")
            
            if len(hist) > 0:
                rate = hist['Close'].iloc[-1] / 100  # Convert from percentage
                return float(rate)
            else:
                return 0.04  # Default 4% if fetch fails
                
        except:
            return 0.04  # Default 4%
