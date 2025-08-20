"""Tests for Order and Position classes."""

import pytest
from backtest.order import Order, Position


class TestOrder:
    """Test the Order class."""
    
    def test_valid_market_buy_order(self):
        """Test creating a valid market buy order."""
        order = Order(side="buy", ticker="AAPL", quantity=100)
        
        assert order.side == "buy"
        assert order.ticker == "AAPL"
        assert order.quantity == 100
        assert order.price is None
        assert order.is_market_order
        assert order.is_buy
        assert not order.is_sell
    
    def test_valid_limit_sell_order(self):
        """Test creating a valid limit sell order."""
        order = Order(side="sell", ticker="MSFT", quantity=50, price=150.0)
        
        assert order.side == "sell"
        assert order.ticker == "MSFT"
        assert order.quantity == 50
        assert order.price == 150.0
        assert not order.is_market_order
        assert not order.is_buy
        assert order.is_sell
    
    def test_invalid_quantity(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Order(side="buy", ticker="AAPL", quantity=-10)
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Order(side="buy", ticker="AAPL", quantity=0)
    
    def test_invalid_price(self):
        """Test that negative price raises error."""
        with pytest.raises(ValueError, match="Price must be positive"):
            Order(side="buy", ticker="AAPL", quantity=100, price=-10.0)
        
        with pytest.raises(ValueError, match="Price must be positive"):
            Order(side="buy", ticker="AAPL", quantity=100, price=0.0)


class TestPosition:
    """Test the Position class."""
    
    def test_valid_long_position(self):
        """Test creating a valid long position."""
        position = Position(ticker="AAPL", quantity=100, avg_cost=150.0)
        
        assert position.ticker == "AAPL"
        assert position.quantity == 100
        assert position.avg_cost == 150.0
        assert position.market_value == 15000.0
        assert position.is_long
        assert not position.is_short
        assert not position.is_flat
    
    def test_valid_short_position(self):
        """Test creating a valid short position."""
        position = Position(ticker="TSLA", quantity=-50, avg_cost=200.0)
        
        assert position.ticker == "TSLA"
        assert position.quantity == -50
        assert position.avg_cost == 200.0
        assert position.market_value == -10000.0
        assert not position.is_long
        assert position.is_short
        assert not position.is_flat
    
    def test_flat_position(self):
        """Test a flat position."""
        position = Position(ticker="GOOGL", quantity=0, avg_cost=100.0)
        
        assert position.ticker == "GOOGL"
        assert position.quantity == 0
        assert position.avg_cost == 100.0
        assert position.market_value == 0.0
        assert not position.is_long
        assert not position.is_short
        assert position.is_flat
    
    def test_invalid_avg_cost(self):
        """Test that negative average cost raises error."""
        with pytest.raises(ValueError, match="Average cost cannot be negative"):
            Position(ticker="AAPL", quantity=100, avg_cost=-10.0)