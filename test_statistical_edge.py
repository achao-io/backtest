#!/usr/bin/env python3
"""
Test the statistical edge of buy-and-hold strategy across multiple stocks.
"""

from datetime import date
from backtest.statistical_testing import StatisticalTester
from strategies.buy_and_hold import BuyAndHoldStrategy


def main():
    """Run statistical tests on buy-and-hold strategy."""
    
    # Initialize tester with 5% transaction costs
    tester = StatisticalTester(transaction_cost_pct=0.05)
    
    # Test parameters
    start_date = date(2025, 1, 2)  # First trading day of January
    end_date = date(2025, 1, 31)   # Last trading day of January
    n_stocks = 50  # Reduced for faster testing
    initial_cash = 100000
    
    print("🧪 TESTING BUY-AND-HOLD STRATEGY FOR STATISTICAL EDGE")
    print(f"Period: {start_date} to {end_date}")
    print(f"Stocks to test: {n_stocks}")
    print(f"Transaction costs: {tester.transaction_cost_pct:.1%}")
    print(f"Starting capital per test: ${initial_cash:,}")
    
    # Run cross-sectional test
    print("\n🔬 Running cross-sectional test...")
    individual_results, summary = tester.run_cross_sectional_test(
        strategy_class=BuyAndHoldStrategy,
        start_date=start_date,
        end_date=end_date,
        n_stocks=n_stocks,
        initial_cash=initial_cash,
        strategy_kwargs={'investment_per_ticker': initial_cash}
    )
    
    # Print detailed summary
    tester.print_summary(summary, "Cross-Sectional Buy-and-Hold Test")
    
    # Show top and bottom performers
    if individual_results:
        sorted_results = sorted(individual_results, key=lambda x: x.return_pct, reverse=True)
        
        print("\n📊 TOP 10 PERFORMERS:")
        print(f"{'Ticker':<8} {'Return':<8} {'Beat SPY':<10} {'Volume':<12} {'Start $':<8} {'End $':<8}")
        print("-" * 70)
        for result in sorted_results[:10]:
            beat_marker = "✅" if result.beat_benchmark else "❌"
            print(f"{result.ticker:<8} {result.return_pct:>7.1%} {beat_marker:<10} "
                  f"{result.volume:>11,} ${result.start_price:>6.2f} ${result.end_price:>6.2f}")
        
        print("\n📉 BOTTOM 10 PERFORMERS:")
        print(f"{'Ticker':<8} {'Return':<8} {'Beat SPY':<10} {'Volume':<12} {'Start $':<8} {'End $':<8}")
        print("-" * 70)
        for result in sorted_results[-10:]:
            beat_marker = "✅" if result.beat_benchmark else "❌"
            print(f"{result.ticker:<8} {result.return_pct:>7.1%} {beat_marker:<10} "
                  f"{result.volume:>11,} ${result.start_price:>6.2f} ${result.end_price:>6.2f}")
        
        # Additional insights
        positive_returns = [r for r in individual_results if r.return_pct > 0]
        negative_returns = [r for r in individual_results if r.return_pct < 0]
        
        print("\n📈 ADDITIONAL INSIGHTS:")
        print(f"Stocks with positive returns: {len(positive_returns)}/{len(individual_results)} ({len(positive_returns)/len(individual_results):.1%})")
        print(f"Stocks with negative returns: {len(negative_returns)}/{len(individual_results)} ({len(negative_returns)/len(individual_results):.1%})")
        
        if individual_results:
            best_return = max(r.return_pct for r in individual_results)
            worst_return = min(r.return_pct for r in individual_results)
            print(f"Best single stock return: {best_return:.1%}")
            print(f"Worst single stock return: {worst_return:.1%}")
            
            # Transaction cost impact
            avg_transaction_cost = sum(r.transaction_costs for r in individual_results) / len(individual_results)
            print(f"Average transaction costs per stock: ${avg_transaction_cost:,.2f}")
    
    print("\n🎯 CONCLUSION:")
    if summary.is_significant:
        if summary.mean_return > summary.benchmark_return:
            print("Buy-and-hold shows STATISTICALLY SIGNIFICANT OUTPERFORMANCE vs SPY")
            print("This suggests the strategy may have a genuine edge.")
        else:
            print("Buy-and-hold shows STATISTICALLY SIGNIFICANT UNDERPERFORMANCE vs SPY")
            print("This suggests the strategy may be inferior to the benchmark.")
    else:
        print("Buy-and-hold shows NO STATISTICALLY SIGNIFICANT EDGE vs SPY")
        print("The strategy's performance is not meaningfully different from random stock selection.")
        print(f"Transaction costs ({tester.transaction_cost_pct:.1%}) may be eroding any potential edge.")


if __name__ == "__main__":
    main()