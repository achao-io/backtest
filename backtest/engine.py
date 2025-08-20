"""Backtesting engine - does ONE thing: orchestrates backtests."""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .data_loader import Bar
from .strategy import Strategy
from .portfolio import Portfolio
from .order import Order


@dataclass
class Results:
    """
    Backtest results - does ONE thing: holds performance data.
    
    Simple container for backtest outcomes.
    """
    initial_cash: float
    final_cash: float
    final_portfolio_value: float
    total_orders: int
    executed_orders: int
    start_date: datetime
    end_date: datetime
    
    @property
    def total_return(self) -> float:
        """Calculate total return percentage."""
        return (self.final_portfolio_value - self.initial_cash) / self.initial_cash
    
    @property
    def execution_rate(self) -> float:
        """Calculate order execution rate."""
        return self.executed_orders / self.total_orders if self.total_orders > 0 else 0.0


class Engine:
    """
    Backtesting engine - does ONE thing: orchestrates strategy execution.
    
    Unix Philosophy: Single responsibility for backtest coordination.
    DRY: Reuses all other components.
    Simple: Linear execution flow.
    """
    
    def __init__(self, initial_cash: float = 100000):
        """
        Initialize backtesting engine.
        
        Args:
            initial_cash: Starting cash for backtests
        """
        if initial_cash <= 0:
            raise ValueError(f"Initial cash must be positive, got {initial_cash}")
        
        self.initial_cash = initial_cash
    
    def run(self, strategy: Strategy, data: List[Bar]) -> Results:
        """
        Run a backtest with the given strategy and data.
        
        Args:
            strategy: Trading strategy to test
            data: Market data bars (should be sorted by timestamp)
            
        Returns:
            Results object with backtest performance
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Initialize portfolio
        portfolio = Portfolio(self.initial_cash)
        
        # Track metrics
        total_orders = 0
        executed_orders = 0
        
        # Process each bar
        for bar in data:
            # Get orders from strategy
            orders = strategy.on_data(bar)
            total_orders += len(orders)
            
            # Execute orders
            for order in orders:
                success = portfolio.execute_order(order, bar.close)
                if success:
                    executed_orders += 1
                    
                    # Update strategy position tracking
                    updated_position = portfolio.get_position(order.ticker)
                    if updated_position:
                        strategy.update_position(updated_position)
                    else:
                        # Position was closed
                        from .order import Position
                        closed_position = Position(order.ticker, 0, 0.0)
                        strategy.update_position(closed_position)
        
        # Calculate final portfolio value
        final_prices = self._get_final_prices(data)
        final_portfolio_value = portfolio.calculate_portfolio_value(final_prices)
        
        return Results(
            initial_cash=self.initial_cash,
            final_cash=portfolio.cash,
            final_portfolio_value=final_portfolio_value,
            total_orders=total_orders,
            executed_orders=executed_orders,
            start_date=data[0].timestamp,
            end_date=data[-1].timestamp
        )
    
    def _get_final_prices(self, data: List[Bar]) -> Dict[str, float]:
        """Extract final prices for each ticker from the data."""
        final_prices = {}
        
        # Get the last price for each ticker
        for bar in reversed(data):
            if bar.ticker not in final_prices:
                final_prices[bar.ticker] = bar.close
        
        return final_prices