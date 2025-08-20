"""Strategy interface for backtesting - does ONE thing: converts data to orders."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .data_loader import Bar
from .order import Order, Position


class Strategy(ABC):
    """
    Abstract strategy class - does ONE thing: processes market data into orders.
    
    Unix Philosophy: Single responsibility for trading logic.
    DRY: Reusable base for all strategy implementations.
    Simple: Minimal interface with clear contract.
    """
    
    def __init__(self):
        """Initialize strategy with empty position tracking."""
        self._positions: dict[str, Position] = {}
    
    @abstractmethod
    def on_data(self, bar: Bar) -> List[Order]:
        """
        Process a market data bar and return orders to execute.
        
        This is the ONLY responsibility: convert data → orders.
        
        Args:
            bar: Market data for a single ticker at a point in time
            
        Returns:
            List of orders to execute (empty list if no action)
        """
        pass
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get current position for a ticker."""
        return self._positions.get(ticker)
    
    def update_position(self, position: Position) -> None:
        """Update position tracking (called by Portfolio)."""
        if position.is_flat:
            self._positions.pop(position.ticker, None)
        else:
            self._positions[position.ticker] = position
    
    @property
    def positions(self) -> dict[str, Position]:
        """Get all current positions."""
        return self._positions.copy()
    
    # Convenience methods for common order types
    def market_buy(self, ticker: str, quantity: int) -> Order:
        """Create a market buy order."""
        return Order(side="buy", ticker=ticker, quantity=quantity)
    
    def market_sell(self, ticker: str, quantity: int) -> Order:
        """Create a market sell order."""
        return Order(side="sell", ticker=ticker, quantity=quantity)
    
    def limit_buy(self, ticker: str, quantity: int, price: float) -> Order:
        """Create a limit buy order."""
        return Order(side="buy", ticker=ticker, quantity=quantity, price=price)
    
    def limit_sell(self, ticker: str, quantity: int, price: float) -> Order:
        """Create a limit sell order.""" 
        return Order(side="sell", ticker=ticker, quantity=quantity, price=price)