# Basic Backtesting Engine

A simple, educational backtesting engine for testing trading strategies on minute-level OHLC data from Polygon.

## Features

- **Simple Data Loading**: Parse Polygon flat files (CSV format)
- **Strategy Interface**: Easy-to-implement strategy base class
- **Basic Execution**: Market order simulation with no slippage/commissions
- **Portfolio Tracking**: Position and cash management
- **Performance Metrics**: Returns, drawdown, and basic statistics
- **Educational Focus**: Clear, readable code for learning backtesting concepts

## Getting Started

### Prerequisites

- Python 3.11+
- UV package manager

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd backtest

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Basic Usage

```python
from backtest import Engine, Strategy, DataLoader

# Load minute OHLC data
data = DataLoader.from_polygon_csv("data/SPY_minute.csv")

# Define a simple buy-and-hold strategy
class BuyAndHold(Strategy):
    def on_data(self, bar):
        if not self.position:
            self.buy(shares=100)

# Run backtest
strategy = BuyAndHold()
engine = Engine(initial_cash=10000)
results = engine.run(strategy, data)

# View results
print(f"Total Return: {results.total_return:.2%}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

## Architecture

### Core Components

1. **DataLoader**: Handles Polygon OHLC flat file parsing
2. **Strategy**: Abstract base class for implementing trading strategies  
3. **Engine**: Main backtesting engine that orchestrates execution
4. **Portfolio**: Tracks positions, cash, and portfolio value
5. **Results**: Performance metrics and analysis

### Data Format

Expected Polygon CSV format:
```
timestamp,open,high,low,close,volume
2024-01-01 09:30:00,100.0,101.0,99.5,100.5,1000
```

## Roadmap

- [x] Project setup and basic structure
- [x] Data loader for Polygon flat files
- [ ] Basic strategy interface
- [ ] Simple order execution
- [ ] Portfolio tracking
- [ ] Performance metrics calculation
- [ ] Example buy-and-hold strategy
- [ ] Basic visualization (optional)

## Example Strategies

Start with these simple strategies to understand the framework:

1. **Buy and Hold**: Buy once and hold
2. **Moving Average Crossover**: Buy when fast MA > slow MA
3. **RSI Mean Reversion**: Buy when RSI < 30, sell when RSI > 70

## Contributing

This is an educational project. Focus on:
- Code clarity over performance
- Simple implementations over complex features
- Step-by-step learning approach
