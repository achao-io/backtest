"""Buy and hold strategy - simplest possible strategy implementation."""

from typing import List

from backtest.strategy import Strategy
from backtest.data_loader import Bar
from backtest.order import Order


class BuyAndHoldStrategy(Strategy):
    """
    Buy and hold strategy - does ONE thing: buys once and holds.
    
    Perfect example of Unix philosophy:
    - Single responsibility: buy on first bar, then do nothing
    - Simple logic that's easy to understand and test
    - Demonstrates the strategy interface
    """
    
    def __init__(self, investment_per_ticker: float = 10000):
        """
        Initialize buy and hold strategy.
        
        Args:
            investment_per_ticker: Dollar amount to invest in each ticker
        """
        super().__init__()
        
        if investment_per_ticker <= 0:
            raise ValueError(f"Investment per ticker must be positive, got {investment_per_ticker}")
        
        self.investment_per_ticker = investment_per_ticker
        self._bought_tickers = set()  # Track which tickers we've already bought
    
    def on_data(self, bar: Bar) -> List[Order]:
        """
        Process market data - buy once per ticker, then hold forever.
        
        Args:
            bar: Market data bar
            
        Returns:
            List containing buy order for first bar of each ticker, empty list afterward
        """
        # Only buy if we haven't bought this ticker yet
        if bar.ticker not in self._bought_tickers:
            # Calculate quantity based on investment amount and current price
            quantity = int(self.investment_per_ticker / bar.close)
            
            if quantity > 0:  # Only buy if we can afford at least 1 share
                self._bought_tickers.add(bar.ticker)
                return [self.market_buy(bar.ticker, quantity)]
        
        # Already bought this ticker or can't afford any shares
        return []