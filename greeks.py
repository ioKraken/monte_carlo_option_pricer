import numpy as np
from scipy.stats import norm
from typing import Dict


class GreeksCalculator:
    """
    Calculator for European option Greeks using analytical Black-Scholes formulas.
    """
    
    @staticmethod
    def black_scholes_price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> float:
        """Calculate Black-Scholes option price."""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return price
    
    @staticmethod
    def calculate_delta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> float:
        """
        Calculate Delta: rate of change of option price with respect to stock price.
        Delta measures the sensitivity of the option price to changes in the underlying asset price.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1
        
        return delta
    
    @staticmethod
    def calculate_gamma(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate Gamma: rate of change of Delta with respect to stock price.
        Gamma measures the curvature of the option value relative to the underlying price.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        return gamma
    
    @staticmethod
    def calculate_vega(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate Vega: rate of change of option price with respect to volatility.
        Vega measures sensitivity to changes in implied volatility.
        Note: Vega is typically expressed per 1% change in volatility.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for 1% change
        
        return vega
    
    @staticmethod
    def calculate_theta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> float:
        """
        Calculate Theta: rate of change of option price with respect to time.
        Theta measures time decay (typically negative for long options).
        Note: Theta is typically expressed per day, so we divide by 365.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == "call":
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            ) / 365
        else:  # put
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            ) / 365
        
        return theta
    
    @staticmethod
    def calculate_rho(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> float:
        """
        Calculate Rho: rate of change of option price with respect to interest rate.
        Rho measures sensitivity to changes in the risk-free rate.
        Note: Rho is typically expressed per 1% change in interest rate.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == "call":
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:  # put
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        return rho
    
    @classmethod
    def calculate_all_greeks(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option.
        
        Returns:
        --------
        dict : Dictionary containing all Greeks (Delta, Gamma, Vega, Theta, Rho)
        """
        greeks = {
            "Delta": cls.calculate_delta(S, K, T, r, sigma, option_type),
            "Gamma": cls.calculate_gamma(S, K, T, r, sigma),
            "Vega": cls.calculate_vega(S, K, T, r, sigma),
            "Theta": cls.calculate_theta(S, K, T, r, sigma, option_type),
            "Rho": cls.calculate_rho(S, K, T, r, sigma, option_type)
        }
        
        return greeks
    
    @staticmethod
    def calculate_implied_volatility(
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = "call",
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Returns:
        --------
        float : Implied volatility (annualized)
        """
        # Initial guess
        sigma = 0.3
        
        for i in range(max_iterations):
            price = GreeksCalculator.black_scholes_price(S, K, T, r, sigma, option_type)
            vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma) * 100  # Undo the /100
            
            diff = option_price - price
            
            if abs(diff) < tolerance:
                return sigma
            
            if vega == 0:
                break
            
            sigma = sigma + diff / vega
            
            # Ensure sigma stays positive
            sigma = max(sigma, 1e-6)
        
        return sigma
