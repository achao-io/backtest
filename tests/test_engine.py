"""Tests for the Engine class."""

import pytest
from datetime import datetime
from backtest.engine import Engine, Results
from backtest.strategy import Strategy
from backtest.data_loader import Bar
from backtest.order import Order


# Simple test strategy for engine testing
class SimpleTestStrategy(Strategy):
    """Test strategy that buys on first bar and sells on last bar."""
    
    def __init__(self):
        super().__init__()
        self.bar_count = 0
        self.total_bars = 0
    
    def set_total_bars(self, total):
        """Set total number of bars to expect."""
        self.total_bars = total
    
    def on_data(self, bar):
        self.bar_count += 1
        
        if self.bar_count == 1:
            # Buy on first bar
            return [self.market_buy(bar.ticker, 100)]
        elif self.bar_count == self.total_bars:
            # Sell on last bar
            return [self.market_sell(bar.ticker, 100)]
        else:
            # Hold
            return []


class TestResults:
    """Test the Results class."""
    
    def test_results_creation(self):
        """Test creating results object."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        results = Results(
            initial_cash=10000,
            final_cash=9000,
            final_portfolio_value=11000,
            total_orders=10,
            executed_orders=8,
            start_date=start_date,
            end_date=end_date
        )
        
        assert results.initial_cash == 10000
        assert results.final_cash == 9000
        assert results.final_portfolio_value == 11000
        assert results.total_orders == 10
        assert results.executed_orders == 8
        assert results.start_date == start_date
        assert results.end_date == end_date
    
    def test_total_return_calculation(self):
        """Test total return calculation."""
        results = Results(
            initial_cash=10000,
            final_cash=5000,
            final_portfolio_value=12000,  # 20% gain
            total_orders=5,
            executed_orders=5,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert results.total_return == 0.2  # 20%
    
    def test_execution_rate_calculation(self):
        """Test execution rate calculation."""
        results = Results(
            initial_cash=10000,
            final_cash=10000,
            final_portfolio_value=10000,
            total_orders=10,
            executed_orders=8,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert results.execution_rate == 0.8  # 80%
    
    def test_execution_rate_no_orders(self):
        """Test execution rate when no orders placed."""
        results = Results(
            initial_cash=10000,
            final_cash=10000,
            final_portfolio_value=10000,
            total_orders=0,
            executed_orders=0,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert results.execution_rate == 0.0


class TestEngine:
    """Test the Engine class."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = Engine(50000)
        assert engine.initial_cash == 50000
    
    def test_invalid_initial_cash(self):
        """Test that invalid initial cash raises error."""
        with pytest.raises(ValueError, match="Initial cash must be positive"):
            Engine(-1000)
        
        with pytest.raises(ValueError, match="Initial cash must be positive"):
            Engine(0)
    
    def test_empty_data_raises_error(self):
        """Test that empty data raises error."""
        engine = Engine(10000)
        strategy = SimpleTestStrategy()
        
        with pytest.raises(ValueError, match="Data cannot be empty"):
            engine.run(strategy, [])
    
    def test_simple_backtest(self):
        """Test a simple backtest with mock data."""
        engine = Engine(10000)
        strategy = SimpleTestStrategy()
        
        # Create test data - 3 bars for same ticker
        bars = [
            Bar(datetime(2024, 1, 1), 100.0, 105.0, 95.0, 100.0, 1000, "TEST"),
            Bar(datetime(2024, 1, 2), 100.0, 110.0, 98.0, 105.0, 1000, "TEST"), 
            Bar(datetime(2024, 1, 3), 105.0, 108.0, 102.0, 107.0, 1000, "TEST")
        ]
        
        strategy.set_total_bars(3)
        results = engine.run(strategy, bars)
        
        # Verify results structure
        assert isinstance(results, Results)
        assert results.initial_cash == 10000
        assert results.start_date == datetime(2024, 1, 1)
        assert results.end_date == datetime(2024, 1, 3)
        assert results.total_orders == 2  # Buy on first, sell on last
        assert results.executed_orders == 2  # Both should execute
        
        # Check that cash changed (bought and sold)
        assert results.final_cash != 10000
    
    def test_no_orders_strategy(self):
        """Test strategy that places no orders."""
        engine = Engine(10000)
        
        # Strategy that never places orders
        class NoOrdersStrategy(Strategy):
            def on_data(self, bar):
                return []
        
        strategy = NoOrdersStrategy()
        bars = [
            Bar(datetime(2024, 1, 1), 100.0, 105.0, 95.0, 100.0, 1000, "TEST")
        ]
        
        results = engine.run(strategy, bars)
        
        assert results.total_orders == 0
        assert results.executed_orders == 0
        assert results.final_cash == 10000  # No change
        assert results.final_portfolio_value == 10000
        assert results.total_return == 0.0
    
    def test_insufficient_funds_orders(self):
        """Test orders that fail due to insufficient funds."""
        engine = Engine(1000)  # Small cash amount
        
        # Strategy that tries to buy expensive stock
        class ExpensiveStrategy(Strategy):
            def on_data(self, bar):
                return [self.market_buy(bar.ticker, 100)]  # Try to buy 100 shares
        
        strategy = ExpensiveStrategy()
        bars = [
            Bar(datetime(2024, 1, 1), 100.0, 105.0, 95.0, 100.0, 1000, "EXPENSIVE")
        ]
        
        results = engine.run(strategy, bars)
        
        assert results.total_orders == 1
        assert results.executed_orders == 0  # Order failed due to insufficient funds
        assert results.final_cash == 1000  # No change
    
    def test_multiple_tickers(self):
        """Test backtest with multiple tickers."""
        engine = Engine(20000)
        
        # Strategy that buys each ticker once
        class MultiTickerStrategy(Strategy):
            def __init__(self):
                super().__init__()
                self.bought_tickers = set()
            
            def on_data(self, bar):
                if bar.ticker not in self.bought_tickers:
                    self.bought_tickers.add(bar.ticker)
                    return [self.market_buy(bar.ticker, 50)]
                return []
        
        strategy = MultiTickerStrategy()
        bars = [
            Bar(datetime(2024, 1, 1), 100.0, 105.0, 95.0, 100.0, 1000, "AAPL"),
            Bar(datetime(2024, 1, 1), 200.0, 205.0, 195.0, 200.0, 1000, "MSFT"),
            Bar(datetime(2024, 1, 2), 101.0, 106.0, 96.0, 102.0, 1000, "AAPL"),
            Bar(datetime(2024, 1, 2), 201.0, 206.0, 196.0, 202.0, 1000, "MSFT")
        ]
        
        results = engine.run(strategy, bars)
        
        assert results.total_orders == 2  # One buy per ticker
        assert results.executed_orders == 2  # Both should execute
        
        # Cash should be reduced by purchases
        expected_cash_reduction = (50 * 100) + (50 * 200)  # AAPL + MSFT purchases
        assert results.final_cash == 20000 - expected_cash_reduction