import numpy as np
from typing import Tuple
import time


class MonteCarloEngine:
    """
    High-performance Monte Carlo simulation engine for option pricing.
    Optimized for rapid computation (10,000+ paths/second).
    """
    
    def __init__(self, seed: int = 42):
        """Initialize the Monte Carlo engine with a random seed."""
        np.random.seed(seed)
        self.last_computation_time = 0
        self.last_num_simulations = 0
        
    def simulate_price_paths(
        self,
        S0: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        num_simulations: int,
        num_steps: int,
        option_type: str = "call"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate stock price paths using Geometric Brownian Motion.
        
        Parameters:
        -----------
        S0 : float
            Initial stock price
        K : float
            Strike price
        T : float
            Time to expiration (in years)
        r : float
            Risk-free interest rate
        sigma : float
            Volatility (annualized)
        num_simulations : int
            Number of Monte Carlo paths to simulate
        num_steps : int
            Number of time steps in each path
        option_type : str
            'call' or 'put'
            
        Returns:
        --------
        price_paths : np.ndarray
            Array of simulated price paths (num_simulations x num_steps)
        terminal_prices : np.ndarray
            Array of terminal stock prices (num_simulations,)
        """
        start_time = time.time()
        
        dt = T / num_steps
        
        # Pre-allocate array for efficiency
        price_paths = np.zeros((num_simulations, num_steps + 1))
        price_paths[:, 0] = S0
        
        # Generate all random numbers at once for better performance
        Z = np.random.standard_normal((num_simulations, num_steps))
        
        # Vectorized computation of price paths
        for t in range(1, num_steps + 1):
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z[:, t-1]
            )
        
        terminal_prices = price_paths[:, -1]
        
        self.last_computation_time = time.time() - start_time
        self.last_num_simulations = num_simulations
        
        return price_paths, terminal_prices
    
    def price_european_option(
        self,
        S0: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        num_simulations: int,
        option_type: str = "call"
    ) -> Tuple[float, float, float]:
        """
        Price a European option using Monte Carlo simulation.
        
        Returns:
        --------
        option_price : float
            Estimated fair value of the option
        std_error : float
            Standard error of the estimate
        computation_time : float
            Time taken for computation (seconds)
        """
        start_time = time.time()
        
        # Simulate final stock prices
        Z = np.random.standard_normal(num_simulations)
        ST = S0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
        
        # Calculate payoffs
        if option_type.lower() == "call":
            payoffs = np.maximum(ST - K, 0)
        else:  # put
            payoffs = np.maximum(K - ST, 0)
        
        # Discount payoffs to present value
        option_price = np.exp(-r * T) * np.mean(payoffs)
        std_error = np.std(payoffs) / np.sqrt(num_simulations)
        
        computation_time = time.time() - start_time
        
        # Update performance metrics
        self.last_computation_time = computation_time
        self.last_num_simulations = num_simulations
        
        return option_price, std_error, computation_time
    
    def price_american_option_lsm(
        self,
        S0: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        num_simulations: int,
        num_steps: int,
        option_type: str = "call"
    ) -> Tuple[float, float]:
        """
        Price an American option using Longstaff-Schwartz (LSM) algorithm.
        
        Returns:
        --------
        option_price : float
            Estimated fair value of the option
        computation_time : float
            Time taken for computation (seconds)
        """
        start_time = time.time()
        
        dt = T / num_steps
        discount_factor = np.exp(-r * dt)
        
        # Simulate price paths
        price_paths, _ = self.simulate_price_paths(
            S0, K, T, r, sigma, num_simulations, num_steps, option_type
        )
        
        # Calculate intrinsic values at all time steps
        if option_type.lower() == "call":
            intrinsic_values = np.maximum(price_paths - K, 0)
        else:  # put
            intrinsic_values = np.maximum(K - price_paths, 0)
        
        # Track cash flows: when and how much each path receives
        cash_flow_time = np.full(num_simulations, num_steps)  # Time of exercise (default: maturity)
        cash_flow_amount = intrinsic_values[:, -1]  # Amount received (default: terminal payoff)
        
        # Backward induction using Longstaff-Schwartz algorithm
        for t in range(num_steps - 1, 0, -1):
            # Find paths that are in-the-money at time t
            itm = intrinsic_values[:, t] > 0
            
            if np.sum(itm) == 0:
                continue
            
            # Get paths that haven't exercised yet and are ITM
            not_exercised = cash_flow_time > t
            eligible = itm & not_exercised
            
            if np.sum(eligible) == 0:
                continue
            
            # Compute discounted future cash flows for regression
            # Discount from exercise time back to time t
            time_to_exercise = cash_flow_time[eligible] - t
            discount_to_t = np.exp(-r * dt * time_to_exercise)
            discounted_cash_flows = cash_flow_amount[eligible] * discount_to_t
            
            # Regression: estimate continuation value as function of stock price
            X = price_paths[eligible, t]
            Y = discounted_cash_flows
            
            # Polynomial regression (degree 2)
            if len(X) > 3:  # Need enough points for regression
                regression = np.polyfit(X, Y, 2)
                continuation_value = np.polyval(regression, X)
                
                # Exercise if immediate payoff exceeds continuation value
                exercise_value = intrinsic_values[eligible, t]
                should_exercise = exercise_value > continuation_value
                
                # Update cash flows for paths that exercise now
                exercise_indices = np.where(eligible)[0][should_exercise]
                cash_flow_time[exercise_indices] = t
                cash_flow_amount[exercise_indices] = intrinsic_values[exercise_indices, t]
        
        # Consider immediate exercise at t=0
        immediate_value = intrinsic_values[:, 0]
        not_exercised = cash_flow_time > 0
        
        if np.sum(not_exercised) > 0:
            # Discount future cash flows to t=0
            time_to_exercise = cash_flow_time[not_exercised]
            discount_to_0 = np.exp(-r * dt * time_to_exercise)
            continuation_value_0 = cash_flow_amount[not_exercised] * discount_to_0
            
            # Exercise now if better
            should_exercise_0 = immediate_value[not_exercised] > continuation_value_0
            exercise_indices_0 = np.where(not_exercised)[0][should_exercise_0]
            cash_flow_time[exercise_indices_0] = 0
            cash_flow_amount[exercise_indices_0] = immediate_value[exercise_indices_0]
        
        # Discount all cash flows to t=0
        discount_to_0 = np.exp(-r * dt * cash_flow_time)
        present_values = cash_flow_amount * discount_to_0
        
        # Option price is expected present value
        option_price = np.mean(present_values)
        
        # Sanity check: American option must be at least as valuable as immediate exercise
        immediate_exercise_value = np.mean(immediate_value)
        option_price = max(option_price, immediate_exercise_value)
        
        computation_time = time.time() - start_time
        
        # Update performance metrics
        self.last_computation_time = computation_time
        self.last_num_simulations = num_simulations
        
        return option_price, computation_time
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics from the last simulation."""
        if self.last_num_simulations > 0 and self.last_computation_time > 0:
            simulations_per_second = self.last_num_simulations / self.last_computation_time
        else:
            simulations_per_second = 0
            
        return {
            "computation_time": self.last_computation_time,
            "num_simulations": self.last_num_simulations,
            "simulations_per_second": simulations_per_second
        }
