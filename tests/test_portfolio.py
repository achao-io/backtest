"""Tests for the Portfolio class."""

import pytest
from backtest.portfolio import Portfolio
from backtest.order import Order, Position


class TestPortfolio:
    """Test the Portfolio class."""
    
    def test_initialization(self):
        """Test portfolio initialization."""
        portfolio = Portfolio(10000)
        
        assert portfolio.cash == 10000
        assert portfolio.initial_cash == 10000
        assert len(portfolio.get_positions()) == 0
    
    def test_invalid_initial_cash(self):
        """Test that invalid initial cash raises error."""
        with pytest.raises(ValueError, match="Initial cash must be positive"):
            Portfolio(-1000)
        
        with pytest.raises(ValueError, match="Initial cash must be positive"):
            Portfolio(0)
    
    def test_execute_buy_order_success(self):
        """Test successful buy order execution."""
        portfolio = Portfolio(10000)
        order = Order(side="buy", ticker="AAPL", quantity=100)
        
        success = portfolio.execute_order(order, 50.0)
        
        assert success
        assert portfolio.cash == 5000  # 10000 - (100 * 50)
        
        position = portfolio.get_position("AAPL")
        assert position is not None
        assert position.ticker == "AAPL"
        assert position.quantity == 100
        assert position.avg_cost == 50.0
    
    def test_execute_buy_order_insufficient_funds(self):
        """Test buy order with insufficient funds."""
        portfolio = Portfolio(1000)
        order = Order(side="buy", ticker="AAPL", quantity=100)
        
        success = portfolio.execute_order(order, 50.0)  # Need $5000, only have $1000
        
        assert not success
        assert portfolio.cash == 1000  # Unchanged
        assert portfolio.get_position("AAPL") is None
    
    def test_execute_sell_order_new_short(self):
        """Test sell order creating new short position."""
        portfolio = Portfolio(10000)
        order = Order(side="sell", ticker="AAPL", quantity=100)
        
        success = portfolio.execute_order(order, 50.0)
        
        assert success
        assert portfolio.cash == 15000  # 10000 + (100 * 50)
        
        position = portfolio.get_position("AAPL")
        assert position is not None
        assert position.ticker == "AAPL"
        assert position.quantity == -100
        assert position.avg_cost == 50.0
    
    def test_execute_sell_order_reduce_position(self):
        """Test sell order reducing existing long position."""
        portfolio = Portfolio(10000)
        
        # First, establish a long position
        buy_order = Order(side="buy", ticker="AAPL", quantity=200)
        portfolio.execute_order(buy_order, 50.0)
        
        # Then, sell part of it
        sell_order = Order(side="sell", ticker="AAPL", quantity=100)
        success = portfolio.execute_order(sell_order, 60.0)
        
        assert success
        assert portfolio.cash == 6000  # 0 + (100 * 60)
        
        position = portfolio.get_position("AAPL")
        assert position is not None
        assert position.quantity == 100  # 200 - 100
        assert position.avg_cost == 50.0  # Original cost maintained
    
    def test_execute_sell_order_close_position(self):
        """Test sell order that closes position completely."""
        portfolio = Portfolio(10000)
        
        # Establish position
        buy_order = Order(side="buy", ticker="AAPL", quantity=100)
        portfolio.execute_order(buy_order, 50.0)
        
        # Close position
        sell_order = Order(side="sell", ticker="AAPL", quantity=100)
        success = portfolio.execute_order(sell_order, 60.0)
        
        assert success
        assert portfolio.cash == 11000  # 5000 + (100 * 60)
        assert portfolio.get_position("AAPL") is None  # Position closed
    
    def test_multiple_positions(self):
        """Test portfolio with multiple positions."""
        portfolio = Portfolio(20000)
        
        # Buy AAPL
        aapl_order = Order(side="buy", ticker="AAPL", quantity=100)
        portfolio.execute_order(aapl_order, 50.0)
        
        # Buy MSFT
        msft_order = Order(side="buy", ticker="MSFT", quantity=50)
        portfolio.execute_order(msft_order, 100.0)
        
        assert portfolio.cash == 10000  # 20000 - 5000 - 5000
        assert len(portfolio.get_positions()) == 2
        
        aapl_position = portfolio.get_position("AAPL")
        msft_position = portfolio.get_position("MSFT")
        
        assert aapl_position.quantity == 100
        assert msft_position.quantity == 50
    
    def test_calculate_portfolio_value(self):
        """Test portfolio value calculation."""
        portfolio = Portfolio(10000)
        
        # Buy positions
        aapl_order = Order(side="buy", ticker="AAPL", quantity=100)
        portfolio.execute_order(aapl_order, 50.0)
        
        msft_order = Order(side="buy", ticker="MSFT", quantity=50)
        portfolio.execute_order(msft_order, 100.0)
        
        # Calculate value with current prices
        current_prices = {"AAPL": 60.0, "MSFT": 110.0}
        total_value = portfolio.calculate_portfolio_value(current_prices)
        
        expected_value = 0 + (100 * 60.0) + (50 * 110.0)  # cash + AAPL + MSFT
        assert total_value == expected_value
    
    def test_invalid_execution_price(self):
        """Test that invalid execution price raises error."""
        portfolio = Portfolio(10000)
        order = Order(side="buy", ticker="AAPL", quantity=100)
        
        with pytest.raises(ValueError, match="Execution price must be positive"):
            portfolio.execute_order(order, -10.0)
        
        with pytest.raises(ValueError, match="Execution price must be positive"):
            portfolio.execute_order(order, 0.0)