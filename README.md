# Basic Backtesting Engine

A simple, educational backtesting engine for testing trading strategies on real market data from Polygon.io flat files.

## Features

- **🔽 Polygon Data Integration**: Direct download from Polygon.io flat files (US Stocks SIP)
- **📊 Flexible Data Loading**: Auto-detect minute vs day timeframes, parse OHLC data
- **💾 Smart Caching**: Local file caching to avoid re-downloading data
- **🎯 Strategy Interface**: Easy-to-implement strategy base class (coming soon)
- **⚡ Performance Focus**: Efficient data handling for large datasets
- **🧪 Comprehensive Testing**: 26 tests covering all functionality
- **📚 Educational Focus**: Clear, readable code for learning backtesting concepts

## Getting Started

### Prerequisites

- Python 3.13+
- UV package manager
- Polygon.io subscription with Flat Files access

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd backtest

# Install dependencies
uv sync

# Set up credentials (copy and edit with your keys)
cp .env.example .env
# Edit .env with your Polygon S3 credentials
```

### Polygon Setup

1. **Get Credentials**: Login to [Polygon.io Dashboard](https://polygon.io/dashboard) → Flat Files section
2. **Copy Keys**: Get your S3 Access Key and Secret Key
3. **Configure**: Add to `.env` file:
   ```
   POLYGON_ACCESS_KEY=your_access_key_here
   POLYGON_SECRET_KEY=your_secret_key_here
   ```

### Quick Start

```python
from backtest import PolygonDownloader, DataLoader

# 1. Download real market data
downloader = PolygonDownloader()
file_path = downloader.download_stock_day_data('2024-08-07')

# 2. Load and analyze data
data = DataLoader.from_polygon_csv(file_path, timeframe='day')
print(f"Loaded {len(data)} stocks for {data[0].timestamp.date()}")

# 3. Examine data
aapl = [bar for bar in data if bar.ticker == 'AAPL'][0]
print(f"AAPL: Open=${aapl.open:.2f}, Close=${aapl.close:.2f}")
```

### Advanced Usage

```python
# Auto-detect timeframe
data = DataLoader.from_polygon_csv("data.csv")  # timeframe="auto"

# Explicit timeframe
minute_data = DataLoader.from_polygon_csv("data.csv", timeframe="minute")
day_data = DataLoader.from_polygon_csv("data.csv", timeframe="day")

# Stream large files
for bar in DataLoader.iter_polygon_csv("large_file.csv"):
    if bar.ticker == "AAPL":
        print(f"{bar.timestamp}: ${bar.close}")

# Download different timeframes
downloader = PolygonDownloader()
day_file = downloader.download_stock_day_data('2024-08-07')
minute_file = downloader.download_stock_minute_data('2024-08-07')
```

## Architecture

### Current Components

1. **PolygonDownloader**: Downloads data from Polygon.io S3 flat files with smart caching
2. **DataLoader**: Flexible OHLC data parsing with auto-timeframe detection
3. **Bar**: Data structure representing OHLC bars with validation

### Coming Soon

4. **Strategy**: Abstract base class for implementing trading strategies  
5. **Engine**: Main backtesting engine that orchestrates execution
6. **Portfolio**: Tracks positions, cash, and portfolio value
7. **Results**: Performance metrics and analysis

### Data Pipeline

```
Polygon API → S3 Download → Local Cache → DataLoader → Strategy → Results
```

### Supported Data

- **Source**: Polygon.io US Stocks SIP flat files
- **Timeframes**: Day aggregates, Minute aggregates
- **Format**: Compressed CSV files (.gz) with automatic decompression
- **Coverage**: 10,000+ US stocks with full market history

**Actual Polygon CSV format:**
```
ticker,volume,open,close,high,low,window_start,transactions
AAPL,4930,200.29,200.5,200.63,200.29,1744792500000000000,129
```

## Development Status

### ✅ Completed
- [x] **Project Setup**: UV package management, dependencies, .gitignore
- [x] **Environment Config**: .env credentials, Polygon S3 authentication  
- [x] **Data Downloader**: Polygon.io flat files integration with S3 API
- [x] **Data Loader**: Flexible CSV parsing with timeframe auto-detection
- [x] **Smart Caching**: Local file storage to avoid re-downloads
- [x] **Comprehensive Testing**: 26 tests covering all functionality
- [x] **Real Data Pipeline**: Download → Cache → Load → Analyze

### 🚧 In Progress
- [ ] **Strategy Interface**: Abstract base class for trading strategies
- [ ] **Order Execution**: Market order simulation engine
- [ ] **Portfolio Tracking**: Position and cash management
- [ ] **Performance Metrics**: Returns, Sharpe ratio, drawdown calculation

### 📋 Planned
- [ ] **Example Strategies**: Buy-and-hold, moving averages, mean reversion
- [ ] **Visualization**: Performance charts and trade analysis
- [ ] **Advanced Features**: Slippage, commissions, position sizing

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Test data pipeline
uv run python demo_downloader.py
```

**Test Coverage**: 26 tests across data loading, downloading, validation, and error handling.

## Data Information

### What's Available
- **US Stocks**: 10,000+ stocks from major exchanges (NYSE, NASDAQ)
- **Historical Range**: Data back to 2003 (day) and recent years (minute)
- **Update Frequency**: Daily files available by 11 AM ET next trading day
- **File Sizes**: Day files (~100MB), Minute files (~1-2GB when uncompressed)

### Sample Data Stats
Recent day file (2024-08-07):
- **10,552 stocks** with OHLC data
- **Popular tickers**: AAPL ($209.82), MSFT ($398.43), GOOGL ($158.94), TSLA ($191.76)
- **Complete market coverage**: From penny stocks to blue chips

Recent minute file (2024-08-07):
- **1.57M+ minute bars** across all stocks
- **Full trading day**: 4:00 AM to 8:00 PM ET (pre-market + regular + after-hours)
- **Multiple tickers**: 10,000+ stocks with minute-level granularity

## Example Use Cases

This framework is perfect for:

1. **Learning Backtesting**: Understand how trading strategies are tested
2. **Strategy Research**: Test ideas on real market data
3. **Education**: Clear, readable code for understanding market data
4. **Prototyping**: Quick iteration on trading concepts

## Contributing

This is an educational project focusing on:
- **Clarity over optimization**: Readable code for learning
- **Real data integration**: Working with actual market data
- **Step-by-step development**: Building complexity gradually
- **Comprehensive testing**: Ensuring reliability
