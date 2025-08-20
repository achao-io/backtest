"""Portfolio management - does ONE thing: manages cash and positions."""

from typing import Dict, Optional

from .order import Order, Position


class Portfolio:
    """
    Portfolio manager - does ONE thing: executes orders and tracks cash/positions.
    
    Unix Philosophy: Single responsibility for money management.
    DRY: Reuses Order and Position classes.
    Simple: Clear interface for order execution.
    """
    
    def __init__(self, initial_cash: float):
        """
        Initialize portfolio with starting cash.
        
        Args:
            initial_cash: Starting cash balance
        """
        if initial_cash <= 0:
            raise ValueError(f"Initial cash must be positive, got {initial_cash}")
        
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self._positions: Dict[str, Position] = {}
    
    def execute_order(self, order: Order, execution_price: float) -> bool:
        """
        Execute an order at the given price.
        
        Args:
            order: The order to execute
            execution_price: Price at which to execute the order
            
        Returns:
            True if order was executed, False if insufficient funds/shares
        """
        if execution_price <= 0:
            raise ValueError(f"Execution price must be positive, got {execution_price}")
        
        trade_value = order.quantity * execution_price
        
        if order.is_buy:
            return self._execute_buy(order, execution_price, trade_value)
        else:
            return self._execute_sell(order, execution_price, trade_value)
    
    def _execute_buy(self, order: Order, price: float, trade_value: float) -> bool:
        """Execute a buy order."""
        # Check if we have enough cash
        if trade_value > self.cash:
            return False  # Insufficient funds
        
        # Update cash
        self.cash -= trade_value
        
        # Update position
        self._update_position(order.ticker, order.quantity, price)
        return True
    
    def _execute_sell(self, order: Order, price: float, trade_value: float) -> bool:
        """Execute a sell order."""
        current_position = self._positions.get(order.ticker)
        
        # For simplicity, allow short selling (negative positions)
        # In real trading, this would require margin requirements
        
        # Update cash (receive money from sale)
        self.cash += trade_value
        
        # Update position (reduce/create short position)
        self._update_position(order.ticker, -order.quantity, price)
        return True
    
    def _update_position(self, ticker: str, quantity_change: int, price: float) -> None:
        """Update position with new shares at given price."""
        current_position = self._positions.get(ticker)
        
        if current_position is None:
            # New position
            self._positions[ticker] = Position(
                ticker=ticker,
                quantity=quantity_change,
                avg_cost=price
            )
        else:
            # Existing position - update with new average cost
            total_quantity = current_position.quantity + quantity_change
            
            if total_quantity == 0:
                # Position closed
                del self._positions[ticker]
            else:
                # Calculate new average cost
                if (current_position.quantity > 0 and quantity_change > 0) or \
                   (current_position.quantity < 0 and quantity_change < 0):
                    # Adding to existing position (same direction)
                    total_cost = (current_position.quantity * current_position.avg_cost + 
                                quantity_change * price)
                    new_avg_cost = total_cost / total_quantity
                else:
                    # Reducing position or changing direction
                    # Keep original avg cost for simplicity
                    new_avg_cost = current_position.avg_cost
                
                self._positions[ticker] = Position(
                    ticker=ticker,
                    quantity=total_quantity,
                    avg_cost=new_avg_cost
                )
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get current position for a ticker."""
        return self._positions.get(ticker)
    
    def get_positions(self) -> Dict[str, Position]:
        """Get all current positions."""
        return self._positions.copy()
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value using current market prices.
        
        Args:
            current_prices: Dict mapping ticker to current price
            
        Returns:
            Total portfolio value (cash + position values)
        """
        total_value = self.cash
        
        for ticker, position in self._positions.items():
            if ticker in current_prices:
                position_value = position.quantity * current_prices[ticker]
                total_value += position_value
        
        return total_value
    
    @property
    def total_return(self) -> float:
        """Calculate total return since inception (requires current prices)."""
        # This is a simplified version - real implementation would need current prices
        return (self.cash - self.initial_cash) / self.initial_cash
    
    def __repr__(self) -> str:
        """String representation of portfolio."""
        return f"Portfolio(cash=${self.cash:.2f}, positions={len(self._positions)})"