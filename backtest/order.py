"""Trading order representation."""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Order:
    """Represents a trading order - does ONE thing: holds order data."""
    
    side: Literal["buy", "sell"]
    ticker: str
    quantity: int
    price: Optional[float] = None  # None = market order
    
    def __post_init__(self):
        """Validate order data."""
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if self.price is not None and self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
    
    @property
    def is_market_order(self) -> bool:
        """Check if this is a market order."""
        return self.price is None
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == "buy"
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == "sell"


@dataclass 
class Position:
    """Represents a position in a single ticker - does ONE thing: holds position data."""
    
    ticker: str
    quantity: int
    avg_cost: float
    
    def __post_init__(self):
        """Validate position data."""
        if self.avg_cost < 0:
            raise ValueError(f"Average cost cannot be negative, got {self.avg_cost}")
    
    @property
    def market_value(self) -> float:
        """Calculate market value at average cost."""
        return self.quantity * self.avg_cost
    
    @property
    def is_long(self) -> bool:
        """Check if this is a long position."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if this is a short position."""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat (no holdings)."""
        return self.quantity == 0