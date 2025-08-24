#!/usr/bin/env python3
"""
Simple test to verify we can retrieve news data from Polygon.io News API using the Python SDK.
"""

import os
from dotenv import load_dotenv
from polygon import RESTClient
from polygon.rest.models import TickerNews

# Load environment variables
load_dotenv()

def test_polygon_news_sdk():
    """Test basic connectivity to Polygon News API using official SDK."""
    
    secret_key = os.getenv('POLYGON_SECRET_KEY')
    print("🔧 Testing Polygon News API using Python SDK...")
    
    # Initialize client
    try:
        client = RESTClient(secret_key)
        print("✅ SDK client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Test 1: Get general recent news
    print("\n📰 Test 1: Getting recent general news...")
    
    try:
        news = []
        count = 0
        for n in client.list_ticker_news(
            order="desc",
            limit=100,
            sort="published_utc"
        ):
            news.append(n)
            count += 1
            if count >= 100:  # Limit to first 10
                break
        
        print(f"✅ Success! Retrieved {len(news)} articles")
        
        # Display results similar to your example
        print(f"\n{'Date':<25}{'Title':<50}")
        print("-" * 75)
        
        for item in news:
            if isinstance(item, TickerNews):
                title = item.title[:47] + "..." if len(item.title) > 50 else item.title
                print(f"{str(item.published_utc):<25}{title:<50}")
        
    except Exception as e:
        print(f"❌ Failed to get general news: {e}")
        return
    
    # Test 2: Get news for a specific ticker (AAPL)
    print("\n📰 Test 2: Getting AAPL-specific news...")
    
    try:
        aapl_news = []
        count = 0
        for n in client.list_ticker_news(
            ticker="AAPL",
            order="desc", 
            limit=5,
            sort="published_utc"
        ):
            aapl_news.append(n)
            count += 1
            if count >= 5:
                break
        
        print(f"✅ Success! Retrieved {len(aapl_news)} AAPL articles")
        
        for item in aapl_news:
            if isinstance(item, TickerNews):
                print(f"  • {item.published_utc}: {item.title[:60]}...")
                if hasattr(item, 'publisher') and item.publisher:
                    print(f"    Publisher: {item.publisher.name}")
                if hasattr(item, 'tickers') and item.tickers:
                    print(f"    Tickers: {', '.join(item.tickers[:5])}")
                print()
        
    except Exception as e:
        print(f"❌ Failed to get AAPL news: {e}")
    
    # Test 3: Search for dilution-related keywords in recent news
    print("\n📰 Test 3: Scanning recent news for dilution keywords...")
    
    dilution_keywords = [
        "warrant", "warrants",
        "shelf offering", "shelf registration", 
        "dilution", "dilutive",
        "direct offering",
        "ATM offering"
    ]
    
    try:
        # Get more news to scan
        all_news = []
        count = 0
        for n in client.list_ticker_news(
            order="desc",
            limit=100,  # Get more articles to scan
            sort="published_utc"
        ):
            all_news.append(n)
            count += 1
            if count >= 100:
                break
        
        print(f"Scanning {len(all_news)} articles for dilution keywords...")
        
        matching_articles = []
        for item in all_news:
            if isinstance(item, TickerNews):
                title_lower = item.title.lower()
                description_lower = getattr(item, 'description', '').lower()
                
                # Check if any dilution keyword is present
                for keyword in dilution_keywords:
                    if keyword.lower() in title_lower or keyword.lower() in description_lower:
                        matching_articles.append((item, keyword))
                        break
        
        if matching_articles:
            print(f"✅ Found {len(matching_articles)} articles with dilution keywords!")
            
            for item, keyword in matching_articles[:5]:  # Show first 5
                print("\n🚨 Dilution Event Detected:")
                print(f"  Keyword: '{keyword}'")
                print(f"  Date: {item.published_utc}")
                print(f"  Title: {item.title}")
                if hasattr(item, 'tickers') and item.tickers:
                    print(f"  Tickers: {', '.join(item.tickers)}")
                if hasattr(item, 'publisher') and item.publisher:
                    print(f"  Publisher: {item.publisher.name}")
        else:
            print("❌ No articles found with dilution keywords in recent news")
        
    except Exception as e:
        print(f"❌ Failed to scan for dilution keywords: {e}")
    
    print("\n✅ Polygon News SDK test completed!")
    print("\nNext steps:")
    print("1. ✅ Confirmed SDK connectivity works")
    print("2. Build automated dilution event scanner")
    print("3. Link news events to price data")
    print("4. Test news-to-price correlation analysis")


if __name__ == "__main__":
    test_polygon_news_sdk()