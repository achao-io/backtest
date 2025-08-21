"""Statistical testing framework for strategy edge detection."""

import numpy as np
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Tuple, Optional
from scipy import stats
import random

from .data_loader import Bar, DataLoader
from .downloader import PolygonDownloader
from .engine import Engine, Results
from .strategy import Strategy


@dataclass
class StatResult:
    """Statistical test result for a single stock."""
    ticker: str
    return_pct: float
    sharpe_ratio: float
    start_price: float
    end_price: float
    volume: int
    market_cap_proxy: float  # price * volume as proxy
    beat_benchmark: bool
    transaction_costs: float


@dataclass
class StatTestSummary:
    """Summary statistics for a group of backtests."""
    n_stocks: int
    mean_return: float
    std_return: float
    win_rate: float  # % that beat benchmark
    mean_sharpe: float
    benchmark_return: float
    t_statistic: float
    p_value: float
    is_significant: bool  # at 95% confidence
    confidence_interval: Tuple[float, float]


class TransactionCostEngine(Engine):
    """Enhanced engine with transaction cost modeling."""
    
    def __init__(self, initial_cash: float = 100000, transaction_cost_pct: float = 0.05):
        """
        Initialize engine with transaction costs.
        
        Args:
            initial_cash: Starting cash
            transaction_cost_pct: Total transaction cost percentage (e.g., 0.05 = 5%)
        """
        super().__init__(initial_cash)
        self.transaction_cost_pct = transaction_cost_pct
    
    def run(self, strategy: Strategy, data: List[Bar]) -> Results:
        """Run backtest with transaction costs applied."""
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Get baseline results
        results = super().run(strategy, data)
        
        # Calculate transaction costs (buy + sell = 2 transactions for buy-and-hold)
        total_invested = self.initial_cash - results.final_cash
        transaction_costs = total_invested * self.transaction_cost_pct
        
        # Apply transaction costs to final portfolio value
        adjusted_portfolio_value = results.final_portfolio_value - transaction_costs
        
        # Create new results with adjusted values
        return Results(
            initial_cash=results.initial_cash,
            final_cash=results.final_cash,
            final_portfolio_value=adjusted_portfolio_value,
            total_orders=results.total_orders,
            executed_orders=results.executed_orders,
            start_date=results.start_date,
            end_date=results.end_date
        )


class StockSelector:
    """Selects stocks for testing based on market cap and volume criteria."""
    
    def __init__(self, min_price: float = 5.0, min_volume: int = 100000):
        """
        Initialize stock selector.
        
        Args:
            min_price: Minimum stock price to avoid penny stocks
            min_volume: Minimum daily volume to ensure liquidity
        """
        self.min_price = min_price
        self.min_volume = min_volume
    
    def select_stocks(self, data_file: str, n_stocks: int, seed: int = 42) -> List[str]:
        """
        Select n stocks from data file based on criteria.
        
        Args:
            data_file: Path to CSV file with stock data
            n_stocks: Number of stocks to select
            seed: Random seed for reproducibility
            
        Returns:
            List of selected ticker symbols
        """
        # Load all data
        all_data = DataLoader.from_polygon_csv(data_file, timeframe="day")
        
        # Filter stocks by criteria and calculate market cap proxy
        eligible_stocks = []
        for bar in all_data:
            if (bar.close >= self.min_price and 
                bar.volume >= self.min_volume and
                bar.ticker.isalpha() and  # Only pure alphabetic tickers
                len(bar.ticker) <= 5):    # Reasonable ticker length
                
                market_cap_proxy = bar.close * bar.volume
                eligible_stocks.append({
                    'ticker': bar.ticker,
                    'price': bar.close,
                    'volume': bar.volume,
                    'market_cap_proxy': market_cap_proxy
                })
        
        # Sort by market cap proxy (descending) and take top candidates
        eligible_stocks.sort(key=lambda x: x['market_cap_proxy'], reverse=True)
        
        # Take top 500 by market cap, then randomly select from those
        top_candidates = eligible_stocks[:min(500, len(eligible_stocks))]
        
        random.seed(seed)
        selected = random.sample(top_candidates, min(n_stocks, len(top_candidates)))
        
        return [stock['ticker'] for stock in selected]


class StatisticalTester:
    """Performs statistical tests on trading strategy performance."""
    
    def __init__(self, transaction_cost_pct: float = 0.05):
        """
        Initialize statistical tester.
        
        Args:
            transaction_cost_pct: Transaction cost percentage (e.g., 0.05 = 5%)
        """
        self.transaction_cost_pct = transaction_cost_pct
        self.downloader = PolygonDownloader()
        self.selector = StockSelector()
    
    def run_cross_sectional_test(
        self,
        strategy_class: type,
        start_date: date,
        end_date: date,
        n_stocks: int = 100,
        initial_cash: float = 100000,
        strategy_kwargs: Optional[Dict] = None
    ) -> Tuple[List[StatResult], StatTestSummary]:
        """
        Run cross-sectional test: many stocks over same time period.
        
        Args:
            strategy_class: Strategy class to test
            start_date: Start date for test
            end_date: End date for test
            n_stocks: Number of stocks to test
            initial_cash: Starting cash per test
            strategy_kwargs: Keyword arguments for strategy initialization
            
        Returns:
            Tuple of (individual results, summary statistics)
        """
        strategy_kwargs = strategy_kwargs or {}
        
        # Download data for start and end dates
        print(f"Downloading data for {start_date} and {end_date}...")
        start_file = self.downloader.download_stock_day_data(start_date)
        end_file = self.downloader.download_stock_day_data(end_date)
        
        # Select stocks from start date data
        print(f"Selecting {n_stocks} stocks...")
        selected_tickers = self.selector.select_stocks(start_file, n_stocks)
        print(f"Selected tickers: {selected_tickers[:10]}{'...' if len(selected_tickers) > 10 else ''}")
        
        # Get benchmark performance (SPY)
        benchmark_return = self._get_benchmark_return(start_file, end_file, "SPY")
        print(f"SPY benchmark return: {benchmark_return:.2%}")
        
        # Run backtests for each stock
        results = []
        engine = TransactionCostEngine(initial_cash, self.transaction_cost_pct)
        
        for i, ticker in enumerate(selected_tickers):
            try:
                # Get stock data for the period
                stock_data = self._get_stock_data_for_period(
                    ticker, start_file, end_file
                )
                
                if len(stock_data) < 2:
                    print(f"Skipping {ticker}: insufficient data")
                    continue
                
                # Run backtest
                strategy = strategy_class(**strategy_kwargs)
                backtest_results = engine.run(strategy, stock_data)
                
                # Calculate metrics
                stat_result = self._calculate_stat_result(
                    ticker, stock_data, backtest_results, benchmark_return
                )
                results.append(stat_result)
                
                if (i + 1) % 10 == 0:
                    print(f"Completed {i + 1}/{len(selected_tickers)} backtests")
                    
            except Exception as e:
                print(f"Error testing {ticker}: {e}")
                continue
        
        # Calculate summary statistics
        summary = self._calculate_summary_stats(results, benchmark_return)
        
        return results, summary
    
    def _get_benchmark_return(self, start_file: str, end_file: str, benchmark_ticker: str) -> float:
        """Get benchmark return for the period."""
        # Use caching for benchmark data too
        if not hasattr(self, '_cached_data'):
            self._cached_data = {}
        
        # Load and cache the files
        if start_file not in self._cached_data:
            self._cached_data[start_file] = DataLoader.from_polygon_csv(start_file, timeframe="day")
        if end_file not in self._cached_data:
            self._cached_data[end_file] = DataLoader.from_polygon_csv(end_file, timeframe="day")
        
        # Get benchmark data
        start_bars = [bar for bar in self._cached_data[start_file] if bar.ticker == benchmark_ticker]
        end_bars = [bar for bar in self._cached_data[end_file] if bar.ticker == benchmark_ticker]
        
        if not start_bars or not end_bars:
            return 0.0
        
        start_price = start_bars[0].close
        end_price = end_bars[0].close
        return (end_price - start_price) / start_price
    
    def _get_stock_data_for_period(self, ticker: str, start_file: str, end_file: str) -> List[Bar]:
        """Get stock data for the specified period."""
        # Cache loaded data to avoid reloading same files
        if not hasattr(self, '_cached_data'):
            self._cached_data = {}
        
        # Load start date data (with caching)
        if start_file not in self._cached_data:
            self._cached_data[start_file] = DataLoader.from_polygon_csv(start_file, timeframe="day")
        start_bars = [bar for bar in self._cached_data[start_file] if bar.ticker == ticker]
        
        # Load end date data (with caching)
        if end_file not in self._cached_data:
            self._cached_data[end_file] = DataLoader.from_polygon_csv(end_file, timeframe="day")
        end_bars = [bar for bar in self._cached_data[end_file] if bar.ticker == ticker]
        
        # Combine and sort
        all_bars = start_bars + end_bars
        all_bars.sort(key=lambda bar: bar.timestamp)
        
        return all_bars
    
    def _calculate_stat_result(
        self,
        ticker: str,
        stock_data: List[Bar],
        backtest_results: Results,
        benchmark_return: float
    ) -> StatResult:
        """Calculate statistical result for a single stock."""
        start_price = stock_data[0].close
        end_price = stock_data[-1].close
        stock_return = backtest_results.total_return
        
        # Calculate transaction costs
        total_invested = backtest_results.initial_cash - backtest_results.final_cash
        transaction_costs = total_invested * self.transaction_cost_pct
        
        # Simple Sharpe ratio calculation (assuming 0 risk-free rate)
        # For a single period, Sharpe = return / volatility
        # Using simple approximation since we only have 2 data points
        sharpe_ratio = stock_return if stock_return != 0 else 0.0
        
        return StatResult(
            ticker=ticker,
            return_pct=stock_return,
            sharpe_ratio=sharpe_ratio,
            start_price=start_price,
            end_price=end_price,
            volume=stock_data[0].volume,
            market_cap_proxy=start_price * stock_data[0].volume,
            beat_benchmark=stock_return > benchmark_return,
            transaction_costs=transaction_costs
        )
    
    def _calculate_summary_stats(
        self,
        results: List[StatResult],
        benchmark_return: float
    ) -> StatTestSummary:
        """Calculate summary statistics from individual results."""
        if not results:
            return StatTestSummary(0, 0, 0, 0, 0, benchmark_return, 0, 1, False, (0, 0))
        
        returns = [r.return_pct for r in results]
        sharpes = [r.sharpe_ratio for r in results]
        wins = [r.beat_benchmark for r in results]
        
        mean_return = float(np.mean(returns))
        std_return = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
        win_rate = float(np.mean(wins))
        mean_sharpe = float(np.mean(sharpes))
        
        # T-test: null hypothesis that mean return equals benchmark return
        if len(returns) > 1 and std_return > 0:
            t_stat = float((mean_return - benchmark_return) / (std_return / np.sqrt(len(returns))))
            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), len(returns) - 1)))  # Two-tailed test
            is_significant = p_value < 0.05
            
            # 95% confidence interval for mean return
            t_critical = float(stats.t.ppf(0.975, len(returns) - 1))
            margin_error = t_critical * (std_return / np.sqrt(len(returns)))
            ci_lower = float(mean_return - margin_error)
            ci_upper = float(mean_return + margin_error)
            confidence_interval = (ci_lower, ci_upper)
        else:
            t_stat = 0.0
            p_value = 1.0
            is_significant = False
            confidence_interval = (mean_return, mean_return)
        
        return StatTestSummary(
            n_stocks=len(results),
            mean_return=mean_return,
            std_return=std_return,
            win_rate=win_rate,
            mean_sharpe=mean_sharpe,
            benchmark_return=benchmark_return,
            t_statistic=t_stat,
            p_value=p_value,
            is_significant=is_significant,
            confidence_interval=confidence_interval
        )
    
    def print_summary(self, summary: StatTestSummary, test_name: str = "Statistical Test"):
        """Print formatted summary of statistical test results."""
        print(f"\n{'='*60}")
        print(f"{test_name.upper()} RESULTS")
        print(f"{'='*60}")
        print(f"Sample Size: {summary.n_stocks} stocks")
        print(f"Benchmark Return (SPY): {summary.benchmark_return:.2%}")
        print("")
        print("PERFORMANCE METRICS:")
        print(f"Mean Return: {summary.mean_return:.2%}")
        print(f"Standard Deviation: {summary.std_return:.2%}")
        print(f"Win Rate vs Benchmark: {summary.win_rate:.1%}")
        print(f"Mean Sharpe Ratio: {summary.mean_sharpe:.3f}")
        print("")
        print("STATISTICAL SIGNIFICANCE TEST:")
        print("Null Hypothesis: Mean return = Benchmark return")
        print(f"T-statistic: {summary.t_statistic:.3f}")
        print(f"P-value: {summary.p_value:.4f}")
        print(f"95% Confidence Interval: [{summary.confidence_interval[0]:.2%}, {summary.confidence_interval[1]:.2%}]")
        print("")
        if summary.is_significant:
            if summary.mean_return > summary.benchmark_return:
                print("✅ SIGNIFICANT OUTPERFORMANCE (p < 0.05)")
                print("The strategy shows statistically significant edge over benchmark.")
            else:
                print("🔴 SIGNIFICANT UNDERPERFORMANCE (p < 0.05)")
                print("The strategy performs significantly worse than benchmark.")
        else:
            print("❌ NO STATISTICAL EDGE (p >= 0.05)")
            print("Cannot reject null hypothesis - no significant difference from benchmark.")
        print(f"{'='*60}")