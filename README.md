# Backtesting Engine

A backtesting framework for testing trading strategies with statistical rigor using real market data.

## Overview

This project implements a backtesting framework following Unix Philosophy principles:
- **Single Responsibility**: Each component does one thing well
- **Composability**: Components work together seamlessly  
- **Statistical Rigor**: Proper significance testing and edge detection
- **Simplicity**: Easy to understand and extend
- **Testability**: Comprehensive test coverage (65+ tests)

## Architecture

### Core Components

1. **Data Pipeline** (`backtest/data_loader.py`, `backtest/downloader.py`)
   - Downloads real market data from Polygon.io flat files
   - Flexible timeframe detection (minute vs day data)
   - Local caching to minimize API calls

2. **Strategy Framework** (`backtest/strategy.py`)
   - Abstract base class for all trading strategies
   - Simple interface: `on_data(bar) -> List[Order]`
   - Built-in position tracking and convenience methods

3. **Portfolio Management** (`backtest/portfolio.py`)
   - Executes orders and tracks cash/positions
   - Supports both long and short positions
   - Real-time portfolio valuation

4. **Order System** (`backtest/order.py`) 
   - Simple Order and Position classes
   - Market and limit order support
   - Clean separation of concerns

5. **Backtesting Engine** (`backtest/engine.py`)
   - Orchestrates strategy execution over market data
   - Linear processing with clear results
   - Performance metrics and statistics

6. **Statistical Testing Framework** (`backtest/statistical_testing.py`) 🆕
   - Rigorous statistical analysis of strategy performance
   - Transaction cost modeling (configurable %)
   - Cross-sectional and time-series testing
   - T-tests, confidence intervals, and significance testing
   - Market cap filtering and stock selection

### Example Strategies

- **Buy and Hold** (`strategies/buy_and_hold.py`): Simple benchmark strategy

## Getting Started

### Prerequisites

- Python 3.13+
- uv package manager
- Polygon.io API credentials (free tier available)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backtest
```

2. Install dependencies:
```bash
uv sync
```

3. Set up credentials:
```bash
cp .env.example .env
# Edit .env with your Polygon.io API key
```

### Quick Start

#### Basic Backtest

```python
from backtest.downloader import PolygonDownloader
from backtest.data_loader import DataLoader
from backtest.engine import Engine
from strategies.buy_and_hold import BuyAndHoldStrategy
from datetime import date

# Download data
downloader = PolygonDownloader()
data_file = downloader.download_stock_day_data(date(2025, 1, 2))

# Load SPY data
data = DataLoader.from_polygon_csv(data_file)
spy_data = [bar for bar in data if bar.ticker == "SPY"]

# Run backtest
engine = Engine(initial_cash=100000)
strategy = BuyAndHoldStrategy(investment_per_ticker=100000)
results = engine.run(strategy, spy_data)

print(f"Total Return: {results.total_return:.2%}")
```

#### Statistical Edge Testing 🆕

```python
from backtest.statistical_testing import StatisticalTester
from strategies.buy_and_hold import BuyAndHoldStrategy
from datetime import date

# Test buy-and-hold strategy for statistical significance
tester = StatisticalTester(transaction_cost_pct=0.05)  # 5% total costs

results, summary = tester.run_cross_sectional_test(
    strategy_class=BuyAndHoldStrategy,
    start_date=date(2025, 1, 2),
    end_date=date(2025, 1, 31),
    n_stocks=100,
    initial_cash=100000
)

tester.print_summary(summary, "Buy-and-Hold Edge Test")
# Output: Statistical analysis with p-values, confidence intervals, win rates
```

### Example Output

```
============================================================
BUY-AND-HOLD EDGE TEST RESULTS
============================================================
Sample Size: 50 stocks
Benchmark Return (SPY): 2.94%

PERFORMANCE METRICS:
Mean Return: -1.95%
Standard Deviation: 10.70%
Win Rate vs Benchmark: 26.0%
Mean Sharpe Ratio: -0.019

STATISTICAL SIGNIFICANCE TEST:
Null Hypothesis: Mean return = Benchmark return
T-statistic: -3.227
P-value: 0.0022
95% Confidence Interval: [-4.99%, 1.10%]

🔴 SIGNIFICANT UNDERPERFORMANCE (p < 0.05)
The strategy performs significantly worse than benchmark.
============================================================
```

### Running Tests

```bash
# Run all tests (65+ tests)
uv run python -m pytest

# Run specific test categories
uv run python -m pytest tests/test_statistical_testing.py

# Code quality checks
uv run ruff check .
uv run ty check
```

## Project Structure

```
backtest/
├── backtest/                    # Core engine components
│   ├── __init__.py
│   ├── data_loader.py          # Data loading from Polygon files
│   ├── downloader.py           # Data downloading from S3
│   ├── engine.py               # Main backtesting orchestration
│   ├── order.py                # Order and Position classes
│   ├── portfolio.py            # Portfolio management
│   ├── strategy.py             # Strategy base class
│   └── statistical_testing.py  # Statistical analysis framework 🆕
├── strategies/                  # Example trading strategies
│   └── buy_and_hold.py         # Buy and hold implementation
├── tests/                      # Comprehensive test suite (65+ tests)
├── data/                       # Downloaded market data (local cache)
├── test_spy_backtest.py        # SPY backtest example
├── test_statistical_edge.py    # Statistical edge testing example 🆕
├── .env.example                # Environment template
├── pyproject.toml              # Project configuration
└── README.md
```

## Features

### ✅ Core Backtesting
- Real Polygon.io market data integration (10,552+ stocks)
- Flexible data loading with automatic timeframe detection
- Portfolio management with long/short position support
- Complete order execution simulation
- Performance metrics and reporting

### ✅ Statistical Analysis 🆕
- **Transaction Cost Modeling**: Configurable costs (commission, slippage, fees)
- **Stock Selection**: Market cap filtering, volume filtering, random sampling
- **Cross-Sectional Testing**: Test strategy across many stocks, same period
- **Time-Series Testing**: Test same stocks across multiple periods (planned)
- **Statistical Significance**: T-tests, p-values, confidence intervals
- **Edge Detection**: Quantitative proof of strategy alpha vs benchmark

### ✅ Quality Assurance
- 65+ comprehensive tests covering all components
- Type checking with `ty` (all types validated)
- Code quality with `ruff` (all standards met)
- Unix philosophy: each component does one thing well

## Data Source

This engine uses [Polygon.io flat files](https://polygon.io/docs/flat-files/quickstart) which provide:
- Real historical US stock market data
- Minute and daily aggregates  
- High-quality, institutional-grade data
- S3-compatible API access

## Statistical Framework

### Transaction Cost Model
The engine includes realistic transaction costs:
- **Configurable percentage**: Default 5% total costs
- **Round-trip costs**: Buy + sell transactions
- **Real-world accuracy**: Accounts for commission, slippage, regulatory fees

### Edge Detection Methodology
1. **Null Hypothesis**: Strategy return = Benchmark return
2. **Sample Selection**: Market cap filtered, random sampling
3. **Statistical Testing**: Student's t-test, 95% confidence
4. **Performance Metrics**: Mean return, standard deviation, win rate, Sharpe ratio
5. **Significance Analysis**: P-values, confidence intervals, effect size

### Key Insights from Testing
- **Buy-and-Hold Individual Stocks**: Shows significant underperformance vs SPY (p=0.0022)
- **Transaction Cost Impact**: 5% costs significantly erode single-stock strategies
- **Diversification Value**: SPY's automatic rebalancing provides systematic advantage
- **Statistical Rigor**: Proper significance testing reveals true strategy edge

## Design Principles

### Unix Philosophy
- **Do one thing well**: Each class has a single, clear responsibility
- **Work together**: Components compose cleanly
- **Text streams**: Data flows through simple, predictable interfaces

### DRY (Don't Repeat Yourself)
- Reusable components across strategies
- Common utilities in base classes
- Consistent interfaces throughout

### Statistical Rigor
- Proper significance testing at 95% confidence
- Transaction cost modeling for realistic results
- Large sample sizes for statistical power
- Benchmark comparisons for edge detection

### Simplicity
- Minimal external dependencies (numpy, scipy, pandas only)
- Clear, readable code
- Educational focus with production-quality implementation

## References
- https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/
- https://jspauld.com/post/35126549635/how-i-made-500k-with-machine-learning-and-hft

## Contributing

1. Follow the existing code style (ruff compliant)
2. Add tests for new functionality (maintain 65+ test coverage)
3. Run quality checks before submitting (`ruff check .`, `ty check`)
4. Keep components focused and simple (Unix philosophy)
5. Include statistical validation for new strategies

## License

MIT License
