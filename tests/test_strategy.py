"""Tests for Strategy classes."""

import pytest
from datetime import datetime
from backtest.strategy import Strategy
from backtest.data_loader import Bar
from backtest.order import Position
from strategies.buy_and_hold import BuyAndHoldStrategy


# Simple test strategy for testing base class functionality
class TestStrategy(Strategy):
    """Test strategy that returns predefined orders."""
    
    def __init__(self, orders_to_return=None):
        super().__init__()
        self.orders_to_return = orders_to_return or []
        self.bars_received = []
    
    def on_data(self, bar):
        self.bars_received.append(bar)
        return self.orders_to_return.copy()


class TestStrategyBase:
    """Test the Strategy base class."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = TestStrategy()
        
        assert len(strategy.positions) == 0
        assert strategy.get_position("AAPL") is None
    
    def test_position_tracking(self):
        """Test position tracking functionality."""
        strategy = TestStrategy()
        
        # Add a position
        position = Position(ticker="AAPL", quantity=100, avg_cost=50.0)
        strategy.update_position(position)
        
        assert strategy.get_position("AAPL") == position
        assert "AAPL" in strategy.positions
    
    def test_position_removal_when_flat(self):
        """Test that flat positions are removed."""
        strategy = TestStrategy()
        
        # Add position then make it flat
        position = Position(ticker="AAPL", quantity=100, avg_cost=50.0)
        strategy.update_position(position)
        
        flat_position = Position(ticker="AAPL", quantity=0, avg_cost=50.0)
        strategy.update_position(flat_position)
        
        assert strategy.get_position("AAPL") is None
        assert "AAPL" not in strategy.positions
    
    def test_convenience_order_methods(self):
        """Test convenience methods for creating orders."""
        strategy = TestStrategy()
        
        # Test market orders
        buy_order = strategy.market_buy("AAPL", 100)
        assert buy_order.side == "buy"
        assert buy_order.ticker == "AAPL"
        assert buy_order.quantity == 100
        assert buy_order.price is None
        
        sell_order = strategy.market_sell("MSFT", 50)
        assert sell_order.side == "sell"
        assert sell_order.ticker == "MSFT"
        assert sell_order.quantity == 50
        assert sell_order.price is None
        
        # Test limit orders
        limit_buy = strategy.limit_buy("GOOGL", 25, 100.0)
        assert limit_buy.side == "buy"
        assert limit_buy.ticker == "GOOGL"
        assert limit_buy.quantity == 25
        assert limit_buy.price == 100.0
        
        limit_sell = strategy.limit_sell("TSLA", 75, 200.0)
        assert limit_sell.side == "sell"
        assert limit_sell.ticker == "TSLA"
        assert limit_sell.quantity == 75
        assert limit_sell.price == 200.0


class TestBuyAndHoldStrategy:
    """Test the BuyAndHoldStrategy implementation."""
    
    def test_initialization(self):
        """Test buy and hold strategy initialization."""
        strategy = BuyAndHoldStrategy(investment_per_ticker=5000)
        
        assert strategy.investment_per_ticker == 5000
        assert len(strategy._bought_tickers) == 0
    
    def test_invalid_investment_amount(self):
        """Test that invalid investment amount raises error."""
        with pytest.raises(ValueError, match="Investment per ticker must be positive"):
            BuyAndHoldStrategy(-1000)
        
        with pytest.raises(ValueError, match="Investment per ticker must be positive"):
            BuyAndHoldStrategy(0)
    
    def test_first_bar_generates_buy_order(self):
        """Test that first bar for a ticker generates buy order."""
        strategy = BuyAndHoldStrategy(investment_per_ticker=1000)
        
        bar = Bar(
            timestamp=datetime.now(),
            open=50.0,
            high=52.0,
            low=49.0,
            close=51.0,
            volume=1000,
            ticker="AAPL"
        )
        
        orders = strategy.on_data(bar)
        
        assert len(orders) == 1
        order = orders[0]
        assert order.side == "buy"
        assert order.ticker == "AAPL"
        assert order.quantity == 19  # 1000 / 51 = 19.6, truncated to 19
        assert order.price is None  # Market order
    
    def test_subsequent_bars_no_orders(self):
        """Test that subsequent bars for same ticker generate no orders."""
        strategy = BuyAndHoldStrategy(investment_per_ticker=1000)
        
        bar = Bar(
            timestamp=datetime.now(),
            open=50.0,
            high=52.0,
            low=49.0,
            close=51.0,
            volume=1000,
            ticker="AAPL"
        )
        
        # First bar - should generate order
        orders1 = strategy.on_data(bar)
        assert len(orders1) == 1
        
        # Second bar - should not generate order
        orders2 = strategy.on_data(bar)
        assert len(orders2) == 0
    
    def test_multiple_tickers(self):
        """Test strategy with multiple tickers."""
        strategy = BuyAndHoldStrategy(investment_per_ticker=1000)
        
        aapl_bar = Bar(
            timestamp=datetime.now(),
            open=50.0, high=52.0, low=49.0, close=50.0,
            volume=1000, ticker="AAPL"
        )
        
        msft_bar = Bar(
            timestamp=datetime.now(),
            open=100.0, high=102.0, low=99.0, close=100.0,
            volume=1000, ticker="MSFT"
        )
        
        # First ticker
        aapl_orders = strategy.on_data(aapl_bar)
        assert len(aapl_orders) == 1
        assert aapl_orders[0].ticker == "AAPL"
        assert aapl_orders[0].quantity == 20  # 1000 / 50
        
        # Second ticker
        msft_orders = strategy.on_data(msft_bar)
        assert len(msft_orders) == 1
        assert msft_orders[0].ticker == "MSFT"
        assert msft_orders[0].quantity == 10  # 1000 / 100
        
        # Repeat first ticker - no new orders
        aapl_orders2 = strategy.on_data(aapl_bar)
        assert len(aapl_orders2) == 0
    
    def test_expensive_stock_no_order(self):
        """Test that very expensive stocks don't generate orders."""
        strategy = BuyAndHoldStrategy(investment_per_ticker=100)
        
        expensive_bar = Bar(
            timestamp=datetime.now(),
            open=1000.0, high=1020.0, low=990.0, close=1000.0,
            volume=100, ticker="EXPENSIVE"
        )
        
        orders = strategy.on_data(expensive_bar)
        assert len(orders) == 0  # Can't afford even 1 share