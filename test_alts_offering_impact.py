#!/usr/bin/env python3
"""
Test ALTS price impact after offering news on 2025-08-11 at 7:00 AM ET.
This should show a clear market reaction during regular trading hours.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from polygon import RESTClient

# Load environment variables
load_dotenv()

def test_alts_offering_impact():
    """Test ALTS price action after offering news at 7:00 AM ET on 2025-08-11."""
    
    secret_key = os.getenv('POLYGON_SECRET_KEY')
    if not secret_key:
        print("❌ Error: POLYGON_SECRET_KEY not found in .env file")
        return
    
    print("📊 Testing ALTS Offering Impact Analysis")
    print("=" * 55)
    print("News Event: Offering announcement")
    print("Date: August 11, 2025")
    print("Time: 7:00 AM ET (11:00 UTC)")
    print("Source: Benzinga")
    print("Ticker: ALTS")
    
    # Initialize client
    try:
        client = RESTClient(secret_key)
        print("✅ Polygon client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Get ALTS minute data for 2025-08-11
    print("\n📈 Getting ALTS minute data for 2025-08-11...")
    
    try:
        # Get minute bars for the entire trading day
        aggs = client.get_aggs(
            ticker="ALTS",
            multiplier=1,
            timespan="minute",
            from_="2025-08-11",
            to="2025-08-11",
            adjusted=True,
            sort="asc",
            limit=5000
        )
        
        if not aggs or len(aggs) == 0:
            print("❌ No price data found for ALTS on 2025-08-11")
            print("Possible reasons:")
            print("- No trading activity that day")
            print("- Ticker symbol incorrect")
            print("- Data not available")
            return
        
        print(f"✅ Retrieved {len(aggs)} minute bars for ALTS")
        
        # Convert to list and analyze
        bars = list(aggs)
        
        print("\nTrading session summary:")
        print(f"First bar: {datetime.fromtimestamp(bars[0].timestamp / 1000)} - Open: ${bars[0].open:.2f}, Close: ${bars[0].close:.2f}")
        print(f"Last bar:  {datetime.fromtimestamp(bars[-1].timestamp / 1000)} - Open: ${bars[-1].open:.2f}, Close: ${bars[-1].close:.2f}")
        
        # Calculate session performance
        session_start_price = bars[0].open
        session_end_price = bars[-1].close
        session_change = session_end_price - session_start_price
        session_change_pct = (session_change / session_start_price) * 100
        
        total_volume = sum(bar.volume for bar in bars)
        session_high = max(bar.high for bar in bars)
        session_low = min(bar.low for bar in bars)
        
        print("\nSession Performance:")
        print(f"Open: ${session_start_price:.2f}")
        print(f"High: ${session_high:.2f}")
        print(f"Low: ${session_low:.2f}")
        print(f"Close: ${session_end_price:.2f}")
        print(f"Change: ${session_change:+.2f} ({session_change_pct:+.1f}%)")
        print(f"Volume: {total_volume:,}")
        
        # News broke at 7:00 AM ET = 11:00 UTC
        # Market opens at 9:30 AM ET = 13:30 UTC
        news_time_utc = datetime(2025, 8, 11, 11, 0, 0)  # 7:00 AM ET
        market_open_utc = datetime(2025, 8, 11, 13, 30, 0)  # 9:30 AM ET
        
        print("\n🔍 Key Timestamps:")
        print(f"News broke: {news_time_utc} (7:00 AM ET)")
        print(f"Market open: {market_open_utc} (9:30 AM ET)")
        print("Gap between news and market open: 2.5 hours")
        
        # Check for pre-market activity (between 7:00 AM and 9:30 AM ET)
        premarket_bars = []
        regular_hours_bars = []
        
        for bar in bars:
            bar_time = datetime.fromtimestamp(bar.timestamp / 1000)
            if bar_time < market_open_utc:
                premarket_bars.append(bar)
            else:
                regular_hours_bars.append(bar)
        
        print("\n📊 Trading Hours Breakdown:")
        print(f"Pre-market bars (before 9:30 AM ET): {len(premarket_bars)}")
        print(f"Regular hours bars (9:30 AM+ ET): {len(regular_hours_bars)}")
        
        if len(premarket_bars) > 0:
            print("\n🌅 PRE-MARKET ACTIVITY (7:00 AM - 9:30 AM ET):")
            pm_first = premarket_bars[0]
            pm_last = premarket_bars[-1]
            pm_volume = sum(bar.volume for bar in premarket_bars)
            pm_change_pct = ((pm_last.close - pm_first.open) / pm_first.open) * 100
            
            print(f"Pre-market range: {datetime.fromtimestamp(pm_first.timestamp / 1000)} to {datetime.fromtimestamp(pm_last.timestamp / 1000)}")
            print(f"Pre-market change: ${pm_first.open:.2f} → ${pm_last.close:.2f} ({pm_change_pct:+.1f}%)")
            print(f"Pre-market volume: {pm_volume:,}")
            
            if pm_change_pct < -5:
                print("✅ STRONG PRE-MARKET REACTION: >5% decline before market open")
            elif pm_change_pct < -2:
                print("⚠️  MODERATE PRE-MARKET REACTION: >2% decline")
            elif pm_change_pct < 0:
                print("📉 MINOR PRE-MARKET DECLINE")
            else:
                print("📈 PRE-MARKET RISE (unexpected for offering news)")
        else:
            print("\n🌅 No pre-market activity detected")
        
        if len(regular_hours_bars) > 0:
            print("\n🏛️ REGULAR HOURS ACTIVITY (9:30 AM+ ET):")
            rh_first = regular_hours_bars[0]
            rh_volume = sum(bar.volume for bar in regular_hours_bars[:30])  # First 30 minutes
            
            # Check for gap at open
            if len(premarket_bars) > 0:
                gap_amount = rh_first.open - premarket_bars[-1].close
                gap_pct = (gap_amount / premarket_bars[-1].close) * 100
                print(f"Gap at open: ${gap_amount:+.2f} ({gap_pct:+.1f}%)")
            
            print(f"Opening price: ${rh_first.open:.2f}")
            print(f"First 30 min volume: {rh_volume:,}")
            
            # Show first hour of trading (first 60 minutes)
            first_hour = regular_hours_bars[:60] if len(regular_hours_bars) >= 60 else regular_hours_bars
            if len(first_hour) > 0:
                fh_high = max(bar.high for bar in first_hour)
                fh_low = min(bar.low for bar in first_hour)
                fh_volume = sum(bar.volume for bar in first_hour)
                fh_change_pct = ((first_hour[-1].close - first_hour[0].open) / first_hour[0].open) * 100
                
                print("\nFirst hour of trading:")
                print(f"Range: ${fh_low:.2f} - ${fh_high:.2f}")
                print(f"Change: {fh_change_pct:+.1f}%")
                print(f"Volume: {fh_volume:,}")
        
        # Show detailed timeline around market open
        print("\n🕐 DETAILED TIMELINE (Market Open Period):")
        print(f"{'Time (ET)':<12} {'Open':<7} {'High':<7} {'Low':<7} {'Close':<7} {'Volume':<8} {'Change'}")
        print("-" * 70)
        
        # Show last few pre-market bars and first few regular hours bars
        timeline_bars = premarket_bars[-3:] + regular_hours_bars[:10]
        
        for i, bar in enumerate(timeline_bars):
            bar_time = datetime.fromtimestamp(bar.timestamp / 1000)
            # Convert UTC to ET (subtract 4 hours during EDT)
            et_time = bar_time.replace(hour=bar_time.hour - 4)
            
            if i > 0:
                prev_price = timeline_bars[i-1].close
                change_pct = ((bar.close - prev_price) / prev_price) * 100
                change_str = f"{change_pct:+.1f}%"
            else:
                change_str = "—"
            
            marker = "🔔 OPEN" if bar in regular_hours_bars[:1] else ""
            
            print(f"{et_time.strftime('%H:%M'):<12} ${bar.open:<6.2f} ${bar.high:<6.2f} ${bar.low:<6.2f} ${bar.close:<6.2f} {bar.volume:<8,} {change_str:<7} {marker}")
        
        # Final assessment
        print("\n🎯 OFFERING NEWS IMPACT ASSESSMENT:")
        
        overall_negative = session_change_pct < 0
        significant_drop = session_change_pct < -5
        moderate_drop = session_change_pct < -2
        
        if significant_drop:
            print("✅ HYPOTHESIS STRONGLY VALIDATED")
            print(f"ALTS dropped {session_change_pct:.1f}% on offering news - significant negative reaction")
        elif moderate_drop:
            print("⚠️  HYPOTHESIS MODERATELY SUPPORTED") 
            print(f"ALTS dropped {session_change_pct:.1f}% on offering news - moderate negative reaction")
        elif overall_negative:
            print("📉 HYPOTHESIS PARTIALLY SUPPORTED")
            print(f"ALTS declined {session_change_pct:.1f}% on offering news - minor negative reaction")
        else:
            print("❌ HYPOTHESIS NOT SUPPORTED")
            print(f"ALTS rose {session_change_pct:.1f}% despite offering news")
        
        print("\nKey Metrics:")
        print(f"• Session change: {session_change_pct:+.1f}%")
        print(f"• Total volume: {total_volume:,}")
        print(f"• Intraday range: {((session_high - session_low) / session_start_price) * 100:.1f}% volatility")
        
    except Exception as e:
        print(f"❌ Failed to get price data: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_alts_offering_impact()