#!/usr/bin/env python3
"""
Demo script showing the complete data pipeline:
Polygon Download → Data Loading → Analysis
"""

from backtest import PolygonDownloader, DataLoader

def main():
    print("🚀 Complete Data Pipeline Demo")
    print("=" * 50)
    
    # Initialize downloader
    downloader = PolygonDownloader()
    
    # Test connection
    print("🔗 Testing connection...")
    if not downloader.test_connection():
        print("❌ Connection failed. Check credentials.")
        return
    
    print()
    print("📊 Downloading and analyzing data...")
    
    # Download day data
    try:
        print("\n1️⃣ Day Data Pipeline:")
        day_file = downloader.download_stock_day_data('2024-08-07')
        day_data = DataLoader.from_polygon_csv(day_file, timeframe='day')
        
        print(f"   ✅ {len(day_data)} stocks for {day_data[0].timestamp.date()}")
        
        # Find some popular stocks
        popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        found_stocks = []
        
        for ticker in popular_tickers:
            stock_data = [bar for bar in day_data if bar.ticker == ticker]
            if stock_data:
                bar = stock_data[0]
                found_stocks.append(f"{ticker}: ${bar.close:.2f}")
        
        print(f"   📈 Sample closes: {', '.join(found_stocks)}")
        
    except Exception as e:
        print(f"   ❌ Day data error: {e}")
    
    # Download minute data (smaller sample)
    try:
        print("\n2️⃣ Minute Data Pipeline:")
        minute_file = downloader.download_stock_minute_data('2024-08-07')
        
        # Load just first 1000 bars for demo (minute data is large)
        print("   📥 Loading sample of minute data...")
        with open(minute_file, 'r') as f:
            lines = f.readlines()
            sample_lines = lines[:1001]  # Header + 1000 data lines
        
        # Write sample to temp file
        sample_file = minute_file.parent / f"sample_{minute_file.name}"
        with open(sample_file, 'w') as f:
            f.writelines(sample_lines)
        
        minute_data = DataLoader.from_polygon_csv(sample_file, timeframe='minute')
        
        print(f"   ✅ {len(minute_data)} minute bars loaded")
        print(f"   🕐 Time range: {minute_data[0].timestamp.strftime('%H:%M')} to {minute_data[-1].timestamp.strftime('%H:%M')}")
        
        # Show AAPL minute progression
        aapl_minute = [bar for bar in minute_data if bar.ticker == 'AAPL'][:5]
        if aapl_minute:
            print(f"   📊 AAPL first 5 minutes:")
            for bar in aapl_minute:
                print(f"      {bar.timestamp.strftime('%H:%M')} - ${bar.close:.2f}")
        
        # Clean up sample file
        sample_file.unlink()
        
    except Exception as e:
        print(f"   ❌ Minute data error: {e}")
    
    print()
    print("🎉 Data pipeline demo complete!")
    print("💡 You now have:")
    print("   - Polygon flat file downloading")
    print("   - Flexible OHLC data loading")
    print("   - Timeframe detection (minute/day)")
    print("   - Local caching for performance")
    print()
    print("🎯 Ready for backtesting implementation!")

if __name__ == "__main__":
    main()