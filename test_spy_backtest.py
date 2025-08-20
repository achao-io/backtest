#!/usr/bin/env python3
"""
Test script to run a buy-and-hold backtest on SPY from 2025-01-01 to 2025-02-01.
"""

import os
from datetime import date, datetime
from backtest.downloader import PolygonDownloader
from backtest.data_loader import DataLoader
from backtest.engine import Engine
from strategies.buy_and_hold import BuyAndHoldStrategy


def main():
    """Run SPY buy-and-hold backtest for January 2025."""
    
    # Initialize downloader and loader
    downloader = PolygonDownloader()
    loader = DataLoader()
    
    # Download data for January 2025 (day aggregates for simplicity)
    print("Downloading SPY data for January 2025...")
    
    january_dates = []
    # Get all weekdays in January 2025
    for day in range(1, 32):  # January has 31 days
        try:
            target_date = date(2025, 1, day)
            # Only download weekdays (markets are closed weekends)
            if target_date.weekday() < 5:  # Monday=0, Friday=4
                january_dates.append(target_date)
        except ValueError:
            break  # Invalid date (like Jan 32)
    
    # Download all the data files
    downloaded_files = []
    for target_date in january_dates:
        try:
            file_path = downloader.download_stock_day_data(target_date)
            downloaded_files.append(file_path)
            print(f"Downloaded: {target_date}")
        except Exception as e:
            print(f"Failed to download {target_date}: {e}")
    
    if not downloaded_files:
        print("No data files downloaded. Cannot run backtest.")
        return
    
    # Load SPY data from all downloaded files
    print(f"\nLoading SPY data from {len(downloaded_files)} files...")
    
    all_spy_data = []
    for file_path in downloaded_files:
        try:
            data = DataLoader.from_polygon_csv(file_path, timeframe="day")
            # Filter for SPY only
            spy_data = [bar for bar in data if bar.ticker == "SPY"]
            all_spy_data.extend(spy_data)
            if spy_data:
                print(f"Loaded {len(spy_data)} SPY bars from {file_path.name}")
        except Exception as e:
            print(f"Failed to load {file_path}: {e}")
    
    if not all_spy_data:
        print("No SPY data found in downloaded files.")
        return
    
    # Sort by timestamp
    all_spy_data.sort(key=lambda bar: bar.timestamp)
    
    print(f"\nTotal SPY bars loaded: {len(all_spy_data)}")
    print(f"Date range: {all_spy_data[0].timestamp.date()} to {all_spy_data[-1].timestamp.date()}")
    print(f"First bar: {all_spy_data[0]}")
    print(f"Last bar: {all_spy_data[-1]}")
    
    # Set up and run backtest
    print("\nRunning buy-and-hold backtest...")
    
    initial_cash = 100000  # $100K starting capital
    engine = Engine(initial_cash)
    strategy = BuyAndHoldStrategy(investment_per_ticker=initial_cash)  # Invest all cash in SPY
    
    # Run the backtest
    results = engine.run(strategy, all_spy_data)
    
    # Display results
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Strategy: Buy and Hold SPY")
    print(f"Period: {results.start_date.date()} to {results.end_date.date()}")
    print(f"Initial Cash: ${results.initial_cash:,.2f}")
    print(f"Final Cash: ${results.final_cash:,.2f}")
    print(f"Final Portfolio Value: ${results.final_portfolio_value:,.2f}")
    print(f"Total Return: {results.total_return:.2%}")
    print(f"Total Orders: {results.total_orders}")
    print(f"Executed Orders: {results.executed_orders}")
    print(f"Execution Rate: {results.execution_rate:.1%}")
    
    # Calculate some additional metrics
    days_elapsed = (results.end_date - results.start_date).days
    if days_elapsed > 0:
        annualized_return = (1 + results.total_return) ** (365 / days_elapsed) - 1
        print(f"Annualized Return: {annualized_return:.2%}")
    
    # Show SPY price performance
    start_price = all_spy_data[0].close
    end_price = all_spy_data[-1].close
    spy_return = (end_price - start_price) / start_price
    print(f"\nSPY Price Performance:")
    print(f"Start Price: ${start_price:.2f}")
    print(f"End Price: ${end_price:.2f}")
    print(f"SPY Return: {spy_return:.2%}")
    
    print("="*50)


if __name__ == "__main__":
    main()