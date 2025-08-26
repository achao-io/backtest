#!/usr/bin/env python3
"""
Test ELAB price impact after warrant news on 2025-08-25 at 4:00 PM ET.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from polygon import RESTClient
from polygon.rest.models import Agg

# Load environment variables
load_dotenv()

def test_elab_price_impact():
    """Test ELAB price action after warrant news at 4:00 PM ET."""
    
    secret_key = os.getenv('POLYGON_SECRET_KEY')
    if not secret_key:
        print("❌ Error: POLYGON_SECRET_KEY not found in .env file")
        return
    
    print("📊 Testing ELAB Price Impact Analysis")
    print("=" * 50)
    print("News Event: $1.67M warrant inducement")
    print("Time: 2025-08-25 at 21:00:00Z (4:00 PM ET)")
    print("Ticker: ELAB (PMGC Holdings Inc.)")
    
    # Initialize client
    try:
        client = RESTClient(secret_key)
        print("✅ Polygon client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Get ELAB minute data for today INCLUDING after-hours
    print(f"\n📈 Getting ELAB minute data for 2025-08-25 (including after-hours)...")
    
    try:
        # Get minute bars for extended hours (4 AM - 8 PM ET)
        aggs = client.get_aggs(
            ticker="ELAB",
            multiplier=1,
            timespan="minute",
            from_="2025-08-25",
            to="2025-08-26",  # Include next day to capture after-hours
            adjusted=True,
            sort="asc",
            limit=5000
        )
        
        if not aggs or len(aggs) == 0:
            print("❌ No price data found for ELAB on 2025-08-25")
            print("Possible reasons:")
            print("- Weekend/holiday (no trading)")
            print("- Low volume stock (sparse data)")
            print("- Data not yet available")
            return
        
        print(f"✅ Retrieved {len(aggs)} minute bars for ELAB")
        
        # Convert to list and analyze
        bars = list(aggs)
        
        if len(bars) == 0:
            print("❌ No bars in the aggregates data")
            return
        
        print(f"\nExtended hours summary:")
        print(f"First bar: {datetime.fromtimestamp(bars[0].timestamp / 1000)} - ${bars[0].close:.2f}")
        print(f"Last bar:  {datetime.fromtimestamp(bars[-1].timestamp / 1000)} - ${bars[-1].close:.2f}")
        
        # Separate regular hours vs after-hours
        regular_hours = []
        after_hours = []
        
        for bar in bars:
            bar_time = datetime.fromtimestamp(bar.timestamp / 1000)
            # Regular hours: 9:30 AM - 4:00 PM ET (13:30 - 20:00 UTC during EST, 14:30 - 21:00 UTC during EDT)  
            # After hours: 4:00 PM - 8:00 PM ET (21:00 - 01:00 UTC next day during EDT)
            hour_utc = bar_time.hour
            
            if 14 <= hour_utc <= 20:  # Rough regular hours (accounting for DST)
                regular_hours.append(bar)
            else:
                after_hours.append(bar)
        
        print(f"Regular hours bars: {len(regular_hours)}")
        print(f"After hours bars: {len(after_hours)}")
        
        if len(after_hours) > 0:
            print(f"After-hours trading detected!")
            print(f"After-hours range: {datetime.fromtimestamp(after_hours[0].timestamp / 1000)} to {datetime.fromtimestamp(after_hours[-1].timestamp / 1000)}")
        else:
            print(f"No after-hours trading data found")
        
        # Find price action around 4:00 PM ET (21:00 UTC = 4:00 PM ET + 1 hour DST)
        # News timestamp: 2025-08-25T21:00:00Z
        news_time_utc = datetime(2025, 8, 25, 21, 0, 0)  # 4:00 PM ET
        news_timestamp_ms = int(news_time_utc.timestamp() * 1000)
        
        print(f"\n🔍 Analyzing price action around news time...")
        print(f"News broke at: {news_time_utc} UTC (4:00 PM ET)")
        
        # Find bars before and after news
        pre_news_bars = []
        post_news_bars = []
        
        for bar in bars:
            if bar.timestamp < news_timestamp_ms:
                pre_news_bars.append(bar)
            else:
                post_news_bars.append(bar)
        
        if len(pre_news_bars) == 0:
            print("❌ No pre-news data available")
            return
        
        # Analyze pre-news vs post-news
        print(f"\nPre-news bars: {len(pre_news_bars)}")
        print(f"Post-news bars: {len(post_news_bars)}")
        
        # Get price just before news (last 30 minutes)
        recent_pre_news = pre_news_bars[-30:] if len(pre_news_bars) >= 30 else pre_news_bars
        
        if len(recent_pre_news) > 0:
            pre_news_price = recent_pre_news[-1].close
            pre_news_volume = sum(bar.volume for bar in recent_pre_news)
            pre_news_high = max(bar.high for bar in recent_pre_news)
            pre_news_low = min(bar.low for bar in recent_pre_news)
            
            print(f"\n📊 PRE-NEWS (30 min before):")
            print(f"Price: ${pre_news_price:.2f}")
            print(f"Range: ${pre_news_low:.2f} - ${pre_news_high:.2f}")
            print(f"Volume: {pre_news_volume:,}")
        
        # Get price after news (specifically look at after-hours)
        if len(post_news_bars) > 0:
            recent_post_news = post_news_bars[:60] if len(post_news_bars) >= 60 else post_news_bars  # Look at more bars for after-hours
            
            post_news_price = recent_post_news[-1].close
            post_news_volume = sum(bar.volume for bar in recent_post_news)
            post_news_high = max(bar.high for bar in recent_post_news)
            post_news_low = min(bar.low for bar in recent_post_news)
            
            print(f"\n📊 POST-NEWS (after 4:00 PM ET):")
            print(f"Price: ${post_news_price:.2f}")
            print(f"Range: ${post_news_low:.2f} - ${post_news_high:.2f}")
            print(f"Volume: {post_news_volume:,}")
            print(f"Time span: {len(recent_post_news)} minutes")
            
            # Calculate impact
            price_change = post_news_price - pre_news_price
            price_change_pct = (price_change / pre_news_price) * 100
            volume_change_pct = ((post_news_volume - pre_news_volume) / pre_news_volume) * 100 if pre_news_volume > 0 else 0
            
            print(f"\n🎯 AFTER-HOURS IMPACT ANALYSIS:")
            print(f"Price change: ${price_change:+.2f} ({price_change_pct:+.1f}%)")
            print(f"Volume change: {volume_change_pct:+.1f}%")
            
            # Determine if this validates the hypothesis
            if price_change_pct < -5:
                print(f"✅ HYPOTHESIS VALIDATED: Stock dropped >5% in after-hours after warrant news")
            elif price_change_pct < -2:
                print(f"⚠️  MODERATE DROP: Stock dropped >2% in after-hours after warrant news")
            elif price_change_pct < 0:
                print(f"📉 MINOR DROP: Stock declined in after-hours after warrant news")
            else:
                print(f"❌ HYPOTHESIS NOT SUPPORTED: Stock rose in after-hours after warrant news")
                
            # Check if there was any after-hours trading at all
            after_hours_post_news = [bar for bar in recent_post_news if datetime.fromtimestamp(bar.timestamp / 1000).hour >= 21]
            if len(after_hours_post_news) > 0:
                print(f"\n🌙 AFTER-HOURS ACTIVITY:")
                print(f"After-hours bars: {len(after_hours_post_news)}")
                ah_volume = sum(bar.volume for bar in after_hours_post_news)
                print(f"After-hours volume: {ah_volume:,}")
                if ah_volume > 0:
                    ah_first_price = after_hours_post_news[0].open
                    ah_last_price = after_hours_post_news[-1].close
                    ah_change_pct = ((ah_last_price - ah_first_price) / ah_first_price) * 100
                    print(f"After-hours price change: {ah_change_pct:+.1f}% (${ah_first_price:.2f} → ${ah_last_price:.2f})")
            else:
                print(f"\n🌙 No after-hours trading activity detected")
        else:
            print(f"\n❌ No post-news data available")
        
        # Show detailed minute-by-minute data around news time
        print(f"\n🕐 MINUTE-BY-MINUTE ANALYSIS:")
        print(f"{'Time (UTC)':<20} {'Price':<8} {'Volume':<10} {'Change':<8}")
        print("-" * 50)
        
        # Show last 10 bars before news and first 10 after
        relevant_bars = pre_news_bars[-10:] + post_news_bars[:10]
        
        for i, bar in enumerate(relevant_bars):
            bar_time = datetime.fromtimestamp(bar.timestamp / 1000)
            marker = " 🚨 NEWS" if bar.timestamp >= news_timestamp_ms and i == len(pre_news_bars) else ""
            
            if i > 0:
                prev_price = relevant_bars[i-1].close
                change_pct = ((bar.close - prev_price) / prev_price) * 100
                change_str = f"{change_pct:+.1f}%"
            else:
                change_str = "—"
            
            print(f"{bar_time.strftime('%H:%M:%S'):<20} ${bar.close:<7.2f} {bar.volume:<9,} {change_str:<8} {marker}")
            
    except Exception as e:
        print(f"❌ Failed to get price data: {e}")
        print(f"Error details: {type(e).__name__}")


if __name__ == "__main__":
    test_elab_price_impact()